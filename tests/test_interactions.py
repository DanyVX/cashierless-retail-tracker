import numpy as np
import pytest

from crt.events.interactions import InteractionDetector
from crt.pose import MarkerWristDetector, Wrist
from crt.track import TrackSnapshot
from crt.zones import ShelfZone, ZoneMap


def setup_zones() -> ZoneMap:
    return ZoneMap([ShelfZone("A", "chips", ((0.5, 0.2), (0.9, 0.2), (0.9, 0.7), (0.5, 0.7)))])


def person(i: int, left: float = 30) -> TrackSnapshot:
    return TrackSnapshot(i, (left, 10, left + 30, 65), "confirmed", 3, 0.0)


def test_normalized_zone_geometry() -> None:
    zone = setup_zones().by_id("A")
    assert zone.contains(60, 30, 100, 100)
    assert zone.contains(120, 60, 200, 200)
    assert not zone.contains(5, 30, 100, 100)


def test_zone_invalid_and_overlap_ambiguous() -> None:
    with pytest.raises(ValueError):
        ShelfZone("x", "sku", ((0.1, 0.1), (0.1, 0.1), (0.1, 0.1)))
    zone = setup_zones().by_id("A")
    with pytest.raises(ValueError):
        ZoneMap([zone, zone])


def test_dwell_emits_on_leave_not_hover_short() -> None:
    detector = InteractionDetector(setup_zones(), min_dwell_seconds=0.2)
    assert (
        detector.update([Wrist(60, 40)], [person(1)], timestamp_seconds=0, width=100, height=100)
        == []
    )
    assert detector.update([], [person(1)], timestamp_seconds=0.1, width=100, height=100) == []
    detector.update([Wrist(60, 40)], [person(1)], timestamp_seconds=1.0, width=100, height=100)
    changed = detector.update([], [person(1)], timestamp_seconds=1.3, width=100, height=100)
    assert len(changed) == 1
    assert changed[0].track_id == 1


def test_two_people_ambiguous_prevents_attribution() -> None:
    detector = InteractionDetector(setup_zones(), min_dwell_seconds=0)
    detector.update(
        [Wrist(60, 40)], [person(1, 30), person(2, 60)], timestamp_seconds=0, width=100, height=100
    )
    changes = detector.update([], [], timestamp_seconds=0.1, width=100, height=100)
    assert changes[0].track_id is None


def test_staff_excluded() -> None:
    detector = InteractionDetector(
        setup_zones(), min_dwell_seconds=0, staff_track_ids=frozenset({1})
    )
    detector.update([Wrist(60, 40)], [person(1)], timestamp_seconds=0, width=100, height=100)
    assert detector.update([], [], timestamp_seconds=1, width=100, height=100)[0].track_id is None


def test_magenta_wrist_synthetic() -> None:
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    frame[4:8, 6:10] = (255, 0, 255)
    assert len(MarkerWristDetector().detect(frame)) == 1


def test_reset_discards_interaction() -> None:
    detector = InteractionDetector(setup_zones())
    detector.update([Wrist(60, 40)], [person(1)], timestamp_seconds=0, width=100, height=100)
    detector.reset()
    assert detector.update([], [], timestamp_seconds=0, width=100, height=100) == []
