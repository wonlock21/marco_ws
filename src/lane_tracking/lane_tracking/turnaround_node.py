"""Serit sonu olayinda odometri geri beslemeli 180 derece donus dugumu."""

import math
from enum import Enum

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String


def normalize_angle(angle):
    """Acisal farki [-pi, pi] araligina getir."""
    return math.atan2(math.sin(angle), math.cos(angle))


def quaternion_yaw(quaternion):
    """geometry_msgs Quaternion'dan yaw acisini hesapla."""
    sin_yaw = 2.0 * (
        quaternion.w * quaternion.z + quaternion.x * quaternion.y)
    cos_yaw = 1.0 - 2.0 * (
        quaternion.y * quaternion.y + quaternion.z * quaternion.z)
    return math.atan2(sin_yaw, cos_yaw)


def angular_command(remaining, gain, minimum, maximum):
    """Hedefe yaklasirken yavaslayan, motor esigini koruyan acisal hiz."""
    if remaining <= 0.0 or maximum <= 0.0:
        return 0.0
    lower = max(0.0, min(float(minimum), float(maximum)))
    return min(float(maximum), max(lower, float(gain) * remaining))


def slew_limited_speed(
        current, target, acceleration, period, deceleration=None):
    """Kalkis ve yavaslamayi ayri sinirlarla yumusak bicimde rampala."""
    rate = acceleration
    if target < current and deceleration is not None:
        rate = deceleration
    maximum_step = max(0.0, float(rate)) * max(0.0, float(period))
    if target > current:
        return min(float(target), float(current) + maximum_step)
    return max(float(target), float(current) - maximum_step)


class TurnState(Enum):
    PASS_THROUGH = 1
    SETTLING = 2
    TURNING = 3
    STOPPING = 4


