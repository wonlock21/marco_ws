#!/usr/bin/env python3
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wrap(value):
    return math.atan2(math.sin(value), math.cos(value))


class SlamTestDrive(Node):
    """Gazebo odometrisine gore kapali cevrim Faz 4 kabul rotasi."""

    def __init__(self):
        super().__init__('slam_test_drive')
        self.declare_parameter('startup_timeout', 45.0)
        self.declare_parameter('waypoint_timeout', 55.0)
        self.declare_parameter('obstacle_timeout', 12.0)
        self.declare_parameter('safety_distance', 0.80)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.done_pub = self.create_publisher(Bool, '/slam_test/completed', 1)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 20)
        self.create_subscription(LaserScan, '/scan', self.scan_cb,
                                 qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, '/map', self.map_cb, 1)
        self.odom = None
        self.have_scan = False
        self.have_map = False
        self.front_range = math.inf
        self.started_wall = time.monotonic()
        self.ready_sim = None
        self.last_count = None
        self.countdown = 5
        self.index = 0
        self.stage_started = None
        self.blocked_since = None
        self.failed = False
        self.finished = False
        # Bos koridorlardan gecen rota. Engel merkezlerinin en az 1.2 m uzaginda.
        self.waypoints = [(0.0, -3.2), (2.0, -3.2), (2.0, -0.3),
                          (0.0, -0.3), (-1.2, -0.3), (-1.2, -3.2),
                          (0.0, -3.2), (0.0, 0.0)]
        self.timer = self.create_timer(0.05, self.step)
        self.get_logger().info('/scan, /odom ve /map bekleniyor...')

    def odom_cb(self, msg):
        self.odom = msg

    def map_cb(self, _msg):
        self.have_map = True

    def scan_cb(self, msg):
        finite = [r for r in msg.ranges if math.isfinite(r)]
        self.have_scan = bool(finite)
        half = math.radians(22.5)
        front = [r for i, r in enumerate(msg.ranges)
                 if math.isfinite(r) and
                 abs(wrap(msg.angle_min + i * msg.angle_increment)) <= half]
        self.front_range = min(front) if front else math.inf

    def publish(self, linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = max(-0.30, min(0.30, linear))
        msg.angular.z = max(-0.50, min(0.50, angular))
        self.pub.publish(msg)

    def stop(self):
        for _ in range(8):
            self.publish()

    def finish(self, failed=False, reason=''):
        if self.finished:
            return
        self.failed = failed
        self.finished = True
        self.stop()
        if failed:
            self.get_logger().error('SLAM surus testi FAIL: ' + reason)
        else:
            self.get_logger().info('Tum waypointler tamamlandi; robot durduruldu.')
        self.done_pub.publish(Bool(data=not failed))

    def step(self):
        if self.finished:
            self.publish()
            return
        ready = self.odom is not None and self.have_scan and self.have_map
        if not ready:
            self.publish()
            if time.monotonic() - self.started_wall > self.get_parameter(
                    'startup_timeout').value:
                self.finish(True, 'topic hazirlik zaman asimi')
            return
        now = self.get_clock().now()
        if self.ready_sim is None:
            self.ready_sim = now
            self.last_count = now
            self.get_logger().info('Topicler hazir; surus 5 saniye sonra baslayacak.')
            return
        if self.countdown:
            if (now - self.last_count).nanoseconds >= 1_000_000_000:
                self.get_logger().info('%d...' % self.countdown)
                self.countdown -= 1
                self.last_count = now
            self.publish()
            return
        if self.stage_started is None:
            self.stage_started = now
            self.get_logger().info('Waypoint 1/%d hedefleniyor.' % len(self.waypoints))
        if (now - self.stage_started).nanoseconds / 1e9 > self.get_parameter(
                'waypoint_timeout').value:
            self.finish(True, 'waypoint %d zaman asimi' % (self.index + 1))
            return
        p = self.odom.pose.pose.position
        yaw = yaw_of(self.odom.pose.pose.orientation)
        tx, ty = self.waypoints[self.index]
        dx, dy = tx - p.x, ty - p.y
        distance = math.hypot(dx, dy)
        if distance < 0.22:
            self.publish()
            self.index += 1
            if self.index == len(self.waypoints):
                self.finish()
                return
            self.stage_started = now
            self.blocked_since = None
            self.get_logger().info('Waypoint %d/%d hedefleniyor.' %
                                   (self.index + 1, len(self.waypoints)))
            return
        error = wrap(math.atan2(dy, dx) - yaw)
        if abs(error) > 0.22:
            self.blocked_since = None
            self.publish(0.0, 1.4 * error)
            return
        if self.front_range < self.get_parameter('safety_distance').value:
            self.publish()
            if self.blocked_since is None:
                self.blocked_since = now
                self.get_logger().warning('On engel: ileri hareket durduruldu.')
            elif (now - self.blocked_since).nanoseconds / 1e9 > self.get_parameter(
                    'obstacle_timeout').value:
                self.finish(True, 'engel kalici')
            return
        self.blocked_since = None
        linear = min(0.30, max(0.10, 0.45 * distance))
        self.publish(linear, 1.2 * error)

    def destroy_node(self):
        if rclpy.ok():
            self.stop()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = SlamTestDrive()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception) as exc:
        if not isinstance(exc, (KeyboardInterrupt, RuntimeError)):
            node.get_logger().error('Surus exception: %s' % exc)
    finally:
        try:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
        except (KeyboardInterrupt, RuntimeError):
            # ros2 launch signals the process group and then each child; a
            # second SIGINT may arrive while rclpy is destroying entities.
            pass


if __name__ == '__main__':
    main()
