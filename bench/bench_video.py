"""Measured, synthetic-only CPU frame decode smoke benchmark. No people or external data."""

import argparse
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from crt.environment import environment_snapshot
from crt.io import Frame, FrameStream, TimelineGap


def benchmark(*, frames: int, width: int, height: int) -> dict[str, object]:
    if frames < 1 or width < 16 or height < 16:
        raise ValueError("frames >=1 and width/height >=16 required")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "generated.avi"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (width, height))
        if not writer.isOpened():
            raise RuntimeError("Synthetic MJPG encoder unavailable")
        try:
            for i in range(frames):
                writer.write(np.full((height, width, 3), i % 256, dtype=np.uint8))
        finally:
            writer.release()
        start = time.perf_counter()
        packets = FrameStream(path, fps_fallback=10.0, synthetic=True)
        decoded = 0
        gaps = 0
        for packet in packets:
            if isinstance(packet, Frame):
                decoded += 1
            elif isinstance(packet, TimelineGap):
                gaps += 1
        seconds = time.perf_counter() - start
    return {
        "name": "synthetic_mjpg_decode_cpu",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "synthetic_only": True,
        "configuration": {"frames": frames, "width": width, "height": height, "codec": "MJPG"},
        "measurements": {
            "decoded_frames": decoded,
            "timeline_gaps": gaps,
            "wall_seconds": seconds,
            "throughput_fps": decoded / seconds if seconds > 0 else None,
        },
        "environment": environment_snapshot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=96)
    parser.add_argument("--out", type=Path, default=Path("results/video_smoke.json"))
    args = parser.parse_args()
    result = benchmark(frames=args.frames, width=args.width, height=args.height)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved measured synthetic-only benchmark to {args.out}")


if __name__ == "__main__":
    main()
