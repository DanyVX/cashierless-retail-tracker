"""Read-only streaming video inputs with explicit timeline discontinuities."""

from crt.io.stream import Frame, FrameStream, TimelineGap, VideoSourceError

__all__ = ["Frame", "FrameStream", "TimelineGap", "VideoSourceError"]
