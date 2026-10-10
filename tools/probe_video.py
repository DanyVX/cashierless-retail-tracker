"""Read-only frame/gap inspection without retaining video or publishing images."""

import argparse
import json
from pathlib import Path

from crt.io import Frame, FrameStream, TimelineGap


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect video frames; never stores imagery")
    parser.add_argument("source", help="Private video filename, RTSP URL, or camera index")
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--width", type=int)
    parser.add_argument("--fps-fallback", type=float)
    parser.add_argument("--max-frames", type=int, default=100)
    parser.add_argument("--consent-confirmed", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    if args.max_frames < 1:
        parser.error("--max-frames must be positive")
    if args.mode == "live" and args.synthetic:
        parser.error("live streams cannot claim to be synthetic")
    source = (
        int(args.source)
        if args.mode == "live" and args.source.isdigit()
        else Path(args.source)
        if args.mode == "offline"
        else args.source
    )
    frames = 0
    gaps: dict[str, int] = {}
    for packet in FrameStream(
        source,
        mode=args.mode,
        width=args.width,
        fps_fallback=args.fps_fallback,
        synthetic=args.synthetic,
        consent_confirmed=args.consent_confirmed,
    ):
        if isinstance(packet, TimelineGap):
            gaps[packet.reason] = gaps.get(packet.reason, 0) + 1
        elif isinstance(packet, Frame):
            frames += 1
            if frames >= args.max_frames:
                break
    print(json.dumps({"frames_read": frames, "timeline_gap_counts": gaps}, indent=2))


if __name__ == "__main__":
    main()
