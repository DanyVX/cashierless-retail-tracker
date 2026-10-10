"""Synthetic wrist marker extraction; opt-in annotation interface for real clips."""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Wrist:
    x: float
    y: float
    score: float = 1.0

    def __post_init__(self) -> None:
        if not np.isfinite((self.x, self.y, self.score)).all() or not 0 <= self.score <= 1:
            raise ValueError("Invalid wrist observation")


class MarkerWristDetector:
    """Find pure magenta dots explicitly drawn in synthetic test footage."""

    def detect(self, image: NDArray[np.uint8]) -> list[Wrist]:
        b, g, r = cv2.split(image[:, :, :3])
        mask = ((b > 190) & (r > 190) & (g < 90)).astype(np.uint8) * 255
        n, _, stats, centers = cv2.connectedComponentsWithStats(mask, connectivity=8)
        return [
            Wrist(float(centers[i, 0]), float(centers[i, 1]))
            for i in range(1, n)
            if stats[i, cv2.CC_STAT_AREA] >= 3
        ]
