"""Mock products are solid color squares; no general SKU recognition claim."""

import cv2
import numpy as np
import pytest

from crt.shelf import ColorSKU, ShelfReader
from crt.zones import ShelfZone, ZoneMap


def reader() -> ShelfReader:
    z = ShelfZone("shelf", "red", ((0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)))
    return ShelfReader(
        ZoneMap([z]), [ColorSKU("red", (20, 20, 245)), ColorSKU("green", (20, 220, 20))]
    )


def image(red: int = 0, green: int = 0) -> np.ndarray:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(red):
        cv2.rectangle(frame, (15 + i * 13, 20), (23 + i * 13, 29), (20, 20, 245), -1)
    for i in range(green):
        cv2.rectangle(frame, (15 + i * 13, 45), (23 + i * 13, 54), (20, 220, 20), -1)
    return frame


def test_pick_return_and_no_motion_false_cart() -> None:
    r = reader()
    initial = r.snapshot(image(red=2, green=1), "shelf")
    after = r.snapshot(image(red=1, green=1), "shelf")
    changes = r.compare(initial, after)
    assert len(changes) == 1
    assert changes[0].sku == "red"
    assert changes[0].quantity_delta == -1
    assert r.compare(after, initial)[0].quantity_delta == 1
    assert r.compare(initial, r.snapshot(image(red=2, green=1), "shelf")) == []


def test_simultaneous_multi_item_and_unknown() -> None:
    r = reader()
    initial = r.snapshot(image(red=2, green=1), "shelf")
    after = r.snapshot(image(), "shelf")
    assert {(x.sku, x.quantity_delta) for x in r.compare(initial, after)} == {
        ("red", -2),
        ("green", -1),
    }
    alien = image()
    alien[20:40, 20:40] = (150, 150, 150)
    assert any(c.unknown for c in r.compare(after, r.snapshot(alien, "shelf")))


def test_reject_wrong_zone_and_sku() -> None:
    r = reader()
    with pytest.raises(ValueError):
        r.compare(r.snapshot(image(), "shelf"), type(r.snapshot(image(), "shelf"))("other", {}, 0))
    with pytest.raises(ValueError):
        ColorSKU("", (1, 2, 3))


def test_zone_normalization_and_background() -> None:
    r = reader()
    assert r.snapshot(image(), "shelf").counts == {"red": 0, "green": 0}
