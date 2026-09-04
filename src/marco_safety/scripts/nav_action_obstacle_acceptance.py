#!/usr/bin/env python3
"""Single visible Nav2/route goal with a Collision Monitor obstacle."""

import json
import os
import time

import rclpy
from action_msgs.msg import GoalStatus, GoalStatusArray
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry, Path
from rclpy.action import ActionClient
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity
from std_msgs.msg import Bool


def uuid_text(value):
    """Return a stable canonical action UUID string."""
    data = bytes(value)
    text = data.hex()
    return '-'.join((text[:8], text[8:12], text[12:16],
                     text[16:20], text[20:]))


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


class Acceptance(Node):
    """Collect action identity, behavior and physical stop evidence."""

    def __init__(self):
        super().__init__('phase8_nav_action_obstacle_acceptance')
        self.declare_parameter(
            'result_path', '/tmp/marco_phase8/nav_action_obstacle.json')
        self.declare_parameter('route_bt', '')
        self.declare_parameter('obstacle_hold_s', 5.0)
        self.nav = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.spawn = self.create_client(SpawnEntity, '/world/marco_test/create')
        self.remove = self.create_client(DeleteEntity, '/world/marco_test/remove')
        self.odom = None
        self.raw = Twist()
        self.safe = Twist()
        self.cmd = Twist()
        self.cross_track = []
        self.status_by_uuid = {}
        self.compute_route_uuids = set()
        self.spin_samples = 0
        self.backup_samples = 0
        self.wait_samples = 0
        self.obstacle_detected = False
        self.collision_zero_seen = False
        self.plan_signatures = set()
        self.create_subscription(Odometry, '/odom', self.odom_cb, 50)
        self.create_subscription(Twist, '/cmd_vel_raw',
                                 lambda msg: setattr(self, 'raw', msg), 50)
        self.create_subscription(Twist, '/cmd_vel_safe',
                                 lambda msg: setattr(self, 'safe', msg), 50)
        self.create_subscription(Twist, '/cmd_vel',
                                 lambda msg: setattr(self, 'cmd', msg), 50)
        self.create_subscription(
            GoalStatusArray, '/navigate_to_pose/_action/status',
            self.nav_status_cb, 20)
        self.create_subscription(
            GoalStatusArray, '/compute_route/_action/status',
            self.route_status_cb, 20)
        self.create_subscription(
            GoalStatusArray, '/spin/_action/status',
            lambda msg: self.count_active(msg, 'spin'), 20)
        self.create_subscription(
            GoalStatusArray, '/backup/_action/status',
            lambda msg: self.count_active(msg, 'backup'), 20)
        self.create_subscription(
            GoalStatusArray, '/wait/_action/status',
            lambda msg: self.count_active(msg, 'wait'), 20)
        self.create_subscription(Path, '/plan', self.plan_cb, 10)
        self.create_subscription(
            Bool, '/safety/obstacle_detected', self.obstacle_cb, 20)

    def odom_cb(self, msg):
        self.odom = msg
        self.cross_track.append(abs(msg.pose.pose.position.y))

    def nav_status_cb(self, msg):
        for item in msg.status_list:
            key = uuid_text(item.goal_info.goal_id.uuid)
            self.status_by_uuid.setdefault(key, []).append(int(item.status))

    def route_status_cb(self, msg):
        for item in msg.status_list:
            if item.status in (GoalStatus.STATUS_ACCEPTED,
                               GoalStatus.STATUS_EXECUTING,
                               GoalStatus.STATUS_SUCCEEDED):
                self.compute_route_uuids.add(
                    uuid_text(item.goal_info.goal_id.uuid))

    def count_active(self, msg, behavior):
        active = any(item.status in (GoalStatus.STATUS_ACCEPTED,
                                     GoalStatus.STATUS_EXECUTING)
                     for item in msg.status_list)
        if active:
            attribute = behavior + '_samples'
            setattr(self, attribute, getattr(self, attribute) + 1)

    def plan_cb(self, msg):
        signature = tuple((round(p.pose.position.x, 2),
                           round(p.pose.position.y, 2)) for p in msg.poses)
        if signature:
            self.plan_signatures.add(signature)

    def obstacle_cb(self, msg):
        self.obstacle_detected = bool(msg.data)
        if (self.obstacle_detected and
                abs(self.safe.linear.x) < 1e-4 and
                abs(self.cmd.linear.x) < 1e-4):
            self.collision_zero_seen = True

    def spin_until(self, predicate, timeout):
        end = time.monotonic() + timeout
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)
            if predicate():
                return True
        return False

    def spawn_obstacle(self):
        sdf = (
            "<sdf version='1.7'><model name='phase8_nav_obstacle'>"
            "<static>true</static><link name='link'><collision name='c'>"
            "<geometry><box><size>0.20 0.80 0.80</size></box></geometry>"
            "</collision><visual name='v'><geometry><box>"
            "<size>0.20 0.80 0.80</size></box></geometry><material>"
            "<ambient>1 0 0 1</ambient><diffuse>1 0 0 1</diffuse>"
            "</material></visual></link></model></sdf>")
        request = SpawnEntity.Request()
        request.entity_factory.name = 'phase8_nav_obstacle'
        request.entity_factory.sdf = sdf
        request.entity_factory.pose.position.x = 1.05
        request.entity_factory.pose.position.y = 0.0
        request.entity_factory.pose.position.z = 0.4
        request.entity_factory.pose.orientation.w = 1.0
        future = self.spawn.call_async(request)
        return self.spin_until(future.done, 10) and future.result().success

    def remove_obstacle(self):
        request = DeleteEntity.Request()
        request.entity.name = 'phase8_nav_obstacle'
        request.entity.type = Entity.MODEL
        future = self.remove.call_async(request)
        return self.spin_until(future.done, 10) and future.result().success

    def run(self):
        ready = (self.nav.wait_for_server(timeout_sec=90) and
                 self.spawn.wait_for_service(timeout_sec=15) and
                 self.remove.wait_for_service(timeout_sec=5) and
                 self.spin_until(lambda: self.odom is not None, 30))
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = 2.0
        goal.pose.pose.orientation.w = 1.0
        goal.behavior_tree = str(self.get_parameter('route_bt').value)
        sent = self.nav.send_goal_async(goal)
        accepted = self.spin_until(sent.done, 10) and sent.result().accepted
        handle = sent.result() if accepted else None
        goal_uuid = uuid_text(handle.goal_id.uuid) if handle else ''
        result_future = handle.get_result_async() if handle else None
        moving = bool(handle and self.spin_until(
            lambda: abs(self.raw.linear.x) > 0.03 and
            self.odom.pose.pose.position.x > 0.15, 30))
        raw_motion_before_obstacle = abs(self.raw.linear.x) > 0.03
        spawn_time = time.monotonic()
        spawned = self.spawn_obstacle() if moving else False
        stopped = bool(spawned and self.spin_until(
            lambda: self.collision_zero_seen, 20))
        stop_time = time.monotonic()
        goal_pending = bool(result_future and not result_future.done())
        hold_s = float(self.get_parameter('obstacle_hold_s').value)
        held = self.spin_until(lambda: False, hold_s) is False
        pending_after_hold = bool(result_future and not result_future.done())
        removed = self.remove_obstacle() if spawned else False
        remove_time = time.monotonic()
        resumed = bool(removed and self.spin_until(
            lambda: abs(self.cmd.linear.x) > 0.02, 20))
        resume_time = time.monotonic()
        finished = bool(result_future and self.spin_until(
            result_future.done, 120))
        action_status = (result_future.result().status if finished else None)
        succeeded = action_status == GoalStatus.STATUS_SUCCEEDED
        final_zero = self.spin_until(
            lambda: abs(self.cmd.linear.x) < 1e-4 and
            abs(self.cmd.angular.z) < 1e-4, 5)
        statuses = self.status_by_uuid.get(goal_uuid, [])
        same_uuid = bool(goal_uuid and statuses and
                         GoalStatus.STATUS_CANCELED not in statuses)
        p95 = percentile(self.cross_track, 0.95)
        replanning_count = max(0, len(self.compute_route_uuids) - 1)
        passed = all((ready, accepted, moving, raw_motion_before_obstacle,
                      spawned, stopped,
                      goal_pending, held, pending_after_hold, removed,
                      resumed, succeeded, final_zero, same_uuid,
                      self.spin_samples == 0, self.backup_samples == 0,
                      replanning_count == 0, len(self.plan_signatures) <= 1,
                      p95 is not None and p95 <= 0.10))
        result = {
            'passed': passed,
            'goal': {'accepted': accepted, 'uuid': goal_uuid,
                     'statuses': statuses, 'same_uuid_continued': same_uuid,
                     'pending_during_obstacle': goal_pending,
                     'pending_after_hold': pending_after_hold,
                     'result_status': action_status,
                     'result': 'SUCCEEDED' if succeeded else 'FAILED'},
            'obstacle': {
                'spawned': spawned, 'removed': removed,
                'collision_monitor_zero': stopped,
                'raw_motion_before_obstacle': raw_motion_before_obstacle,
                'obstacle_state_and_safe_output_zero': stopped,
                'hold_s': hold_s,
                'stop_detection_s': stop_time - spawn_time,
                'resumed': resumed,
                'resume_s': resume_time - remove_time,
            },
            'behavior': {
                'wait_samples': self.wait_samples,
                'spin_samples': self.spin_samples,
                'backup_samples': self.backup_samples,
                'compute_route_goal_count': len(self.compute_route_uuids),
                'replanning_count': replanning_count,
                'path_signature_count': len(self.plan_signatures),
                'alternative_route_observed': len(self.plan_signatures) > 1,
            },
            'metrics': {
                'cross_track_p95_m': p95,
                'cross_track_max_m': max(self.cross_track, default=None),
                'samples': len(self.cross_track),
                'final_twist': {'linear_x': self.cmd.linear.x,
                                'angular_z': self.cmd.angular.z},
            },
        }
        path = str(self.get_parameter('result_path').value)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
        self.get_logger().info('PHASE8_NAV_ACTION=%s %s' %
                               ('PASS' if passed else 'FAIL', path))
        return passed


def main():
    rclpy.init()
    node = Acceptance()
    try:
        success = node.run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
