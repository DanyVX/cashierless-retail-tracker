"""Detection backends, deliberately not facial recognition."""

from crt.detect.person import ColorMarkerDetector, Detection, OpenCVHOGDetector

__all__ = ["ColorMarkerDetector", "Detection", "OpenCVHOGDetector"]
