"""Competition field graph compatibility tests for the mission layer."""

import json
import threading

from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import MissionAbort


def _point(feature_id, name, role, station_id, x, y, yaw=0.0, custom=None):
    return {
        "type": "Feature",
        "properties": {
            "id": feature_id,
            "frame": "map",
            "name": name,
            "metadata": {
                "role": role,
                "station_id": station_id,
                "yaw": yaw,
                "custom": custom or {},
            },
        },
        "geometry": {"type": "Point", "coordinates": [x, y]},
    }


def test_competition_station_aliases_and_roles_are_accepted(tmp_path):
    graph_path = tmp_path / "route.geojson"
    graph_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [
            _point(0, "wait_pose", "wait", "WAIT", 0.0, 0.0),
            _point(1, "pickup_pose", "pickup_dock", "A1", 1.0, 0.0, 1.2),
            _point(2, "dropoff_pose", "dropoff_dock", "B1", 2.0, 0.0),
            _point(3, "gate_pose", "gate_q5", "q5", 1.5, 0.0),
            _point(4, "return_gate_pose", "gate_q6", "q6", 1.7, 0.0),
        ],
    }), encoding="utf-8")

    manager = MissionManager.__new__(MissionManager)
    manager._configured_gate_node = "kapi_q5"
    manager._configured_home_node = "bekla_A"
    manager._nodes = MissionManager._load_graph(str(graph_path))
    manager._resolve_special_nodes()

    assert manager._gate_node == "q5"
    assert manager._return_gate_node == "q6"
    assert manager._home_node == "WAIT"
    assert manager._nodes["A1"]["name"] == "pickup_pose"
    assert manager._nodes["A1"]["yaw"] == 1.2
    assert manager._validate_route(["A1", "B1"]) is None
    assert "pickup_dock" in manager._validate_route(["B1", "A1"])


def test_station_approach_config_is_loaded_from_graph(tmp_path):
    graph_path = tmp_path / "route.geojson"
    graph_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [_point(
            1, "pickup_pose", "pickup_dock", "A1", 1.0, 0.0,
            custom={
                "approach_qr_id": "q2",
                "dock_heading_yaw": 1.57,
                "turn_direction": "left",
                "line_follow_duration_s": 4.8,
            },
        )],
    }), encoding="utf-8")

    nodes = MissionManager._load_graph(str(graph_path))
    assert nodes["A1"]["approach_qr_id"] == "q2"
    assert nodes["A1"]["line_follow_duration_s"] == 4.8


def test_station_id_alias_stays_on_dock_and_approach_is_resolved(tmp_path):
    graph_path = tmp_path / "route.geojson"
    graph_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [
            _point(1, "A1_dock", "pickup_dock", "A1", 1.0, 0.0),
            _point(2, "q2_pose", "pickup_approach", "A1", 0.5, 0.0),
        ],
    }), encoding="utf-8")
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = MissionManager._load_graph(str(graph_path))

    assert manager._nodes["A1"]["role"] == "pickup_dock"
    assert manager._station_approach_target("A1") == "q2_pose"


def test_turn_direction_is_deterministic_and_auto_is_fail_safe():
    left = MissionManager._directed_turn(0.0, 3.141592653589793, "left")
    right = MissionManager._directed_turn(0.0, 3.141592653589793, "right")
    assert left > 0.0
    assert right < 0.0

    try:
        MissionManager._directed_turn(0.0, 3.141592653589793, "auto")
    except MissionAbort as error:
        assert "auto" in str(error)
    else:
        raise AssertionError("auto direction must fail until costmap comparison exists")


def test_configured_station_turn_contract_is_checked_before_mission(tmp_path):
    graph_path = tmp_path / "route.geojson"
    graph_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [
            _point(
                1, "A1_dock", "pickup_dock", "A1", 1.0, 0.0,
                custom={
                    "approach_qr_id": "q2",
                    "dock_heading_yaw": 3.14159,
                    "turn_direction": "auto",
                },
            ),
            _point(2, "q2_pose", "pickup_approach", "A1", 0.5, 0.0),
            _point(3, "B1_dock", "dropoff_dock", "B1", 2.0, 0.0),
            _point(4, "wait_pose", "wait", "WAIT", 0.0, 0.0),
            _point(5, "gate_pose", "gate_q5", "q5", 1.5, 0.0),
        ],
    }), encoding="utf-8")
    manager = MissionManager.__new__(MissionManager)
    manager._configured_gate_node = "q5"
    manager._configured_home_node = "WAIT"
    manager._nodes = MissionManager._load_graph(str(graph_path))
    manager._resolve_special_nodes()

    error = manager._validate_route(["A1", "B1"])

    assert "turn_direction" in error


def test_legacy_phase10_name_validation_is_preserved(tmp_path):
    graph_path = tmp_path / "legacy.geojson"
    graph_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [
            _point(0, "bekla_A", "", "", 0.0, 0.0),
            _point(1, "alma_1", "", "", 1.0, 0.0),
            _point(2, "birak_1", "", "", 2.0, 0.0),
            _point(3, "kapi_q5", "", "", 1.5, 0.0),
        ],
    }), encoding="utf-8")

    manager = MissionManager.__new__(MissionManager)
    manager._configured_gate_node = "kapi_q5"
    manager._configured_home_node = "bekla_A"
    manager._nodes = MissionManager._load_graph(str(graph_path))
    manager._resolve_special_nodes()

    assert manager._validate_route(["alma_1", "birak_1"]) is None


def test_production_route_rejects_legacy_single_gate(tmp_path):
    graph_path = tmp_path / "legacy.geojson"
    graph_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [
            _point(0, "bekla_A", "", "", 0.0, 0.0),
            _point(1, "alma_1", "", "", 1.0, 0.0),
            _point(2, "birak_1", "", "", 2.0, 0.0),
            _point(3, "kapi_q5", "", "", 1.5, 0.0),
        ],
    }), encoding="utf-8")
    manager = MissionManager.__new__(MissionManager)
    manager._configured_gate_node = "kapi_q5"
    manager._configured_home_node = "bekla_A"
    manager._nodes = MissionManager._load_graph(str(graph_path))
    manager._resolve_special_nodes()
    manager._require_active_field = True

    assert "gate_q6" in manager._validate_route(["alma_1", "birak_1"])


def test_production_mission_requires_verified_active_field():
    manager = MissionManager.__new__(MissionManager)
    manager._lock = threading.RLock()
    manager._busy = False
    manager._require_active_field = True
    manager._active_field_ready = False

    error = manager._reserve("task-1", ["A1", "B1"], "gui")

    assert error == "dogrulanmis etkin saha paketi hazir degil"
