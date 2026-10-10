"""Portable normalized zone calibration from explicit points; GUI requires desktop OpenCV."""

import argparse
import json
from pathlib import Path

from crt.zones import ShelfZone


def write_zone(
    *,
    points: list[tuple[int, int]],
    width: int,
    height: int,
    zone_id: str,
    sku: str,
    output: Path,
) -> None:
    if width <= 0 or height <= 0:
        raise ValueError("Camera resolution must be positive")
    polygon = ShelfZone(
        zone_id,
        sku,
        tuple((x / width, y / height) for x, y in points),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "reference_width": width,
                "reference_height": height,
                "zones": [
                    {"zone_id": polygon.zone_id, "sku": polygon.sku, "vertices": polygon.vertices}
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create resolution-normalized shelf zone JSON")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--zone", required=True)
    parser.add_argument("--sku", required=True)
    parser.add_argument("--points", nargs="+", required=True, help="x,y points, >=3")
    parser.add_argument("--out", type=Path, default=Path("configs/shelf_zones.json"))
    args = parser.parse_args()
    try:
        vertices = [tuple(int(v) for v in point.split(",")) for point in args.points]
        if any(len(pt) != 2 for pt in vertices):
            raise ValueError("Each point must be x,y")
        write_zone(
            points=vertices,
            width=args.width,
            height=args.height,
            zone_id=args.zone,
            sku=args.sku,
            output=args.out,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Saved normalized shelf polygon to {args.out}")


if __name__ == "__main__":
    main()
