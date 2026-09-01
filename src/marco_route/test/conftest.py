from pathlib import Path

import pytest
import yaml

from marco_route.field_store import FieldStore


def create_field(root: Path, name: str = "field") -> FieldStore:
    field = root / name
    field.mkdir()
    (field / "map.pgm").write_bytes(
        b"P5\n200 200\n255\n" + bytes([254]) * 40_000
    )
    (field / "map.yaml").write_text(
        yaml.safe_dump({
            "image": "map.pgm",
            "resolution": 0.1,
            "origin": [-5.0, -5.0, 0.0],
        }),
        encoding="utf-8",
    )
    (field / "field.yaml").write_text(
        yaml.safe_dump({
            "version": 2,
            "field_name": name,
            "profile": "competition",
            "map": {"width": 200, "height": 200},
            "files": {},
        }),
        encoding="utf-8",
    )
    (field / "mapping_pose.yaml").write_text(
        "frame_id: map\nchild_frame_id: base_footprint\n",
        encoding="utf-8",
    )
    (field / "calibration_snapshot.yaml").write_text(
        "vehicle_contract:\n  geometry:\n"
        "    footprint: [[0.5, 0.35], [0.5, -0.35], "
        "[-1.2, -0.35], [-1.2, 0.35]]\n",
        encoding="utf-8",
    )
    return FieldStore(root)


@pytest.fixture
def field_store(tmp_path):
    return create_field(tmp_path)