class TurnaroundNode(Node):
    """Serit komutunu iletir; olay geldiginde cikisi donus icin devralir."""

    def __init__(self):
        super().__init__('turnaround_node')
        self._declare_parameters()

        self.turn_angle = math.radians(float(
            self.get_parameter('turn_angle_degrees').value))
        requested_direction = int(self.get_parameter('turn_direction').value)
        self.direction = 1.0 if requested_direction >= 0 else -1.0
        self.max_angular_speed = float(
            self.get_parameter('turn_max_angular_speed').value)
        self.min_angular_speed = float(
            self.get_parameter('turn_min_angular_speed').value)
        self.angular_gain = float(
            self.get_parameter('turn_angular_gain').value)
        self.angular_acceleration = float(
            self.get_parameter('turn_angular_acceleration').value)
        self.angular_deceleration = float(
            self.get_parameter('turn_angular_deceleration').value)
        self.angle_tolerance = math.radians(float(
            self.get_parameter('turn_tolerance_degrees').value))
        self.settle_duration = float(
            self.get_parameter('settle_duration').value)
        self.stop_duration = float(
            self.get_parameter('stop_duration').value)
        self.command_timeout = float(
            self.get_parameter('lane_command_timeout').value)
        self.odom_timeout = float(
            self.get_parameter('odom_timeout').value)
        self.turn_timeout = float(
            self.get_parameter('turn_timeout').value)

        lane_topic = str(self.get_parameter('lane_command_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)
        odom_topic = str(self.get_parameter('odom_topic').value)

        self.cmd_pub = self.create_publisher(Twist, output_topic, 10)
        self.complete_pub = self.create_publisher(
            Bool, '/lane_tracking/turn_complete', 10)
        self.create_subscription(
            Twist, lane_topic, self._lane_command_callback, 10)
        self.create_subscription(
            Bool, '/lane_tracking/end_detected', self._end_callback, 10)
        self.create_subscription(
            String, '/task_command', self._command_callback, 10)
        self.create_subscription(Odometry, odom_topic, self._odom_callback, 20)

        self.state = TurnState.PASS_THROUGH
        self.last_lane_command = Twist()
        self.last_lane_command_time = None
        self.current_yaw = None
        self.last_odom_time = None
        self.previous_turn_yaw = None
        self.turned_angle = 0.0
        self.commanded_angular_speed = 0.0
        self.state_started = self._now()

        control_rate = max(
            1.0, float(self.get_parameter('control_rate').value))
        self.control_period = 1.0 / control_rate
        self.timer = self.create_timer(self.control_period, self._control)
        self.get_logger().info(
            f'180 derece donus hazir | lane={lane_topic} | odom={odom_topic} '
            f'| cikis={output_topic} | '
            f'yon={"sol" if self.direction > 0 else "sag"}')

    def _declare_parameters(self):
        self.declare_parameter('lane_command_topic', '/cmd_vel_lane')
        self.declare_parameter('output_topic', '/cmd_vel')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('control_rate', 30.0)
        self.declare_parameter('turn_angle_degrees', 180.0)
        self.declare_parameter('turn_direction', 1)
        self.declare_parameter('turn_max_angular_speed', 0.24)
        self.declare_parameter('turn_min_angular_speed', 0.18)
        self.declare_parameter('turn_angular_gain', 0.22)
        self.declare_parameter('turn_angular_acceleration', 0.12)
        self.declare_parameter('turn_angular_deceleration', 0.18)
        self.declare_parameter('turn_tolerance_degrees', 2.5)
        self.declare_parameter('settle_duration', 0.80)
        self.declare_parameter('stop_duration', 0.80)
        self.declare_parameter('lane_command_timeout', 0.25)
        self.declare_parameter('odom_timeout', 0.50)
        self.declare_parameter('turn_timeout', 25.0)

    def _now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _lane_command_callback(self, msg):
        self.last_lane_command = msg
        self.last_lane_command_time = self._now()

    def _end_callback(self, msg):
        if not msg.data or self.state is not TurnState.PASS_THROUGH:
            return
        self.state = TurnState.SETTLING
        self.state_started = self._now()
        self.turned_angle = 0.0
        self.commanded_angular_speed = 0.0
        self.previous_turn_yaw = None
        self._publish_stop()
        self.get_logger().warning(
            '=== DONUS MODU === Serit sonu algilandi; arac durduruluyor, '
            'odometri kontrollu 180 derece donus baslayacak')

    def _command_callback(self, msg):
        if msg.data.strip().upper() != 'STOP':
            return
        was_turning = self.state is not TurnState.PASS_THROUGH
        self.state = TurnState.PASS_THROUGH
        self.last_lane_command = Twist()
        self.last_lane_command_time = self._now()
        self.previous_turn_yaw = None
        self.turned_angle = 0.0
        self.commanded_angular_speed = 0.0
        self._publish_stop()
        if was_turning:
            self.get_logger().warning(
                '180 derece donus STOP komutuyla iptal edildi')

    def _odom_callback(self, msg):
        yaw = quaternion_yaw(msg.pose.pose.orientation)
        self.current_yaw = yaw
        self.last_odom_time = self._now()
        if self.state is TurnState.TURNING:
            if self.previous_turn_yaw is not None:
                step = self.direction * normalize_angle(
                    yaw - self.previous_turn_yaw)
                # Teker kaymasi veya olcum titresimi ters yonde kucuk bir fark
                # uretebilir; tamamlanma ilerlemesini geriye sarmasin.
                self.turned_angle += max(0.0, step)
            self.previous_turn_yaw = yaw

    def _odom_is_fresh(self, now):
        return (self.last_odom_time is not None
                and now - self.last_odom_time <= self.odom_timeout)

    def _control(self):
        now = self._now()
        if self.state is TurnState.PASS_THROUGH:
            if (self.last_lane_command_time is not None
                    and now - self.last_lane_command_time
                    <= self.command_timeout):
                self.cmd_pub.publish(self.last_lane_command)
            else:
                self._publish_stop()
            return

        if self.state is TurnState.SETTLING:
            self._publish_stop()
            if now - self.state_started < self.settle_duration:
                return
            if not self._odom_is_fresh(now):
                self.get_logger().error(
                    '180 derece donus bekliyor: guncel odometri yok',
                    throttle_duration_sec=2.0)
                return
            self.previous_turn_yaw = self.current_yaw
            self.turned_angle = 0.0
            self.commanded_angular_speed = 0.0
            self.state = TurnState.TURNING
            self.state_started = now
            self.get_logger().warning(
                '=== DONUS BASLADI === Odometri hazir; hedef 180 derece')
            return

        if self.state is TurnState.TURNING:
            if not self._odom_is_fresh(now):
                self._publish_stop()
                self.get_logger().error(
                    'Donus durduruldu: odometri zaman asimina ugradi',
                    throttle_duration_sec=2.0)
                return
            if now - self.state_started >= self.turn_timeout:
                self._publish_stop()
                self.commanded_angular_speed = 0.0
                self.state = TurnState.STOPPING
                self.state_started = now
                self.get_logger().error(
                    f'Donus guvenlik zaman asimi: '
                    f'{math.degrees(self.turned_angle):.1f} derecede '
                    'durduruldu')
                return
            remaining = self.turn_angle - self.turned_angle
            if remaining <= self.angle_tolerance:
                self._publish_stop()
                self.commanded_angular_speed = 0.0
                self.state = TurnState.STOPPING
                self.state_started = now
                self.complete_pub.publish(Bool(data=True))
                self.get_logger().info(
                    f'180 derece donus tamamlandi: '
                    f'{math.degrees(self.turned_angle):.1f} derece')
                return
            target_speed = angular_command(
                remaining, self.angular_gain,
                self.min_angular_speed, self.max_angular_speed)
            self.commanded_angular_speed = slew_limited_speed(
                self.commanded_angular_speed, target_speed,
                self.angular_acceleration, self.control_period,
                self.angular_deceleration)
            command = Twist()
            command.angular.z = (
                self.direction * self.commanded_angular_speed)
            self.cmd_pub.publish(command)
            return

        self._publish_stop()
        if now - self.state_started >= self.stop_duration:
            self.state = TurnState.PASS_THROUGH
            self.complete_pub.publish(Bool(data=False))

    def _publish_stop(self):
        self.cmd_pub.publish(Twist())

    def destroy_node(self):
        # launch SIGINT sirasinda ROS baglami dugumden once kapanmis olabilir.
        if rclpy.ok():
            self._publish_stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TurnaroundNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
