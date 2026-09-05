#!/usr/bin/env python3
"""Fail-safe shared Phase-10 mission state machine for PLC, mock PLC and GUI."""

from __future__ import annotations

import copy
import json
import math
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import rclpy
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Pose2D, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, Path
from nav2_msgs.action import ComputeRoute, FollowPath, Spin
from nav2_msgs.msg import SpeedLimit
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from rclpy.time import Time
from sensor_msgs.msg import BatteryState, Imu, LaserScan
from std_msgs.msg import Bool, Empty, Float32, String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformException, TransformListener

from marco_mission.localization_validity import LocalizationHealth
from marco_mission.localization_validity import evaluate_localization
from marco_mission.station_qr_gate import StationQrGate
from marco_msgs.action import DockToStation, LiftLoad
from marco_msgs.msg import ActiveField, QrDetection, RobotStatus
from marco_msgs.srv import (AssignTask, CancelMission, GatePermission,
                            ResetMissionSafety, StartMission, SubmitManualTask,
                            SubmitMission, TaskComplete)


class MissionAbort(RuntimeError):
    """Controlled mission failure carrying a PLC-safe diagnostic."""


class MissionActionFailure(MissionAbort):
    """Action failure retaining the ROS goal status for bounded recovery."""

    def __init__(self, label: str, status: int) -> None:
        super().__init__(f'{label} status={status}')
        self.status = int(status)


@dataclass(frozen=True)
class JunctionManeuver:
    """One geometry-derived transit-node turn in a computed route."""

    node_id: int
    node_name: str
    x: float
    y: float
    incoming_heading: float
    outgoing_heading: float
    turn_angle: float


def _route_edge_heading(edge, movement_direction: str = 'forward') -> float:
    """Return robot body heading on one directed route edge."""
    dx = float(edge.end.x - edge.start.x)
    dy = float(edge.end.y - edge.start.y)
    if not all(math.isfinite(value) for value in (dx, dy)):
        raise MissionAbort('rota kenari sonlu olmayan koordinat iceriyor')
    if math.hypot(dx, dy) <= 1.0e-6:
        raise MissionAbort('rota kenari sifir uzunlukta')
    heading = math.atan2(dy, dx)
    if movement_direction == 'reverse':
        heading += math.pi
    return math.atan2(math.sin(heading), math.cos(heading))


def _route_junction_maneuvers(
    route,
    node_records: Dict[int, Dict[str, Any]],
    edge_directions: Dict[int, str],
    minimum_turn: float,
    maximum_turn: float,
):
    """Find approximately 90-degree turns from ordered route geometry."""
    nodes = list(getattr(route, 'nodes', []))
    edges = list(getattr(route, 'edges', []))
    if not edges:
        return [], None
    if len(nodes) != len(edges) + 1:
        raise MissionAbort('Route Server dugum/kenar sirasi tutarsiz')
    maneuvers = []
    for index, (incoming, outgoing) in enumerate(zip(edges, edges[1:])):
        junction = nodes[index + 1]
        record = node_records.get(int(junction.nodeid))
        if record is None or record.get('role') != 'transit':
            continue
        incoming_heading = _route_edge_heading(
            incoming,
            edge_directions.get(int(incoming.edgeid), 'forward'),
        )
        outgoing_heading = _route_edge_heading(
            outgoing,
            edge_directions.get(int(outgoing.edgeid), 'forward'),
        )
        turn_angle = math.atan2(
            math.sin(outgoing_heading - incoming_heading),
            math.cos(outgoing_heading - incoming_heading),
        )
        if minimum_turn <= abs(turn_angle) <= maximum_turn:
            maneuvers.append(JunctionManeuver(
                node_id=int(junction.nodeid),
                node_name=str(record.get('name', junction.nodeid)),
                x=float(junction.position.x),
                y=float(junction.position.y),
                incoming_heading=incoming_heading,
                outgoing_heading=outgoing_heading,
                turn_angle=turn_angle,
            ))
    last = edges[-1]
    final_heading = _route_edge_heading(
        last,
        edge_directions.get(int(last.edgeid), 'forward'),
    )
    return maneuvers, final_heading


def _split_path_at_junctions(
    path: Path,
    maneuvers,
    match_tolerance: float,
):
    """Split a Route Server path at ordered maneuver coordinates."""
    if not maneuvers:
        return [copy.deepcopy(path)]
    if len(path.poses) < 2:
        raise MissionAbort('segmentlenecek rota en az iki pose icermeli')
    split_indices = []
    previous = 0
    for maneuver in maneuvers:
        candidates = range(previous + 1, len(path.poses) - 1)
        try:
            index = min(candidates, key=lambda item: math.hypot(
                float(path.poses[item].pose.position.x) - maneuver.x,
                float(path.poses[item].pose.position.y) - maneuver.y,
            ))
        except ValueError as error:
            raise MissionAbort(
                f'{maneuver.node_name}: rota junction noktasinda bolunemedi'
            ) from error
        distance = math.hypot(
            float(path.poses[index].pose.position.x) - maneuver.x,
            float(path.poses[index].pose.position.y) - maneuver.y,
        )
        if distance > match_tolerance:
            raise MissionAbort(
                f'{maneuver.node_name}: junction/path esleme hatasi '
                f'{distance:.3f} m'
            )
        split_indices.append(index)
        previous = index

    segments = []
    start = 0
    for end in [*split_indices, len(path.poses) - 1]:
        segment = Path()
        segment.header = copy.deepcopy(path.header)
        segment.poses = copy.deepcopy(path.poses[start:end + 1])
        if len(segment.poses) < 2:
            raise MissionAbort('junction rota segmenti en az iki pose icermeli')
        segments.append(segment)
        start = end
    return segments


def _last_path_segment_heading(path) -> float:
    """Return the geometric heading of the last non-zero path segment."""
    if len(path.poses) < 2:
        raise MissionAbort('rota heading icin en az iki pose gerekli')
    end = path.poses[-1].pose.position
    for stamped in reversed(path.poses[:-1]):
        start = stamped.pose.position
        dx = float(end.x - start.x)
        dy = float(end.y - start.y)
        if math.hypot(dx, dy) > 1.0e-6:
            return math.atan2(dy, dx)
    raise MissionAbort('rota heading hesaplanabilecek sonlu segment yok')


def _terminal_abort_is_acceptable(
    *,
    target_x: float,
    target_y: float,
    target_yaw: float,
    robot_x: float,
    robot_y: float,
    robot_yaw: float,
    position_tolerance: float,
    yaw_tolerance: float,
):
    """Accept only an ABORTED FollowPath already inside strict tolerances."""
    position_error = math.hypot(target_x - robot_x, target_y - robot_y)
    yaw_error = abs(math.atan2(
        math.sin(target_yaw - robot_yaw),
        math.cos(target_yaw - robot_yaw),
    ))
    accepted = (
        position_error <= position_tolerance
        and yaw_error <= yaw_tolerance
    )
    return accepted, position_error, yaw_error


