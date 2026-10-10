from pathlib import Path

import pytest
from tools.calibrate_zones import write_zone


def test_headless_calibration_outputs_valid_polygon(tmp_path: Path) -> None:
    out = tmp_path / "calibration.json"
    write_zone(
        points=[(20, 20), (80, 20), (80, 80), (20, 80)],
        width=100,
        height=100,
        zone_id="A",
        sku="chips",
        output=out,
    )
    assert '"zone_id": "A"' in out.read_text(encoding="utf-8")


def test_out_of_frame_points_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_zone(
            points=[(-1, 0), (50, 0), (0, 50)],
            width=100,
            height=100,
            zone_id="A",
            sku="chips",
            output=tmp_path / "bad.json",
        )
