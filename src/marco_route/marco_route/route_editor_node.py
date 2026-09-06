#!/usr/bin/env python3
"""ROS service facade for semantic field route editing."""

from __future__ import annotations

import json
import math
import os
import shutil
import signal
import subprocess
import threading
import time

import rclpy
from marco_msgs.msg import (
    ActiveField,
    FieldEdge,
    FieldNode,
    FieldPackageStatus,
    StationApproachConfig,
)
from marco_msgs.msg import MappingStatus, RobotStatus
from marco_msgs.srv import (
    ActivateField,
    ArchiveField,
    DeactivateField,
    DeleteFieldEdge,
    DeleteFieldNode,
    GetActiveField,
    GetFieldGraph,
    GetStationApproachConfigs,
    PixelToMap,
    SaveCurrentPoseNode,
    SaveFieldEdge,
    SaveFieldNode,
    SaveStationApproachConfig,
    ValidateField,
)
from lifecycle_msgs.msg import State
from lifecycle_msgs.srv import GetState
from nav2_msgs.srv import DynamicEdges, ManageLifecycleNodes
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import GetParameters, SetParameters
from rclpy.callback_groups import (
    MutuallyExclusiveCallbackGroup,
    ReentrantCallbackGroup,
)
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from std_msgs.msg import Bool
from tf2_ros import Buffer, TransformException, TransformListener

from .coordinates import pixel_to_map
from .field_store import FieldStore, StoreError
from .graph_model import EdgeData, GraphError, NodeData
from .station_config import config_from_node, update_station
from .validator import ValidationResult, validate_field


