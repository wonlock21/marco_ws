#!/usr/bin/env python3
"""ROS service facade for semantic field route editing."""

from __future__ import annotations

import json
import math
import os
import threading

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
from nav2_msgs.srv import ManageLifecycleNodes
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters
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
            lambda message: setattr(
                self, "_linear_speed", float(message.twist.twist.linear.x)
            ),
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

    def _on_robot_status(self, message: RobotStatus) -> None:
        self._robot_status_seen = True
        self._mission_state = message.mission_state
        self._linear_speed = float(message.linear_speed)

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

    def _ensure_activation_safe(self) -> None:
        runtime_present = any(
            client.service_is_ready() for client in self._lifecycle_clients
        )
        if runtime_present and not self._robot_status_seen:
            raise StoreError(
                "field cannot change until current robot status is available"
            )
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
            return
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

    def _transition_runtime(self, field_name: str) -> None:
        field_dir = self._store.field_directory(field_name)
        managed = self._manage_runtime(ManageLifecycleNodes.Request.PAUSE)
        try:
            self._set_runtime_parameter(
                self._map_parameters,
                "yaml_filename",
                str(field_dir / "map.yaml"),
            )
            self._set_runtime_parameter(
                self._route_parameters,
                "graph_filepath",
                str(field_dir / "route.geojson"),
            )
        except Exception:
            for client in reversed(managed):
                request = ManageLifecycleNodes.Request()
                request.command = ManageLifecycleNodes.Request.RESUME
                try:
                    self._wait_future(client.call_async(request))
                except StoreError:
                    pass
            raise
        for client in reversed(managed):
            request = ManageLifecycleNodes.Request()
            request.command = ManageLifecycleNodes.Request.RESUME
            response = self._wait_future(client.call_async(request))
            if response is None or not response.success:
                raise StoreError("lifecycle manager failed to resume new field")

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
        self, value: dict | None, message: str = ""
    ) -> ActiveField:
        output = ActiveField()
        output.header.stamp = self._now()
        output.header.frame_id = str(self.get_parameter("map_frame").value)
        output.active = value is not None
        if value:
            output.field_name = str(value.get("field_name", ""))
            output.package_version = str(value.get("package_version", ""))
            output.package_hash = str(value.get("package_hash", ""))
            output.graph_file = str(value.get("graph_file", ""))
            output.activated_at = str(value.get("activated_at", ""))
        output.message = message
        return output

    def _publish_active(self) -> ActiveField:
        try:
            value = self._verified_active()
            message = "Active field ready" if value else "No active field"
        except StoreError as error:
            value, message = None, str(error)
        output = self._active_message(value, message)
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
                self._transition_runtime(request.field_name)
                # Always compare the validated hash again inside activation. This
                # also closes the race when a rosbridge client omits expected_hash.
                value = self._store.activate(
                    request.field_name,
                    package_hash,
                    bool(self.get_parameter("competition_profile").value),
                )
                response.active_field = self._active_message(
                    value, "Field activated atomically"
                )
                response.status.state = FieldPackageStatus.STATE_ACTIVE
                response.status.message = "Field package is active"
                self._active_pub.publish(response.active_field)
                self._status_pub.publish(response.status)
                response.success = True
                response.message = "Field activated atomically"
            except (StoreError, GraphError, ValueError, TypeError) as error:
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
                "Active field ready",
            )
            response.success = True
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
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
