"""End-to-end CPU mock shelf perception with explicitly synthetic SKU/wrist semantics."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from crt.detect import ColorMarkerDetector, Detection, OpenCVHOGDetector
from crt.events import CartEngine, CartEvent, InteractionDetector
from crt.io import Frame, TimelineGap
from crt.pose import MarkerWristDetector, Wrist
from crt.shelf import ShelfReader, ShelfSnapshot
from crt.track import TrackSnapshot, Tracker


@dataclass(frozen=True)
class PipelineOutput:
    timestamp_seconds: float
    tracks: tuple[TrackSnapshot, ...]
    events: tuple[CartEvent, ...]
    wrists: tuple[Wrist, ...]


class ShelfPipeline:
    """Opt-in synthetic wrist and color SKU backend, not real-world cashierless inference."""

    def __init__(self, shelf: ShelfReader, *, person_backend: str = "synthetic") -> None:
        if person_backend not in ("synthetic", "hog"):
            raise ValueError("Unknown detection backend")
        self.people: ColorMarkerDetector | OpenCVHOGDetector = (
            ColorMarkerDetector() if person_backend == "synthetic" else OpenCVHOGDetector()
        )
        self.hands = MarkerWristDetector()
        self.tracker = Tracker(min_hits=2)
        self.interactions = InteractionDetector(
            shelf.zones, min_dwell_seconds=0.1, max_attribution_distance=120.0
        )
        self.shelf = shelf
        self.cart = CartEngine(minimum_confidence=0.4)
        self._last_clear: dict[str, ShelfSnapshot] = {}
        self._active_before: dict[str, ShelfSnapshot] = {}

    def reset_timeline(self) -> None:
        self.tracker.reset()
        self.interactions.reset()
        self._active_before.clear()
        self._last_clear.clear()

    def process(self, packet: Frame | TimelineGap) -> PipelineOutput | None:
        if isinstance(packet, TimelineGap):
            self.reset_timeline()
            return None
        frame: NDArray[np.uint8] = packet.image
        height, width = frame.shape[:2]
        detections: list[Detection] = self.people.detect(frame)
        tracks = self.tracker.update(detections, packet.timestamp_seconds)
        wrists = self.hands.detect(frame)
        previous = dict(self.interactions.active)
        candidates = self.interactions.update(
            wrists, tracks, timestamp_seconds=packet.timestamp_seconds, width=width, height=height
        )
        for zone_id in self.interactions.active:
            if zone_id not in previous and zone_id in self._last_clear:
                self._active_before[zone_id] = self._last_clear[zone_id]
        events: list[CartEvent] = []
        for item in candidates:
            before = self._active_before.pop(item.zone_id, None)
            after = self.shelf.snapshot(frame, item.zone_id)
            if before is not None:
                changes = self.shelf.compare(before, after)
                events.extend(
                    self.cart.apply(changes, item, timestamp_seconds=packet.timestamp_seconds)
                )
            self._last_clear[item.zone_id] = after
        wrist_zones = {
            z.zone_id for wrist in wrists for z in self.shelf.zones.zones
            if z.contains(wrist.x, wrist.y, width, height)
        }
        for zone in self.shelf.zones.zones:
            if zone.zone_id not in self.interactions.active and zone.zone_id not in wrist_zones:
                self._last_clear[zone.zone_id] = self.shelf.snapshot(frame, zone.zone_id)
        return PipelineOutput(packet.timestamp_seconds, tuple(tracks), tuple(events), tuple(wrists))