class RouteEditorNode(Node):
    def __init__(self) -> None:
        super().__init__("route_editor")
        self.declare_parameter("data_root", "~/marco_data/fields")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("robot_frame", "base_footprint")
        self.declare_parameter("tf_timeout", 2.0)
        self.declare_parameter("competition_profile", True)
        self.declare_parameter("route_runtime_timeout_s", 25.0)

        root = os.path.expanduser(str(self.get_parameter("data_root").value))
        self._store = FieldStore(root)
        self._callbacks = MutuallyExclusiveCallbackGroup()
        self._client_callbacks = ReentrantCallbackGroup()
        self._operation_lock = threading.RLock()
        self._tf = Buffer()
        self._tf_listener = TransformListener(self._tf, self)
        self._mission_state = RobotStatus.STATE_IDLE
        self._robot_status_seen = False
        self._mapping_state = MappingStatus.STATE_IDLE
        self._linear_speed = 0.0
        self._angular_speed = 0.0
        self._estop_active = False
        self._route_process: subprocess.Popen | None = None
        self._external_route_pid: int | None = None
        self._runtime_stopping = False
        self._runtime_ready = False
        self._runtime_field_name = ""
        self._runtime_package_hash = ""
        self._runtime_graph_file = ""
        self._constraints_ready = False
        self._constraints_ready_at = 0.0
        self._startup_reconcile_started = time.monotonic()
        self._startup_reconcile_done = False

        latched = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._active_pub = self.create_publisher(
            ActiveField, "/fields/active", latched
        )
        self._status_pub = self.create_publisher(
            FieldPackageStatus, "/fields/package_status", latched
        )
        self._stop_publishers = [
            self.create_publisher(Twist, topic, 10)
            for topic in ("/cmd_vel_manual", "/cmd_vel_nav", "/cmd_vel")
        ]
        self.create_subscription(
            RobotStatus,
            "/robot_status",
            self._on_robot_status,
            10,
            callback_group=self._client_callbacks,
        )
        self.create_subscription(
            MappingStatus,
            "/mapping/status",
            lambda message: setattr(self, "_mapping_state", message.state),
            latched,
            callback_group=self._client_callbacks,
        )
        self.create_subscription(
            Odometry,
            "/odom",
            self._on_odom,
            10,
            callback_group=self._client_callbacks,
        )
        self._lifecycle_clients = [
            self.create_client(
                ManageLifecycleNodes,
                service,
                callback_group=self._client_callbacks,
            )
            for service in (
                "/lifecycle_manager_navigation/manage_nodes",
                "/lifecycle_manager_route/manage_nodes",
                "/lifecycle_manager_localization/manage_nodes",
            )
        ]
        self._route_parameters = self.create_client(
            SetParameters,
            "/route_server/set_parameters",
            callback_group=self._client_callbacks,
        )
        self._map_parameters = self.create_client(
            SetParameters,
            "/map_server/set_parameters",
            callback_group=self._client_callbacks,
        )
        self._route_parameters_get = self.create_client(
            GetParameters,
            "/route_server/get_parameters",
            callback_group=self._client_callbacks,
        )
        self._guard_parameters_get = self.create_client(
            GetParameters,
            "/route_guard/get_parameters",
            callback_group=self._client_callbacks,
        )
        self._route_state_client = self.create_client(
            GetState,
            "/route_server/get_state",
            callback_group=self._client_callbacks,
        )
        self._dynamic_edges = self.create_client(
            DynamicEdges,
            "/route_server/DynamicEdgesScorer/adjust_edges",
            callback_group=self._client_callbacks,
        )
        self.create_subscription(
            Bool,
            "/route/load_constraints_ready",
            self._on_constraints_ready,
            latched,
            callback_group=self._client_callbacks,
        )
        services = (
            (GetFieldGraph, "/fields/get_graph", self._on_get_graph),
            (
                GetStationApproachConfigs,
                "/fields/get_station_approach_configs",
                self._on_get_station_configs,
            ),
            (SaveFieldNode, "/fields/save_node", self._on_save_node),
            (
                SaveStationApproachConfig,
                "/fields/save_station_approach_config",
                self._on_save_station_config,
            ),
            (
                SaveCurrentPoseNode,
                "/fields/save_current_pose_node",
                self._on_save_current_pose_node,
            ),
            (DeleteFieldNode, "/fields/delete_node", self._on_delete_node),
            (SaveFieldEdge, "/fields/save_edge", self._on_save_edge),
            (DeleteFieldEdge, "/fields/delete_edge", self._on_delete_edge),
            (ValidateField, "/fields/validate", self._on_validate),
            (ActivateField, "/fields/activate", self._on_activate),
            (DeactivateField, "/fields/deactivate", self._on_deactivate),
            (ArchiveField, "/fields/archive", self._on_archive),
            (GetActiveField, "/fields/get_active", self._on_get_active),
            (PixelToMap, "/fields/pixel_to_map", self._on_pixel_to_map),
        )
        self._services = [
            self.create_service(
                service_type,
                name,
                callback,
                callback_group=self._callbacks,
            )
            for service_type, name, callback in services
        ]
        self._publish_active()
        self.create_timer(
            0.5,
            self._monitor_route_runtime,
            callback_group=self._client_callbacks,
        )
        self.create_timer(
            0.5,
            self._reconcile_active_runtime,
            # Runtime reconciliation performs synchronous waits on clients in
            # _client_callbacks.  Keep the timer mutually exclusive with
            # field mutations so another timer/service callback cannot occupy
            # the executor thread needed to complete those client futures.
            callback_group=self._callbacks,
        )

    def _on_robot_status(self, message: RobotStatus) -> None:
        self._robot_status_seen = True
        self._mission_state = message.mission_state
        self._linear_speed = float(message.linear_speed)
        self._estop_active = bool(message.estop_active)

    def _on_odom(self, message: Odometry) -> None:
        self._linear_speed = float(message.twist.twist.linear.x)
        self._angular_speed = float(message.twist.twist.angular.z)

    def _on_constraints_ready(self, message: Bool) -> None:
        self._constraints_ready = bool(message.data)
        if message.data:
            self._constraints_ready_at = time.monotonic()

    @staticmethod
    def _wait_future(future, timeout: float = 5.0):
        completed = threading.Event()
        future.add_done_callback(lambda _future: completed.set())
        if not completed.wait(timeout):
            raise StoreError("runtime transition timed out")
        error = future.exception()
        if error is not None:
            raise StoreError(f"runtime transition failed: {error}")
        return future.result()

    def _publish_safe_stop(self) -> None:
        for publisher in self._stop_publishers:
            publisher.publish(Twist())

    def _ensure_activation_safe(self, require_robot_status: bool = False) -> None:
        runtime_present = any(
            client.service_is_ready() for client in self._lifecycle_clients
        )
        if (require_robot_status or runtime_present) and not self._robot_status_seen:
            raise StoreError(
                "field cannot change until current robot status is available"
            )
        if self._estop_active or self._mission_state == RobotStatus.STATE_ESTOP:
            raise StoreError("field cannot change while e-stop is active")
        if self._mission_state not in (
            RobotStatus.STATE_IDLE,
            RobotStatus.STATE_ERROR,
        ):
            raise StoreError("field cannot change while a mission is active")
        if self._mapping_state in (
            MappingStatus.STATE_STARTING,
            MappingStatus.STATE_MAPPING,
            MappingStatus.STATE_STOPPING,
            MappingStatus.STATE_SAVING,
        ):
            raise StoreError("field cannot change while mapping is active")
        if abs(self._linear_speed) > 0.02:
            raise StoreError("field cannot change while the robot is moving")
        if abs(self._angular_speed) > 0.03:
            raise StoreError("field cannot change while the robot is rotating")
        self._publish_safe_stop()

    def _manage_runtime(self, command: int) -> list:
        managed = []
        try:
            for client in self._lifecycle_clients:
                if not client.wait_for_service(timeout_sec=0.15):
                    continue
                request = ManageLifecycleNodes.Request()
                request.command = command
                response = self._wait_future(client.call_async(request))
                if response is None or not response.success:
                    raise StoreError(
                        f"lifecycle manager rejected command {command}"
                    )
                managed.append(client)
        except Exception:
            if command == ManageLifecycleNodes.Request.PAUSE:
                for client in reversed(managed):
                    request = ManageLifecycleNodes.Request()
                    request.command = ManageLifecycleNodes.Request.RESUME
                    try:
                        self._wait_future(client.call_async(request))
                    except StoreError:
                        pass
            raise
        return managed

    def _set_runtime_parameter(
        self, client, name: str, value: str
    ) -> None:
        if not client.wait_for_service(timeout_sec=0.15):
            raise StoreError(
                f"{name} runtime update service is unavailable"
            )
        request = SetParameters.Request()
        request.parameters = [
            Parameter(
                name=name,
                value=ParameterValue(
                    type=ParameterType.PARAMETER_STRING,
                    string_value=value,
                ),
            )
        ]
        response = self._wait_future(client.call_async(request))
        if (
            response is None
            or not response.results
            or not all(result.successful for result in response.results)
        ):
            reason = (
                response.results[0].reason
                if response is not None and response.results
                else "no result"
            )
            raise StoreError(f"{name} runtime update rejected: {reason}")

    @staticmethod
    def _process_running(process: subprocess.Popen | None) -> bool:
        return process is not None and process.poll() is None

    @staticmethod
    def _runtime_command_matches(arguments: list[str], graph_file: str) -> bool:
        """Recognize only this package's launcher for the exact field graph."""
        expected_graph = os.path.realpath(graph_file)
        launch_match = any(
            arguments[index:index + 3] == [
                "launch", "marco_navigation", "route_runtime.launch.py"
            ]
            for index in range(max(0, len(arguments) - 2))
        )
        graph_match = any(
            argument.startswith("graf:=")
            and os.path.realpath(argument.split(":=", 1)[1]) == expected_graph
            for argument in arguments
        )
        return launch_match and graph_match

    def _route_runtime_pids(self, graph_file: str) -> list[int]:
        """Find same-user route launchers bound to exactly one graph file."""
        matches = []
        try:
            entries = os.scandir("/proc")
        except OSError:
            return matches
        with entries:
            for entry in entries:
                if not entry.name.isdigit():
                    continue
                pid = int(entry.name)
                if pid == os.getpid():
                    continue
                try:
                    if entry.stat(follow_symlinks=False).st_uid != os.getuid():
                        continue
                    with open(
                        os.path.join(entry.path, "cmdline"), "rb"
                    ) as stream:
                        arguments = [
                            value.decode("utf-8", errors="replace")
                            for value in stream.read().split(b"\0")
                            if value
                        ]
                except (FileNotFoundError, PermissionError, ProcessLookupError,
                        OSError):
                    continue
                if self._runtime_command_matches(arguments, graph_file):
                    matches.append(pid)
        return sorted(matches)

    @staticmethod
    def _pid_running(pid: int) -> bool:
        try:
            with open(f"/proc/{pid}/stat", encoding="utf-8") as stream:
                fields = stream.read().split()
            return len(fields) > 2 and fields[2] != "Z"
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            return False

    def _terminate_external_runtime(self, pid: int, graph_file: str) -> None:
        """Stop an adopted orphan only after rechecking PID, UID and command."""
        if not self._pid_running(pid):
            return
        candidates = self._route_runtime_pids(graph_file)
        if candidates != [pid]:
            raise StoreError(
                "adopted route runtime identity changed; refusing broad stop"
            )
        try:
            process_group = os.getpgid(pid)
        except ProcessLookupError:
            return
        if process_group != pid:
            raise StoreError(
                "adopted route runtime is not an isolated process group"
            )
        os.killpg(process_group, signal.SIGINT)
        deadline = time.monotonic() + 8.0
        while self._pid_running(pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        if self._pid_running(pid):
            os.killpg(process_group, signal.SIGTERM)
            deadline = time.monotonic() + 3.0
            while self._pid_running(pid) and time.monotonic() < deadline:
                time.sleep(0.05)
        if self._pid_running(pid):
            raise StoreError("adopted route runtime could not be stopped safely")

    def _runtime_services_present(self) -> bool:
        return any(client.service_is_ready() for client in (
            self._route_parameters_get,
            self._guard_parameters_get,
            self._route_state_client,
            self._dynamic_edges,
        ))

    def _navigation_tf_ready(self) -> bool:
        """Return true only when the localization TF chain is available."""
        try:
            return bool(self._tf.can_transform(
                str(self.get_parameter("map_frame").value),
                str(self.get_parameter("robot_frame").value),
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.0),
            ))
        except (TransformException, ValueError):
            return False

    def _runtime_parameter(self, client, name: str) -> str:
        request = GetParameters.Request()
        request.names = [name]
        response = self._wait_future(client.call_async(request), timeout=3.0)
        if response is None or len(response.values) != 1:
            raise StoreError(f"route runtime parameter missing: {name}")
        value = response.values[0]
        if value.type != ParameterType.PARAMETER_STRING:
            raise StoreError(f"route runtime parameter is not a string: {name}")
        return os.path.realpath(value.string_value)

    def _verify_existing_route_runtime(self, graph_file: str) -> None:
        clients = (
            self._route_parameters_get,
            self._guard_parameters_get,
            self._route_state_client,
            self._dynamic_edges,
        )
        if not all(client.service_is_ready() for client in clients):
            raise StoreError("existing route runtime services are incomplete")
        expected = os.path.realpath(graph_file)
        route_graph = self._runtime_parameter(
            self._route_parameters_get, "graph_filepath"
        )
        guard_graph = self._runtime_parameter(
            self._guard_parameters_get, "graph_file"
        )
        if route_graph != expected or guard_graph != expected:
            raise StoreError(
                "existing route runtime graph mismatch: "
                f"expected={expected}, route_server={route_graph}, "
                f"route_guard={guard_graph}"
            )
        state = self._wait_future(
            self._route_state_client.call_async(GetState.Request()), timeout=3.0
        )
        if (
            state is None
            or state.current_state.id != State.PRIMARY_STATE_ACTIVE
        ):
            label = state.current_state.label if state is not None else "missing"
            raise StoreError(f"existing route_server is not active: {label}")
        if not self._constraints_ready:
            raise StoreError("existing route_guard constraints are not ready")

    def _adopt_existing_route_runtime(self, value: dict) -> None:
        field_name = str(value.get("field_name", ""))
        package_hash = str(value.get("package_hash", ""))
        graph_file = os.path.realpath(str(value.get("graph_file", "")))
        self._verify_existing_route_runtime(graph_file)
        launchers = self._route_runtime_pids(graph_file)
        if len(launchers) != 1:
            raise StoreError(
                "existing route runtime launcher count is not one: "
                f"{len(launchers)}"
            )
        self._route_process = None
        self._external_route_pid = launchers[0]
        self._runtime_ready = True
        self._runtime_field_name = field_name
        self._runtime_package_hash = package_hash
        self._runtime_graph_file = graph_file

    def _reconcile_active_runtime(self) -> None:
        """Restore the persisted active-field runtime after a ROS restart."""
        if self._startup_reconcile_done or self._runtime_ready:
            self._startup_reconcile_done = True
            return
        elapsed = time.monotonic() - self._startup_reconcile_started
        # Give DDS discovery and transient-local constraint delivery time to
        # reveal an existing runtime before considering a new launch.
        if elapsed < 2.0:
            return
        timeout = float(self.get_parameter("route_runtime_timeout_s").value)
        with self._operation_lock:
            try:
                value = self._verified_active()
                if value is None:
                    self._startup_reconcile_done = True
                    return
                graph_file = os.path.realpath(str(value.get("graph_file", "")))
                launchers = self._route_runtime_pids(graph_file)
                services_present = self._runtime_services_present()
                if services_present:
                    if not self._constraints_ready and elapsed < timeout:
                        return
                    self._adopt_existing_route_runtime(value)
                    message = "Persisted field and existing route runtime restored"
                elif launchers and elapsed < timeout:
                    # The exact launcher exists but DDS services have not
                    # appeared yet. Starting another copy would be unsafe.
                    return
                elif launchers:
                    raise StoreError(
                        "persisted route runtime launcher has no ready services"
                    )
                else:
                    # real_system starts its control plane before the operator
                    # selects a map.  Starting Nav2 here without the complete
                    # map -> odom -> base_footprint chain makes the local
                    # costmap wait indefinitely for a frame that cannot exist
                    # yet.  Keep the persisted field pointer and retry after
                    # localization becomes available.
                    if not self._navigation_tf_ready():
                        return
                    self._ensure_activation_safe()
                    self._start_route_runtime(
                        str(value.get("field_name", "")),
                        str(value.get("package_hash", "")),
                    )
                    message = "Persisted field route runtime restarted"
                self._active_pub.publish(self._active_message(
                    value, message, active=True
                ))
                self.get_logger().info(message)
                self._startup_reconcile_done = True
            except (StoreError, OSError, subprocess.SubprocessError) as error:
                if elapsed < timeout:
                    return
                self._startup_reconcile_done = True
                self.get_logger().error(
                    f"active field runtime restore failed: {error}"
                )
                try:
                    value = self._store.read_active()
                except StoreError:
                    value = None
                self._active_pub.publish(self._active_message(
                    value,
                    f"Active field runtime restore failed: {error}",
                    active=False,
                ))

    def _wait_for_route_runtime(self, graph_file: str, started_at: float) -> None:
        timeout = float(self.get_parameter("route_runtime_timeout_s").value)
        deadline = time.monotonic() + timeout
        clients = (
            self._route_parameters_get,
            self._guard_parameters_get,
            self._route_state_client,
            self._dynamic_edges,
        )
        while time.monotonic() < deadline:
            if not self._process_running(self._route_process):
                code = self._route_process.poll() if self._route_process else None
                raise StoreError(
                    f"route runtime exited before readiness (exit={code})"
                )
            if all(client.service_is_ready() for client in clients):
                break
            time.sleep(0.05)
        else:
            raise StoreError(
                "route runtime services did not become available: "
                "route_server/route_guard/DynamicEdges"
            )

        while time.monotonic() < deadline:
            names = self.get_node_names_and_namespaces()
            counts = {
                required_name: sum(
                    1 for name, namespace in names
                    if name == required_name and namespace == "/"
                )
                for required_name in ("route_server", "route_guard")
            }
            duplicates = {
                name: count for name, count in counts.items() if count > 1
            }
            if duplicates:
                details = ", ".join(
                    f"/{name}={count}" for name, count in duplicates.items()
                )
                raise StoreError(
                    f"duplicate production route nodes detected: {details}"
                )
            if all(count == 1 for count in counts.values()):
                break
            time.sleep(0.05)
        else:
            details = ", ".join(
                f"/{name}={count}" for name, count in counts.items()
            )
            raise StoreError(
                f"route runtime nodes were not discovered exactly once: {details}"
            )

        route_graph = self._runtime_parameter(
            self._route_parameters_get, "graph_filepath"
        )
        guard_graph = self._runtime_parameter(
            self._guard_parameters_get, "graph_file"
        )
        expected = os.path.realpath(graph_file)
        if route_graph != expected or guard_graph != expected:
            raise StoreError(
                "route runtime graph mismatch: "
                f"expected={expected}, route_server={route_graph}, "
                f"route_guard={guard_graph}"
            )

        state = self._wait_future(
            self._route_state_client.call_async(GetState.Request()), timeout=3.0
        )
        if (
            state is None
            or state.current_state.id != State.PRIMARY_STATE_ACTIVE
        ):
            label = state.current_state.label if state is not None else "missing"
            raise StoreError(f"route_server is not active: {label}")

        while time.monotonic() < deadline:
            if not self._process_running(self._route_process):
                raise StoreError("route runtime exited while applying constraints")
            if (
                self._constraints_ready
                and self._constraints_ready_at >= started_at
            ):
                return
            time.sleep(0.02)
        raise StoreError(
            "route_guard did not confirm a successful DynamicEdges update"
        )

    def _stop_route_runtime(self) -> None:
        context_ok = rclpy.ok()
        if context_ok:
            self._publish_safe_stop()
        process = self._route_process
        external_pid = self._external_route_pid
        graph_file = self._runtime_graph_file
        self._runtime_ready = False
        self._runtime_field_name = ""
        self._runtime_package_hash = ""
        self._runtime_graph_file = ""
        self._constraints_ready = False
        self._constraints_ready_at = 0.0
        if process is None:
            if external_pid is not None:
                self._runtime_stopping = True
                try:
                    self._terminate_external_runtime(external_pid, graph_file)
                finally:
                    self._external_route_pid = None
                    self._runtime_stopping = False
                if not context_ok:
                    return
                deadline = time.monotonic() + 5.0
                while (
                    self._runtime_services_present()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.05)
                if self._runtime_services_present():
                    raise StoreError(
                        "adopted route runtime services remained after shutdown"
                    )
                return
            if not context_ok:
                return
            if self._runtime_services_present():
                raise StoreError(
                    "an existing route runtime is not owned by route_editor; "
                    "stop the previous route launch before changing the field"
                )
            return
        self._runtime_stopping = True
        try:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=8.0)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=3.0)
                    except subprocess.TimeoutExpired as error:
                        raise StoreError(
                            "route runtime could not be stopped safely"
                        ) from error
        finally:
            self._route_process = None
            self._external_route_pid = None
            self._runtime_stopping = False

        if not rclpy.ok():
            return
        deadline = time.monotonic() + 5.0
        while self._runtime_services_present() and time.monotonic() < deadline:
            time.sleep(0.05)
        if self._runtime_services_present():
            raise StoreError("route runtime services remained after shutdown")

    def _start_route_runtime(
        self, field_name: str, package_hash: str
    ) -> None:
        graph_file = os.path.realpath(str(self._store.graph_path(field_name)))
        if self._process_running(self._route_process):
            self._stop_route_runtime()
        elif self._runtime_services_present():
            raise StoreError(
                "route_server/route_guard already exists outside the managed "
                "production runtime; duplicate nodes were not started"
            )
        ros2 = shutil.which("ros2")
        if not ros2:
            raise StoreError("ros2 executable is not available in PATH")
        self._constraints_ready = False
        self._constraints_ready_at = 0.0
        started_at = time.monotonic()
        try:
            self._external_route_pid = None
            self._route_process = subprocess.Popen(
                [
                    ros2,
                    "launch",
                    "marco_navigation",
                    "route_runtime.launch.py",
                    f"graf:={graph_file}",
                ],
                start_new_session=True,
            )
            self._wait_for_route_runtime(graph_file, started_at)
        except Exception:
            if self._route_process is not None:
                try:
                    self._stop_route_runtime()
                except StoreError as stop_error:
                    self.get_logger().error(str(stop_error))
            raise
        self._runtime_ready = True
        self._runtime_field_name = field_name
        self._runtime_package_hash = package_hash
        self._runtime_graph_file = graph_file

    def _transition_runtime(self, field_name: str, package_hash: str) -> None:
        # Controlled restart guarantees that route_guard cannot retain a
        # previous field graph and avoids mutable runtime parameter races.
        self._start_route_runtime(field_name, package_hash)

    def _monitor_route_runtime(self) -> None:
        process = self._route_process
        external_pid = self._external_route_pid
        if process is None and external_pid is not None:
            if self._pid_running(external_pid) or self._runtime_stopping:
                return
            exit_code = "adopted-process-exited"
            self._external_route_pid = None
        elif process is None:
            return
        elif process.poll() is None or self._runtime_stopping:
            return
        else:
            exit_code = process.poll()
            self._route_process = None
        self._runtime_ready = False
        self._runtime_field_name = ""
        self._runtime_package_hash = ""
        self._runtime_graph_file = ""
        self._constraints_ready = False
        self._constraints_ready_at = 0.0
        self.get_logger().error(
            f"managed route runtime exited unexpectedly (exit={exit_code})"
        )
        try:
            value = self._store.read_active()
        except StoreError:
            value = None
        self._active_pub.publish(self._active_message(
            value,
            f"Route runtime unavailable (exit={exit_code})",
            active=False,
        ))

    def _now(self):
        return self.get_clock().now().to_msg()

    @staticmethod
    def _node_from_msg(message: FieldNode) -> NodeData:
        return NodeData(
            node_id=message.node_id,
            name=message.name,
            role=message.role,
            station=message.station_id,
            x=message.pose.x,
            y=message.pose.y,
            yaw=message.pose.theta,
            load_rule=message.load_rule,
            approach_mode=message.approach_mode,
            metadata=message.metadata_json,
        ).checked()

    @staticmethod
    def _node_msg(node: NodeData) -> FieldNode:
        message = FieldNode()
        message.node_id = node.node_id
        message.name = node.name
        message.role = node.role
        message.station_id = node.station
        message.pose.x = node.x
        message.pose.y = node.y
        message.pose.theta = node.yaw
        message.load_rule = node.load_rule
        message.approach_mode = node.approach_mode
        message.metadata_json = json.dumps(
            node.metadata, ensure_ascii=False, sort_keys=True
        )
        return message

    @staticmethod
    def _edge_from_msg(message: FieldEdge) -> EdgeData:
        return EdgeData(
            edge_id=message.edge_id,
            start_node_id=message.start_node_id,
            end_node_id=message.end_node_id,
            bidirectional=message.bidirectional,
            cost=message.cost,
            max_speed=message.max_speed,
            load_rule=message.load_rule,
            movement_direction=message.movement_direction,
            gate_event=message.gate_event,
            metadata=message.metadata_json,
        ).checked()

    @staticmethod
    def _edge_msg(edge: EdgeData) -> FieldEdge:
        message = FieldEdge()
        message.edge_id = edge.edge_id
        message.start_node_id = edge.start_node_id
        message.end_node_id = edge.end_node_id
        message.bidirectional = edge.bidirectional
        message.cost = edge.cost
        message.max_speed = edge.max_speed
        message.load_rule = edge.load_rule
        message.movement_direction = edge.movement_direction
        message.gate_event = edge.gate_event
        message.metadata_json = json.dumps(
            edge.metadata, ensure_ascii=False, sort_keys=True
        )
        return message

    def _active_message(
        self,
        value: dict | None,
        message: str = "",
        active: bool | None = None,
    ) -> ActiveField:
        output = ActiveField()
        output.header.stamp = self._now()
        output.header.frame_id = str(self.get_parameter("map_frame").value)
        output.active = value is not None if active is None else bool(active)
        if value:
            output.field_name = str(value.get("field_name", ""))
            output.package_version = str(value.get("package_version", ""))
            output.package_hash = str(value.get("package_hash", ""))
            output.graph_file = str(value.get("graph_file", ""))
            output.activated_at = str(value.get("activated_at", ""))
        output.message = message
        return output

    def _runtime_matches(self, value: dict | None) -> bool:
        if not value or not self._runtime_ready:
            return False
        return bool(
            str(value.get("field_name", "")) == self._runtime_field_name
            and str(value.get("package_hash", ""))
            == self._runtime_package_hash
            and os.path.realpath(str(value.get("graph_file", "")))
            == self._runtime_graph_file
            and self._constraints_ready
        )

    def _publish_active(self) -> ActiveField:
        try:
            value = self._verified_active()
            ready = self._runtime_matches(value)
            if value and not ready:
                message = "Active field pointer exists; route runtime is not ready"
            else:
                message = "Active field ready" if value else "No active field"
        except StoreError as error:
            value, ready, message = None, False, str(error)
        output = self._active_message(value, message, active=bool(value and ready))
        self._active_pub.publish(output)
        return output

    def _verified_active(self) -> dict | None:
        value = self._store.read_active()
        if value is None:
            return None
        field_name = str(value.get("field_name", ""))
        current_hash = self._store.package_hash(field_name)
        if value.get("package_hash") != current_hash:
            raise StoreError("active package hash no longer matches disk")
        report = self._store.read_validation(field_name)
        if (
            report.get("package_hash") != current_hash
            or report.get("valid") is not True
            or report.get("competition_profile")
            is not bool(self.get_parameter("competition_profile").value)
        ):
            raise StoreError("active package has no matching successful validation")
        graph = self._store.load_graph(field_name)
        result = validate_field(
            self._store,
            graph,
            bool(self.get_parameter("competition_profile").value),
        )
        if not result.valid:
            raise StoreError("active package is invalid: " + "; ".join(result.errors))
        return value

    def _is_currently_active(self, field_name: str) -> bool:
        active = self._store.read_active()
        return bool(active and active.get("field_name") == field_name)

    def _ensure_editable(self, field_name: str) -> None:
        if self._is_currently_active(field_name):
            raise StoreError(
                "active field is immutable; activate another field before editing"
            )

    def _validate(self, field_name: str) -> tuple[object, ValidationResult, str]:
        graph = self._store.load_graph(field_name)
        result = validate_field(
            self._store,
            graph,
            bool(self.get_parameter("competition_profile").value),
        )
        package_hash = self._store.package_hash(field_name)
        return graph, result, package_hash

    def _status_message(
        self,
        field_name: str,
        graph,
        result: ValidationResult,
        package_hash: str,
    ) -> FieldPackageStatus:
        status = FieldPackageStatus()
        status.header.stamp = self._now()
        status.header.frame_id = str(self.get_parameter("map_frame").value)
        status.field_name = field_name
        status.package_hash = package_hash
        status.node_count = len(graph.nodes)
        status.edge_count = len(graph.edges)
        status.errors = result.errors
        status.warnings = result.warnings
        if result.valid:
            status.state = FieldPackageStatus.STATE_VALID
            try:
                active = self._store.read_active()
                if (
                    active
                    and active.get("field_name") == field_name
                    and active.get("package_hash") == package_hash
                ):
                    status.state = FieldPackageStatus.STATE_ACTIVE
            except StoreError:
                pass
            status.message = "Field package is valid"
        else:
            status.state = FieldPackageStatus.STATE_ERROR
            status.message = f"Field package has {len(result.errors)} error(s)"
        self._status_pub.publish(status)
        return status

    def _publish_draft(self, field_name: str, graph, package_hash: str) -> None:
        status = FieldPackageStatus()
        status.header.stamp = self._now()
        status.header.frame_id = str(self.get_parameter("map_frame").value)
        status.state = FieldPackageStatus.STATE_DRAFT
        status.field_name = field_name
        status.package_hash = package_hash
        status.node_count = len(graph.nodes)
        status.edge_count = len(graph.edges)
        status.message = "Field graph changed; validation is required"
        self._status_pub.publish(status)

    def _on_get_graph(self, request, response):
        try:
            graph, result, package_hash = self._validate(request.field_name)
            response.nodes = [
                self._node_msg(node)
                for node in sorted(graph.nodes.values(), key=lambda item: item.node_id)
            ]
            response.edges = [
                self._edge_msg(edge)
                for edge in sorted(graph.edges.values(), key=lambda item: item.edge_id)
            ]
            response.status = self._status_message(
                request.field_name, graph, result, package_hash
            )
            response.success = True
            response.message = "Field graph loaded"
        except (StoreError, GraphError, ValueError, TypeError) as error:
            response.success = False
            response.message = str(error)
        return response

    @staticmethod
    def _station_config_msg(node: NodeData) -> StationApproachConfig:
        values = config_from_node(node)
        if values is None:
            raise GraphError(
                f"station '{node.station}' has no approach configuration"
            )
        message = StationApproachConfig()
        message.station_id = node.station
        message.station_node_id = node.node_id
        message.approach_qr_id = values["approach_qr_id"]
        message.dock_heading_yaw = values["dock_heading_yaw"]
        message.turn_direction = values["turn_direction"]
        message.line_follow_duration_s = values["line_follow_duration_s"]
        return message

    def _on_get_station_configs(self, request, response):
        try:
            graph = self._store.load_graph(request.field_name)
            response.configs = [
                self._station_config_msg(node)
                for node in sorted(graph.nodes.values(), key=lambda item: item.node_id)
                if node.role in ("pickup_dock", "dropoff_dock")
                and config_from_node(node) is not None
            ]
            response.package_hash = self._store.package_hash(request.field_name)
            response.success = True
            response.message = "Station approach configurations loaded"
        except (StoreError, GraphError, ValueError, TypeError) as error:
            response.success = False
            response.message = str(error)
        return response

    def _on_save_station_config(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_editable(request.field_name)
                graph = self._store.load_graph(request.field_name)
                config = request.config
                node = update_station(
                    graph,
                    config.station_id,
                    config.approach_qr_id,
                    config.dock_heading_yaw,
                    config.turn_direction,
                    config.line_follow_duration_s,
                )
                if (
                    config.station_node_id
                    and config.station_node_id != node.node_id
                ):
                    raise GraphError(
                        "station_node_id does not match the selected station"
                    )
                response.package_hash = self._store.save_graph(graph)
                self._publish_draft(
                    request.field_name, graph, response.package_hash
                )
                response.saved_config = self._station_config_msg(node)
                response.success = True
                response.message = "Station approach configuration saved atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_save_node(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_editable(request.field_name)
                graph = self._store.load_graph(request.field_name)
                node = graph.upsert_node(self._node_from_msg(request.node))
                response.package_hash = self._store.save_graph(graph)
                self._publish_draft(
                    request.field_name, graph, response.package_hash
                )
                response.saved_node = self._node_msg(node)
                response.success = True
                response.message = "Node saved atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _lookup_pose(self) -> tuple[float, float, float]:
        map_frame = str(self.get_parameter("map_frame").value)
        robot_frame = str(self.get_parameter("robot_frame").value)
        timeout = float(self.get_parameter("tf_timeout").value)
        try:
            transform = self._tf.lookup_transform(
                map_frame,
                robot_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=timeout),
            )
        except TransformException as error:
            raise StoreError(
                f"{map_frame} -> {robot_frame} transform unavailable: {error}"
            ) from error
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        yaw = math.atan2(
            2.0 * (rotation.w * rotation.z + rotation.x * rotation.y),
            1.0 - 2.0 * (rotation.y * rotation.y + rotation.z * rotation.z),
        )
        values = (translation.x, translation.y, yaw)
        if not all(math.isfinite(value) for value in values):
            raise StoreError("current TF pose contains non-finite values")
        return tuple(float(value) for value in values)

    def _on_save_current_pose_node(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_editable(request.field_name)
                node = self._node_from_msg(request.node)
                x, y, yaw = self._lookup_pose()
                node = NodeData(
                    node_id=node.node_id,
                    name=node.name,
                    role=node.role,
                    station=node.station,
                    x=x,
                    y=y,
                    yaw=yaw,
                    load_rule=node.load_rule,
                    approach_mode=node.approach_mode,
                    metadata=node.metadata,
                ).checked()
                graph = self._store.load_graph(request.field_name)
                graph.upsert_node(node)
                response.package_hash = self._store.save_graph(graph)
                self._publish_draft(
                    request.field_name, graph, response.package_hash
                )
                response.saved_node = self._node_msg(node)
                response.success = True
                response.message = "Current localized TF pose saved atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_delete_node(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_editable(request.field_name)
                graph = self._store.load_graph(request.field_name)
                response.deleted_edge_count = graph.delete_node(
                    request.node_id, request.delete_connected_edges
                )
                response.package_hash = self._store.save_graph(graph)
                self._publish_draft(
                    request.field_name, graph, response.package_hash
                )
                response.success = True
                response.message = "Node deleted atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_save_edge(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_editable(request.field_name)
                graph = self._store.load_graph(request.field_name)
                edge = graph.upsert_edge(self._edge_from_msg(request.edge))
                response.package_hash = self._store.save_graph(graph)
                self._publish_draft(
                    request.field_name, graph, response.package_hash
                )
                response.saved_edge = self._edge_msg(edge)
                response.success = True
                response.message = "Edge saved atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_delete_edge(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_editable(request.field_name)
                graph = self._store.load_graph(request.field_name)
                graph.delete_edge(request.edge_id)
                response.package_hash = self._store.save_graph(graph)
                self._publish_draft(
                    request.field_name, graph, response.package_hash
                )
                response.success = True
                response.message = "Edge deleted atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_validate(self, request, response):
        try:
            graph, result, package_hash = self._validate(request.field_name)
            self._store.write_validation(
                request.field_name,
                package_hash,
                result.valid,
                result.errors,
                result.warnings,
                bool(self.get_parameter("competition_profile").value),
            )
            response.status = self._status_message(
                request.field_name, graph, result, package_hash
            )
            response.success = result.valid
            response.message = response.status.message
        except (StoreError, GraphError, ValueError, TypeError) as error:
            response.success = False
            response.message = str(error)
        return response

    def _on_activate(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_activation_safe()
                graph, result, package_hash = self._validate(request.field_name)
                response.status = self._status_message(
                    request.field_name, graph, result, package_hash
                )
                if not result.valid:
                    raise StoreError("field package validation failed")
                if request.expected_hash and request.expected_hash != package_hash:
                    raise StoreError("requested hash does not match validated package")
                report = self._store.read_validation(request.field_name)
                if (
                    report.get("package_hash") != package_hash
                    or report.get("valid") is not True
                    or report.get("competition_profile")
                    is not bool(self.get_parameter("competition_profile").value)
                ):
                    raise StoreError(
                        "current package must have a matching successful validation"
                    )
                # Mission consumers see inactive while the controlled runtime
                # restart is in progress.  The active=true publication happens
                # only after both graph users and DynamicEdges are verified.
                previous = self._store.read_active()
                self._active_pub.publish(self._active_message(
                    previous,
                    "Route runtime is switching fields",
                    active=False,
                ))
                self._transition_runtime(request.field_name, package_hash)
                try:
                    # Always compare the validated hash again inside activation.
                    # This closes the race when a client omits expected_hash.
                    value = self._store.activate(
                        request.field_name,
                        package_hash,
                        bool(self.get_parameter("competition_profile").value),
                    )
                except Exception:
                    self._stop_route_runtime()
                    raise
                response.active_field = self._active_message(
                    value, "Field and route runtime activated atomically"
                )
                response.status.state = FieldPackageStatus.STATE_ACTIVE
                response.status.message = "Field package is active"
                self._active_pub.publish(response.active_field)
                self._status_pub.publish(response.status)
                response.success = True
                response.message = "Field and route runtime activated atomically"
            except (
                StoreError,
                GraphError,
                ValueError,
                TypeError,
                OSError,
                subprocess.SubprocessError,
            ) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_deactivate(self, request, response):
        with self._operation_lock:
            try:
                self._ensure_activation_safe(require_robot_status=True)
                active = self._store.read_active()
                if active is None:
                    raise StoreError("no active field to deactivate")
                field_name = str(active.get("field_name", ""))
                if field_name != str(request.field_name).strip():
                    raise StoreError(
                        f"active field mismatch: requested {request.field_name}, "
                        f"active {field_name}"
                    )
                package_hash = self._store.package_hash(field_name)
                if str(active.get("package_hash", "")) != package_hash:
                    raise StoreError("active package hash no longer matches disk")
                if request.expected_hash and request.expected_hash != package_hash:
                    raise StoreError(
                        "expected_hash does not match active package"
                    )

                # Stop motion-capable route components before making the field
                # editable.  Failure leaves the active pointer intact.
                self._stop_route_runtime()
                previous = self._store.deactivate(
                    field_name, request.expected_hash
                )
                graph, result, current_hash = self._validate(field_name)
                response.status = self._status_message(
                    field_name, graph, result, current_hash
                )
                response.status.state = (
                    FieldPackageStatus.STATE_VALID
                    if result.valid
                    else FieldPackageStatus.STATE_DRAFT
                )
                response.status.message = "Field deactivated and editable"
                response.active_field = self._active_message(
                    previous,
                    "Field deactivated; validate then activate after editing",
                    active=False,
                )
                self._active_pub.publish(response.active_field)
                self._status_pub.publish(response.status)
                response.success = True
                response.message = "Field deactivated and editable"
            except (StoreError, GraphError, ValueError, TypeError, OSError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_archive(self, request, response):
        with self._operation_lock:
            try:
                target = self._store.archive(request.field_name)
                response.success = True
                response.message = "Field archived atomically"
                response.archive_directory = str(target)
                status = FieldPackageStatus()
                status.header.stamp = self._now()
                status.state = FieldPackageStatus.STATE_ARCHIVED
                status.field_name = request.field_name
                status.message = response.message
                self._status_pub.publish(status)
            except (StoreError, OSError, ValueError) as error:
                response.success = False
                response.message = str(error)
        return response

    def _on_get_active(self, _request, response):
        try:
            value = self._verified_active()
            if value is None:
                response.success = False
                response.message = "No active field"
                response.active_field = self._active_message(None, response.message)
                return response
            field_name = str(value.get("field_name", ""))
            graph, result, package_hash = self._validate(field_name)
            response.status = self._status_message(
                field_name, graph, result, package_hash
            )
            response.active_field = self._active_message(
                value,
                (
                    "Active field ready"
                    if self._runtime_matches(value)
                    else "Active field pointer exists; route runtime is not ready"
                ),
                active=self._runtime_matches(value),
            )
            response.success = self._runtime_matches(value)
            response.message = response.active_field.message
        except (StoreError, GraphError, ValueError, TypeError) as error:
            response.success = False
            response.message = str(error)
        return response

    def _on_pixel_to_map(self, request, response):
        try:
            config = self._store.map_config(request.field_name)
            width, height = self._store.map_dimensions(request.field_name)
            pixel_x, pixel_y = float(request.pixel_x), float(request.pixel_y)
            screen_yaw = float(request.screen_yaw)
            if not all(math.isfinite(value) for value in (
                pixel_x, pixel_y, screen_yaw
            )):
                raise StoreError("pixel coordinates and yaw must be finite")
            resolution = float(config["resolution"])
            origin = tuple(
                float(value) for value in config["origin"]
            )
            x, y, yaw, inside = pixel_to_map(
                pixel_x,
                pixel_y,
                screen_yaw,
                width,
                height,
                resolution,
                origin,
            )
            response.pose.x = x
            response.pose.y = y
            response.pose.theta = yaw
            response.inside_map = inside
            response.map_width = width
            response.map_height = height
            response.success = True
            response.message = (
                "Pixel converted to map coordinates"
                if response.inside_map
                else "Pixel converted but lies outside the map"
            )
        except (StoreError, ValueError, TypeError) as error:
            response.success = False
            response.message = str(error)
        return response


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RouteEditorNode()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        try:
            node._stop_route_runtime()
        except StoreError as error:
            node.get_logger().error(str(error))
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
