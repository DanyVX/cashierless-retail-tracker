"""Ephemeral per-session tracking; no cross-session reidentification."""

from crt.track.multi import Tracker, TrackSnapshot

__all__ = ["TrackSnapshot", "Tracker"]
