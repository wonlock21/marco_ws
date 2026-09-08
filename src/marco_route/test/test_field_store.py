import json

import pytest

from conftest import create_field
from marco_route.field_store import StoreError
from marco_route.graph_model import EdgeData, FieldGraph, NodeData
from marco_route.station_config import (
    config_from_node,
    derived_dock_heading,
    update_station,
)


def basic_graph(name="field"):
    graph = FieldGraph(name)
    graph.upsert_node(NodeData(
        10, "wait", "wait", "WAIT", 1.0, 1.0, 0.0
    ))
    graph.upsert_node(NodeData(
        20, "q5", "gate_q5", "q5", 2.0, 1.0, 0.0
    ))
    graph.upsert_edge(EdgeData(
        2**40,
        10,
        20,
        bidirectional=True,
        max_speed=0.2,
        gate_event="request_permission",
    ))
    return graph


def test_crud_roundtrip_and_derived_stations(field_store):
    graph = basic_graph()
    first_hash = field_store.save_graph(graph)
    loaded = field_store.load_graph("field")
    assert loaded == graph
    stations = field_store.read_stations("field")
    assert [entry["station_id"] for entry in stations["nodes"]] == ["WAIT", "q5"]

    loaded.upsert_node(NodeData(
        30, "transit", "transit", "", 3.0, 1.0, 0.0
    ))
    loaded.upsert_edge(EdgeData(8, 20, 30, max_speed=0.15))
    second_hash = field_store.save_graph(loaded)
    assert second_hash != first_hash
    loaded.delete_edge(8)
    loaded.delete_node(30)
    assert field_store.save_graph(loaded) == first_hash


def test_station_approach_config_roundtrip(field_store):
    graph = basic_graph()
    graph.upsert_node(NodeData(
        25, "q2", "pickup_approach", "A1", 2.5, 1.0, 0.0
    ))
    graph.upsert_node(NodeData(
        30, "pickup_a1", "pickup_dock", "A1", 3.0, 1.0, 0.0
    ))
    graph.upsert_edge(EdgeData(8, 20, 25, max_speed=0.15))
    graph.upsert_edge(EdgeData(9, 25, 30, max_speed=0.15))
    update_station(graph, "A1", "q2", 1.57, "left", 4.8)

    field_store.save_graph(graph)
    loaded = field_store.load_graph("field")
    values = config_from_node(loaded.nodes[30])
    assert values["approach_qr_id"] == "q2"
    assert "line_follow_duration_s" not in values
    assert "dock_heading_yaw" not in values
    assert "turn_direction" not in values
    assert "dock_heading_yaw" not in loaded.nodes[30].metadata
    assert "turn_direction" not in loaded.nodes[30].metadata
    assert "line_follow_duration_s" not in loaded.nodes[30].metadata
    assert derived_dock_heading(loaded, "A1") == pytest.approx(3.141592653589793)
    station = next(
        item for item in field_store.read_stations("field")["nodes"]
        if item["station_id"] == "A1" and item["role"] == "pickup_dock"
    )
    assert "dock_heading_yaw" not in station["station_approach"]


def test_hash_covers_stations_and_calibration(field_store):
    graph = basic_graph()
    route_hash = field_store.save_graph(graph)
    field = field_store.field_directory("field")
    (field / "calibration_snapshot.yaml").write_text("version: 1\n", encoding="utf-8")
    calibration_hash = field_store.package_hash("field")
    assert calibration_hash != route_hash
    stations = field / "stations.yaml"
    stations.write_text(stations.read_text() + "# changed\n", encoding="utf-8")
    assert field_store.package_hash("field") != calibration_hash


def test_activation_requires_current_successful_validation(field_store):
    package_hash = field_store.save_graph(basic_graph())
    with pytest.raises(StoreError, match="validation.json"):
        field_store.activate("field", package_hash, competition_profile=False)

    field_store.write_validation(
        "field", package_hash, True, [], [], competition_profile=False
    )
    active = field_store.activate(
        "field", package_hash, competition_profile=False
    )
    assert active["package_hash"] == package_hash
    assert active["package_version"] == "2"
    assert (field_store.root / "active.yaml").is_file()

    route = field_store.field_directory("field") / "route.geojson"
    content = json.loads(route.read_text(encoding="utf-8"))
    content["name"] = "changed"
    route.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(StoreError, match="hash mismatch"):
        field_store.activate("field", package_hash, competition_profile=False)


def test_activation_rejects_incomplete_package(field_store):
    package_hash = field_store.save_graph(basic_graph())
    field_store.write_validation(
        "field", package_hash, True, [], [], competition_profile=False
    )
    (field_store.field_directory("field") / "calibration_snapshot.yaml").unlink()
    with pytest.raises(StoreError, match="calibration_snapshot.yaml"):
        field_store.activate("field", package_hash, competition_profile=False)


def test_archive_moves_inactive_field_atomically(tmp_path):
    store = create_field(tmp_path, "archive_me")
    store.save_graph(basic_graph("archive_me"))
    target = store.archive("archive_me")
    assert target.parent.name == "_archive"
    assert target.is_dir()
    assert not (tmp_path / "archive_me").exists()


def test_archive_rejects_active_field(field_store):
    package_hash = field_store.save_graph(basic_graph())
    field_store.write_validation(
        "field", package_hash, True, [], [], competition_profile=False
    )
    field_store.activate("field", package_hash, competition_profile=False)

    with pytest.raises(StoreError, match="active field cannot be archived"):
        field_store.archive("field")


def test_deactivate_clears_only_active_pointer(field_store):
    package_hash = field_store.save_graph(basic_graph())
    field_store.write_validation(
        "field", package_hash, True, [], [], competition_profile=False
    )
    field_store.activate("field", package_hash, competition_profile=False)
    field_dir = field_store.field_directory("field")
    files_before = sorted(path.name for path in field_dir.iterdir())

    previous = field_store.deactivate("field", package_hash)

    assert previous["package_hash"] == package_hash
    assert field_store.read_active() is None
    assert sorted(path.name for path in field_dir.iterdir()) == files_before


def test_deactivate_rejects_wrong_field_and_hash(field_store):
    package_hash = field_store.save_graph(basic_graph())
    field_store.write_validation(
        "field", package_hash, True, [], [], competition_profile=False
    )
    field_store.activate("field", package_hash, competition_profile=False)

    with pytest.raises(StoreError, match="active field mismatch"):
        field_store.deactivate("another", package_hash)
    with pytest.raises(StoreError, match="expected_hash"):
        field_store.deactivate("field", "stale-hash")

    assert field_store.read_active()["field_name"] == "field"
