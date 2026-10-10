"""CPU person detection backends and validated bounding boxes."""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    score: float

    def __post_init__(self) -> None:
        values = np.array((self.x1, self.y1, self.x2, self.y2, self.score))
        if not np.isfinite(values).all() or self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("Invalid bounding box")
        if not 0 <= self.score <= 1:
            raise ValueError("score must be in [0,1]")

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    @property
    def size(self) -> tuple[float, float]:
        return self.x2 - self.x1, self.y2 - self.y1


class ColorMarkerDetector:
    """Synthetic mock-scene detector, NOT a real-world human detector.

    In generated clips people are blue BGR rectangles, with shelf objects in
    other colors. There is no pretrained model and zero biometric processing.
    """

    def __init__(self, *, min_area: int = 60) -> None:
        if min_area <= 0:
            raise ValueError("min_area must be positive")
        self.min_area = min_area

    def detect(self, image: NDArray[np.uint8]) -> list[Detection]:
        if image.ndim != 3 or image.shape[-1] < 3:
            raise ValueError("Expected BGR image")
        b, g, r = cv2.split(image[:, :, :3])
        mask = ((b > 160) & (g < 110) & (r < 110)).astype(np.uint8) * 255
        count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        found: list[Detection] = []
        for i in range(1, count):
            x, y, w, h, area = (int(v) for v in stats[i])
            if area >= self.min_area:
                found.append(Detection(x, y, x + w, y + h, 0.95))
        return sorted(found, key=lambda d: (d.x1, d.y1))


class OpenCVHOGDetector:
    """OpenCV's built-in pedestrian HOG detector. Weak baseline; no accuracy claim."""

    def __init__(self, *, minimum_score: float = 0.3) -> None:
        if not 0 <= minimum_score <= 1:
            raise ValueError("minimum_score must lie in [0,1]")
        self.minimum_score = minimum_score
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(np.asarray(cv2.HOGDescriptor.getDefaultPeopleDetector(), dtype=np.float32))

    def detect(self, image: NDArray[np.uint8]) -> list[Detection]:
        if image.ndim != 3 or image.shape[2] not in (3, 4):
            raise ValueError("Expected BGR/BGRA image")
        if image.shape[0] < 128 or image.shape[1] < 64:
            return []
        boxes, weights = self.hog.detectMultiScale(image[:, :, :3])
        detections: list[Detection] = []
        for (x, y, w, h), weight in zip(boxes, weights, strict=True):
            # HOG margin is uncalibrated; bounded sigmoid is display confidence only.
            score = float(1 / (1 + np.exp(-float(weight))))
            if score >= self.minimum_score:
                detections.append(Detection(float(x), float(y), float(x + w), float(y + h), score))
        return detections
