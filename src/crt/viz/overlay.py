"""Render tracks, zones, ephemeral carts and current events on a frame copy."""

import cv2
import numpy as np
from numpy.typing import NDArray

from crt.pipeline import PipelineOutput
from crt.zones import ZoneMap


def render_overlay(
    frame: NDArray[np.uint8],
    output: PipelineOutput,
    zones: ZoneMap,
    carts: dict[int, dict[str, int]],
) -> NDArray[np.uint8]:
    """Returns an annotated copy; caller MUST pass only synthetic or fully approved media."""
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Expected BGR")
    result = frame.copy()
    h, w = result.shape[:2]
    for z in zones.zones:
        poly = np.array([(int(x * w), int(y * h)) for x, y in z.vertices], np.int32)
        cv2.polylines(result, [poly], True, (120, 220, 220), 1)
        cv2.putText(
            result, z.zone_id, tuple(poly[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1
        )
    for person in output.tracks:
        x1, y1, x2, y2 = [int(v) for v in person.bbox]
        cv2.rectangle(result, (x1, y1), (x2, y2), (90, 255, 90), 1)
        cv2.putText(
            result,
            f"session {person.track_id}",
            (x1, max(10, y1 - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (255, 255, 255),
            1,
        )
    for wrist in output.wrists:
        cv2.circle(result, (int(wrist.x), int(wrist.y)), 4, (255, 50, 255), 1)
    row = 10
    for tid, cart in sorted(carts.items()):
        title = f"cart {tid}: " + ", ".join(f"{k} x{v}" for k, v in cart.items())
        cv2.putText(result, title, (3, h - row), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (255, 255, 255), 1)
        row += 12
    for event in output.events:
        title = f"{event.kind} {event.sku or '?'} x{event.quantity} ({event.status})"
        cv2.putText(result, title, (3, row), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (90, 255, 90), 1)
        row += 12
    return result
