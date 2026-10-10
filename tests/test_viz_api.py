import numpy as np
import pytest

from crt.api.events import EventBuffer
from crt.events import CartEvent
from crt.pipeline import PipelineOutput
from crt.viz import render_overlay
from crt.zones import ShelfZone, ZoneMap


def test_api_bounded_buffer_without_frames() -> None:
    buf = EventBuffer(max_items=1)
    sample = CartEvent("PICK", 1, 7, "A", "chips", 1, 1, "applied")
    buf.publish(sample)
    buf.publish(sample)
    assert buf.snapshot()["dropped_events"] == 1
    assert len(buf.snapshot()["events"]) == 1
    with pytest.raises(ValueError):
        EventBuffer(max_items=0)


def test_overlay_does_not_mutate_source() -> None:
    src = np.zeros((100, 200, 3), dtype=np.uint8)
    z = ZoneMap([ShelfZone("A", "chips", ((0.5, 0.1), (0.9, 0.1), (0.9, 0.8)))])
    overlay = render_overlay(src, PipelineOutput(0, (), (), ()), z, {})
    assert overlay.shape == src.shape
    assert np.count_nonzero(overlay) > 0
    assert np.count_nonzero(src) == 0
