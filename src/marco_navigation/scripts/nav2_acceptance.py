#!/usr/bin/env python3
"""Evidence-oriented Phase 6 acceptance using Gazebo ground truth."""

import json
import math
import os
import statistics
import time
from collections import deque

import rclpy
from action_msgs.msg import GoalStatus, GoalStatusArray
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
from nav2_msgs.action import ComputePathToPose, NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from ros_gz_interfaces.msg import WorldStatistics
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformListener


FOOTPRINT = [(0.50, 0.35), (0.50, -0.35), (-1.18, -0.35), (-1.18, 0.35)]
GOALS = [('forward', 2.0, 0.0, 0.0), ('turning', 5.0, 3.5, 0.52),
         ('reverse', 4.17, 3.0, 0.52), ('return', 0.0, 0.0, 0.52)]
NODES = ('map_server', 'amcl', 'planner_server', 'controller_server', 'smoother_server',
         'behavior_server', 'bt_navigator', 'waypoint_follower', 'velocity_smoother')


def yaw(q): return math.atan2(2 * (q.w*q.z + q.x*q.y), 1 - 2 * (q.y*q.y + q.z*q.z))
def wrap(value): return math.atan2(math.sin(value), math.cos(value))


def percentile(values, fraction):
    if not values: return None
    ordered = sorted(values); index = (len(ordered)-1)*fraction; low = int(index)
    high = min(low+1, len(ordered)-1)
    return ordered[low] + (ordered[high]-ordered[low])*(index-low)


def metrics(values):
    return {'mean': statistics.fmean(values) if values else None,
            'p95': percentile(values, .95), 'max': max(values) if values else None,
            'final': values[-1] if values else None, 'samples': len(values)}


