"""Generated mock-shelf scenarios with reference labels, no people or real video."""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from crt.environment import environment_snapshot
from crt.io import Frame
from crt.pipeline import ShelfPipeline
from crt.shelf import ColorSKU, ShelfReader
from crt.zones import ShelfZone, ZoneMap
from eval.metrics import EventLabel, cart_metrics, event_metrics

SCENARIOS = (
    "single_shopper",
    "hover",
    "multi_item",
    "pick_return",
    "two_shoppers",
    "staff_restock",
    "occlusion",
    "low_light",
    "fast_shopper",
)


def make_shelf() -> ShelfReader:
    return ShelfReader(
        ZoneMap([ShelfZone("A", "chips", ((0.48, 0.1), (0.95, 0.1), (0.95, 0.85), (0.48, 0.85)))]),
        [ColorSKU("chips", (20, 20, 245))],
    )


def build_image(*, count: int, wrist: bool, two: bool = False, low: bool = False) -> np.ndarray:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    cv2.rectangle(image, (60, 15), (90, 85), (230, 40, 40), -1)
    if two:
        cv2.rectangle(image, (8, 10), (36, 80), (230, 40, 40), -1)
    for i in range(count):
        cv2.rectangle(image, (125 + i * 17, 30), (136 + i * 17, 41), (20, 20, 245), -1)
    if wrist:
        cv2.rectangle(image, (111, 60), (116, 65), (255, 0, 255), -1)
    if low:
        image = (image.astype(float) * 0.2).astype(np.uint8)
    return image


def evaluate_one(name: str) -> dict[str, object]:
    pipe = ShelfPipeline(make_shelf())
    two = name == "two_shoppers"
    low = name == "low_light"
    # Deliberately tiny scenes; controls force expected failures and reveal limits.
    take = name not in ("hover", "staff_restock")
    amount = 2 if name == "multi_item" else 1
    times = (0.0, 0.1, 0.2, 0.3, 0.55)
    if name == "fast_shopper":
        times = (0.0, 0.05, 0.08, 0.09, 0.12)
    counts = [3, 3, 3, 3 - amount if take else 3, 3 - amount if take else 3]
    observations: list[EventLabel] = []
    started = time.perf_counter()
    for i, (stamp, count) in enumerate(zip(times, counts, strict=True)):
        image = build_image(count=count, wrist=i in (2, 3), two=two, low=low)
        if name == "occlusion" and i == 3:
            image[60:90, 100:125] = 0
        frame = Frame(i, stamp, image, "pts", stamp)
        output = pipe.process(frame)
        if output:
            for event in output.events:
                if event.kind in ("PICK", "RETURN") and event.sku is not None:
                    observations.append(
                        EventLabel(event.timestamp_seconds, event.kind, event.sku, event.quantity)
                    )
    measured = time.perf_counter() - started
    truth = [EventLabel(times[-1], "PICK", "chips", amount)] if take else []
    metrics = event_metrics(truth, observations, tolerance=0.25)
    expected_cart = {"chips": amount} if take else {}
    carts = [dict(v) for v in pipe.cart.carts.values()]
    actual_cart = carts[0] if len(carts) == 1 else {}
    return {
        "scenario": name,
        "frames": len(times),
        "events": metrics,
        "cart": cart_metrics([expected_cart], [actual_cart]),
        "observed_event_count": len(observations),
        "wall_seconds": measured,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate generated colored mock shelf")
    parser.add_argument("--out", type=Path, default=Path("results/synthetic_eval.json"))
    args = parser.parse_args()
    scenarios = [evaluate_one(name) for name in SCENARIOS]
    output = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "scope": "synthetic-color-marker-toy-test-only",
        "environment": environment_snapshot(),
        "scenarios": scenarios,
        "limitations": "No real people, camera, pretrained SKU model or human annotations",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scenarios_run": len(scenarios), "output": str(args.out)}))


if __name__ == "__main__":
    main()
