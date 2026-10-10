"""Generate deterministic synthetic-only annotated scene and event JSON."""

import argparse
import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from crt.io import Frame
from crt.pipeline import ShelfPipeline
from crt.privacy.redact import FaceRedactor, require_synthetic_media
from crt.shelf import ColorSKU, ShelfReader
from crt.viz import render_overlay
from crt.zones import ShelfZone, ZoneMap


def demo(out: Path, *, make_gif: bool = True) -> dict[str, object]:
    require_synthetic_media(source_is_synthetic=True)
    zone = ZoneMap([ShelfZone("A", "chips", ((0.48, 0.1), (0.95, 0.1),
                                               (0.95, 0.85), (0.48, 0.85)))])
    shelf = ShelfReader(zone, [ColorSKU("chips", (20, 20, 245))])
    engine = ShelfPipeline(shelf)
    redactor = FaceRedactor()
    all_events: list[dict[str, object]] = []
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        video = Path(tmp) / "synthetic.avi"
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"),
                                 10.0, (400, 240))
        if not writer.isOpened():
            raise RuntimeError("Synthetic video writer unavailable")
        try:
            for i in range(20):
                frame = np.zeros((120, 200, 3), dtype=np.uint8)
                cv2.rectangle(frame, (60, 15), (90, 85), (230, 40, 40), -1)
                count = 2 if i < 9 else 1
                for j in range(count):
                    cv2.rectangle(frame, (125 + j * 17, 30), (136 + j * 17, 41),
                                  (20, 20, 245), -1)
                if 5 <= i <= 9:
                    cv2.rectangle(frame, (111, 60), (116, 65), (255, 0, 255), -1)
                packet = Frame(i, i / 10, frame, "pts", i / 10)
                result = engine.process(packet)
                if result is None:
                    continue
                all_events.extend(asdict(event) for event in result.events)
                blurred, _ = redactor.redact(frame)
                overlay = render_overlay(blurred, result, zone, engine.cart.carts)
                writer.write(cv2.resize(overlay, (400, 240)))
        finally:
            writer.release()
        if make_gif:
            executable = shutil.which("ffmpeg")
            if executable is None:
                raise RuntimeError("ffmpeg required for GIF; run with --no-gif for JSON")
            command = [executable, "-loglevel", "error", "-y", "-i", str(video),
                       "-vf", "fps=5,scale=400:-1:flags=lanczos", str(out / "synthetic.gif")]
            subprocess.run(command, check=True, timeout=30)
    payload = {
        "scope": "fully synthetic scenes, not real humans",
        "events": all_events,
        "carts": engine.cart.carts,
        "limitations": "Colored marker demonstration is not real shopper/product recognition",
    }
    (out / "events.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results/demo"))
    parser.add_argument("--no-gif", action="store_true")
    args = parser.parse_args()
    result = demo(args.out, make_gif=not args.no_gif)
    print(json.dumps({"event_count": len(result["events"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
