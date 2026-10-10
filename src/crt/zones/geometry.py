"""Normalized polygons avoid hard-coded camera resolutions."""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ShelfZone:
    zone_id: str
    sku: str
    vertices: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if not self.zone_id or not self.sku or len(self.vertices) < 3:
            raise ValueError("Zone requires ID, SKU, >=3 vertices")
        pts = np.asarray(self.vertices, dtype=float)
        if not np.isfinite(pts).all() or np.any(pts < 0) or np.any(pts > 1):
            raise ValueError("Zone vertices must use normalized 0..1 coordinates")
        # Degenerate zones are not valid shelf locations.
        if abs(cv2.contourArea(pts.astype(np.float32))) < 1e-7:
            raise ValueError("Zone polygon has zero area")

    def contains(self, x: float, y: float, width: int, height: int) -> bool:
        if width <= 0 or height <= 0:
            raise ValueError("Frame dimensions must be positive")
        points = np.asarray([(a * width, b * height) for a, b in self.vertices], dtype=np.float32)
        return cv2.pointPolygonTest(points, (float(x), float(y)), False) >= 0

    def bounds(self, width: int, height: int) -> tuple[int, int, int, int]:
        arr = np.array(self.vertices)
        left, top = arr.min(axis=0)
        right, bottom = arr.max(axis=0)
        return (
            max(0, int(left * width)),
            max(0, int(top * height)),
            min(width, int(np.ceil(right * width))),
            min(height, int(np.ceil(bottom * height))),
        )


class ZoneMap:
    def __init__(self, zones: list[ShelfZone]) -> None:
        ids = [z.zone_id for z in zones]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate zone ID")
        self.zones = zones

    def at(self, x: float, y: float, width: int, height: int) -> ShelfZone | None:
        matches = [z for z in self.zones if z.contains(x, y, width, height)]
        return matches[0] if len(matches) == 1 else None

    def by_id(self, zone_id: str) -> ShelfZone:
        for z in self.zones:
            if z.zone_id == zone_id:
                return z
        raise KeyError(zone_id)
