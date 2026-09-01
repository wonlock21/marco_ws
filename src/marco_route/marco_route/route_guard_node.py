"""Runtime monitor for selected Nav2 graph paths and route deviation."""

from __future__ import annotations

import json
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Path
from nav2_msgs.msg import SpeedLimit
from nav2_msgs.srv import DynamicEdges
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from std_msgs.msg import Bool, Float32, String
from tf2_ros import Buffer, TransformException, TransformListener

from .route_guard_core import (
    RouteEdge,
    edge_allowed,
    guard_decision,
    load_route_graph,
    nearest_edge,
    nearest_projection,
)


class RouteGuard(Node):
    def __init__(self) -> None:
        super().__init__("route_guard")
        self.declare_parameter("graph_file", "")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter("warning_threshold_m", 0.05)
        self.declare_parameter("slowdown_threshold_m", 0.08)
        self.declare_parameter("stop_threshold_m", 0.10)
        self.declare_parameter("slowdown_speed_mps", 0.06)
        self.declare_parameter("command_freshness_s", 0.50)
        graph_file = str(self.get_parameter("graph_file").value).strip()
        if not graph_file:
            raise ValueError("route_guard graph_file cannot be empty")
        self._graph = load_route_graph(graph_file)
        self._map_frame = str(self.get_parameter("map_frame").value)
        self._base_frame = str(self.get_parameter("base_frame").value)
        self._warning = float(self.get_parameter("warning_threshold_m").value)
        self._slowdown = float(self.get_parameter("slowdown_threshold_m").value)
        self._stop = float(self.get_parameter("stop_threshold_m").value)
        self._slow_speed = float(self.get_parameter("slowdown_speed_mps").value)
        self._command_freshness = float(
            self.get_parameter("command_freshness_s").value
        )
        # Validate parameters before any motion-related publisher is created.
        guard_decision(
            0.0, self._warning, self._slowdown, self._stop, self._slow_speed
        )

        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._cte_pub = self.create_publisher(
            Float32, "/route/cross_track_error", 10
        )
        self._edge_pub = self.create_publisher(String, "/route/active_edge", 10)
        self._next_pub = self.create_publisher(String, "/route/next_node", 10)
        self._state_pub = self.create_publisher(String, "/route/state", latched)
        self._event_pub = self.create_publisher(String, "/route/events", 20)
        self._path_pub = self.create_publisher(Path, "/route/selected_path", latched)
        self._constraints_pub = self.create_publisher(
            Bool, "/route/load_constraints_ready", latched
        )
        self._limit_pub = self.create_publisher(
            SpeedLimit, "/route/guard_speed_limit", 10
        )
        self._edge_limit_pub = self.create_publisher(
            SpeedLimit, "/route_speed_limit", 10
        )
        self._guard_pub = self.create_publisher(
            Twist, "/cmd_vel_safety_guard", 10
        )

        self.create_subscription(Path, "/received_global_plan", self._on_path, 10)
        self.create_subscription(Path, "/plan", self._on_path, 10)
        self.create_subscription(Twist, "/cmd_vel_raw", self._on_command, 10)
        self.create_subscription(Bool, "/route/load_state", self._on_load, latched)

        self._dynamic = self.create_client(
            DynamicEdges,
            "/route_server/DynamicEdgesScorer/adjust_edges",
        )
        self._tf = Buffer()
        self._listener = TransformListener(self._tf, self)
        self._path: list[tuple[float, float]] = []
        self._selected_edges: tuple[RouteEdge, ...] = ()
        self._active_edge: RouteEdge | None = None
        self._last_command_wall = 0.0
        self._command_moving = False
        self._loaded = False
        self._desired_closed: set[int] = set()
        self._applied_closed: set[int] = set()
        self._dynamic_future = None
        self._constraints_ready = False
        self._last_band = "idle"
        self._last_state = ""
        self._update_load_constraints()
        self._constraints_pub.publish(Bool(data=False))
        self.create_timer(0.05, self._tick)
        self.get_logger().info(
            f"route_guard ready: {len(self._graph.edges)} edges, "
            f"bands={self._warning:.2f}/{self._slowdown:.2f}/{self._stop:.2f} m"
        )

    def _event(self, event: str, **fields) -> None:
        payload = {
            "stamp": self.get_clock().now().nanoseconds / 1.0e9,
            "event": event,
        }
        payload.update(fields)
        self._event_pub.publish(
            String(data=json.dumps(payload, ensure_ascii=True, sort_keys=True))
        )

    def _on_command(self, message: Twist) -> None:
        self._last_command_wall = time.monotonic()
        self._command_moving = (
            abs(message.linear.x) > 1.0e-4
            or abs(message.linear.y) > 1.0e-4
            or abs(message.angular.z) > 1.0e-4
        )

    def _on_load(self, message: Bool) -> None:
        loaded = bool(message.data)
        if loaded == self._loaded:
            return
        self._loaded = loaded
        self._update_load_constraints()
        self._set_constraints_ready(False)
        self._event("load_state_changed", loaded=loaded)

    def _update_load_constraints(self) -> None:
        self._desired_closed = {
            edge.feature_id
            for edge in self._graph.edges
            if not edge_allowed(edge, self._loaded)
        }

    def _update_dynamic_edges(self) -> None:
        if self._dynamic_future is not None:
            if not self._dynamic_future.done():
                return
            try:
                response = self._dynamic_future.result()
                if response is None or not response.success:
                    self.get_logger().error("Route Server load edge update rejected")
                    self._set_constraints_ready(False)
                    self._dynamic_future = None
                    return
                self._applied_closed = set(self._dynamic_target)
                self._set_constraints_ready(True)
            except Exception as error:  # ROS future boundary
                self.get_logger().error(f"Route Server load edge update failed: {error}")
                self._set_constraints_ready(False)
            self._dynamic_future = None
        if self._desired_closed == self._applied_closed:
            self._set_constraints_ready(True)
            return
        if not self._dynamic.service_is_ready():
            return
        request = DynamicEdges.Request()
        request.closed_edges = sorted(self._desired_closed - self._applied_closed)
        request.opened_edges = sorted(self._applied_closed - self._desired_closed)
        self._dynamic_target = set(self._desired_closed)
        self._dynamic_future = self._dynamic.call_async(request)

    def _set_constraints_ready(self, ready: bool) -> None:
        ready = bool(ready)
        if ready == self._constraints_ready:
            return
        self._constraints_ready = ready
        self._constraints_pub.publish(Bool(data=ready))

    def _on_path(self, message: Path) -> None:
        if message.header.frame_id not in ("", self._map_frame):
            self.get_logger().warning(
                f"route path frame rejected: {message.header.frame_id}"
            )
            return
        points = [
            (float(pose.pose.position.x), float(pose.pose.position.y))
            for pose in message.poses
        ]
        if len(points) < 2 or not all(
            math.isfinite(value) for point in points for value in point
        ):
            return
        self._path = points
        ordered: list[RouteEdge] = []
        # Sampling avoids publishing hundreds of duplicate nearest-edge matches.
        stride = max(1, len(points) // 100)
        for point in points[::stride] + [points[-1]]:
            match = nearest_edge(point, self._graph.edges)
            if match is not None and (
                not ordered or ordered[-1].feature_id != match[0].feature_id
            ):
                ordered.append(match[0])
        self._selected_edges = tuple(ordered)
        output = Path()
        output.header = message.header
        output.header.frame_id = self._map_frame
        output.header.stamp = self.get_clock().now().to_msg()
        output.poses = list(message.poses)
        self._path_pub.publish(output)
        self._event(
            "route_selected",
            edge_ids=[edge.logical_id for edge in self._selected_edges],
        )

    def _publish_limit(self, value: float) -> None:
        message = SpeedLimit()
        message.percentage = False
        message.speed_limit = float(value)
        self._limit_pub.publish(message)

    def _publish_edge_limit(self, value: float) -> None:
        message = SpeedLimit()
        message.percentage = False
        message.speed_limit = float(value)
        self._edge_limit_pub.publish(message)

    def _publish_state(self, payload: dict) -> None:
        text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        if text != self._last_state:
            self._state_pub.publish(String(data=text))
            self._last_state = text

    def _set_active_edge(self, edge: RouteEdge | None) -> None:
        if edge is self._active_edge or (
            edge is not None
            and self._active_edge is not None
            and edge.feature_id == self._active_edge.feature_id
        ):
            return
        previous = self._active_edge
        if previous is not None:
            self._event(
                "edge_exit",
                edge_id=previous.logical_id,
                gate_event=previous.gate_event,
            )
        self._active_edge = edge
        if edge is not None:
            self._event(
                "edge_enter",
                edge_id=edge.logical_id,
                next_node=edge.end_name,
                gate_event=edge.gate_event,
            )

    def _tick(self) -> None:
        self._update_dynamic_edges()
        if len(self._path) < 2:
            self._publish_state({"state": "idle", "reason": "no_selected_path"})
            return
        try:
            transform = self._tf.lookup_transform(
                self._map_frame, self._base_frame, Time()
            )
        except TransformException as error:
            self._publish_state({"state": "unavailable", "reason": str(error)})
            return
        point = (
            float(transform.transform.translation.x),
            float(transform.transform.translation.y),
        )
        projection = nearest_projection(point, self._path)
        candidates = self._selected_edges or self._graph.edges
        active_match = nearest_edge(point, candidates)
        active_edge = active_match[0] if active_match is not None else None
        self._set_active_edge(active_edge)
        decision = guard_decision(
            projection.distance,
            self._warning,
            self._slowdown,
            self._stop,
            self._slow_speed,
        )
        self._cte_pub.publish(Float32(data=float(projection.distance)))
        self._edge_pub.publish(String(
            data=str(active_edge.logical_id) if active_edge is not None else ""
        ))
        self._next_pub.publish(String(
            data=active_edge.end_name if active_edge is not None else ""
        ))
        self._publish_limit(decision.speed_limit)
        self._publish_edge_limit(active_edge.max_speed if active_edge else 0.0)
        command_active = (
            self._command_moving
            and time.monotonic() - self._last_command_wall
            <= self._command_freshness
        )
        if decision.stop and command_active:
            self._guard_pub.publish(Twist())
        if decision.band != self._last_band:
            self._event(
                "deviation_band_changed",
                previous=self._last_band,
                current=decision.band,
                cross_track_error=projection.distance,
            )
            self._last_band = decision.band
        self._publish_state({
            "state": decision.band,
            "cross_track_error": projection.distance,
            "speed_limit": decision.speed_limit,
            "stop": bool(decision.stop and command_active),
            "stop_reason": decision.reason if decision.stop else "",
            "active_edge": active_edge.logical_id if active_edge else None,
            "next_node": active_edge.end_name if active_edge else "",
            "selected_edges": [edge.logical_id for edge in self._selected_edges],
            "loaded": self._loaded,
            "load_blocked_feature_edges": sorted(self._desired_closed),
        })


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RouteGuard()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
