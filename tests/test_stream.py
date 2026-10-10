"""Deterministic fake capture and real synthetic-video integration tests."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from crt.io import Frame, FrameStream, TimelineGap, VideoSourceError
from crt.privacy import PrivacyViolation


def synthetic_stream(*args, **kwargs):
    return FrameStream(*args, synthetic=True, **kwargs)


class FakeCapture:
    def __init__(self, values: list[tuple[bool, float | None]], fps: float = 10, count: int = 0):
        self.values = values
        self.fps = fps
        self.count = count
        self.i = 0
        self.pts_ms = 0.0
        self.released = False

    def isOpened(self) -> bool:
        return True

    def read(self):
        if self.i >= len(self.values):
            return False, None
        ok, ts = self.values[self.i]
        self.i += 1
        self.pts_ms = ts if ts is not None else float("nan")
        return ok, (np.zeros((8, 16, 3), dtype=np.uint8) if ok else None)

    def get(self, prop: int) -> float:
        if prop == cv2.CAP_PROP_POS_MSEC:
            return self.pts_ms
        if prop == cv2.CAP_PROP_FPS:
            return self.fps
        if prop == cv2.CAP_PROP_FRAME_COUNT:
            return self.count
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        return True

    def release(self) -> None:
        self.released = True


def test_variable_pts_preserved_and_possible_drop_marked() -> None:
    cap = FakeCapture([(True, 0), (True, 80), (True, 180), (True, 600)], fps=10)
    packets = list(synthetic_stream("unused", capture_factory=lambda _: cap))
    frames = [p for p in packets if isinstance(p, Frame)]
    gaps = [p for p in packets if isinstance(p, TimelineGap)]
    assert [round(f.timestamp_seconds, 2) for f in frames] == [0, 0.08, 0.18, 0.6]
    assert [g.reason for g in gaps] == ["timestamp_jump"]
    assert gaps[0].estimated_missing_frames == 3
    assert cap.released


def test_nonmonotonic_pts_is_marked_and_clamped() -> None:
    cap = FakeCapture([(True, 0), (True, 100), (True, 60), (True, 300)], fps=10)
    packets = list(synthetic_stream("unused", capture_factory=lambda _: cap))
    frames = [p for p in packets if isinstance(p, Frame)]
    assert frames[2].timestamp_seconds == pytest.approx(0.2)
    assert any(isinstance(p, TimelineGap) and p.reason == "timestamp_regression" for p in packets)


def test_fps_fallback_when_pts_missing() -> None:
    cap = FakeCapture([(True, None), (True, None)], fps=20)
    packets = list(synthetic_stream("unused", capture_factory=lambda _: cap))
    frames = [p for p in packets if isinstance(p, Frame)]
    assert frames[1].timestamp_seconds == pytest.approx(0.05)
    assert frames[1].timestamp_source == "fps_fallback"


def test_early_corrupt_decode_emits_gap_and_recovers() -> None:
    cap = FakeCapture([(True, 0), (False, None), (True, 200)], fps=10, count=3)
    packets = list(synthetic_stream("unused", capture_factory=lambda _: cap))
    assert sum(isinstance(p, Frame) for p in packets) == 2
    assert any(isinstance(p, TimelineGap) and p.reason == "decode_error" for p in packets)


def test_live_disconnect_reopens_without_silent_continuity() -> None:
    captures = [FakeCapture([(True, 10), (False, None)]), FakeCapture([(True, 10), (False, None)])]
    delays = []
    tick = iter([0.0, 0.1, 0.2, 0.3])

    def get_capture(_):
        return captures.pop(0)

    with pytest.raises(VideoSourceError, match="reconnect"):
        list(
            synthetic_stream(
                "rtsp://private.example/stream",
                mode="live",
                max_reconnects=1,
                capture_factory=get_capture,
                sleeper=delays.append,
                clock=lambda: next(tick),
            )
        )
    assert delays == [0.25]


def test_input_validation() -> None:
    for kwargs in ({"width": 0}, {"fps_fallback": -1}, {"jump_factor": 1}, {"max_reconnects": -1}):
        with pytest.raises(ValueError):
            synthetic_stream("unused", **kwargs)


def test_resize_and_mirror_without_storing_frames() -> None:
    cap = FakeCapture([(True, 0)], fps=10)
    packets = list(
        synthetic_stream(Path("synthetic.mp4"), width=8, mirror=True, capture_factory=lambda _: cap)
    )
    frame = next(p for p in packets if isinstance(p, Frame))
    assert frame.image.shape == (4, 8, 3)


def test_real_synthetic_video_decodes_offline(tmp_path: Path) -> None:
    video = tmp_path / "synthetic.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 24))
    if not writer.isOpened():
        pytest.skip("MJPG writer unavailable on this OpenCV build")
    for i in range(5):
        writer.write(np.full((24, 32, 3), i * 20, dtype=np.uint8))
    writer.release()
    packets = list(synthetic_stream(video, fps_fallback=10))
    frames = [p for p in packets if isinstance(p, Frame)]
    assert len(frames) == 5
    assert frames[-1].index == 4
    assert all(frames[i].timestamp_seconds < frames[i + 1].timestamp_seconds for i in range(4))


def test_live_and_offline_sources_require_consent() -> None:
    cap = FakeCapture([(True, 0)], fps=10)
    with pytest.raises(PrivacyViolation, match="consent"):
        list(FrameStream("rtsp://invalid", mode="live", capture_factory=lambda _: cap))
    with pytest.raises(PrivacyViolation, match="consent"):
        list(FrameStream("private.mp4", capture_factory=lambda _: cap))
    assert cap.i == 0
