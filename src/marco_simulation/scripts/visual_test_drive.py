#!/usr/bin/env python3
import math

import rclpy
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rosgraph_msgs.msg import Clock


class VisualTestDrive(Node):
    def __init__(self):
        super().__init__('visual_test_drive')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Clock, '/clock', self.clock_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.have_clock = self.have_odom = self.have_scan = False
        self.last_odom = None
        self.start_odom = None
        self.phase = -1
        self.phase_started = None
        self.countdown = 5
        self.last_countdown = None
        self.finished = False
        self.phases = [
            (3.0, 0.0, 0.0, 'Ekranların açılması bekleniyor.'),
            (5.0, 0.20, 0.0, 'Robot 0.20 m/s ile ileri gidiyor.'),
            (2.0, 0.0, 0.0, 'Robot duruyor.'),
            (4.0, 0.0, 0.35, 'Robot sola dönüyor.'),
            (2.0, 0.0, 0.0, 'Robot duruyor.'),
            (6.0, 0.18, -0.20, 'Robot sağa kavis çiziyor.'),
            (2.0, 0.0, 0.0, 'Robot duruyor.'),
            (3.0, -0.10, 0.0, 'Robot güvenli şekilde geri gidiyor.'),
        ]
        self.timer = self.create_timer(0.05, self.step)
        self.get_logger().info('/clock, /odom ve /scan bekleniyor...')

    def clock_cb(self, _msg):
        self.have_clock = True

    def odom_cb(self, msg):
        self.have_odom = True
        self.last_odom = msg

    def scan_cb(self, msg):
        self.have_scan = any(math.isfinite(value) for value in msg.ranges)

    def publish(self, linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.pub.publish(msg)

    def position_text(self, odom):
        p = odom.pose.pose.position
        return f'x={p.x:.3f} m, y={p.y:.3f} m'

    def step(self):
        if self.finished:
            self.publish()
            return
        if not (self.have_clock and self.have_odom and self.have_scan):
            self.publish()
            return
        now = self.get_clock().now()
        if self.start_odom is None:
            self.start_odom = self.last_odom
            self.last_countdown = now
            self.get_logger().info('Görsel test 5 saniye sonra başlayacak.')
            self.get_logger().info('Başlangıç odometrisi: ' + self.position_text(self.start_odom))
            return
        if self.countdown > 0:
            if (now - self.last_countdown).nanoseconds >= 1_000_000_000:
                self.get_logger().info(f'{self.countdown}...')
                self.countdown -= 1
                self.last_countdown = now
            self.publish()
            return
        if self.phase < 0:
            self.phase = 0
            self.phase_started = now
            self.get_logger().info(self.phases[0][3])
        duration, linear, angular, _ = self.phases[self.phase]
        self.publish(linear, angular)
        if (now - self.phase_started).nanoseconds >= int(duration * 1e9):
            self.publish()
            self.phase += 1
            if self.phase >= len(self.phases):
                self.finished = True
                self.get_logger().info('Bitiş odometrisi: ' + self.position_text(self.last_odom))
                self.get_logger().info('Görsel sürüş testi tamamlandı; ekranlar açık bırakılıyor.')
                return
            self.phase_started = now
            self.get_logger().info(self.phases[self.phase][3])

    def destroy_node(self):
        if rclpy.ok():
            for _ in range(5):
                self.publish()
        return super().destroy_node()


def main(args=None):
    # Keep the context valid while handling Ctrl+C so the final zero Twist can
    # actually be delivered before shutdown.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = VisualTestDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            # ros2 launch may forward a second SIGINT while entities are being
            # destroyed; the final zero Twist has already been published.
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