class MissionManager(Node):
    """Own exactly one mission and one motion action at a time."""

    def __init__(self) -> None:
        super().__init__('mission_manager')
        graph_default = os.path.join(get_package_share_directory('marco_navigation'),
                                     'graphs', 'phase10_route.geojson')
        for name, default in (
            ('task_source', 'plc'), ('manual_task_enabled', False),
            ('simulate_steps', False),
            ('graph_file', graph_default), ('gate_node', 'kapi_q5'),
            ('return_gate_node', 'kapi_q6'),
            ('home_node', 'bekla_A'), ('action_timeout_s', 120.0),
            ('gate_timeout_s', 30.0), ('plc_freshness_s', 3.0),
            ('localization_tf_timeout_s', 2.0),
            ('localization_scan_timeout_s', 2.0),
            ('localization_odom_timeout_s', 2.0),
            ('localization_tf_lookup_timeout_s', 0.05),
            ('localization_max_position_covariance', 1.0),
            ('route_constraints_timeout_s', 3.0),
            ('station_qr_max_age_s', 0.75),
            ('station_qr_debounce_s', 0.15),
            ('station_qr_wait_s', 3.0),
            ('station_turn_timeout_s', 30.0),
            ('station_turn_yaw_tolerance_deg', 3.0),
            ('station_turn_min_angle_deg', 150.0),
            ('station_turn_max_angle_deg', 210.0),
            ('station_turn_imu_timeout_s', 0.5),
            ('junction_turn_timeout_s', 20.0),
            ('junction_turn_yaw_tolerance_deg', 5.0),
            ('junction_turn_min_angle_deg', 60.0),
            ('junction_turn_max_angle_deg', 120.0),
            ('junction_path_match_tolerance_m', 0.25),
            ('imu_enabled', True),
            ('route_terminal_position_tolerance_m', 0.075),
            ('route_terminal_yaw_tolerance_deg', 10.0),
            ('motion_stop_timeout_s', 3.0),
            ('motion_stop_settle_s', 0.4),
            ('motion_stop_linear_tolerance', 0.01),
            ('motion_stop_angular_tolerance', 0.03),
            ('require_safety_supervisor', True),
            ('require_base_communication', True),
            ('base_communication_timeout_s', 1.0),
            ('require_active_field', False),
            ('status_rate_hz', 5.0),
        ):
            self.declare_parameter(name, default)
        self._default_source = str(self.get_parameter('task_source').value)
        if bool(self.get_parameter('simulate_steps').value):
            raise ValueError('Faz 10 sahte sleep modu kaldirildi; simulate_steps:=false kullan')
        self._manual_enabled = bool(self.get_parameter('manual_task_enabled').value)
        self._configured_gate_node = str(self.get_parameter('gate_node').value)
        self._configured_return_gate_node = str(
            self.get_parameter('return_gate_node').value)
        self._configured_home_node = str(self.get_parameter('home_node').value)
        self._gate_node = self._configured_gate_node
        self._return_gate_node = self._configured_return_gate_node
        self._home_node = self._configured_home_node
        self._action_timeout = float(self.get_parameter('action_timeout_s').value)
        self._gate_timeout = float(self.get_parameter('gate_timeout_s').value)
        self._plc_freshness = float(self.get_parameter('plc_freshness_s').value)
        self._tf_freshness = float(
            self.get_parameter('localization_tf_timeout_s').value)
        self._scan_freshness = float(
            self.get_parameter('localization_scan_timeout_s').value)
        self._odom_freshness = float(
            self.get_parameter('localization_odom_timeout_s').value)
        self._tf_lookup_timeout = float(
            self.get_parameter('localization_tf_lookup_timeout_s').value)
        self._max_position_covariance = float(
            self.get_parameter('localization_max_position_covariance').value)
        self._route_constraints_timeout = float(
            self.get_parameter('route_constraints_timeout_s').value)
        self._imu_enabled = bool(self.get_parameter('imu_enabled').value)
        self._require_active_field = bool(
            self.get_parameter('require_active_field').value)
        self._require_safety_supervisor = bool(
            self.get_parameter('require_safety_supervisor').value)
        self._require_base_communication = bool(
            self.get_parameter('require_base_communication').value)
        self._base_communication_timeout = float(
            self.get_parameter('base_communication_timeout_s').value)
        self._graph_file = os.path.realpath(
            str(self.get_parameter('graph_file').value))
        self._nodes = self._load_graph(self._graph_file)
        self._edge_directions = self._load_edge_directions(self._graph_file)
        self._resolve_special_nodes()
        if self._default_source not in ('plc', 'mock_plc'):
            raise ValueError('task_source plc veya mock_plc olmali')

        self._cb = ReentrantCallbackGroup()
        self._lock = threading.RLock()
        self._busy = False
        self._running = False
        self._abort_reason = ''
        self._latched_abort = False
        self._active_goal = None
        self._active_kind = ''
        self._state = RobotStatus.STATE_IDLE
        self._task_id = self._source = self._pickup = self._dropoff = ''
        self._route_nodes = []
        self._current_stop_index = 0
        self._return_home = True
        self._known_task_ids = set()
        self._next_node = self._edge = self._last_qr = ''
        self._last_qr_detected = False
        self._last_qr_pose = Pose2D()
        self._last_qr_confidence = 0.0
        self._last_qr_camera = ''
        self._last_qr_seen = 0.0
        self._qr_gate = StationQrGate(
            max_age_s=float(self.get_parameter('station_qr_max_age_s').value),
            debounce_s=float(self.get_parameter('station_qr_debounce_s').value),
        )
        self._mission_started_wall = 0.0
        self._mission_elapsed = 0.0
        self._status_detail = 'goreve hazir'
        self._current_node = self._home_node
        self._gate_ok = self._estop = self._manual = self._obstacle = False
        self._gate_entry_node = ''
        self._gate_direction = ''
        self._gate_crossing_id = ''
        self._gate_sequence = 0
        self._base_communication_ok = False
        self._base_communication_seen = 0.0
        self._plc_connected = False
        self._plc_seen = 0.0
        self._loaded = False
        self._pose: Optional[PoseWithCovarianceStamped] = None
        self._scan_seen = 0.0
        self._odom_seen = 0.0
        self._filtered_odom_seen = 0.0
        self._imu_seen = 0.0
        self._filtered_yaw = math.nan
        self._cross_track = math.nan
        self._route_speed_limit = 0.0
        self._route_guard_state = 'idle'
        self._route_stop_reason = ''
        self._selected_route_edges = []
        self._route_constraints_ready = False
        self._linear_speed = 0.0
        self._angular_speed = 0.0
        self._battery_voltage = math.nan
        self._battery_current = math.nan
        self._battery_temperature = math.nan
        self._active_field_ready = False
        self._active_field_name = ''
        self._active_field_version = ''
        self._active_field_hash = ''
        self._docking_target = ''
        self._docking_duration = 0.0
        self._docking_elapsed = 0.0
        self._docking_remaining = 0.0
        self._docking_lane_active = False
        self._docking_camera_valid = False
        self._docking_stopped = True
        self._docking_error = ''

        self._tf_buffer = Buffer(cache_time=Duration(seconds=10.0))
        self._tf_listener = TransformListener(
            self._tf_buffer, self, spin_thread=False)

        self._status_pub = self.create_publisher(RobotStatus, '/robot_status', 10)
        self._event_pub = self.create_publisher(String, '/mission/events', 50)
        self._task_pub = self.create_publisher(String, '/task_command', 10)
        self._speed_reset_pub = self.create_publisher(
            Empty, '/route/speed_limit_reset', 10)
        load_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._load_state_pub = self.create_publisher(
            Bool, '/route/load_state', load_qos)
        self.create_subscription(Bool, '/base/estop', self._on_estop, 10,
                                 callback_group=self._cb)
        self.create_subscription(Bool, '/base/manual_mode', self._on_manual, 10,
                                 callback_group=self._cb)
        self.create_subscription(
            Bool, '/base/communication_ok', self._on_base_communication, 10,
            callback_group=self._cb)
        self.create_subscription(Bool, '/safety/obstacle_detected',
                                 lambda m: setattr(self, '_obstacle', bool(m.data)), 10,
                                 callback_group=self._cb)
        self.create_subscription(Bool, '/safety/navigation_abort',
                                 self._on_safety_abort, 10, callback_group=self._cb)
        self.create_subscription(Bool, '/plc/connected', self._on_plc_connected, 10,
                                 callback_group=self._cb)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose',
                                 self._on_pose, 10, callback_group=self._cb)
        self.create_subscription(LaserScan, '/scan', self._on_scan,
                                 qos_profile_sensor_data,
                                 callback_group=self._cb)
        self.create_subscription(Odometry, '/odom', self._on_odom, 10,
                                 callback_group=self._cb)
        self.create_subscription(Odometry, '/odometry/filtered',
                                 self._on_filtered_odom, 10,
                                 callback_group=self._cb)
        self.create_subscription(Imu, '/imu/data_raw', self._on_imu,
                                 qos_profile_sensor_data,
                                 callback_group=self._cb)
        self.create_subscription(Float32, '/route/cross_track_error',
                                 lambda m: setattr(self, '_cross_track', float(m.data)),
                                 10, callback_group=self._cb)
        self.create_subscription(String, '/route/active_edge',
                                 lambda m: setattr(self, '_edge', m.data), 10,
                                 callback_group=self._cb)
        self.create_subscription(String, '/route/next_node',
                                 lambda m: setattr(self, '_next_node', m.data), 10,
                                 callback_group=self._cb)
        self.create_subscription(String, '/route/state', self._on_route_state, 10,
                                 callback_group=self._cb)
        self.create_subscription(
            Bool, '/route/load_constraints_ready',
            lambda m: setattr(self, '_route_constraints_ready', bool(m.data)),
            load_qos, callback_group=self._cb)
        self.create_subscription(SpeedLimit, '/speed_limit',
                                 lambda m: setattr(
                                     self, '_route_speed_limit',
                                     float(m.speed_limit)), 10,
                                 callback_group=self._cb)
        self._safety_reset = self.create_client(
            Trigger, '/safety/reset', callback_group=self._cb)
        self.create_subscription(QrDetection, '/qr/detection', self._on_qr, 10,
                                 callback_group=self._cb)
        self.create_subscription(BatteryState, '/base/battery', self._on_battery,
                                 10, callback_group=self._cb)
        active_field_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(
            ActiveField, '/fields/active', self._on_active_field,
            active_field_qos, callback_group=self._cb)

        self._assign = self.create_client(AssignTask, '/plc/assign_task',
                                          callback_group=self._cb)
        self._gate = self.create_client(GatePermission, '/plc/gate_permission',
                                        callback_group=self._cb)
        self._complete = self.create_client(TaskComplete, '/plc/task_complete',
                                            callback_group=self._cb)
        self._compute_route = ActionClient(
            self, ComputeRoute, '/compute_route', callback_group=self._cb)
        self._follow_path = ActionClient(
            self, FollowPath, '/follow_path', callback_group=self._cb)
        self._spin = ActionClient(
            self, Spin, '/spin', callback_group=self._cb)
        self._dock = ActionClient(self, DockToStation, '/dock_to_station',
                                  callback_group=self._cb)
        self._lift = ActionClient(self, LiftLoad, '/lift_load',
                                  callback_group=self._cb)
        self.create_service(StartMission, '/mission/start', self._on_start,
                            callback_group=self._cb)
        self.create_service(SubmitManualTask, '/mission/submit_manual_task',
                            self._on_manual_task, callback_group=self._cb)
        self.create_service(SubmitMission, '/mission/submit',
                            self._on_submit_mission, callback_group=self._cb)
        self.create_service(CancelMission, '/mission/cancel', self._on_cancel,
                            callback_group=self._cb)
        self.create_service(ResetMissionSafety, '/mission/reset_safety',
                            self._on_reset_safety, callback_group=self._cb)
        self.create_service(Trigger, '/mission/emergency_stop',
                            self._on_emergency_stop, callback_group=self._cb)
        rate = float(self.get_parameter('status_rate_hz').value)
        self.create_timer(1.0 / rate, self._publish_status)
        self._publish_load_state(False)
        self._event('ready', source=self._default_source,
                    manual_task_enabled=self._manual_enabled,
                    imu_enabled=self._imu_enabled,
                    graph_nodes=len(self._nodes))

    @staticmethod
    def _load_graph(path: str) -> Dict[str, Dict[str, Any]]:
        with open(path, encoding='utf-8') as stream:
            data = json.load(stream)
        nodes = {}
        for feature in data.get('features', []):
            if feature.get('geometry', {}).get('type') != 'Point':
                continue
            prop = feature.get('properties', {})
            metadata = prop.get('metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
            name = str(prop.get('name', prop['id']))
            station_id = str(
                metadata.get('station_id', metadata.get('station', ''))).strip()
            custom = metadata.get('custom', {})
            if not isinstance(custom, dict):
                custom = {}
            record = {
                'id': int(prop['id']),
                'xy': feature['geometry']['coordinates'][:2],
                'yaw': float(metadata.get('yaw', 0.0)),
                'name': name,
                'station_id': station_id,
                'role': str(metadata.get('role', '')).strip().lower(),
                'approach_qr_id': str(
                    custom.get('approach_qr_id', '')).strip(),
                'dock_heading_yaw': custom.get('dock_heading_yaw'),
                'turn_direction': str(
                    custom.get('turn_direction', '')).strip().lower(),
                'line_follow_duration_s': custom.get(
                    'line_follow_duration_s'),
            }
            aliases = [name]
            if role := record['role']:
                if (
                    role not in (
                        'pickup_approach',
                        'dropoff_approach',
                        'qr_trigger',
                    )
                    and station_id
                ):
                    aliases.append(station_id)
            elif station_id:
                aliases.append(station_id)
            for alias in aliases:
                if not alias:
                    continue
                if alias in nodes and nodes[alias]['id'] != record['id']:
                    raise ValueError(f'duplicate graph node alias: {alias}')
                nodes[alias] = record
        if not nodes:
            raise ValueError('graph has no named route nodes')
        return nodes

    @staticmethod
    def _load_edge_directions(path: str) -> Dict[int, str]:
        """Load body-motion semantics keyed by Nav2 route feature ID."""
        with open(path, encoding='utf-8') as stream:
            data = json.load(stream)
        directions = {}
        for feature in data.get('features', []):
            geometry_type = feature.get('geometry', {}).get('type')
            if geometry_type not in ('LineString', 'MultiLineString'):
                continue
            properties = feature.get('properties', {})
            metadata = properties.get('metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
            direction = str(
                metadata.get('movement_direction', 'forward')
            ).strip().lower()
            if direction not in ('forward', 'reverse', 'either'):
                raise ValueError(
                    f"edge {properties.get('id')} has invalid "
                    f'movement_direction: {direction}'
                )
            directions[int(properties['id'])] = direction
        return directions

    def _resolve_special_nodes(self) -> None:
        def resolve(configured: str, role: str) -> str:
            if configured in self._nodes:
                return configured
            candidates = [
                (alias, node) for alias, node in self._nodes.items()
                if node.get('role') == role
            ]
            if not candidates:
                raise ValueError(
                    f"graph has neither '{configured}' nor role '{role}'")
            preferred = next(
                (alias for alias, node in candidates
                 if alias == node.get('station_id') and alias),
                candidates[0][0],
            )
            return preferred

        self._gate_node = resolve(self._configured_gate_node, 'gate_q5')
        try:
            self._return_gate_node = resolve(
                getattr(self, '_configured_return_gate_node', 'kapi_q6'),
                'gate_q6',
            )
        except ValueError:
            # Eski phase10/demo graflarinda q6 yoktur. Production saha paketi
            # validator'dan gecmek icin ayri gate_q6 tanimlamak zorundadir.
            self._return_gate_node = self._gate_node
        self._home_node = resolve(self._configured_home_node, 'wait')

    def _event(self, event: str, **fields: Any) -> None:
        payload = {'stamp': self.get_clock().now().nanoseconds / 1e9,
                   'event': event, 'state': int(self._state),
                   'task_id': self._task_id, 'source': self._source}
        payload.update(fields)
        text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        self._event_pub.publish(String(data=text))
        self.get_logger().info(text)

    def _on_pose(self, msg: PoseWithCovarianceStamped) -> None:
        self._pose = msg

    def _on_scan(self, _msg: LaserScan) -> None:
        self._scan_seen = time.monotonic()

    def _on_odom(self, msg: Odometry) -> None:
        self._odom_seen = time.monotonic()
        self._linear_speed = float(msg.twist.twist.linear.x)
        self._angular_speed = float(msg.twist.twist.angular.z)

    def _on_filtered_odom(self, msg: Odometry) -> None:
        self._on_odom(msg)
        self._filtered_odom_seen = time.monotonic()
        orientation = msg.pose.pose.orientation
        self._filtered_yaw = math.atan2(
            2.0 * (
                orientation.w * orientation.z
                + orientation.x * orientation.y
            ),
            1.0 - 2.0 * (
                orientation.y * orientation.y
                + orientation.z * orientation.z
            ),
        )

    def _on_imu(self, msg: Imu) -> None:
        orientation = msg.orientation
        values = (
            orientation.x,
            orientation.y,
            orientation.z,
            orientation.w,
        )
        norm = math.sqrt(sum(value * value for value in values))
        if all(math.isfinite(value) for value in values) and 0.5 <= norm <= 1.5:
            self._imu_seen = time.monotonic()

    def _on_qr(self, msg: QrDetection) -> None:
        self._last_qr_detected = bool(msg.detected)
        self._last_qr_pose = msg.pose_in_camera
        self._last_qr_confidence = float(msg.confidence)
        self._last_qr_camera = msg.camera_frame
        self._last_qr_seen = time.monotonic()
        if msg.detected:
            self._last_qr = msg.data
        stamp_ns = (
            int(msg.header.stamp.sec) * 1_000_000_000
            + int(msg.header.stamp.nanosec)
        )
        age_s = (
            max(0.0, (self.get_clock().now().nanoseconds - stamp_ns) / 1e9)
            if stamp_ns > 0 else None
        )
        result = self._qr_gate.observe(
            msg.data, bool(msg.detected), age_s=age_s
        )
        if result.accepted:
            self._event(
                'station_qr_verified',
                station=self._qr_gate.target_station,
                qr_id=msg.data,
            )
        elif self._qr_gate.armed and result.reason != 'invalid_qr':
            self._event(
                'station_qr_rejected',
                station=self._qr_gate.target_station,
                expected_qr_id=self._qr_gate.expected_qr_id,
                received_qr_id=msg.data,
                reason=result.reason,
            )

    def _begin_station_approach(self, station: str) -> None:
        """Arm the F7A trigger when the station has an approach QR."""
        self._docking_target = ''
        self._docking_duration = 0.0
        self._docking_elapsed = 0.0
        self._docking_remaining = 0.0
        self._docking_lane_active = False
        self._docking_camera_valid = False
        self._docking_stopped = True
        self._docking_error = ''
        expected = str(self._nodes[station].get('approach_qr_id', '')).strip()
        if not expected:
            self._qr_gate.reset()
            return
        self._qr_gate.arm(station, expected)
        self._event(
            'station_qr_armed', station=station, expected_qr_id=expected
        )

    def _finish_station_approach(self) -> None:
        """Disarm QR actions during forward station exit."""
        if self._qr_gate.phase != StationQrGate.IDLE:
            self._qr_gate.exiting()

    def _exit_station(self, station: str, loaded: bool) -> None:
        """Stop rear-lane control and return to the station approach with Nav2."""
        self._finish_station_approach()
        self._task_pub.publish(String(data='STOP'))
        self._docking_lane_active = False
        self._event(
            'station_exit_lane_stopped',
            station=station,
            command='STOP',
        )
        self._wait_until_stopped(f'{station} lane-Nav2 devri')
        if not str(self._nodes[station].get('approach_qr_id', '')).strip():
            # Geriye uyumlu test graflarinda approach dugumu olmayabilir.
            # Competition validator production paketinde buna izin vermez.
            self._event(
                'station_exit_nav_skipped',
                station=station,
                reason='legacy_graph_without_approach',
            )
            return
        approach = self._station_approach_target(station)
        self._event(
            'station_exit_nav_started',
            station=station,
            target=approach,
        )
        self._navigate(approach, loaded=loaded)
        self._event(
            'station_exit_nav_completed',
            station=station,
            target=approach,
        )

    def _gate_entry_for_direction(self, direction: str) -> str:
        """Return the direction-specific waiting node for a gate crossing."""
        if direction == 'outbound':
            return self._gate_node
        if direction == 'return':
            return self._return_gate_node
        raise MissionAbort(f'gecersiz kapi gecis yonu: {direction}')

    def _navigate_via_gate(
        self, target: str, loaded: bool, direction: str
    ) -> None:
        """Acquire a fresh permission at q5/q6, then consume it once."""
        entry = self._gate_entry_for_direction(direction)
        self._gate_sequence += 1
        crossing_id = (
            f'{self._task_id or "mission"}:{self._gate_sequence}:{direction}'
        )
        self._gate_ok = False
        self._gate_entry_node = entry
        self._gate_direction = direction
        self._gate_crossing_id = crossing_id
        try:
            self._navigate(entry, loaded=loaded)
            self._wait_until_stopped(f'{entry} kapi izin bekleme')
            self._set_state(RobotStatus.STATE_WAITING_PLC, entry)
            request = GatePermission.Request()
            request.task_id = self._task_id
            request.crossing_id = crossing_id
            request.node_id = entry
            request.direction = direction
            self._event(
                'gate_permission_requested',
                gate_entry=entry,
                direction=direction,
                crossing_id=crossing_id,
            )
            reply = self._service_call(
                self._gate,
                request,
                self._gate_timeout,
                f'PLC gate_permission:{direction}',
            )
            if reply.crossing_id != crossing_id:
                raise MissionAbort(
                    f'{entry}: eski/gecersiz kapi izin yaniti '
                    f'({reply.crossing_id or "bos"})'
                )
            if not reply.granted:
                raise MissionAbort(f'kapi reddi: {reply.message}')
            self._gate_ok = True
            self._event(
                'gate_permission_granted',
                gate_entry=entry,
                direction=direction,
                crossing_id=crossing_id,
            )
            self._event(
                'gate_crossing_started',
                gate_entry=entry,
                direction=direction,
                crossing_id=crossing_id,
                target=target,
            )
            self._navigate(target, loaded=loaded)
            self._event(
                'gate_crossing_completed',
                gate_entry=entry,
                direction=direction,
                crossing_id=crossing_id,
                target=target,
            )
        finally:
            self._gate_ok = False
            self._gate_entry_node = ''
            self._gate_direction = ''
            self._gate_crossing_id = ''

    def _unique_graph_nodes(self):
        """Return graph records once even though aliases share records."""
        return {node['id']: node for node in self._nodes.values()}.values()

    def _station_approach_target(self, station: str) -> str:
        """Resolve the QR/approach node associated with a station."""
        dock = self._nodes[station]
        expected_role = (
            'pickup_approach'
            if dock.get('role') == 'pickup_dock'
            else 'dropoff_approach'
        )
        candidates = [
            node for node in self._unique_graph_nodes()
            if node.get('station_id') == station
            and node.get('role') in (expected_role, 'qr_trigger')
        ]
        preferred = [
            node for node in candidates if node.get('role') == expected_role
        ]
        selected = preferred or candidates
        if len(selected) != 1:
            raise MissionAbort(
                f'{station}: tam bir QR/yaklasim dugumu gerekli'
            )
        return str(selected[0]['name'])

    def _wait_for_station_qr(self, station: str) -> None:
        timeout = float(self.get_parameter('station_qr_wait_s').value)
        deadline = time.monotonic() + timeout
        while self._qr_gate.phase == StationQrGate.APPROACHING:
            self._check_abort()
            if time.monotonic() >= deadline:
                raise MissionAbort(
                    f'{station}: beklenen QR zamaninda dogrulanmadi '
                    f'({self._qr_gate.expected_qr_id})'
                )
            time.sleep(0.02)
        if self._qr_gate.phase != StationQrGate.VERIFIED:
            raise MissionAbort(f'{station}: QR tetik oturumu gecersiz')

    def _wait_until_stopped(self, label: str) -> None:
        timeout = float(self.get_parameter('motion_stop_timeout_s').value)
        settle = float(self.get_parameter('motion_stop_settle_s').value)
        linear_limit = float(
            self.get_parameter('motion_stop_linear_tolerance').value)
        angular_limit = float(
            self.get_parameter('motion_stop_angular_tolerance').value)
        deadline = time.monotonic() + timeout
        stable_since = None
        self._safe_stop()
        while time.monotonic() < deadline:
            self._check_abort()
            stopped = (
                abs(self._linear_speed) <= linear_limit
                and abs(self._angular_speed) <= angular_limit
            )
            if stopped:
                stable_since = stable_since or time.monotonic()
                if time.monotonic() - stable_since >= settle:
                    return
            else:
                stable_since = None
            time.sleep(0.02)
        raise MissionAbort(f'{label}: arac sifir hizda sabitlenemedi')

    @staticmethod
    def _yaw_from_pose(pose: PoseWithCovarianceStamped) -> float:
        orientation = pose.pose.pose.orientation
        return math.atan2(
            2.0 * (
                orientation.w * orientation.z
                + orientation.x * orientation.y
            ),
            1.0 - 2.0 * (
                orientation.y * orientation.y
                + orientation.z * orientation.z
            ),
        )

    @staticmethod
    def _wrap_angle(value: float) -> float:
        return math.atan2(math.sin(value), math.cos(value))

    @staticmethod
    def _directed_turn(current: float, target: float, direction: str) -> float:
        if direction == 'left':
            return (target - current) % (2.0 * math.pi)
        if direction == 'right':
            return -((current - target) % (2.0 * math.pi))
        raise MissionAbort(
            'turn_direction=auto henuz iki costmap yayi '
            'karsilastirilmadan kullanilamaz'
        )

    def _turn_at_junction(self, maneuver: JunctionManeuver) -> None:
        """Align to the next route edge with one explicit bounded Spin."""
        self._check_action_health(require_turn_sensors=True)
        if self._pose is None or not math.isfinite(self._filtered_yaw):
            raise MissionAbort(
                f'{maneuver.node_name}: junction yon bilgisi gecersiz'
            )
        start_map_yaw = self._yaw_from_pose(self._pose)
        start_filtered_yaw = self._filtered_yaw
        relative_turn = self._wrap_angle(
            maneuver.outgoing_heading - start_map_yaw
        )
        timeout = float(
            self.get_parameter('junction_turn_timeout_s').value)
        goal = Spin.Goal()
        goal.target_yaw = float(relative_turn)
        goal.time_allowance = Duration(seconds=timeout).to_msg()
        self._status_detail = (
            f'{maneuver.node_name}: junction donusu '
            f'{math.degrees(relative_turn):+.1f} derece'
        )
        self._event(
            'junction_turn_started',
            junction=maneuver.node_name,
            node_id=maneuver.node_id,
            incoming_heading=maneuver.incoming_heading,
            outgoing_heading=maneuver.outgoing_heading,
            route_turn_rad=maneuver.turn_angle,
            commanded_turn_rad=relative_turn,
        )
        try:
            self._action(
                self._spin,
                goal,
                f'junction_turn:{maneuver.node_name}',
                timeout + 2.0,
                require_turn_sensors=True,
            )
            self._wait_until_stopped(
                f'{maneuver.node_name} junction donus sonu')
            self._check_action_health(require_turn_sensors=True)
            if self._pose is None:
                raise MissionAbort(
                    f'{maneuver.node_name}: junction donus sonu AMCL pozu yok'
                )
            final_map_yaw = self._yaw_from_pose(self._pose)
            yaw_error = abs(self._wrap_angle(
                maneuver.outgoing_heading - final_map_yaw
            ))
            measured_turn = self._wrap_angle(
                self._filtered_yaw - start_filtered_yaw
            )
            fused_turn_error = abs(self._wrap_angle(
                relative_turn - measured_turn
            ))
            tolerance = math.radians(float(self.get_parameter(
                'junction_turn_yaw_tolerance_deg').value
            ))
            if yaw_error > tolerance:
                raise MissionAbort(
                    f'{maneuver.node_name}: junction yon hatasi '
                    f'{math.degrees(yaw_error):.2f} derece'
                )
            turn_source = (
                'imu+encoder' if self._imu_enabled else 'encoder'
            )
            if fused_turn_error > tolerance:
                raise MissionAbort(
                    f'{maneuver.node_name}: {turn_source} junction donus '
                    f'hatasi {math.degrees(fused_turn_error):.2f} derece'
                )
        except MissionAbort as error:
            reason = 'obstacle' if self._obstacle else str(error)
            self._event(
                'junction_turn_failed',
                junction=maneuver.node_name,
                node_id=maneuver.node_id,
                reason=reason,
            )
            raise
        self._event(
            'junction_turn_completed',
            junction=maneuver.node_name,
            node_id=maneuver.node_id,
            final_map_yaw=final_map_yaw,
            measured_fused_turn=measured_turn,
            turn_source=turn_source,
            yaw_error_rad=yaw_error,
            fused_turn_error_rad=fused_turn_error,
        )

    def _turn_at_station(self, station: str) -> None:
        config = self._nodes[station]
        direction = str(config.get('turn_direction', '')).lower()
        try:
            target_yaw = float(config.get('dock_heading_yaw'))
        except (TypeError, ValueError) as error:
            raise MissionAbort(
                f'{station}: dock_heading_yaw gecersiz'
            ) from error
        self._check_action_health(require_turn_sensors=True)
        if self._pose is None or not math.isfinite(self._filtered_yaw):
            raise MissionAbort(f'{station}: donus oncesi yon bilgisi gecersiz')
        start_map_yaw = self._yaw_from_pose(self._pose)
        start_filtered_yaw = self._filtered_yaw
        relative_turn = self._directed_turn(
            start_map_yaw, target_yaw, direction
        )
        angle_deg = abs(math.degrees(relative_turn))
        minimum = float(
            self.get_parameter('station_turn_min_angle_deg').value)
        maximum = float(
            self.get_parameter('station_turn_max_angle_deg').value)
        if not minimum <= angle_deg <= maximum:
            raise MissionAbort(
                f'{station}: hedef yon {angle_deg:.1f} derece donus '
                f'gerektiriyor; izinli bant {minimum:.1f}-{maximum:.1f}'
            )

        timeout = float(self.get_parameter('station_turn_timeout_s').value)
        goal = Spin.Goal()
        goal.target_yaw = float(relative_turn)
        goal.time_allowance = Duration(seconds=timeout).to_msg()
        self._qr_gate.turning()
        self._status_detail = f'{station}: guvenli 180 derece donus'
        self._event(
            'station_turn_started',
            station=station,
            direction=direction,
            relative_turn_rad=relative_turn,
            target_yaw=target_yaw,
        )
        try:
            self._action(
                self._spin,
                goal,
                f'station_turn:{station}',
                timeout + 2.0,
                require_turn_sensors=True,
            )
        except MissionAbort as error:
            reason = 'obstacle' if self._obstacle else str(error)
            self._event(
                'station_turn_failed', station=station, reason=reason
            )
            raise

        self._wait_until_stopped(f'{station} donus sonu')
        self._check_action_health(require_turn_sensors=True)
        if self._pose is None:
            raise MissionAbort(f'{station}: donus sonu AMCL pozu yok')
        final_map_yaw = self._yaw_from_pose(self._pose)
        yaw_error = abs(self._wrap_angle(target_yaw - final_map_yaw))
        measured_turn = self._wrap_angle(
            self._filtered_yaw - start_filtered_yaw
        )
        fused_turn_error = abs(self._wrap_angle(
            relative_turn - measured_turn
        ))
        turn_source = 'imu+encoder' if self._imu_enabled else 'encoder'
        tolerance = math.radians(float(
            self.get_parameter('station_turn_yaw_tolerance_deg').value
        ))
        if yaw_error > tolerance:
            raise MissionAbort(
                f'{station}: donus yon hatasi '
                f'{math.degrees(yaw_error):.2f} derece'
            )
        if fused_turn_error > tolerance:
            raise MissionAbort(
                f'{station}: {turn_source} donus hatasi '
                f'{math.degrees(fused_turn_error):.2f} derece'
            )
        self._qr_gate.line_follow_ready()
        self._status_detail = f'{station}: docking devrine hazir'
        self._event(
            'station_turn_completed',
            station=station,
            final_map_yaw=final_map_yaw,
            measured_fused_turn=measured_turn,
            turn_source=turn_source,
            yaw_error_rad=yaw_error,
            fused_turn_error_rad=fused_turn_error,
        )

    def _on_plc_connected(self, msg: Bool) -> None:
        self._plc_connected = bool(msg.data)
        if msg.data:
            self._plc_seen = time.monotonic()
        elif self._busy and self._source in ('plc', 'mock_plc'):
            self._request_abort('PLC baglantisi kayboldu', latch=False)

    def _on_manual(self, msg: Bool) -> None:
        self._manual = bool(msg.data)

    def _on_battery(self, msg: BatteryState) -> None:
        self._battery_voltage = float(msg.voltage)
        self._battery_current = float(msg.current)
        self._battery_temperature = float(msg.temperature)

    def _on_route_state(self, msg: String) -> None:
        try:
            state = json.loads(msg.data)
            if not isinstance(state, dict):
                return
            self._route_guard_state = str(state.get('state', 'unavailable'))
            self._route_stop_reason = str(state.get('stop_reason', ''))
            self._selected_route_edges = [
                int(value) for value in state.get('selected_edges', [])
                if 0 <= int(value) <= (1 << 64) - 1
            ]
        except (TypeError, ValueError, json.JSONDecodeError):
            self._route_guard_state = 'unavailable'
            self._route_stop_reason = 'invalid_route_state'

    def _publish_load_state(self, loaded: bool) -> None:
        loaded = bool(loaded)
        if loaded != self._loaded:
            self._route_constraints_ready = False
        self._loaded = loaded
        self._load_state_pub.publish(Bool(data=self._loaded))

    def _await_route_constraints(self) -> None:
        deadline = time.monotonic() + self._route_constraints_timeout
        while not self._route_constraints_ready:
            if self._abort_reason:
                raise MissionAbort(self._abort_reason)
            if time.monotonic() >= deadline:
                raise MissionAbort('rota yuk/yon kurallari uygulanamadi')
            time.sleep(0.02)

    def _on_active_field(self, msg: ActiveField) -> None:
        with self._lock:
            if self._busy and msg.package_hash != self._active_field_hash:
                self._active_field_ready = False
                self._event(
                    "active_field_rejected",
                    reason="field changed while mission was reserved",
                )
                return
            if msg.active and msg.graph_file:
                try:
                    graph_file = os.path.realpath(msg.graph_file)
                    nodes = self._load_graph(graph_file)
                    edge_directions = self._load_edge_directions(graph_file)
                    self._nodes = nodes
                    self._edge_directions = edge_directions
                    self._graph_file = graph_file
                    self._resolve_special_nodes()
                    self._current_node = self._home_node
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
                    self._active_field_ready = False
                    self._event("active_field_rejected", reason=str(error))
                    return
            self._active_field_ready = bool(
                msg.active
                and msg.package_hash
                and msg.graph_file
                and os.path.realpath(msg.graph_file) == self._graph_file
            )
            self._active_field_name = msg.field_name
            self._active_field_version = msg.package_version
            self._active_field_hash = msg.package_hash

    def _on_estop(self, msg: Bool) -> None:
        self._estop = bool(msg.data)
        if msg.data:
            self._state = RobotStatus.STATE_ESTOP
            self._status_detail = 'e-stop aktif'
            self._request_abort('e-stop aktif', latch=True)

    def _on_base_communication(self, msg: Bool) -> None:
        self._base_communication_ok = bool(msg.data)
        self._base_communication_seen = time.monotonic()
        if not msg.data and self._busy:
            self._request_abort('STM32/UART iletisimi kayip', latch=True)

    def _base_communication_healthy(self) -> bool:
        return (
            not self._require_base_communication
            or (
                self._base_communication_ok
                and self._base_communication_seen > 0.0
                and time.monotonic() - self._base_communication_seen
                <= self._base_communication_timeout
            )
        )

    def _on_safety_abort(self, msg: Bool) -> None:
        if msg.data:
            self._request_abort('safety abort', latch=True)

    def _request_abort(self, reason: str, latch: bool) -> None:
        with self._lock:
            if latch:
                self._latched_abort = True
            if not self._busy:
                if latch:
                    self._state = RobotStatus.STATE_ESTOP
                    self._abort_reason = reason
                    self._status_detail = reason
                    self._safe_stop()
                    self._event('abort_latched', reason=reason)
                return
            if not self._running:
                self._busy = False
                self._abort_reason = reason
                self._state = (RobotStatus.STATE_ESTOP if latch else
                               RobotStatus.STATE_IDLE)
                self._status_detail = reason
                self._next_node = ''
                self._safe_stop()
                self._event('queued_mission_aborted', reason=reason)
                return
            self._abort_reason = self._abort_reason or reason
            goal = self._active_goal
        self._event('abort_requested', reason=reason, active_action=self._active_kind)
        if goal is not None:
            goal.cancel_goal_async()
        self._safe_stop()

    def _safe_stop(self) -> None:
        self._speed_reset_pub.publish(Empty())

    def _validate_route(self, route_nodes) -> Optional[str]:
        if not route_nodes:
            return 'bos gorev'
        if len(route_nodes) < 2 or len(route_nodes) % 2:
            return 'rota alma/birakma ciftlerinden olusmali'
        if (
            getattr(self, '_require_active_field', False)
            and self._return_gate_node == self._gate_node
        ):
            return 'production saha paketinde ayri gate_q6 dugumu gerekli'
        required = tuple(route_nodes) + (
            self._gate_node, self._return_gate_node, self._home_node)
        missing = [node for node in required if node not in self._nodes]
        if missing:
            return f"gecersiz graph node: {', '.join(sorted(set(missing)))}"
        for index, node in enumerate(route_nodes):
            expected_role = 'pickup_dock' if index % 2 == 0 else 'dropoff_dock'
            role = self._nodes[node].get('role', '')
            if role:
                if role != expected_role:
                    return (
                        f'{index + 1}. durak {expected_role} rolunde olmali: '
                        f'{node}'
                    )
            else:
                prefix = 'alma_' if index % 2 == 0 else 'birak_'
                if not node.startswith(prefix):
                    return f'{index + 1}. durak {prefix} ile baslamali: {node}'
            if index and node == route_nodes[index - 1]:
                return 'ayni alma/birakma noktasi kullanilamaz'
            config = self._nodes[node]
            if str(config.get('approach_qr_id', '')).strip():
                try:
                    self._station_approach_target(node)
                except MissionAbort as error:
                    return str(error)
                direction = str(
                    config.get('turn_direction', '')
                ).strip().lower()
                if direction not in ('left', 'right'):
                    return (
                        f'{node}: turn_direction left veya right olmali'
                    )
                try:
                    target_yaw = float(config.get('dock_heading_yaw'))
                except (TypeError, ValueError):
                    return f'{node}: dock_heading_yaw gecersiz'
                if not math.isfinite(target_yaw):
                    return f'{node}: dock_heading_yaw sonlu olmali'
                try:
                    duration = float(config.get('line_follow_duration_s'))
                except (TypeError, ValueError):
                    return f'{node}: line_follow_duration_s gecersiz'
                if not math.isfinite(duration) or not 0.1 <= duration <= 120.0:
                    return (
                        f'{node}: line_follow_duration_s 0.1-120.0 '
                        'araliginda olmali'
                    )
        return None

    def _transform_age(self, target: str, source: str) -> Optional[float]:
        try:
            transform = self._tf_buffer.lookup_transform(
                target, source, Time(),
                timeout=Duration(seconds=self._tf_lookup_timeout))
        except TransformException:
            return None
        stamp = transform.header.stamp
        stamp_ns = int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)
        if stamp_ns <= 0:
            return None
        return max(0.0, (self.get_clock().now().nanoseconds - stamp_ns) / 1e9)

    def _localization_health(self) -> LocalizationHealth:
        pose = self._pose
        covariance = math.inf
        pose_finite = False
        if pose is not None:
            values = (
                pose.pose.pose.position.x, pose.pose.pose.position.y,
                pose.pose.pose.position.z, pose.pose.pose.orientation.x,
                pose.pose.pose.orientation.y, pose.pose.pose.orientation.z,
                pose.pose.pose.orientation.w, *pose.pose.covariance)
            pose_finite = all(math.isfinite(float(value)) for value in values)
            covariance = float(pose.pose.covariance[0] +
                               pose.pose.covariance[7])
        now = time.monotonic()
        return evaluate_localization(
            has_pose=pose is not None,
            pose_finite=pose_finite,
            position_covariance=covariance,
            max_position_covariance=self._max_position_covariance,
            map_odom_tf_age=self._transform_age('map', 'odom'),
            odom_base_tf_age=self._transform_age('odom', 'base_footprint'),
            tf_timeout=self._tf_freshness,
            scan_age=(now - self._scan_seen if self._scan_seen else None),
            scan_timeout=self._scan_freshness,
            odom_age=(now - self._odom_seen if self._odom_seen else None),
            odom_timeout=self._odom_freshness)

    def _reserve(self, task_id: str, route_nodes, source: str,
                 return_home: bool = True, start_immediately: bool = True,
                 require_localization: bool = False) -> Optional[str]:
        with self._lock:
            if self._busy:
                return f'aktif gorev var: {self._source}/{self._task_id}'
            if self._require_active_field and not self._active_field_ready:
                return 'dogrulanmis etkin saha paketi hazir degil'
            if self._estop or self._latched_abort:
                return 'e-stop/safety kilidi aktif; operator reset gerekli'
            if self._obstacle:
                return 'engel algilandi; gorev kabul edilmedi'
            if not self._base_communication_healthy():
                return 'STM32/UART iletisimi hazir degil'
            if not task_id:
                return 'task_id bos olamaz'
            if task_id in self._known_task_ids:
                return f'mukerrer task_id: {task_id}'
            if require_localization:
                health = self._localization_health()
                if not health.valid:
                    return f'lokalizasyon gecersiz: {health.reason}'
            error = self._validate_route(route_nodes)
            if error:
                return error
            self._busy = True
            self._running = start_immediately
            self._abort_reason = ''
            self._route_nodes = list(route_nodes)
            self._current_stop_index = 0
            self._return_home = bool(return_home)
            self._task_id = task_id
            self._pickup, self._dropoff = route_nodes[0], route_nodes[1]
            self._source = source
            self._mission_started_wall = 0.0
            self._mission_elapsed = 0.0
            self._status_detail = 'gorev kabul edildi'
            self._known_task_ids.add(task_id)
        self._state = RobotStatus.STATE_TASK_RECEIVED
        self._next_node = route_nodes[0]
        self._event('task_accepted', pickup=self._pickup, dropoff=self._dropoff,
                    route_nodes=list(route_nodes), queued=not start_immediately)
        if start_immediately:
            threading.Thread(target=self._run, daemon=True).start()
        return None

    def _on_start(self, _req: StartMission.Request,
                  res: StartMission.Response) -> StartMission.Response:
        with self._lock:
            if self._busy:
                if self._source == 'gui' and not self._running:
                    if self._estop or self._latched_abort:
                        res.accepted, res.message = False, 'guvenlik kilidi aktif'
                        return res
                    if self._obstacle:
                        res.accepted, res.message = False, 'engel algilandi'
                        return res
                    if not self._base_communication_healthy():
                        res.accepted = False
                        res.message = 'STM32/UART iletisimi hazir degil'
                        return res
                    health = self._localization_health()
                    if not health.valid:
                        res.accepted = False
                        res.message = f'lokalizasyon gecersiz: {health.reason}'
                        return res
                    self._running = True
                    threading.Thread(target=self._run, daemon=True).start()
                    res.accepted, res.message = True, 'GUI gorevi baslatildi'
                    self._event('mission_started', route_nodes=self._route_nodes)
                    return res
                res.accepted, res.message = False, 'aktif gorev var'
                return res
            if self._require_active_field and not self._active_field_ready:
                res.accepted = False
                res.message = 'dogrulanmis etkin saha paketi hazir degil'
                return res
            if self._estop or self._latched_abort:
                res.accepted, res.message = False, 'guvenlik kilidi aktif'
                return res
            self._busy = True  # reserve while PLC request is in flight
            self._source = self._default_source
        try:
            reply = self._service_call(self._assign, AssignTask.Request(), 5.0,
                                       'PLC assign_task')
            if not reply.success:
                raise MissionAbort(reply.message)
            with self._lock:
                self._busy = False
            error = self._reserve(reply.task_id,
                                  [reply.pickup_node, reply.dropoff_node],
                                  self._default_source)
            res.accepted, res.message = error is None, error or 'gorev kabul edildi'
        except MissionAbort as exc:
            with self._lock:
                self._busy = False
            res.accepted, res.message = False, str(exc)
            self._event('task_rejected', reason=str(exc))
        return res

    def _on_manual_task(self, req: SubmitManualTask.Request,
                        res: SubmitManualTask.Response) -> SubmitManualTask.Response:
        if not self._manual_enabled:
            res.accepted, res.message = False, 'manual_task_enabled=false'
            self._event('task_rejected', requested_source='gui', reason=res.message)
            return res
        task_id = req.task_id or f'gui_{int(time.time())}'
        error = self._reserve(task_id, [req.pickup_node, req.dropoff_node], 'gui')
        res.accepted, res.message = error is None, error or 'GUI gorevi kabul edildi'
        if error:
            self._event('task_rejected', requested_source='gui', reason=error)
        return res

    def _on_submit_mission(self, req: SubmitMission.Request,
                           res: SubmitMission.Response) -> SubmitMission.Response:
        if not self._manual_enabled:
            res.accepted, res.message = False, 'manual_task_enabled=false'
        else:
            error = self._reserve(req.task_id, list(req.route_nodes), 'gui',
                                  return_home=req.return_home,
                                  start_immediately=False,
                                  require_localization=True)
            res.accepted = error is None
            res.message = error or 'GUI gorevi kabul edildi; baslatma bekleniyor'
        if not res.accepted:
            self._event('task_rejected', requested_source='gui', reason=res.message)
        return res

    def _on_cancel(self, _req: CancelMission.Request,
                   res: CancelMission.Response) -> CancelMission.Response:
        if not self._busy:
            res.accepted, res.message = False, 'aktif gorev yok'
            return res
        self._request_abort('operator cancel', latch=False)
        res.accepted, res.message = True, 'iptal istendi'
        return res

    def _on_reset_safety(self, _req: ResetMissionSafety.Request,
                         res: ResetMissionSafety.Response) -> ResetMissionSafety.Response:
        with self._lock:
            if self._busy or self._estop:
                res.accepted, res.message = False, 'gorev/e-stop halen aktif'
                return res
        if self._require_safety_supervisor:
            try:
                reply = self._service_call(
                    self._safety_reset, Trigger.Request(), 2.0,
                    'safety supervisor reset')
            except MissionAbort as error:
                res.accepted, res.message = False, str(error)
                return res
            if not reply.success:
                res.accepted = False
                res.message = f'safety reset reddedildi: {reply.message}'
                return res
        with self._lock:
            if self._busy or self._estop:
                res.accepted, res.message = False, 'gorev/e-stop halen aktif'
                return res
            self._latched_abort = False
            self._abort_reason = ''
            self._state = RobotStatus.STATE_IDLE
            self._status_detail = 'goreve hazir'
            res.accepted, res.message = True, 'operator safety reset kabul edildi'
            self._event('safety_reset')
        return res

    def _on_emergency_stop(self, _req: Trigger.Request,
                           res: Trigger.Response) -> Trigger.Response:
        self._state = RobotStatus.STATE_ESTOP
        self._status_detail = 'GUI yazilimsal acil durdurma'
        self._request_abort('GUI yazilimsal acil durdurma', latch=True)
        res.success = True
        res.message = 'yazilimsal acil durdurma kilitlendi; fiziksel e-stop yerine gecmez'
        return res

    def _service_call(self, client, request, timeout: float, label: str):
        if not client.wait_for_service(timeout_sec=min(timeout, 2.0)):
            raise MissionAbort(f'{label} servisi yok')
        future = client.call_async(request)
        end = time.monotonic() + timeout
        while rclpy.ok() and not future.done():
            self._check_abort()
            if time.monotonic() >= end:
                raise MissionAbort(f'{label} timeout')
            time.sleep(0.02)
        if future.result() is None:
            raise MissionAbort(f'{label} cagri hatasi')
        return future.result()

    def _check_abort(self) -> None:
        if self._abort_reason:
            raise MissionAbort(self._abort_reason)
        if not self._base_communication_healthy():
            raise MissionAbort('STM32/UART iletisimi bayat/kayip')
        if self._source in ('plc', 'mock_plc') and self._plc_seen:
            if time.monotonic() - self._plc_seen > self._plc_freshness:
                raise MissionAbort('PLC heartbeat timeout')

    def _check_action_health(self, require_turn_sensors: bool) -> None:
        if not require_turn_sensors:
            return
        now = time.monotonic()
        if self._imu_enabled:
            timeout = float(
                self.get_parameter('station_turn_imu_timeout_s').value)
            if now - self._imu_seen > timeout:
                raise MissionAbort('manevra sirasinda IMU verisi bayat/kayip')
        if now - self._filtered_odom_seen > self._odom_freshness:
            raise MissionAbort(
                'manevra sirasinda filtreli odometri bayat/kayip'
            )
        if not self._localization_health().valid:
            raise MissionAbort('manevra sirasinda lokalizasyon/TF gecersiz')

    def _action(self, client, goal, label: str, timeout: Optional[float] = None,
                require_turn_sensors: bool = False, feedback_callback=None):
        limit = timeout or self._action_timeout
        self._check_abort()
        if not client.wait_for_server(timeout_sec=2.0):
            raise MissionAbort(f'{label} action server yok')
        sent = client.send_goal_async(
            goal, feedback_callback=feedback_callback)
        end = time.monotonic() + limit
        while not sent.done():
            self._check_abort()
            self._check_action_health(require_turn_sensors)
            if time.monotonic() >= end:
                raise MissionAbort(f'{label} goal timeout')
            time.sleep(0.02)
        handle = sent.result()
        if handle is None or not handle.accepted:
            raise MissionAbort(f'{label} reddedildi')
        with self._lock:
            if self._active_goal is not None:
                handle.cancel_goal_async()
                raise MissionAbort('tek action sahipligi ihlali')
            self._active_goal, self._active_kind = handle, label
        self._event('action_started', action=label)
        result_future = handle.get_result_async()
        try:
            if self._abort_reason:
                handle.cancel_goal_async()
                raise MissionAbort(self._abort_reason)
            while not result_future.done():
                self._check_abort()
                self._check_action_health(require_turn_sensors)
                if time.monotonic() >= end:
                    handle.cancel_goal_async()
                    raise MissionAbort(f'{label} timeout')
                time.sleep(0.02)
            wrapped = result_future.result()
            if wrapped.status != GoalStatus.STATUS_SUCCEEDED:
                raise MissionActionFailure(label, wrapped.status)
            result = wrapped.result
            if hasattr(result, 'success') and not result.success:
                raise MissionAbort(f'{label}: {getattr(result, "message", "failed")}')
            if hasattr(result, 'error_code') and result.error_code != 0:
                raise MissionAbort(f'{label} error_code={result.error_code}')
            self._event('action_finished', action=label, outcome='success')
            return result
        except Exception:
            handle.cancel_goal_async()
            raise
        finally:
            with self._lock:
                self._active_goal, self._active_kind = None, ''

    def _set_state(self, state: int, next_node: str = '') -> None:
        self._state, self._next_node = state, next_node
        details = {
            RobotStatus.STATE_IDLE: 'goreve hazir',
            RobotStatus.STATE_TASK_RECEIVED: 'gorev isleniyor',
            RobotStatus.STATE_MOVING_UNLOADED: 'yuksuz hareket',
            RobotStatus.STATE_MOVING_LOADED: 'yuklu hareket',
            RobotStatus.STATE_WAITING_PLC: 'PLC izni bekleniyor',
            RobotStatus.STATE_RETURNING: 'bekleme noktasina donuyor',
            RobotStatus.STATE_ERROR: 'gorev hatasi',
            RobotStatus.STATE_ESTOP: 'acil durdurma aktif',
        }
        self._status_detail = details.get(state, 'bilinmeyen durum')
        if next_node:
            self._status_detail += f': {next_node}'
        self._event('state_transition', next_node=next_node)

    def _navigate(self, target: str, loaded: bool) -> None:
        self._await_route_constraints()
        self._set_state(RobotStatus.STATE_MOVING_LOADED if loaded else
                        RobotStatus.STATE_MOVING_UNLOADED, target)
        target_node = self._nodes[target]
        route_goal = ComputeRoute.Goal()
        route_goal.goal_id = int(target_node['id'])
        route_goal.use_start = False
        route_goal.use_poses = False
        route_result = self._action(
            self._compute_route,
            route_goal,
            f'compute_route:{target}',
        )
        path = route_result.path
        if path.header.frame_id not in ('', 'map') or len(path.poses) < 2:
            raise MissionAbort(f'{target}: Route Server gecerli path uretmedi')
        route = getattr(route_result, 'route', None)
        maneuvers = []
        final_heading = None
        if route is not None and list(getattr(route, 'edges', [])):
            minimum = math.radians(float(self.get_parameter(
                'junction_turn_min_angle_deg').value))
            maximum = math.radians(float(self.get_parameter(
                'junction_turn_max_angle_deg').value))
            match_tolerance = float(self.get_parameter(
                'junction_path_match_tolerance_m').value)
            if not (
                math.isfinite(minimum)
                and math.isfinite(maximum)
                and 0.0 < minimum <= maximum <= math.pi
            ):
                raise MissionAbort('junction donus aci bandi gecersiz')
            if not math.isfinite(match_tolerance) or match_tolerance <= 0.0:
                raise MissionAbort('junction path esleme toleransi gecersiz')
            node_records = {
                int(node['id']): node for node in self._unique_graph_nodes()
            }
            maneuvers, final_heading = _route_junction_maneuvers(
                route,
                node_records,
                self._edge_directions,
                minimum,
                maximum,
            )
            segments = _split_path_at_junctions(
                path, maneuvers, match_tolerance)
            route_edge_ids = [
                int(edge.edgeid) for edge in route.edges
            ]
        else:
            # Unit/legacy action adapters may return only a Path. They retain
            # the safe F8A terminal-heading behavior without junction Spin.
            segments = [copy.deepcopy(path)]
            route_edge_ids = []
        if final_heading is None:
            final_heading = _last_path_segment_heading(segments[-1])
        terminal_headings = [
            maneuver.incoming_heading for maneuver in maneuvers
        ] + [final_heading]
        if len(segments) != len(terminal_headings):
            raise MissionAbort('junction segment/heading sayisi tutarsiz')
        self._event(
            'route_execution_planned',
            target=target,
            route_edge_ids=route_edge_ids,
            segment_count=len(segments),
            junctions=[maneuver.node_name for maneuver in maneuvers],
        )

        for index, (segment, yaw) in enumerate(zip(
            segments, terminal_headings
        )):
            segment.header.frame_id = 'map'
            for pose in segment.poses:
                pose.header.frame_id = 'map'
            # Normal transit/q/gate/D hedefleri kayitli dugum yaw'ina
            # zorlanmaz. Her FollowPath terminal yonu aktif edge
            # geometrisidir; keskin junction yonu ayri Spin sorumlulugudur.
            segment.poses[-1].pose.orientation.x = 0.0
            segment.poses[-1].pose.orientation.y = 0.0
            segment.poses[-1].pose.orientation.z = math.sin(yaw / 2.0)
            segment.poses[-1].pose.orientation.w = math.cos(yaw / 2.0)
            segment_target = (
                maneuvers[index].node_name
                if index < len(maneuvers)
                else target
            )
            follow_goal = FollowPath.Goal()
            follow_goal.path = segment
            follow_goal.controller_id = 'FollowPath'
            self._edge = f'{self._current_node}->{segment_target}'
            self._event(
                'route_segment_started',
                target=target,
                segment_target=segment_target,
                segment_index=index + 1,
                segment_count=len(segments),
            )
            try:
                self._action(
                    self._follow_path,
                    follow_goal,
                    f'follow_route:{segment_target}',
                )
            except MissionActionFailure as error:
                if (
                    error.status != GoalStatus.STATUS_ABORTED
                    or self._pose is None
                    or not self._localization_health().valid
                ):
                    raise
                current = self._pose.pose.pose.position
                current_yaw = self._yaw_from_pose(self._pose)
                goal_position = segment.poses[-1].pose.position
                position_tolerance = float(self.get_parameter(
                    'route_terminal_position_tolerance_m').value)
                yaw_tolerance = math.radians(float(self.get_parameter(
                    'route_terminal_yaw_tolerance_deg').value))
                accepted, position_error, yaw_error = (
                    _terminal_abort_is_acceptable(
                        target_x=float(goal_position.x),
                        target_y=float(goal_position.y),
                        target_yaw=yaw,
                        robot_x=float(current.x),
                        robot_y=float(current.y),
                        robot_yaw=current_yaw,
                        position_tolerance=position_tolerance,
                        yaw_tolerance=yaw_tolerance,
                    )
                )
                if not accepted:
                    raise MissionAbort(
                        f'follow_route:{segment_target} '
                        f'status={error.status}, '
                        f'konum hatasi={position_error:.3f} m, '
                        f'yon hatasi={math.degrees(yaw_error):.1f} derece'
                    ) from error
                self._event(
                    'route_terminal_abort_accepted',
                    target=segment_target,
                    position_error_m=position_error,
                    yaw_error_rad=yaw_error,
                )
            self._current_node, self._edge = segment_target, ''
            self._event(
                'route_segment_completed',
                target=target,
                segment_target=segment_target,
                segment_index=index + 1,
                segment_count=len(segments),
            )
            if index < len(maneuvers):
                maneuver = maneuvers[index]
                self._wait_until_stopped(
                    f'{maneuver.node_name} FollowPath sonu')
                self._turn_at_junction(maneuver)

    def _do_dock(self, station: str, pickup: bool) -> None:
        goal = DockToStation.Goal()
        goal.station_id = station
        goal.position_tolerance = 0.075
        goal.yaw_tolerance = math.radians(5.0)
        goal.approach_type = (DockToStation.Goal.APPROACH_PICKUP if pickup else
                              DockToStation.Goal.APPROACH_DROPOFF)
        configured = bool(self._nodes[station].get('approach_qr_id'))
        if configured:
            duration = float(
                self._nodes[station].get('line_follow_duration_s'))
            goal.line_follow_duration_s = duration
            goal.reverse_motion = True
            goal.camera_source = 'rear_camera'
            goal.timeout = min(self._action_timeout, duration + 8.0)
            self._qr_gate.docking()
            self._docking_target = station
            self._docking_duration = duration
            self._docking_elapsed = 0.0
            self._docking_remaining = duration
            self._docking_lane_active = False
            self._docking_camera_valid = False
            self._docking_stopped = False
            self._docking_error = ''
            self._event(
                'timed_reverse_docking_started', station=station,
                duration_s=duration, camera='rear_camera')

            def feedback_callback(message):
                feedback = message.feedback
                self._docking_elapsed = float(feedback.elapsed_s)
                self._docking_remaining = float(feedback.remaining_s)
                self._docking_lane_active = bool(
                    feedback.lane_control_active)
                self._docking_camera_valid = bool(feedback.camera_valid)
                self._docking_stopped = bool(feedback.stopped)
                self._status_detail = (
                    f'{station}: geri serit '
                    f'{self._docking_elapsed:.1f}/{duration:.1f} s')

            try:
                self._action(
                    self._dock, goal, f'timed_docking:{station}',
                    goal.timeout + 2.0, require_turn_sensors=True,
                    feedback_callback=feedback_callback)
                self._wait_until_stopped(f'{station} docking sonu')
            except Exception as error:
                self._docking_error = str(error)
                self._event(
                    'timed_reverse_docking_failed', station=station,
                    reason=str(error))
                raise
            self._docking_elapsed = duration
            self._docking_remaining = 0.0
            self._docking_lane_active = False
            self._docking_stopped = True
            self._qr_gate.docking_complete(pickup)
            self._event(
                'timed_reverse_docking_completed', station=station,
                duration_s=duration,
                next_phase=self._qr_gate.phase)
            return
        goal.timeout = min(self._action_timeout, 60.0)
        self._action(self._dock, goal, f'docking:{station}', goal.timeout + 2.0)

    def _do_lift(self, station: str, pickup: bool) -> None:
        goal = LiftLoad.Goal()
        goal.command = (LiftLoad.Goal.COMMAND_PICKUP if pickup else
                        LiftLoad.Goal.COMMAND_DROPOFF)
        goal.station_id = station
        goal.timeout = min(self._action_timeout, 30.0)
        self._action(self._lift, goal, f'lift:{"pickup" if pickup else "dropoff"}',
                     goal.timeout + 2.0)

    def _run(self) -> None:
        success, reason = False, ''
        self._mission_started_wall = time.monotonic()
        self._mission_elapsed = 0.0
        try:
            self._gate_ok = False
            self._gate_entry_node = ''
            self._gate_direction = ''
            self._gate_crossing_id = ''
            loaded = self._loaded
            self._set_state(RobotStatus.STATE_TASK_RECEIVED,
                            self._route_nodes[0])
            for index, station in enumerate(self._route_nodes):
                self._current_stop_index = index
                pickup = index % 2 == 0
                self._pickup = station if pickup else self._pickup
                self._dropoff = (self._route_nodes[index + 1] if pickup else station)
                self._begin_station_approach(station)
                configured_approach = bool(
                    self._nodes[station].get('approach_qr_id')
                )
                navigation_target = (
                    self._station_approach_target(station)
                    if configured_approach else station
                )
                if index == 0:
                    self._navigate(navigation_target, loaded=loaded)
                else:
                    direction = 'outbound' if not pickup else 'return'
                    self._navigate_via_gate(
                        navigation_target,
                        loaded=loaded,
                        direction=direction,
                    )
                if configured_approach:
                    self._wait_for_station_qr(station)
                    self._wait_until_stopped(
                        f'{station} Nav2-donus devri'
                    )
                    self._turn_at_station(station)
                self._do_dock(station, pickup=pickup)
                self._current_node = station
                self._do_lift(station, pickup=pickup)
                loaded = pickup
                self._publish_load_state(loaded)
                self._exit_station(station, loaded=loaded)
            self._current_stop_index = len(self._route_nodes)
            if self._return_home:
                self._set_state(RobotStatus.STATE_RETURNING, self._home_node)
                self._navigate_via_gate(
                    self._home_node,
                    loaded=False,
                    direction='return',
                )
            success = True
            self._set_state(RobotStatus.STATE_IDLE)
        except Exception as exc:  # mission boundary must always fail safe
            reason = str(exc)
            if not self._estop:
                self._state = RobotStatus.STATE_ERROR
            self._status_detail = reason or 'gorev hatasi'
            self._event('mission_failed', reason=reason)
        finally:
            if self._mission_started_wall:
                self._mission_elapsed = max(
                    0.0, time.monotonic() - self._mission_started_wall)
            self._safe_stop()
            self._notify_complete(success, reason or 'gorev tamam')
            self._event('mission_complete', success=success, reason=reason)
            with self._lock:
                self._busy = False
                self._running = False
                self._active_goal, self._active_kind = None, ''
                if not self._latched_abort and not self._estop and not success:
                    self._state = RobotStatus.STATE_ERROR
            self._qr_gate.reset()

    def _notify_complete(self, success: bool, message: str) -> None:
        if not self._task_id or not self._complete.wait_for_service(timeout_sec=1.0):
            self._event('plc_completion_unacknowledged', success=success)
            return
        req = TaskComplete.Request()
        req.task_id, req.success, req.message = self._task_id, success, message
        future = self._complete.call_async(req)
        end = time.monotonic() + 2.0
        while not future.done() and time.monotonic() < end:
            time.sleep(0.02)

    def _publish_status(self) -> None:
        health = self._localization_health()
        msg = RobotStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.mission_state = self._state
        if self._mission_started_wall and self._running:
            msg.mission_elapsed_s = float(
                max(0.0, time.monotonic() - self._mission_started_wall))
        else:
            msg.mission_elapsed_s = float(self._mission_elapsed)
        msg.status_detail = self._abort_reason or self._status_detail
        msg.manual_mode_enabled, msg.estop_active = self._manual, self._estop
        if self._pose is not None:
            msg.pose = self._pose
            cov = self._pose.pose.covariance
            msg.position_covariance = float(cov[0] + cov[7])
        else:
            msg.pose = PoseWithCovarianceStamped()
            msg.pose.header = msg.header
            msg.position_covariance = math.inf
        msg.localization_valid = health.valid
        msg.current_route_edge, msg.next_node = self._edge, self._next_node
        msg.cross_track_error = float(self._cross_track)
        msg.route_speed_limit = float(self._route_speed_limit)
        msg.route_guard_state = self._route_guard_state
        msg.route_stop_reason = self._route_stop_reason
        msg.selected_route_edges = list(self._selected_route_edges)
        msg.obstacle_detected = self._obstacle
        msg.linear_speed = float(self._linear_speed)
        msg.battery_voltage = float(self._battery_voltage)
        msg.battery_current = float(self._battery_current)
        msg.battery_temperature = float(self._battery_temperature)
        msg.task_id, msg.task_source = self._task_id, self._source
        msg.pickup_node, msg.dropoff_node = self._pickup, self._dropoff
        msg.route_nodes = list(self._route_nodes)
        msg.current_stop_index = self._current_stop_index
        msg.return_home = self._return_home
        msg.last_qr_data = self._last_qr
        msg.last_qr_detected = self._last_qr_detected
        msg.last_qr_pose_in_camera = self._last_qr_pose
        msg.last_qr_confidence = float(self._last_qr_confidence)
        msg.last_qr_camera_frame = self._last_qr_camera
        msg.last_qr_age_s = float(
            time.monotonic() - self._last_qr_seen
            if self._last_qr_seen else math.inf)
        msg.plc_connected = (self._plc_connected and
                             time.monotonic() - self._plc_seen <= self._plc_freshness)
        msg.gate_permission_granted = self._gate_ok
        msg.gate_entry_node = self._gate_entry_node
        msg.gate_direction = self._gate_direction
        msg.gate_crossing_id = self._gate_crossing_id
        msg.station_phase = self._qr_gate.phase
        msg.qr_trigger_armed = self._qr_gate.armed
        msg.expected_qr_id = self._qr_gate.expected_qr_id
        msg.qr_target_station = self._qr_gate.target_station
        msg.last_qr_reject_reason = self._qr_gate.last_reject_reason
        msg.docking_target_station = self._docking_target
        msg.docking_configured_duration_s = float(self._docking_duration)
        msg.docking_elapsed_s = float(self._docking_elapsed)
        msg.docking_remaining_s = float(self._docking_remaining)
        msg.docking_lane_control_active = self._docking_lane_active
        msg.docking_camera_valid = self._docking_camera_valid
        msg.docking_stopped = self._docking_stopped
        msg.docking_error_reason = self._docking_error
        msg.active_field_ready = self._active_field_ready
        msg.active_field_name = self._active_field_name
        msg.active_field_version = self._active_field_version
        msg.active_field_hash = self._active_field_hash
        self._status_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = MissionManager()
    executor = MultiThreadedExecutor(num_threads=6)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
