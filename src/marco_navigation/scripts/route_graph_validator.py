#!/usr/bin/env python3
"""CLI wrapper around marco_route's canonical field package validator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory

from marco_route.field_store import FieldStore
from marco_route.validator import validate_field


def _vehicle_footprint() -> list[tuple[float, float]]:
    contract = (
        Path(get_package_share_directory("marco_bringup"))
        / "config"
        / "vehicle_contract.yaml"
    )
    with contract.open("r", encoding="utf-8") as stream:
        content = yaml.safe_load(stream) or {}
    raw = content["geometry"]["footprint"]
    return [(float(point[0]), float(point[1])) for point in raw]


def validate(graph_path: str, map_yaml: str | None = None) -> dict:
    graph_file = Path(graph_path).expanduser().resolve()
    field_dir = graph_file.parent
    if graph_file.name != "route.geojson":
        raise ValueError(
            "canonical validation requires <field>/route.geojson"
        )
    if map_yaml and Path(map_yaml).expanduser().resolve() != field_dir / "map.yaml":
        raise ValueError("--map must identify the same field package map.yaml")
    store = FieldStore(field_dir.parent)
    graph = store.load_graph(field_dir.name)
    result = validate_field(
        store,
        graph,
        competition_profile=True,
        footprint=_vehicle_footprint(),
    )
    package_hash = store.package_hash(field_dir.name)
    store.write_validation(
        field_dir.name,
        package_hash,
        result.valid,
        result.errors,
        result.warnings,
        True,
    )
    summary = {
        "passed": result.valid,
        "field_name": field_dir.name,
        "package_hash": package_hash,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "errors": result.errors,
        "warnings": result.warnings,
    }
    return summary


def _atomic_result(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a canonical MarCO field route package"
    )
    parser.add_argument("graph", help="<field>/route.geojson")
    parser.add_argument("--map", help="<field>/map.yaml (optional consistency check)")
    parser.add_argument("--result", help="write a JSON summary atomically")
    args = parser.parse_args()
    result = None
    try:
        result = validate(args.graph, args.map)
        if not result["passed"]:
            raise ValueError("; ".join(result["errors"]))
        print(
            "PASS field validator: "
            f"{result['nodes']} nodes, {result['edges']} logical edges"
        )
        exit_code = 0
    except Exception as error:
        if result is None:
            result = {"passed": False, "error": str(error)}
        else:
            result["error"] = str(error)
        print(f"FAIL field validator: {error}", file=sys.stderr)
        exit_code = 2
    if args.result:
        _atomic_result(Path(args.result).expanduser().resolve(), result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
