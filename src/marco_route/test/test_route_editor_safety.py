import threading
import time
from types import SimpleNamespace

import pytest

from marco_msgs.msg import MappingStatus, RobotStatus
from marco_route.field_store import StoreError
from marco_route.route_editor_node import RouteEditorNode


class _Client:
    def __init__(self, ready=False):
        self._ready = ready

    def service_is_ready(self):
        return self._ready

    def wait_for_service(self, timeout_sec=0.0):
        return self._ready


def _editor():
    editor = RouteEditorNode.__new__(RouteEditorNode)
    editor._lifecycle_clients = []
    editor._robot_status_seen = True
    editor._mission_state = RobotStatus.STATE_IDLE
    editor._mapping_state = MappingStatus.STATE_IDLE
    editor._linear_speed = 0.0
    editor._angular_speed = 0.0
    editor._estop_active = False
    editor._publish_safe_stop = lambda: None
    return editor


@pytest.mark.parametrize(
    "attribute,value,message",
    [
        ("_mission_state", RobotStatus.STATE_MOVING_UNLOADED, "mission is active"),
        ("_mapping_state", MappingStatus.STATE_MAPPING, "mapping is active"),
        ("_linear_speed", 0.1, "robot is moving"),
        ("_angular_speed", 0.1, "robot is rotating"),
        ("_estop_active", True, "e-stop is active"),
    ],
)
def test_field_change_rejects_unsafe_runtime_state(attribute, value, message):
    editor = _editor()
    setattr(editor, attribute, value)

    with pytest.raises(StoreError, match=message):
        editor._ensure_activation_safe()


def test_runtime_parameter_service_cannot_be_silently_skipped():
    editor = _editor()

    with pytest.raises(StoreError, match="service is unavailable"):
        editor._set_runtime_parameter(_Client(ready=False), "graph_filepath", "x")


def test_deactivate_requires_observed_robot_status_even_without_runtime():
    editor = _editor()
    editor._robot_status_seen = False

    with pytest.raises(StoreError, match="robot status is available"):
        editor._ensure_activation_safe(require_robot_status=True)


def test_runtime_command_match_requires_exact_launcher_and_graph():
    graph = "/home/orangepi/marco_data/fields/saha_test/route.geojson"
    command = [
        "/usr/bin/python3",
        "/opt/ros/humble/bin/ros2",
        "launch",
        "marco_navigation",
        "route_runtime.launch.py",
        f"graf:={graph}",
    ]

    assert RouteEditorNode._runtime_command_matches(command, graph) is True
    assert RouteEditorNode._runtime_command_matches(
        command, "/home/orangepi/marco_data/fields/other/route.geojson"
    ) is False
    assert RouteEditorNode._runtime_command_matches(
        ["ros2", "launch", "another_package", "route_runtime.launch.py"],
        graph,
    ) is False


def test_existing_matching_runtime_can_be_adopted_after_ros_restart():
    editor = _editor()
    graph = "/home/orangepi/marco_data/fields/saha_test/route.geojson"
    editor._verify_existing_route_runtime = lambda value: None
    editor._route_runtime_pids = lambda value: [12345]
    editor._route_process = None
    editor._external_route_pid = None
    editor._runtime_ready = False

    editor._adopt_existing_route_runtime({
        "field_name": "saha_test",
        "package_hash": "abc123",
        "graph_file": graph,
    })

    assert editor._route_process is None
    assert editor._external_route_pid == 12345
    assert editor._runtime_ready is True
    assert editor._runtime_field_name == "saha_test"
    assert editor._runtime_package_hash == "abc123"
    assert editor._runtime_graph_file == graph


def test_persisted_runtime_waits_for_localization_tf_before_starting():
    editor = _editor()
    graph = "/home/orangepi/marco_data/fields/saha_test/route.geojson"
    editor._startup_reconcile_started = time.monotonic() - 3.0
    editor._startup_reconcile_done = False
    editor._runtime_ready = False
    editor._operation_lock = threading.RLock()
    editor.get_parameter = lambda _name: SimpleNamespace(value=25.0)
    editor._verified_active = lambda: {
        "field_name": "saha_test",
        "package_hash": "abc123",
        "graph_file": graph,
    }
    editor._route_runtime_pids = lambda _graph: []
    editor._runtime_services_present = lambda: False
    editor._navigation_tf_ready = lambda: False
    started = []
    editor._start_route_runtime = lambda *args: started.append(args)

    editor._reconcile_active_runtime()

    assert started == []
    assert editor._startup_reconcile_done is False


def test_adopted_runtime_is_stopped_by_exact_pid_and_graph():
    editor = _editor()
    graph = "/home/orangepi/marco_data/fields/saha_test/route.geojson"
    editor._route_process = None
    editor._external_route_pid = 12345
    editor._runtime_ready = True
    editor._runtime_field_name = "saha_test"
    editor._runtime_package_hash = "abc123"
    editor._runtime_graph_file = graph
    editor._constraints_ready = True
    editor._constraints_ready_at = 1.0
    editor._runtime_stopping = False
    stopped = []
    editor._terminate_external_runtime = (
        lambda pid, graph: stopped.append((pid, graph))
    )

    editor._stop_route_runtime()

    assert stopped == [(12345, graph)]
    assert editor._external_route_pid is None
    assert editor._runtime_ready is False
