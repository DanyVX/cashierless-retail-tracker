"""Ephemeral per-session tracking; no cross-session reidentification."""

from crt.track.multi import TrackSnapshot, Tracker

__all__ = ["TrackSnapshot", "Tracker"]
