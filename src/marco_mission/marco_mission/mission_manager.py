#!/usr/bin/env python3
"""Fail-safe shared Phase-10 mission state machine for PLC, mock PLC and GUI."""

from __future__ import annotations

import json
import math
import os
import threading
import time
from typing import Any, Dict, Optional

import rclpy
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav2_msgs.action import ComputeRoute, FollowPath
from nav2_msgs.msg import SpeedLimit
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String

from marco_msgs.action import DockToStation, LiftLoad
from marco_msgs.msg import QrDetection, RobotStatus
from marco_msgs.srv import (AssignTask, CancelMission, GatePermission,
                            ResetMissionSafety, StartMission, SubmitManualTask,
                            TaskComplete)


class MissionAbort(RuntimeError):
    """Controlled mission failure carrying a PLC-safe diagnostic."""


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
            ('home_node', 'bekla_A'), ('action_timeout_s', 120.0),
            ('gate_timeout_s', 30.0), ('plc_freshness_s', 3.0),
            ('localization_freshness_s', 2.0), ('status_rate_hz', 5.0),
        ):
            self.declare_parameter(name, default)
        self._default_source = str(self.get_parameter('task_source').value)
        if bool(self.get_parameter('simulate_steps').value):
            raise ValueError('Faz 10 sahte sleep modu kaldirildi; simulate_steps:=false kullan')
        self._manual_enabled = bool(self.get_parameter('manual_task_enabled').value)
        self._gate_node = str(self.get_parameter('gate_node').value)
        self._home_node = str(self.get_parameter('home_node').value)
        self._action_timeout = float(self.get_parameter('action_timeout_s').value)
        self._gate_timeout = float(self.get_parameter('gate_timeout_s').value)
        self._plc_freshness = float(self.get_parameter('plc_freshness_s').value)
        self._loc_freshness = float(
            self.get_parameter('localization_freshness_s').value)
        self._nodes = self._load_graph(str(self.get_parameter('graph_file').value))
        if self._default_source not in ('plc', 'mock_plc'):
            raise ValueError('task_source plc veya mock_plc olmali')

        self._cb = ReentrantCallbackGroup()
        self._lock = threading.RLock()
        self._busy = False
        self._abort_reason = ''
        self._latched_abort = False
        self._active_goal = None
        self._active_kind = ''
        self._state = RobotStatus.STATE_IDLE
        self._task_id = self._source = self._pickup = self._dropoff = ''
        self._next_node = self._edge = self._last_qr = ''
        self._current_node = self._home_node
        self._gate_ok = self._estop = self._manual = self._obstacle = False
        self._plc_connected = False
        self._plc_seen = 0.0
        self._pose: Optional[PoseWithCovarianceStamped] = None
        self._pose_seen = 0.0
        self._cross_track = math.nan

        self._status_pub = self.create_publisher(RobotStatus, '/robot_status', 10)
        self._event_pub = self.create_publisher(String, '/mission/events', 50)
        self._speed_pub = self.create_publisher(SpeedLimit, '/speed_limit', 10)
        self.create_subscription(Bool, '/base/estop', self._on_estop, 10,
                                 callback_group=self._cb)
        self.create_subscription(Bool, '/base/manual_mode', self._on_manual, 10,
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
        self.create_subscription(Float32, '/route/cross_track_error',
                                 lambda m: setattr(self, '_cross_track', float(m.data)),
                                 10, callback_group=self._cb)
        self.create_subscription(String, '/route/active_edge',
                                 lambda m: setattr(self, '_edge', m.data), 10,
                                 callback_group=self._cb)
        self.create_subscription(QrDetection, '/qr/detection', self._on_qr, 10,
                                 callback_group=self._cb)

        self._assign = self.create_client(AssignTask, '/plc/assign_task',
                                          callback_group=self._cb)
        self._gate = self.create_client(GatePermission, '/plc/gate_permission',
                                        callback_group=self._cb)
        self._complete = self.create_client(TaskComplete, '/plc/task_complete',
                                            callback_group=self._cb)
        self._route = ActionClient(self, ComputeRoute, '/compute_route',
                                   callback_group=self._cb)
        self._follow = ActionClient(self, FollowPath, '/follow_path',
                                    callback_group=self._cb)
        self._dock = ActionClient(self, DockToStation, '/dock_to_station',
                                  callback_group=self._cb)
        self._lift = ActionClient(self, LiftLoad, '/lift_load',
                                  callback_group=self._cb)
        self.create_service(StartMission, '/mission/start', self._on_start,
                            callback_group=self._cb)
        self.create_service(SubmitManualTask, '/mission/submit_manual_task',
                            self._on_manual_task, callback_group=self._cb)
        self.create_service(CancelMission, '/mission/cancel', self._on_cancel,
                            callback_group=self._cb)
        self.create_service(ResetMissionSafety, '/mission/reset_safety',
                            self._on_reset_safety, callback_group=self._cb)
        rate = float(self.get_parameter('status_rate_hz').value)
        self.create_timer(1.0 / rate, self._publish_status)
        self._event('ready', source=self._default_source,
                    manual_task_enabled=self._manual_enabled,
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
            nodes[str(prop.get('name', prop['id']))] = {
                'id': int(prop['id']), 'xy': feature['geometry']['coordinates'][:2]}
        return nodes

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
        self._pose_seen = time.monotonic()

    def _on_qr(self, msg: QrDetection) -> None:
        if msg.detected:
            self._last_qr = msg.data

    def _on_plc_connected(self, msg: Bool) -> None:
        self._plc_connected = bool(msg.data)
        if msg.data:
            self._plc_seen = time.monotonic()
        elif self._busy and self._source in ('plc', 'mock_plc'):
            self._request_abort('PLC baglantisi kayboldu', latch=False)

    def _on_manual(self, msg: Bool) -> None:
        self._manual = bool(msg.data)

    def _on_estop(self, msg: Bool) -> None:
        self._estop = bool(msg.data)
        if msg.data:
            self._state = RobotStatus.STATE_ESTOP
            self._request_abort('e-stop aktif', latch=True)

    def _on_safety_abort(self, msg: Bool) -> None:
        if msg.data:
            self._request_abort('safety abort', latch=True)

    def _request_abort(self, reason: str, latch: bool) -> None:
        with self._lock:
            if not self._busy:
                return
            self._abort_reason = self._abort_reason or reason
            self._latched_abort = self._latched_abort or latch
            goal = self._active_goal
        self._event('abort_requested', reason=reason, active_action=self._active_kind)
        if goal is not None:
            goal.cancel_goal_async()
        self._safe_stop()

    def _safe_stop(self) -> None:
        reset = SpeedLimit()
        reset.percentage = False
        reset.speed_limit = 0.0
        self._speed_pub.publish(reset)

    def _validate(self, pickup: str, dropoff: str) -> Optional[str]:
        required = (pickup, dropoff, self._gate_node, self._home_node)
        missing = [node for node in required if node not in self._nodes]
        return f"gecersiz graph node: {', '.join(missing)}" if missing else None

    def _reserve(self, task_id: str, pickup: str, dropoff: str,
                 source: str) -> Optional[str]:
        with self._lock:
            if self._busy:
                return f'aktif gorev var: {self._source}/{self._task_id}'
            if self._estop or self._latched_abort:
                return 'e-stop/safety kilidi aktif; operator reset gerekli'
            error = self._validate(pickup, dropoff)
            if error:
                return error
            self._busy = True
            self._abort_reason = ''
            self._task_id, self._pickup, self._dropoff = task_id, pickup, dropoff
            self._source = source
        self._event('task_accepted', pickup=pickup, dropoff=dropoff)
        threading.Thread(target=self._run, daemon=True).start()
        return None

    def _on_start(self, _req: StartMission.Request,
                  res: StartMission.Response) -> StartMission.Response:
        with self._lock:
            if self._busy:
                res.accepted, res.message = False, 'aktif gorev var'
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
            error = self._reserve(reply.task_id, reply.pickup_node,
                                  reply.dropoff_node, self._default_source)
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
        error = self._reserve(task_id, req.pickup_node, req.dropoff_node, 'gui')
        res.accepted, res.message = error is None, error or 'GUI gorevi kabul edildi'
        if error:
            self._event('task_rejected', requested_source='gui', reason=error)
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
            else:
                self._latched_abort = False
                self._abort_reason = ''
                self._state = RobotStatus.STATE_IDLE
                res.accepted, res.message = True, 'operator safety reset kabul edildi'
                self._event('safety_reset')
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
        if self._source in ('plc', 'mock_plc') and self._plc_seen:
            if time.monotonic() - self._plc_seen > self._plc_freshness:
                raise MissionAbort('PLC heartbeat timeout')

    def _action(self, client, goal, label: str, timeout: Optional[float] = None):
        limit = timeout or self._action_timeout
        self._check_abort()
        if not client.wait_for_server(timeout_sec=2.0):
            raise MissionAbort(f'{label} action server yok')
        sent = client.send_goal_async(goal)
        end = time.monotonic() + limit
        while not sent.done():
            self._check_abort()
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
                if time.monotonic() >= end:
                    handle.cancel_goal_async()
                    raise MissionAbort(f'{label} timeout')
                time.sleep(0.02)
            wrapped = result_future.result()
            if wrapped.status != GoalStatus.STATUS_SUCCEEDED:
                raise MissionAbort(f'{label} status={wrapped.status}')
            result = wrapped.result
            if hasattr(result, 'success') and not result.success:
                raise MissionAbort(f'{label}: {getattr(result, "message", "failed")}')
            if hasattr(result, 'error_code') and result.error_code != 0:
                raise MissionAbort(f'{label} error_code={result.error_code}')
            self._event('action_finished', action=label, outcome='success')
            return result
        finally:
            with self._lock:
                self._active_goal, self._active_kind = None, ''

    def _set_state(self, state: int, next_node: str = '') -> None:
        self._state, self._next_node = state, next_node
        self._event('state_transition', next_node=next_node)

    def _navigate(self, target: str, loaded: bool) -> None:
        self._set_state(RobotStatus.STATE_MOVING_LOADED if loaded else
                        RobotStatus.STATE_MOVING_UNLOADED, target)
        route_goal = ComputeRoute.Goal()
        route_goal.start_id = self._nodes[self._current_node]['id']
        route_goal.goal_id = self._nodes[target]['id']
        route_goal.use_start = True
        route_goal.use_poses = False
        route_result = self._action(self._route, route_goal,
                                    f'route:{self._current_node}->{target}')
        follow_goal = FollowPath.Goal()
        follow_goal.path = route_result.path
        follow_goal.controller_id = 'FollowPath'
        self._edge = f'{self._current_node}->{target}'
        self._action(self._follow, follow_goal, f'navigation:{target}')
        self._current_node, self._edge = target, ''

    def _do_dock(self, station: str, pickup: bool) -> None:
        goal = DockToStation.Goal()
        goal.station_id = station
        goal.position_tolerance = 0.075
        goal.yaw_tolerance = math.radians(5.0)
        goal.approach_type = (DockToStation.Goal.APPROACH_PICKUP if pickup else
                              DockToStation.Goal.APPROACH_DROPOFF)
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
        try:
            self._gate_ok = False
            self._set_state(RobotStatus.STATE_TASK_RECEIVED, self._pickup)
            self._navigate(self._pickup, loaded=False)
            self._do_dock(self._pickup, pickup=True)
            self._do_lift(self._pickup, pickup=True)
            self._navigate(self._gate_node, loaded=True)
            self._set_state(RobotStatus.STATE_WAITING_PLC, self._gate_node)
            gate_req = GatePermission.Request()
            gate_req.node_id = self._gate_node
            gate = self._service_call(self._gate, gate_req, self._gate_timeout,
                                      'PLC gate_permission')
            if not gate.granted:
                raise MissionAbort(f'kapi reddi: {gate.message}')
            self._gate_ok = True
            self._navigate(self._dropoff, loaded=True)
            self._do_dock(self._dropoff, pickup=False)
            self._do_lift(self._dropoff, pickup=False)
            self._set_state(RobotStatus.STATE_RETURNING, self._home_node)
            self._navigate(self._home_node, loaded=False)
            success = True
            self._set_state(RobotStatus.STATE_IDLE)
        except Exception as exc:  # mission boundary must always fail safe
            reason = str(exc)
            if not self._estop:
                self._state = RobotStatus.STATE_ERROR
            self._event('mission_failed', reason=reason)
        finally:
            self._safe_stop()
            self._notify_complete(success, reason or 'gorev tamam')
            self._event('mission_complete', success=success, reason=reason)
            with self._lock:
                self._busy = False
                self._active_goal, self._active_kind = None, ''
                if not self._latched_abort and not self._estop and not success:
                    self._state = RobotStatus.STATE_ERROR

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
        msg = RobotStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.mission_state = self._state
        msg.manual_mode_enabled, msg.estop_active = self._manual, self._estop
        if self._pose is not None:
            msg.pose = self._pose
            cov = self._pose.pose.covariance
            msg.position_covariance = float(cov[0] + cov[7])
            msg.localization_valid = (time.monotonic() - self._pose_seen <=
                                      self._loc_freshness and
                                      math.isfinite(msg.position_covariance))
        else:
            msg.pose = PoseWithCovarianceStamped()
            msg.pose.header = msg.header
            msg.position_covariance = math.inf
            msg.localization_valid = False
        msg.current_route_edge, msg.next_node = self._edge, self._next_node
        msg.cross_track_error = float(self._cross_track)
        msg.obstacle_detected = self._obstacle
        msg.task_id, msg.task_source = self._task_id, self._source
        msg.pickup_node, msg.dropoff_node = self._pickup, self._dropoff
        msg.last_qr_data = self._last_qr
        msg.plc_connected = (self._plc_connected and
                             time.monotonic() - self._plc_seen <= self._plc_freshness)
        msg.gate_permission_granted = self._gate_ok
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
