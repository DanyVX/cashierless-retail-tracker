"""Small ByteTrack-inspired two-stage Hungarian tracker with Kalman motion prediction.

Not an implementation of the full ByteTrack paper; HOTA/MOTA/IDF1 not yet measured.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import linear_sum_assignment

from crt.detect import Detection

TrackState = Literal["tentative", "confirmed", "lost", "removed"]


@dataclass(frozen=True)
class TrackSnapshot:
    track_id: int
    bbox: tuple[float, float, float, float]
    state: TrackState
    hits: int
    timestamp_seconds: float


class _Track:
    def __init__(self, track_id: int, detection: Detection, timestamp: float) -> None:
        cx, cy = detection.center
        self.track_id = track_id
        self.x = np.array([cx, cy, 0.0, 0.0], dtype=float)
        self.p = np.diag([8.0, 8.0, 50.0, 50.0])
        self.width, self.height = detection.size
        self.hits = 1
        self.state: TrackState = "tentative"
        self.missed = 0
        self.last_timestamp = timestamp

    def predict(self, dt: float) -> None:
        transition = np.array(
            [[1.0, 0.0, dt, 0.0], [0.0, 1.0, 0.0, dt], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        )
        noise = np.diag([1.0 + dt, 1.0 + dt, 2.0, 2.0])
        self.x = transition @ self.x
        self.p = transition @ self.p @ transition.T + noise

    def update(self, detection: Detection, min_hits: int) -> None:
        h = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0]])
        r = np.eye(2) * 4.0
        innovation = np.array(detection.center) - h @ self.x
        s = h @ self.p @ h.T + r
        gain = self.p @ h.T @ np.linalg.inv(s)
        self.x = self.x + gain @ innovation
        self.p = (np.eye(4) - gain @ h) @ self.p
        self.width, self.height = detection.size
        self.hits += 1
        self.missed = 0
        self.state = "confirmed" if self.hits >= min_hits else "tentative"

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        x, y = self.x[:2]
        return (
            float(x - self.width / 2),
            float(y - self.height / 2),
            float(x + self.width / 2),
            float(y + self.height / 2),
        )

    def snapshot(self) -> TrackSnapshot:
        return TrackSnapshot(self.track_id, self.bbox, self.state, self.hits, self.last_timestamp)


class Tracker:
    """Two-stage high/low-confidence assignment using predicted centers.

    Detections assigned to a lost track are allowed to recover it within max_age.
    A removed track's ID is never reused within this Tracker instance.
    """

    def __init__(
        self,
        *,
        high_threshold: float = 0.6,
        low_threshold: float = 0.1,
        max_distance: float = 55.0,
        min_hits: int = 2,
        max_age: int = 8,
    ) -> None:
        if not 0 <= low_threshold <= high_threshold <= 1:
            raise ValueError("Invalid detection confidence thresholds")
        if max_distance <= 0 or min_hits < 1 or max_age < 1:
            raise ValueError("Invalid lifecycle thresholds")
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.max_distance = max_distance
        self.min_hits = min_hits
        self.max_age = max_age
        self._tracks: list[_Track] = []
        self._next_id = 1
        self._last_timestamp: float | None = None

    def reset(self) -> None:
        """Discontinuity resets motion history, never fabricating identity continuity."""
        self._tracks.clear()
        self._last_timestamp = None

    def _associate(
        self, tracks: list[_Track], detections: list[Detection]
    ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        if not tracks or not detections:
            return [], list(range(len(tracks))), list(range(len(detections)))
        cost = np.empty((len(tracks), len(detections)), dtype=float)
        for i, track in enumerate(tracks):
            for j, det in enumerate(detections):
                cost[i, j] = np.linalg.norm(track.x[:2] - np.array(det.center))
        row, col = linear_sum_assignment(cost)
        matched = [(int(i), int(j)) for i, j in zip(row, col) if cost[i, j] <= self.max_distance]
        used_t = {i for i, _ in matched}
        used_d = {j for _, j in matched}
        return (
            matched,
            [i for i in range(len(tracks)) if i not in used_t],
            [j for j in range(len(detections)) if j not in used_d],
        )

    def update(self, detections: list[Detection], timestamp_seconds: float) -> list[TrackSnapshot]:
        if not np.isfinite(timestamp_seconds) or timestamp_seconds < 0:
            raise ValueError("Timestamp must be finite and nonnegative")
        if self._last_timestamp is not None and timestamp_seconds <= self._last_timestamp:
            raise ValueError("Timestamps must increase; call reset on source gaps")
        dt = (
            min(timestamp_seconds - self._last_timestamp, 5.0)
            if self._last_timestamp is not None
            else 0.0
        )
        self._last_timestamp = timestamp_seconds
        for track in self._tracks:
            track.predict(dt)
            track.last_timestamp = timestamp_seconds
        high = [d for d in detections if d.score >= self.high_threshold]
        low = [d for d in detections if self.low_threshold <= d.score < self.high_threshold]
        available = [t for t in self._tracks if t.state != "removed"]
        matched, unassigned_t, unassigned_h = self._associate(available, high)
        for i, j in matched:
            available[i].update(high[j], self.min_hits)
        remaining = [available[i] for i in unassigned_t]
        second, unmatched_t, _ = self._associate(remaining, low)
        for i, j in second:
            remaining[i].update(low[j], self.min_hits)
        for i in unmatched_t:
            track = remaining[i]
            track.missed += 1
            track.state = "removed" if track.missed > self.max_age else "lost"
        for i in unassigned_h:
            track = _Track(self._next_id, high[i], timestamp_seconds)
            if self.min_hits == 1:
                track.state = "confirmed"
            self._next_id += 1
            self._tracks.append(track)
        self._tracks = [t for t in self._tracks if t.state != "removed"]
        return [t.snapshot() for t in self._tracks if t.state == "confirmed"]
