import cv2
import numpy as np
import pytest

from crt.events import CartEngine, Interaction
from crt.io import Frame, TimelineGap
from crt.pipeline import ShelfPipeline
from crt.shelf import ColorSKU, ShelfChange, ShelfReader
from crt.zones import ShelfZone, ZoneMap


def interaction(track: int | None = 1, confidence: float = 1) -> Interaction:
    return Interaction("shelf", track, 0, 0.5, confidence)


def change(delta: int, sku: str = "chips") -> ShelfChange:
    return ShelfChange("shelf", sku, delta, 1)


def test_pick_return_net_zero_and_no_negative() -> None:
    cart = CartEngine()
    assert cart.apply([change(-1)], interaction(), timestamp_seconds=1)[0].status == "applied"
    assert cart.current_cart(1) == {"chips": 1}
    cart.apply([change(1)], interaction(), timestamp_seconds=2)
    assert cart.current_cart(1) == {}
    assert cart.apply([change(1)], interaction(), timestamp_seconds=3)[0].status == "review"
    assert cart.current_cart(1) == {}


def test_duplicate_low_confidence_unattributed_and_order() -> None:
    cart = CartEngine()
    cart.apply([change(-1)], interaction(), timestamp_seconds=1)
    assert cart.apply([change(-1)], interaction(), timestamp_seconds=1.1) == []
    assert (
        cart.apply([change(-2)], interaction(confidence=0.2), timestamp_seconds=2)[0].status
        == "review"
    )
    assert (
        cart.apply([change(-1)], interaction(None), timestamp_seconds=3)[0].status == "unattributed"
    )
    with pytest.raises(ValueError):
        cart.apply([change(-1)], interaction(), timestamp_seconds=2.5)


def test_session_end_clears_and_track_ids_not_merged() -> None:
    cart = CartEngine()
    cart.apply([change(-2)], interaction(), timestamp_seconds=1)
    assert cart.end_session(1, 2).quantity == 2
    assert cart.current_cart(1) == {}
    assert cart.current_cart(2) == {}


def shelf() -> ShelfReader:
    return ShelfReader(
        ZoneMap(
            [ShelfZone("shelf", "chips", ((0.48, 0.1), (0.95, 0.1), (0.95, 0.85), (0.48, 0.85)))]
        ),
        [ColorSKU("chips", (20, 20, 245))],
    )


def frame(t: float, *, count: int, wrist: bool) -> Frame:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    cv2.rectangle(image, (60, 15), (90, 85), (230, 40, 40), -1)
    for i in range(count):
        cv2.rectangle(image, (125 + i * 17, 30), (136 + i * 17, 41), (20, 20, 245), -1)
    if wrist:
        cv2.rectangle(image, (111, 60), (116, 65), (255, 0, 255), -1)
    return Frame(int(t * 10), t, image, "pts", t)


def test_full_synthetic_pipeline_detects_pick() -> None:
    pipe = ShelfPipeline(shelf())
    sequence = [
        frame(0, count=2, wrist=False),
        frame(0.1, count=2, wrist=False),
        frame(0.2, count=2, wrist=True),
        frame(0.3, count=1, wrist=True),
        frame(0.5, count=1, wrist=False),
    ]
    outputs = [pipe.process(f) for f in sequence]
    events = [e for output in outputs if output is not None for e in output.events]
    assert len(events) == 1
    assert events[0].kind == "PICK"
    assert events[0].status == "applied"
    assert pipe.cart.current_cart(events[0].track_id or 0) == {"chips": 1}


def test_timeline_gap_resets_no_fabricated_event() -> None:
    pipe = ShelfPipeline(shelf())
    pipe.process(frame(0, count=2, wrist=False))
    pipe.process(frame(0.1, count=2, wrist=False))
    pipe.process(frame(0.2, count=2, wrist=True))
    assert pipe.process(TimelineGap("disconnect", 2)) is None
    result = pipe.process(frame(0.3, count=1, wrist=False))
    assert result is not None and result.events == ()
