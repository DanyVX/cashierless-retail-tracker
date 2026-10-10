"""Synthetic-only deterministic tracker lifecycle and color scene tests."""

import cv2
import numpy as np
import pytest

from crt.detect import ColorMarkerDetector, Detection, OpenCVHOGDetector
from crt.track import Tracker


def det(x: int, score: float = 0.9) -> Detection:
    return Detection(float(x), 10, float(x + 15), 35, score)


def test_detector_invalid_boxes() -> None:
    with pytest.raises(ValueError):
        Detection(1, 2, 1, 4, 0.9)
    with pytest.raises(ValueError):
        Detection(1, 2, 4, 4, 1.5)


def test_marker_detector_finds_rectangles() -> None:
    frame = np.zeros((80, 140, 3), dtype=np.uint8)
    cv2.rectangle(frame, (10, 10), (30, 50), (230, 40, 40), -1)
    cv2.rectangle(frame, (70, 10), (95, 50), (230, 40, 40), -1)
    found = ColorMarkerDetector().detect(frame)
    assert len(found) == 2
    assert found[0].center[0] < found[1].center[0]


def test_stable_tracks_under_motion_and_two_stage_matching() -> None:
    tracker = Tracker(min_hits=2)
    assert tracker.update([det(10)], 0) == []
    first = tracker.update([det(12)], 0.1)
    assert len(first) == 1
    track_id = first[0].track_id
    recovered = tracker.update([det(14, 0.4)], 0.2)
    assert recovered[0].track_id == track_id
    assert tracker.update([det(17)], 0.3)[0].track_id == track_id


def test_lost_removed_and_new_session() -> None:
    tracker = Tracker(max_age=1, min_hits=1)
    first = tracker.update([det(15)], 0.0)[0].track_id
    assert tracker.update([], 0.1) == []
    assert tracker.update([], 0.2) == []
    second = tracker.update([det(15)], 0.3)[0].track_id
    assert second != first


def test_crossing_people_graceful_degradation() -> None:
    tracker = Tracker(min_hits=1, max_distance=40)
    assert len(tracker.update([det(5), det(100)], 0.0)) == 2
    assert len(tracker.update([det(20), det(85)], 0.1)) == 2
    assert len(tracker.update([det(40), det(65)], 0.2)) == 2


def test_source_gap_requires_explicit_reset() -> None:
    tracker = Tracker(min_hits=1)
    first = tracker.update([det(5)], 1.0)[0].track_id
    with pytest.raises(ValueError):
        tracker.update([det(5)], 1.0)
    tracker.reset()
    second = tracker.update([det(5)], 0.0)[0].track_id
    assert first != second


def test_hog_does_not_fail_on_tiny_or_empty_scene() -> None:
    backend = OpenCVHOGDetector()
    assert backend.detect(np.zeros((20, 20, 3), dtype=np.uint8)) == []


def test_invalid_tracker_parameters() -> None:
    with pytest.raises(ValueError):
        Tracker(high_threshold=0.1, low_threshold=0.9)
    with pytest.raises(ValueError):
        Tracker(max_age=0)