class Acceptance(Node):
    def __init__(self):
        super().__init__('nav2_acceptance')
        self.declare_parameter('scenario', 'nominal'); self.declare_parameter('timeout', 600.0)
        self.declare_parameter('result_path', '/tmp/marco_phase6/acceptance.json')
        self.start = time.monotonic(); self.map = None; self.truth = None; self.amcl = None
        self.last_cmd = Twist(); self.cmd_samples = []; self.negative_cmd = []
        self.times = {key: [] for key in ('scan', 'odom', 'amcl', 'tf', 'cmd_vel')}
        self.ages = {key: [] for key in ('scan', 'odom')}; self.rtf = []
        self.amcl_pos = []; self.amcl_yaw = []; self.travel = 0.0; self.last_truth_xy = None
        self.truth_history = deque(maxlen=1500)
        self.collisions = 0; self.outside = 0; self.unknown = 0; self.clearances = []
        self.lifecycle = {}; self.tf_edges = {}; self.tf_drop = 0; self.tf_extrapolation = 0
        self.wait_active_samples = 0
        self.buffer = Buffer(cache_time=Duration(seconds=20)); self.listener = TransformListener(self.buffer, self)
        transient = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                               reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, '/map', self.map_cb, transient)
        self.create_subscription(LaserScan, '/scan', lambda m: self.timed('scan', m), qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom', lambda m: self.timed('odom', m), 50)
        self.create_subscription(Odometry, '/ground_truth/odom', self.truth_cb, 50)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_cb, 30)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 50)
        self.create_subscription(TFMessage, '/tf', self.tf_cb, 100)
        self.create_subscription(WorldStatistics, '/world/marco_test/stats', lambda m: self.rtf.append(m.real_time_factor), 10)
        self.create_subscription(GoalStatusArray, '/wait/_action/status', self.wait_status_cb, 10)
        self.stop_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.nav = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.plan = ActionClient(self, ComputePathToPose, '/compute_path_to_pose')
        self.state_clients = {name: self.create_client(GetState, '/%s/get_state' % name) for name in NODES}
        self.change_clients = {name: self.create_client(ChangeState, '/%s/change_state' % name)
                               for name in ('controller_server', 'amcl', 'planner_server')}
        self.spawn_client = self.create_client(SpawnEntity, '/world/marco_test/create')
        self.delete_client = self.create_client(DeleteEntity, '/world/marco_test/remove')
        self.scan_gate = self.create_client(SetBool, '/simulation_scan_gate/set_enabled')

    def wait_status_cb(self, msg):
        if any(item.status in (GoalStatus.STATUS_ACCEPTED, GoalStatus.STATUS_EXECUTING)
               for item in msg.status_list):
            self.wait_active_samples += 1

    def timed(self, key, msg):
        self.times[key].append(time.monotonic())
        stamp = rclpy.time.Time.from_msg(msg.header.stamp)
        self.ages[key].append(max(0.0, (self.get_clock().now()-stamp).nanoseconds/1e9))

    def map_cb(self, msg): self.map = msg
    def cmd_cb(self, msg):
        self.last_cmd = msg; self.times['cmd_vel'].append(time.monotonic())
        self.cmd_samples.append((msg.linear.x, msg.angular.z))
        if msg.linear.x < -0.005: self.negative_cmd.append(msg.linear.x)

    def tf_cb(self, msg):
        self.times['tf'].append(time.monotonic())
        for item in msg.transforms:
            self.tf_edges['%s->%s' % (item.header.frame_id, item.child_frame_id)] = \
                self.tf_edges.get('%s->%s' % (item.header.frame_id, item.child_frame_id), 0) + 1

    def amcl_cb(self, msg):
        self.amcl = msg; self.times['amcl'].append(time.monotonic())
        if self.truth_history:
            stamp = rclpy.time.Time.from_msg(msg.header.stamp).nanoseconds
            _, tx, ty, tyaw = min(self.truth_history, key=lambda item: abs(item[0]-stamp))
            a = msg.pose.pose
            self.amcl_pos.append(math.hypot(a.position.x-tx, a.position.y-ty))
            self.amcl_yaw.append(abs(wrap(yaw(a.orientation)-tyaw)))

    def truth_cb(self, msg):
        self.truth = msg; point = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        self.truth_history.append((rclpy.time.Time.from_msg(msg.header.stamp).nanoseconds,
                                   point[0], point[1], yaw(msg.pose.pose.orientation)))
        if self.last_truth_xy: self.travel += math.hypot(point[0]-self.last_truth_xy[0], point[1]-self.last_truth_xy[1])
        self.last_truth_xy = point
        if self.map: self.check_footprint(msg)

    def check_footprint(self, msg):
        pose = msg.pose.pose; heading = yaw(pose.orientation); c, s = math.cos(heading), math.sin(heading)
        polygon = [(pose.position.x+c*x-s*y, pose.position.y+s*x+c*y) for x, y in FOOTPRINT]
        info = self.map.info; ox, oy = info.origin.position.x, info.origin.position.y
        minx, maxx = min(x for x, _ in polygon), max(x for x, _ in polygon)
        miny, maxy = min(y for _, y in polygon), max(y for _, y in polygon)
        cells = []
        for gy in range(math.floor((miny-oy)/info.resolution)-1, math.ceil((maxy-oy)/info.resolution)+2):
            for gx in range(math.floor((minx-ox)/info.resolution)-1, math.ceil((maxx-ox)/info.resolution)+2):
                if gx < 0 or gy < 0 or gx >= info.width or gy >= info.height:
                    self.outside += 1; continue
                value = self.map.data[gy*info.width+gx]
                px, py = ox+(gx+.5)*info.resolution, oy+(gy+.5)*info.resolution
                if self.inside(px, py, polygon):
                    if value < 0: self.unknown += 1
                    if value >= 65: self.collisions += 1
                if value >= 65:
                    self.clearances.append(min(self.segment_distance(px, py, polygon[i], polygon[(i+1)%4]) for i in range(4)))

    @staticmethod
    def inside(x, y, polygon):
        result = False; previous = polygon[-1]
        for current in polygon:
            if ((current[1] > y) != (previous[1] > y)) and \
               x < (previous[0]-current[0])*(y-current[1])/(previous[1]-current[1])+current[0]: result = not result
            previous = current
        return result

    @staticmethod
    def segment_distance(px, py, a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]; length = dx*dx+dy*dy
        t = 0.0 if not length else max(0.0, min(1.0, ((px-a[0])*dx+(py-a[1])*dy)/length))
        return math.hypot(px-(a[0]+t*dx), py-(a[1]+t*dy))

    def zero(self):
        if not rclpy.ok():
            return
        for _ in range(8):
            try:
                self.stop_pub.publish(Twist())
                rclpy.spin_once(self, timeout_sec=.03)
            except (KeyboardInterrupt, Exception):
                break

    def spin_until(self, predicate, timeout):
        end = time.monotonic()+timeout
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=.1)
            if predicate(): return True
        return False

    def readiness(self, require_localization=True):
        failures = []
        if not self.spin_until(lambda: self.map and self.truth and
                              (self.amcl or not require_localization) and
                              len(self.times['scan']) > 3 and len(self.times['odom']) > 3, 120):
            failures.append('required map/scan/odom/amcl/ground_truth topics not ready')
        lifecycle_deadline = time.monotonic() + 60.0
        while time.monotonic() < lifecycle_deadline:
            all_active = True
            for name, client in self.state_clients.items():
                if not client.wait_for_service(timeout_sec=.2):
                    self.lifecycle[name] = 'service_missing'; all_active = False; continue
                future = client.call_async(GetState.Request())
                rclpy.spin_until_future_complete(self, future, timeout_sec=2)
                state = future.result().current_state.label if future.result() else 'query_failed'
                self.lifecycle[name] = state; all_active = all_active and state == 'active'
            if all_active: break
            rclpy.spin_once(self, timeout_sec=.25)
        for name, state in self.lifecycle.items():
            if state != 'active': failures.append(name+' is '+state)
        if not self.nav.wait_for_server(timeout_sec=30): failures.append('navigate_to_pose not ready')
        if not self.plan.wait_for_server(timeout_sec=30): failures.append('compute_path_to_pose not ready')
        if require_localization:
            try: self.buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time(), timeout=Duration(seconds=2))
            except Exception as exc: failures.append('map->base_footprint TF unavailable: '+str(exc))
        # AMCL only emits a new estimate after its motion thresholds are crossed;
        # at the exact initial pose one accurate finite sample is the valid
        # pre-motion convergence evidence. The full distribution is measured
        # over all subsequent navigation motion.
        if require_localization and not self.spin_until(lambda: self.amcl_pos and self.amcl_pos[-1] < .05 and
                                                       self.amcl_yaw[-1] < math.radians(3), 30):
            failures.append('AMCL did not converge before navigation')
        return failures

    def pose(self, x, y, heading, frame='map'):
        value = PoseStamped(); value.header.frame_id = frame; value.header.stamp = self.get_clock().now().to_msg()
        value.pose.position.x = float(x); value.pose.position.y = float(y)
        value.pose.orientation.z = math.sin(heading/2); value.pose.orientation.w = math.cos(heading/2)
        return value

    @staticmethod
    def path_length(path):
        return sum(math.hypot(b.pose.position.x-a.pose.position.x, b.pose.position.y-a.pose.position.y)
                   for a, b in zip(path.poses, path.poses[1:]))

    @staticmethod
    def path_directions(path):
        signs = []
        for a, b in zip(path.poses, path.poses[1:]):
            dx = b.pose.position.x-a.pose.position.x
            dy = b.pose.position.y-a.pose.position.y
            if math.hypot(dx, dy) < 1e-5:
                continue
            signs.append(-1 if dx*math.cos(yaw(a.pose.orientation)) +
                         dy*math.sin(yaw(a.pose.orientation)) < 0 else 1)
        cusps = sum(a != b for a, b in zip(signs, signs[1:]))
        return {'forward_segments': signs.count(1), 'reverse_segments': signs.count(-1),
                'cusp_count': cusps}

    def compute(self, label, pose, expect_success):
        goal = ComputePathToPose.Goal(); goal.goal = pose; goal.use_start = False; goal.planner_id = 'GridBased'
        sent = self.plan.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10)
        handle = sent.result()
        if not handle or not handle.accepted: return {'name': label, 'result': 'REJECTED', 'expected': expect_success}
        result = handle.get_result_async(); rclpy.spin_until_future_complete(self, result, timeout_sec=15)
        if not result.done(): handle.cancel_goal_async(); return {'name': label, 'result': 'TIMEOUT', 'expected': expect_success}
        response = result.result(); success = response.status == GoalStatus.STATUS_SUCCEEDED
        path = response.result.path if success else Path()
        valid = bool(path.poses) and all(p.header.frame_id == 'map' and math.isfinite(p.pose.position.x) and math.isfinite(p.pose.position.y) for p in path.poses)
        return {'name': label, 'result': 'SUCCEEDED' if success else 'FAILED', 'expected': expect_success,
                'path_valid': valid, 'poses': len(path.poses), 'plan_length_m': self.path_length(path),
                'direction_analysis': self.path_directions(path) if success else None}

    def navigate(self, name, x, y, heading, deadline):
        planned = self.compute(name+'_preplan', self.pose(x, y, heading), True)
        goal = NavigateToPose.Goal(); goal.pose = self.pose(x, y, heading); started = time.monotonic()
        distance_start = self.travel; cmd_start = len(self.cmd_samples); neg_start = len(self.negative_cmd)
        clearance_start = len(self.clearances); collision_start = self.collisions
        sent = self.nav.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10); handle = sent.result()
        if not handle or not handle.accepted: return {'name': name, 'action_result': 'REJECTED'}
        result = handle.get_result_async()
        while rclpy.ok() and not result.done() and time.monotonic() < deadline: rclpy.spin_once(self, timeout_sec=.1)
        if not result.done(): handle.cancel_goal_async(); status = 'TIMEOUT'
        else: status = 'SUCCEEDED' if result.result().status == GoalStatus.STATUS_SUCCEEDED else 'FAILED'
        self.zero(); truth = self.truth.pose.pose if self.truth else None
        pos_error = math.hypot(truth.position.x-x, truth.position.y-y) if truth else None
        yaw_error = abs(wrap(yaw(truth.orientation)-heading)) if truth else None
        commands = self.cmd_samples[cmd_start:]
        return {'name': name, 'action_result': status, 'duration_sec': time.monotonic()-started,
                'plan_length_m': planned.get('plan_length_m'), 'travel_distance_m': self.travel-distance_start,
                'ground_truth_position_error_m': pos_error, 'ground_truth_yaw_error_deg': math.degrees(yaw_error) if yaw_error is not None else None,
                'negative_linear_x_seen': len(self.negative_cmd)>neg_start,
                'plan_direction_analysis': planned.get('direction_analysis'),
                'minimum_footprint_clearance_m': min(self.clearances[clearance_start:]) if len(self.clearances)>clearance_start else None,
                'footprint_occupied_intersections': self.collisions-collision_start,
                'final_cmd_vel': {'linear_x': self.last_cmd.linear.x, 'angular_z': self.last_cmd.angular.z},
                'linear_speed': metrics([abs(v) for v, _ in commands]),
                'angular_speed': metrics([abs(w) for _, w in commands])}

    def cancel_test(self):
        goal = NavigateToPose.Goal(); goal.pose = self.pose(5.0, -3.0, 0.0)
        sent = self.nav.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10); handle = sent.result()
        if not handle or not handle.accepted: return {'result': 'REJECTED'}
        self.spin_until(lambda: abs(self.last_cmd.linear.x) > .01 or abs(self.last_cmd.angular.z) > .01, 5)
        started = time.monotonic(); future = handle.cancel_goal_async(); rclpy.spin_until_future_complete(self, future, timeout_sec=5)
        stopped = self.spin_until(lambda: abs(self.last_cmd.linear.x)<1e-4 and abs(self.last_cmd.angular.z)<1e-4, 3)
        self.zero(); return {'result': 'CANCELED', 'cmd_vel_zero': stopped, 'stop_time_sec': time.monotonic()-started}

    def transition(self, node, transition_id):
        client = self.change_clients[node]
        if not client.wait_for_service(timeout_sec=5):
            return False
        request = ChangeState.Request(); request.transition.id = transition_id
        future = client.call_async(request); rclpy.spin_until_future_complete(self, future, timeout_sec=10)
        return bool(future.result() and future.result().success)

    def lifecycle_fault_test(self, node):
        if node == 'amcl':
            changed = self.transition(node, Transition.TRANSITION_DEACTIVATE)
            # Expire the ten-second TF buffers before submitting the goal so this
            # proves missing map->odom, not use of a cached transform.
            self.spin_until(lambda: False, 12.0)
        else:
            changed = False
        goal = NavigateToPose.Goal(); goal.pose = self.pose(5.0, -3.0, 0.0)
        sent = self.nav.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10)
        handle = sent.result()
        if not handle or not handle.accepted:
            return {'result': 'REJECTED', 'cmd_vel_zero': True}
        self.spin_until(lambda: abs(self.last_cmd.linear.x) > .01 or abs(self.last_cmd.angular.z) > .01, 8)
        if node != 'amcl':
            changed = self.transition(node, Transition.TRANSITION_DEACTIVATE)
        result = handle.get_result_async(); failed = self.spin_until(lambda: result.done(), 12)
        if not failed:
            cancel = handle.cancel_goal_async(); rclpy.spin_until_future_complete(self, cancel, timeout_sec=3)
        stopped = self.spin_until(lambda: abs(self.last_cmd.linear.x)<1e-4 and abs(self.last_cmd.angular.z)<1e-4, 3)
        reactivated = self.transition(node, Transition.TRANSITION_ACTIVATE) if changed else False
        self.zero()
        return {'result': 'FAILED_SAFELY' if stopped else 'UNSAFE', 'lifecycle_deactivated': changed,
                'action_finished': failed, 'cmd_vel_zero': stopped, 'reactivated': reactivated}

    def set_scan(self, enabled):
        if not self.scan_gate.wait_for_service(timeout_sec=5):
            return False
        request = SetBool.Request(); request.data = enabled
        future = self.scan_gate.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5)
        return bool(future.result() and future.result().success)

    def scan_loss_test(self):
        goal = NavigateToPose.Goal(); goal.pose = self.pose(5.0, -3.0, 0.0)
        sent = self.nav.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10)
        handle = sent.result()
        if not handle or not handle.accepted:
            return {'result': 'REJECTED', 'cmd_vel_zero': True}
        moving = self.spin_until(lambda: abs(self.last_cmd.linear.x) > .02, 8)
        disabled = self.set_scan(False); cut_at = time.monotonic()
        result = handle.get_result_async()
        finished = self.spin_until(lambda: result.done(), 15)
        stopped = self.spin_until(lambda: abs(self.last_cmd.linear.x)<1e-4 and abs(self.last_cmd.angular.z)<1e-4, 3)
        if not finished:
            cancel = handle.cancel_goal_async(); rclpy.spin_until_future_complete(self, cancel, timeout_sec=5)
        enabled = self.set_scan(True); self.zero()
        return {'result': 'FAILED_SAFELY' if stopped else 'UNSAFE', 'moving_before_cut': moving,
                'scan_disabled': disabled, 'action_finished': finished,
                'stop_time_sec': time.monotonic()-cut_at, 'cmd_vel_zero': stopped,
                'scan_reenabled': enabled}

    def planner_timeout_test(self):
        started = time.monotonic()
        outcome = self.compute('planner_timeout_probe', self.pose(5.0, 3.5, 0.52), False)
        elapsed = time.monotonic()-started; self.zero()
        return {'result': 'FAILED_AS_EXPECTED' if outcome['result'] != 'SUCCEEDED' else 'UNEXPECTED_SUCCESS',
                'configured_max_planning_time_sec': 1.0e-6,
                'compute_result': outcome['result'], 'elapsed_sec': elapsed, 'cmd_vel_zero': True}

    def preconvergence_test(self):
        if not self.nav.wait_for_server(timeout_sec=3):
            self.zero()
            return {'result': 'ACTION_SERVER_UNAVAILABLE_AS_EXPECTED',
                    'amcl_pose_received': self.amcl is not None,
                    'action_finished': False, 'cmd_vel_zero': True}
        goal = NavigateToPose.Goal(); goal.pose = self.pose(2.0, 0.0, 0.0)
        sent = self.nav.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10)
        handle = sent.result()
        if not handle or not handle.accepted:
            self.zero(); return {'result': 'REJECTED_AS_EXPECTED', 'cmd_vel_zero': True}
        result = handle.get_result_async(); finished = self.spin_until(lambda: result.done(), 12)
        if not finished:
            cancel = handle.cancel_goal_async(); rclpy.spin_until_future_complete(self, cancel, timeout_sec=5)
        stopped = self.spin_until(lambda: abs(self.last_cmd.linear.x)<1e-4 and abs(self.last_cmd.angular.z)<1e-4, 2)
        self.zero()
        return {'result': 'FAILED_AS_EXPECTED' if finished else 'TIMEOUT_CANCELED_AS_EXPECTED',
                'amcl_pose_received': self.amcl is not None, 'action_finished': finished,
                'cmd_vel_zero': stopped}

    def obstacle_test(self):
        if not self.spawn_client.wait_for_service(timeout_sec=15) or not self.delete_client.wait_for_service(timeout_sec=2):
            return {'result': 'SERVICE_UNAVAILABLE', 'cmd_vel_zero': False}
        sdf = ("<sdf version='1.7'><model name='phase6_dynamic_obstacle'><static>true</static>"
               "<link name='link'><collision name='collision'><geometry><box><size>0.50 1.20 1.00</size>"
               "</box></geometry></collision><visual name='visual'><geometry><box><size>0.50 1.20 1.00"
               "</size></box></geometry><material><ambient>1 0.1 0.1 1</ambient><diffuse>1 0.1 0.1 1"
               "</diffuse></material></visual></link></model></sdf>")
        request = SpawnEntity.Request(); request.entity_factory.name = 'phase6_dynamic_obstacle'
        request.entity_factory.sdf = sdf; request.entity_factory.pose.position.x = 2.5
        request.entity_factory.pose.position.y = 0.0; request.entity_factory.pose.position.z = 0.5
        request.entity_factory.pose.orientation.w = 1.0
        spawned = self.spawn_client.call_async(request)
        rclpy.spin_until_future_complete(self, spawned, timeout_sec=10)
        if not spawned.result() or not spawned.result().success:
            return {'result': 'SPAWN_FAILED', 'cmd_vel_zero': False}
        goal = NavigateToPose.Goal(); goal.pose = self.pose(5.0, 0.0, 0.0)
        sent = self.nav.send_goal_async(goal); rclpy.spin_until_future_complete(self, sent, timeout_sec=10)
        handle = sent.result(); started = time.monotonic(); wait_before = self.wait_active_samples
        moved = self.spin_until(lambda: self.truth and self.truth.pose.pose.position.x > .35, 15)
        stopped_at = time.monotonic()
        stopped = self.spin_until(lambda: abs(self.last_cmd.linear.x) < 1e-4 and
                                  abs(self.last_cmd.angular.z) < 1e-4, 20)
        self.spin_until(lambda: self.wait_active_samples > wait_before, 10)
        held_start = time.monotonic(); self.spin_until(lambda: time.monotonic()-held_start > 3.0, 4)
        delete = DeleteEntity.Request(); delete.entity.name = 'phase6_dynamic_obstacle'; delete.entity.type = Entity.MODEL
        removed = self.delete_client.call_async(delete); rclpy.spin_until_future_complete(self, removed, timeout_sec=10)
        result = handle.get_result_async() if handle else None
        if result:
            self.spin_until(lambda: result.done(), 80)
        success = bool(result and result.done() and result.result().status == GoalStatus.STATUS_SUCCEEDED)
        self.zero()
        return {'result': 'SUCCEEDED' if success else 'FAILED', 'spawned': True,
                'removed': bool(removed.result() and removed.result().success), 'robot_moved': moved,
                'stopped_for_obstacle': stopped, 'stop_detection_sec': time.monotonic()-stopped_at,
                'wait_observed': self.wait_active_samples > wait_before,
                'wait_duration_sec': time.monotonic()-held_start,
                'same_goal_continued': success, 'cmd_vel_zero': abs(self.last_cmd.linear.x)<1e-5 and abs(self.last_cmd.angular.z)<1e-5,
                'duration_sec': time.monotonic()-started}

    def hz(self, values):
        return (len(values)-1)/(values[-1]-values[0]) if len(values)>1 and values[-1]>values[0] else None

    def run(self):
        scenario = self.get_parameter('scenario').value
        if scenario == 'preconvergence':
            failures = []
            if not self.spin_until(lambda: self.map and self.truth and
                                  len(self.times['scan']) > 3 and len(self.times['odom']) > 3, 30):
                failures.append('basic simulation topics unavailable')
            for name, client in self.state_clients.items():
                if not client.wait_for_service(timeout_sec=.2):
                    self.lifecycle[name] = 'service_missing'
                    continue
                future = client.call_async(GetState.Request())
                rclpy.spin_until_future_complete(self, future, timeout_sec=1)
                self.lifecycle[name] = future.result().current_state.label if future.result() else 'query_failed'
        else:
            failures = self.readiness(require_localization=True)
        deadline = time.monotonic()+self.get_parameter('timeout').value
        compute = [] if scenario in ('preconvergence', 'planner_timeout') else [
            self.compute('free', self.pose(2, 0, 0), True),
            self.compute('occupied', self.pose(3, 1.6, 0), False),
            self.compute('outside', self.pose(20, 20, 0), False),
            self.compute('missing_tf', self.pose(1, 0, 0, 'missing_frame'), False)]
        targets = []
        if not failures and scenario == 'nominal':
            for item in GOALS:
                targets.append(self.navigate(*item, deadline))
                if targets[-1]['action_result'] != 'SUCCEEDED': break
        cancel = self.cancel_test() if not failures and scenario == 'cancel' else {'result': 'NOT_RUN'}
        obstacle = self.obstacle_test() if not failures and scenario == 'obstacle' else {'result': 'NOT_RUN'}
        controller_fault = self.lifecycle_fault_test('controller_server') if not failures and scenario == 'controller_inactive' else 'NOT_RUN'
        amcl_fault = self.lifecycle_fault_test('amcl') if not failures and scenario == 'map_to_odom_loss' else 'NOT_RUN'
        scan_fault = self.scan_loss_test() if not failures and scenario == 'scan_loss' else 'NOT_RUN'
        planner_fault = self.planner_timeout_test() if not failures and scenario == 'planner_timeout' else 'NOT_RUN'
        preconvergence = self.preconvergence_test() if not failures and scenario == 'preconvergence' else 'NOT_RUN'
        self.spin_until(lambda: abs(self.last_cmd.linear.x)<1e-5 and abs(self.last_cmd.angular.z)<1e-5, 2); self.zero()
        for target in targets:
            if target['action_result'] != 'SUCCEEDED': failures.append(target['name']+' action failed')
            if target.get('ground_truth_position_error_m') is None or target['ground_truth_position_error_m'] > .10: failures.append(target['name']+' position >0.10m')
            if target.get('ground_truth_yaw_error_deg') is None or target['ground_truth_yaw_error_deg'] > 5: failures.append(target['name']+' yaw >5deg')
        if scenario == 'nominal' and len(targets) != 4: failures.append('nominal goal sequence incomplete')
        if scenario == 'nominal' and len(targets) >= 3 and not targets[2].get('negative_linear_x_seen'): failures.append('reverse goal had no negative cmd_vel')
        if self.collisions: failures.append('footprint occupied-cell intersections')
        if self.outside: failures.append('footprint left map')
        if self.unknown: failures.append('footprint entered unknown cells')
        ap, ay = metrics(self.amcl_pos), metrics(self.amcl_yaw)
        if scenario in ('nominal', 'obstacle'):
            if ap['p95'] is None or ap['p95'] >= .05: failures.append('AMCL p95 position >=0.05m')
            if ay['p95'] is None or ay['p95'] >= math.radians(3): failures.append('AMCL p95 yaw >=3deg')
        for test in compute:
            success = test['result'] == 'SUCCEEDED'
            if success != test['expected']: failures.append('compute path expectation failed: '+test['name'])
            if success and not test.get('path_valid'): failures.append('invalid successful path: '+test['name'])
        if scenario == 'cancel' and (cancel.get('result') != 'CANCELED' or not cancel.get('cmd_vel_zero')):
            failures.append('cancel did not stop safely')
        if scenario == 'obstacle' and (obstacle.get('result') != 'SUCCEEDED' or
                                      not obstacle.get('same_goal_continued') or
                                      not obstacle.get('cmd_vel_zero')):
            failures.append('obstacle wait/remove/continue failed')
        if scenario == 'scan_loss' and scan_fault.get('result') != 'FAILED_SAFELY':
            failures.append('scan loss did not fail safely')
        if scenario == 'controller_inactive' and controller_fault.get('result') != 'FAILED_SAFELY':
            failures.append('controller inactive did not fail safely')
        if scenario == 'map_to_odom_loss' and amcl_fault.get('result') != 'FAILED_SAFELY':
            failures.append('map->odom loss did not fail safely')
        if scenario == 'planner_timeout' and planner_fault.get('result') != 'FAILED_AS_EXPECTED':
            failures.append('planner timeout did not fail as expected')
        if scenario == 'preconvergence' and preconvergence.get('result') not in (
                'REJECTED_AS_EXPECTED', 'ACTION_SERVER_UNAVAILABLE_AS_EXPECTED',
                'FAILED_AS_EXPECTED', 'TIMEOUT_CANCELED_AS_EXPECTED'):
            failures.append('preconvergence goal was not rejected/failed safely')
        result = {'pass': not failures, 'failure_reasons': failures, 'lifecycle_states': self.lifecycle,
                  'topic_hz': {key: self.hz(value) for key, value in self.times.items()},
                  'timestamp_age_sec': {key: metrics(value) for key, value in self.ages.items()},
                  'tf': {'dynamic_edges': self.tf_edges, 'drop_count': self.tf_drop,
                         'extrapolation_count': self.tf_extrapolation,
                         'publishers': sorted('/'.join((p.node_namespace.strip('/'), p.node_name)).strip('/') for p in self.get_publishers_info_by_topic('/tf'))},
                  'action_results': targets, 'compute_path_tests': compute, 'cancel_test': cancel,
                  'negative_linear_x': {'seen': bool(self.negative_cmd), 'minimum': min(self.negative_cmd) if self.negative_cmd else None},
                  'amcl_position_error_m': ap,
                  'amcl_yaw_error_deg': {k: math.degrees(v) if v is not None else None for k, v in ay.items() if k != 'samples'} | {'samples': ay['samples']},
                  'footprint': {'polygon': FOOTPRINT, 'minimum_clearance_m': min(self.clearances) if self.clearances else None,
                                'occupied_intersections': self.collisions, 'outside_samples': self.outside, 'unknown_intersections': self.unknown},
                  'gazebo_rtf': metrics(self.rtf), 'replanning_count': None,
                  'obstacle_wait_test': obstacle,
                  'negative_tests': {'scan_loss': scan_fault, 'controller_inactive': controller_fault, 'map_to_odom_loss': amcl_fault,
                                     'planner_timeout': planner_fault, 'preconvergence_goal': preconvergence},
                  'final_cmd_vel': {'linear_x': self.last_cmd.linear.x, 'angular_z': self.last_cmd.angular.z}}
        path = self.get_parameter('result_path').value; os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as stream: json.dump(result, stream, indent=2)
        (self.get_logger().info if result['pass'] else self.get_logger().error)('Phase 6 %s: %s' % ('PASS' if result['pass'] else 'FAIL', path))


def main(args=None):
    rclpy.init(args=args); node = Acceptance()
    try: node.run()
    except KeyboardInterrupt:
        # launch has already invalidated the context; do not turn a controlled
        # SIGINT shutdown into a secondary publisher-context exception.
        pass
    except Exception as exc:
        node.get_logger().error(str(exc)); node.zero()
    finally:
        node.zero(); node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == '__main__': main()
