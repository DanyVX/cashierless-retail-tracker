"""Best-effort face redaction; unverified misses forbid publishing real people."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class RedactionStats:
    detected_regions: int
    applied_regions: int


class FaceRedactor:
    """OpenCV Haar baseline; not guaranteed to detect profile/occluded faces."""

    def __init__(self) -> None:
        path = str(
            Path(cv2.__file__).resolve().parent / "data" / "haarcascade_frontalface_default.xml"
        )
        self.classifier = cv2.CascadeClassifier(path)
        if self.classifier.empty():
            raise RuntimeError("Bundled Haar face model could not be loaded")

    def redact(self, image: NDArray[np.uint8]) -> tuple[NDArray[np.uint8], RedactionStats]:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Expected 3-channel BGR frame")
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.classifier.detectMultiScale(
            grayscale, scaleFactor=1.1, minNeighbors=4, minSize=(20, 20)
        )
        output = image.copy()
        n = 0
        for x, y, w, h in faces:
            roi = output[y : y + h, x : x + w]
            if roi.size == 0:
                continue
            # Strong blur, not a guarantee of irreversible anonymization.
            output[y : y + h, x : x + w] = cv2.GaussianBlur(roi, (41, 41), 0)
            n += 1
        return output, RedactionStats(len(faces), n)


def require_synthetic_media(*, source_is_synthetic: bool) -> None:
    """Fail closed on public output for unvalidated footage of real people."""
    if not source_is_synthetic:
        raise PermissionError(
            "Public export blocked: consent and a measured face-blur miss rate are required"
        )
