"""Explicitly calibrated solid-color mock products, not general SKU recognition."""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from crt.zones import ZoneMap


@dataclass(frozen=True)
class ColorSKU:
    sku: str
    bgr: tuple[int, int, int]
    tolerance: int = 22
    min_blob_area: int = 22

    def __post_init__(self) -> None:
        if not self.sku or not all(0 <= x <= 255 for x in self.bgr):
            raise ValueError("Invalid SKU color")
        if not 0 <= self.tolerance <= 100 or self.min_blob_area < 1:
            raise ValueError("Invalid color tolerance / blob area")


@dataclass(frozen=True)
class ShelfSnapshot:
    zone_id: str
    counts: dict[str, int]
    unknown_pixels: int


@dataclass(frozen=True)
class ShelfChange:
    zone_id: str
    sku: str | None
    quantity_delta: int
    confidence: float
    unknown: bool = False


class ShelfReader:
    """Calibrated color-marker SKU counter for a controlled mock shelf.

    A real retail product classifier is NOT included; similarity-looking goods,
    reflections and unlabeled stock are explicitly unresolved.
    """

    def __init__(self, zones: ZoneMap, skus: list[ColorSKU]) -> None:
        names = [s.sku for s in skus]
        if not skus or len(names) != len(set(names)):
            raise ValueError("Unique known SKU calibrations required")
        self.zones = zones
        self.skus = skus

    def snapshot(self, image: NDArray[np.uint8], zone_id: str) -> ShelfSnapshot:
        if image.ndim != 3 or image.shape[2] < 3:
            raise ValueError("Expected BGR image")
        zone = self.zones.by_id(zone_id)
        height, width = image.shape[:2]
        x1, y1, x2, y2 = zone.bounds(width, height)
        if x2 <= x1 or y2 <= y1:
            raise ValueError("Zone outside frame")
        crop = image[y1:y2, x1:x2, :3].astype(np.int16)
        poly = np.asarray([(a * width - x1, b * height - y1) for a, b in zone.vertices], np.int32)
        valid = np.zeros(crop.shape[:2], dtype=np.uint8)
        cv2.fillPoly(valid, [poly], 255)
        claimed = np.zeros_like(valid, dtype=np.uint8)
        counts: dict[str, int] = {}
        for sku in self.skus:
            color = np.array(sku.bgr, dtype=np.int16)
            close = np.all(np.abs(crop - color) <= sku.tolerance, axis=2)
            mask = (close & (valid > 0) & (claimed == 0)).astype(np.uint8)
            n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
            counts[sku.sku] = sum(
                1 for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= sku.min_blob_area
            )
            claimed[mask > 0] = 255
        # Synthetic background is near black: any colored unmatched region is unknown.
        significant = np.max(crop, axis=2) >= 95
        unknown = int(np.count_nonzero(significant & (valid > 0) & (claimed == 0)))
        return ShelfSnapshot(zone_id, counts, unknown)

    def compare(
        self,
        before: ShelfSnapshot,
        after: ShelfSnapshot,
        *,
        unknown_pixel_threshold: int = 80,
    ) -> list[ShelfChange]:
        if before.zone_id != after.zone_id:
            raise ValueError("Cannot compare different zones")
        if before.counts.keys() != after.counts.keys():
            raise ValueError("SKU calibration mismatch")
        deltas = [
            ShelfChange(before.zone_id, sku, after.counts[sku] - before.counts[sku], 1.0)
            for sku in before.counts
            if after.counts[sku] != before.counts[sku]
        ]
        if abs(after.unknown_pixels - before.unknown_pixels) >= unknown_pixel_threshold:
            deltas.append(ShelfChange(before.zone_id, None, 0, 0.0, unknown=True))
        return deltas
