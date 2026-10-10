"""Streaming video reader. Temporal uncertainty is explicit and never a silent cart event."""

import math
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, cast

import cv2
import numpy as np
from numpy.typing import NDArray

from crt.config import Settings
from crt.privacy import require_recording_consent


class VideoSourceError(RuntimeError):
    """The requested stream cannot be opened or decoded reliably."""


class Capture(Protocol):
    def isOpened(self) -> bool: ...
    def read(self) -> tuple[bool, NDArray[np.uint8] | None]: ...
    def get(self, prop: int) -> float: ...
    def set(self, prop: int, value: float) -> bool: ...
    def release(self) -> None: ...


def _default_capture(source: str | int) -> Capture:
    return cast(Capture, cv2.VideoCapture(source))


@dataclass(frozen=True)
class Frame:
    """A single decoded frame. Image arrays are ephemeral; consumers must not retain them."""

    index: int
    timestamp_seconds: float
    image: NDArray[np.uint8]
    timestamp_source: Literal["pts", "fps_fallback", "monotonic"]
    source_pts_seconds: float | None


@dataclass(frozen=True)
class TimelineGap:
    """Discontinuity: downstream temporal event inference must reset state at this boundary."""

    reason: Literal["decode_error", "disconnect", "timestamp_regression", "timestamp_jump"]
    after_index: int
    estimated_missing_frames: int | None = None


VideoPacket = Frame | TimelineGap


class FrameStream:
    """Iterate frames without buffering an entire source into memory.

    VFR is supported when the backend exposes actual millisecond timestamps;
    OpenCV backends that do not expose PTS fall back to reported FPS, marked
    explicitly as an estimate. A PTS jump indicates a *possible* gap, not proof
    of a dropped frame. Live reconnects always produce a gap marker.
    """

    def __init__(
        self,
        source: str | Path | int,
        *,
        mode: Literal["offline", "live"] = "offline",
        width: int | None = None,
        fps_fallback: float | None = None,
        jump_factor: float = 2.5,
        max_reconnects: int = 3,
        max_decode_errors: int = 3,
        reconnect_base_delay: float = 0.25,
        mirror: bool = False,
        synthetic: bool = False,
        consent_confirmed: bool = False,
        capture_factory: Callable[[str | int], Capture] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if width is not None and width < 1:
            raise ValueError("width must be positive")
        if fps_fallback is not None and not (math.isfinite(fps_fallback) and fps_fallback > 0):
            raise ValueError("fps_fallback must be finite and positive")
        if not math.isfinite(jump_factor) or jump_factor <= 1:
            raise ValueError("jump_factor must exceed one")
        if max_reconnects < 0 or max_decode_errors < 1:
            raise ValueError("invalid reconnect/decode-error limits")
        if not math.isfinite(reconnect_base_delay) or reconnect_base_delay < 0:
            raise ValueError("reconnect_base_delay must be nonnegative")
        self._source = str(source) if isinstance(source, Path) else source
        self._mode = mode
        self._width = width
        self._fps_fallback = fps_fallback
        self._jump_factor = jump_factor
        self._max_reconnects = max_reconnects
        self._max_decode_errors = max_decode_errors
        self._reconnect_base_delay = reconnect_base_delay
        self._mirror = mirror
        self._synthetic = synthetic
        self._consent_confirmed = consent_confirmed
        self._factory: Callable[[str | int], Capture] = capture_factory or _default_capture
        self._sleeper = sleeper
        self._clock = clock
        if mode not in ("offline", "live"):
            raise ValueError("mode must be offline or live")

    def _open(self) -> Capture:
        cap = self._factory(self._source)
        if not cap.isOpened():
            cap.release()
            raise VideoSourceError("Failed to open video source (location not logged)")
        if hasattr(cv2, "CAP_PROP_ORIENTATION_AUTO"):
            cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1.0)
        return cap

    def _resize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.ndim != 3 or image.shape[2] not in (3, 4):
            raise VideoSourceError("Decoded frame must be a 3/4-channel image")
        if self._width is not None and image.shape[1] != self._width:
            height = max(1, round(image.shape[0] * self._width / image.shape[1]))
            image = cast(
                NDArray[np.uint8],
                cv2.resize(image, (self._width, height), interpolation=cv2.INTER_AREA),
            )
        if self._mirror:
            image = cast(NDArray[np.uint8], cv2.flip(image, 1))
        return image

    def __iter__(self) -> Iterator[VideoPacket]:
        if not self._synthetic:
            require_recording_consent(
                consent_confirmed=self._consent_confirmed, settings=Settings()
            )
        cap = self._open()
        index = 0
        errors = 0
        reconnects = 0
        last_ts: float | None = None
        start_clock = self._clock()
        try:
            while True:
                fps = cap.get(cv2.CAP_PROP_FPS)
                if not (math.isfinite(fps) and fps > 0):
                    fps = self._fps_fallback or 0.0
                period = 1.0 / fps if fps > 0 else None
                count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                ok, image = cap.read()
                if not ok or image is None or image.size == 0:
                    if self._mode == "offline":
                        # Metadata can be missing. Without a declared length, read failure
                        # is EOF; with a declared remaining length, it is a decode gap.
                        if not (math.isfinite(count) and count > index + 1):
                            break
                        errors += 1
                        yield TimelineGap(reason="decode_error", after_index=index - 1)
                        if errors >= self._max_decode_errors:
                            raise VideoSourceError("Too many decode failures before declared EOF")
                        continue
                    cap.release()
                    yield TimelineGap(reason="disconnect", after_index=index - 1)
                    if reconnects >= self._max_reconnects:
                        raise VideoSourceError("Live camera reconnect budget exhausted")
                    self._sleeper(min(30.0, self._reconnect_base_delay * (2**reconnects)))
                    reconnects += 1
                    cap = self._open()
                    errors = 0
                    continue
                errors = 0
                image = self._resize(image)
                raw_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                source_pts = (
                    raw_msec / 1000.0 if math.isfinite(raw_msec) and raw_msec >= 0 else None
                )
                source: Literal["pts", "fps_fallback", "monotonic"]
                if self._mode == "live":
                    timestamp = self._clock() - start_clock
                    source = "monotonic"
                elif source_pts is not None and (source_pts > 0 or index == 0):
                    timestamp = source_pts
                    source = "pts"
                elif period is not None:
                    timestamp = index * period
                    source = "fps_fallback"
                else:
                    raise VideoSourceError("No usable video timestamps or FPS; set fps_fallback")
                if last_ts is not None and timestamp <= last_ts:
                    yield TimelineGap(reason="timestamp_regression", after_index=index - 1)
                    if period is None:
                        raise VideoSourceError("Nonmonotonic timestamp without a known FPS")
                    timestamp = last_ts + period
                    source = "fps_fallback"
                elif last_ts is not None and period is not None:
                    delta = timestamp - last_ts
                    if delta > self._jump_factor * period:
                        missing = max(1, round(delta / period) - 1)
                        yield TimelineGap(
                            reason="timestamp_jump",
                            after_index=index - 1,
                            estimated_missing_frames=missing,
                        )
                last_ts = timestamp
                yield Frame(
                    index=index,
                    timestamp_seconds=timestamp,
                    image=image,
                    timestamp_source=source,
                    source_pts_seconds=source_pts,
                )
                index += 1
        finally:
            cap.release()
