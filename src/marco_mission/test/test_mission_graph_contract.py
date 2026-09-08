"""Competition field graph compatibility tests for the mission layer."""

import json
import threading
from types import SimpleNamespace

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
    assert "dock_heading_yaw" not in nodes["A1"]
    assert "turn_direction" not in nodes["A1"]


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


def test_calculated_turn_direction_is_deterministic():
    left = MissionManager._directed_turn(0.0, 3.141592653589793, "left")
    right = MissionManager._directed_turn(0.0, 3.141592653589793, "right")
    assert left > 0.0
    assert right < 0.0

    try:
        MissionManager._directed_turn(0.0, 3.141592653589793, "invalid")
    except MissionAbort as error:
        assert "gecersiz" in str(error)
    else:
        raise AssertionError("an invalid calculated direction must fail")


def test_legacy_station_turn_direction_is_ignored_before_mission(tmp_path):
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

    assert error is None


def test_production_docking_uses_lane_end_without_station_duration():
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = {
        "A3": {"approach_qr_id": "q4"},
    }
    manager._action_timeout = 120.0
    manager._docking_duration = 0.0
    manager._docking_elapsed = 0.0
    manager._docking_remaining = 0.0
    manager._docking_lane_active = False
    manager._docking_camera_valid = False
    manager._docking_stopped = True
    manager._docking_error = ""
    manager._dock = object()
    manager._qr_gate = SimpleNamespace(phase="LINE_FOLLOW_READY")
    manager._qr_gate.docking = lambda: setattr(
        manager._qr_gate, "phase", "LINE_FOLLOW_DOCKING"
    )
    manager._qr_gate.docking_complete = lambda _pickup: setattr(
        manager._qr_gate, "phase", "PICKUP_READY"
    )
    manager.events = []
    manager._event = lambda event, **fields: manager.events.append(
        (event, fields)
    )
    manager._wait_until_stopped = lambda _label: None
    captured = {}

    def action(
        _client, goal, label, timeout, require_turn_sensors=False,
        feedback_callback=None,
    ):
        captured.update(
            goal=goal,
            label=label,
            timeout=timeout,
            require_turn_sensors=require_turn_sensors,
        )
        feedback_callback(SimpleNamespace(feedback=SimpleNamespace(
            configured_duration_s=30.0,
            elapsed_s=4.2,
            remaining_s=25.8,
            lane_control_active=False,
            camera_valid=True,
            stopped=True,
        )))

    manager._action = action

    manager._do_dock("A3", pickup=True)

    assert captured["goal"].line_follow_duration_s == 0.0
    assert captured["goal"].reverse_motion is True
    assert captured["goal"].camera_source == "rear_camera"
    assert captured["goal"].timeout == 0.0
    assert captured["label"] == "lane_end_docking:A3"
    assert captured["timeout"] == 120.0
    assert captured["require_turn_sensors"] is True
    assert manager._qr_gate.phase == "PICKUP_READY"
    assert manager.events[-1][0] == "lane_end_reverse_docking_completed"


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


def test_production_mission_requires_ready_route_runtime():
    manager = MissionManager.__new__(MissionManager)
    manager._lock = threading.RLock()
    manager._busy = False
    manager._require_active_field = True
    manager._active_field_ready = True
    manager._active_field_hash = "verified-hash"
    manager._graph_file = "/data/field/route.geojson"
    manager._route_constraints_ready = False

    error = manager._reserve("task-1", ["A1", "B1"], "gui")

    assert error == "aktif saha route runtime hazir degil"
