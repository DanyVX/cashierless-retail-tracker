"""Dwell-based candidate shelf interactions and conservative track attribution."""

from dataclasses import dataclass

import numpy as np

from crt.pose import Wrist
from crt.track import TrackSnapshot
from crt.zones import ZoneMap


@dataclass(frozen=True)
class Interaction:
    zone_id: str
    track_id: int | None
    start_seconds: float
    end_seconds: float
    confidence: float


class InteractionDetector:
    def __init__(
        self,
        zones: ZoneMap,
        *,
        min_dwell_seconds: float = 0.12,
        max_attribution_distance: float = 80.0,
        ambiguity_margin: float = 15.0,
        staff_track_ids: frozenset[int] = frozenset(),
    ) -> None:
        if min_dwell_seconds < 0 or max_attribution_distance <= 0 or ambiguity_margin < 0:
            raise ValueError("Invalid interaction thresholds")
        self.zones = zones
        self.dwell = min_dwell_seconds
        self.max_distance = max_attribution_distance
        self.margin = ambiguity_margin
        self.staff = staff_track_ids
        self.active: dict[str, tuple[float, int | None, float]] = {}
        self._last_time: float | None = None

    def reset(self) -> None:
        self.active.clear()
        self._last_time = None

    def _owner(self, wrist: Wrist, tracks: list[TrackSnapshot]) -> tuple[int | None, float]:
        candidates: list[tuple[float, int]] = []
        for t in tracks:
            if t.state != "confirmed" or t.track_id in self.staff:
                continue
            x1, y1, x2, y2 = t.bbox
            # Distance to the nearest point on the pedestrian bounding box.
            dx = max(x1 - wrist.x, 0.0, wrist.x - x2)
            dy = max(y1 - wrist.y, 0.0, wrist.y - y2)
            candidates.append((float(np.hypot(dx, dy)), t.track_id))
        candidates.sort()
        if not candidates or candidates[0][0] > self.max_distance:
            return None, 0.0
        if len(candidates) > 1 and candidates[1][0] - candidates[0][0] <= self.margin:
            return None, 0.0
        distance, owner = candidates[0]
        return owner, round(float(wrist.score * (1 - distance / self.max_distance)), 4)

    def update(
        self,
        wrists: list[Wrist],
        tracks: list[TrackSnapshot],
        *,
        timestamp_seconds: float,
        width: int,
        height: int,
    ) -> list[Interaction]:
        if self._last_time is not None and timestamp_seconds <= self._last_time:
            raise ValueError("Interaction timestamps must increase")
        self._last_time = timestamp_seconds
        present: dict[str, tuple[int | None, float]] = {}
        for wrist in wrists:
            zone = self.zones.at(wrist.x, wrist.y, width, height)
            if zone is None:
                continue
            owner, conf = self._owner(wrist, tracks)
            if zone.zone_id in present:
                # Simultaneous wrists: explicitly unattributed, not arbitrary assignment.
                present[zone.zone_id] = (None, 0.0)
            else:
                present[zone.zone_id] = (owner, conf)
        emitted: list[Interaction] = []
        for zone_id, (started, owner, confidence) in list(self.active.items()):
            current = present.get(zone_id)
            if current is None:
                if timestamp_seconds - started >= self.dwell:
                    emitted.append(Interaction(zone_id, owner, started, timestamp_seconds, confidence))
                del self.active[zone_id]
            elif current[0] != owner:
                # Cannot safely stitch interacting hands that change owner.
                self.active[zone_id] = (timestamp_seconds, None, 0.0)
        for zone_id, (owner, confidence) in present.items():
            if zone_id not in self.active:
                self.active[zone_id] = (timestamp_seconds, owner, confidence)
        return emitted
