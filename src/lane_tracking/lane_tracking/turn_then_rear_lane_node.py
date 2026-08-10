"""Once 180 derece don, sonra arka kamerayla hizalanip seridi takip et."""

import math
from enum import Enum

import cv2
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

from .imgprocess_node import combine_lane_errors, scale_lane_error
from .lane_detector import LaneDetector
from .turnaround_node import (
    angular_command,
    normalize_angle,
    quaternion_yaw,
    slew_limited_speed,
)


class StartState(Enum):
    WAIT_ODOM = 1
    SETTLING = 2
    TURNING = 3
    CAMERA_START = 4
    ALIGNING = 5
    TRACKING = 6
    STOPPED = 7


def alignment_confirmed(
        found, confidence, combined_error, heading_error,
        minimum_confidence, error_tolerance, heading_tolerance):
    """Seridin hem konum hem yon olarak ortalandigini denetle."""
    return (
        bool(found)
        and float(confidence) >= float(minimum_confidence)
        and abs(float(combined_error)) <= float(error_tolerance)
        and abs(float(heading_error)) <= float(heading_tolerance)
    )


def camera_steering_command(combined_error, maximum_speed, steering_sign):
    """Kamera bakis yonune gore goruntu hatasini acisal hiza cevir."""
    error = max(-1.0, min(1.0, float(combined_error)))
    return -error * max(0.0, float(maximum_speed)) * float(steering_sign)


class TurnThenRearLaneNode(Node):
    """Baslangicta donus, arka kamera hizalama ve serit takibini yonetir."""

    def __init__(self):
        super().__init__('turn_then_rear_lane_node')
        self._declare_parameters()
        self._read_parameters()

        self.cmd_pub = self.create_publisher(Twist, self.output_topic, 10)
        self.debug_pub = self.create_publisher(
            CompressedImage, '/lane_tracking/debug/compressed', 1)
        self.create_subscription(
            Odometry, self.odom_topic, self._odom_cb, 20)
        self.create_subscription(String, '/task_command', self._command_cb, 10)

        self.state = StartState.WAIT_ODOM
        self.state_started = self._now()
        self.current_yaw = None
        self.last_odom_time = None
        self.previous_yaw = None
        self.turned_angle = 0.0
        self.commanded_angular = 0.0
        self.cap = None
        self.detector = None
        self.aligned_frames = 0
        self.missed_frames = 0
        self.filtered_lane_angular = 0.0

        self.control_period = 1.0 / max(1.0, self.control_rate)
        self.timer = self.create_timer(self.control_period, self._control)
        self.get_logger().warning(
            '=== DONUS SONRASI SERIT BASLANGICI === Kamera kapali; '
            'odometri bekleniyor, '
            'ardindan yavas 180 derece donus yapilacak')

    def _declare_parameters(self):
        self.declare_parameter('output_topic', '/cmd_vel')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('control_rate', 30.0)
        self.declare_parameter('turn_angle_degrees', 180.0)
        self.declare_parameter('turn_direction', 1)
        self.declare_parameter('turn_max_angular_speed', 0.20)
        self.declare_parameter('turn_min_angular_speed', 0.16)
        self.declare_parameter('turn_angular_gain', 0.18)
        self.declare_parameter('turn_angular_acceleration', 0.10)
        self.declare_parameter('turn_angular_deceleration', 0.16)
        self.declare_parameter('turn_tolerance_degrees', 2.5)
        self.declare_parameter('turn_settle_duration', 0.80)
        self.declare_parameter('turn_timeout', 30.0)
        self.declare_parameter('odom_timeout', 0.50)

        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 320)
        self.declare_parameter('frame_height', 240)
        self.declare_parameter('frame_rate', 30.0)
        self.declare_parameter('lane_adaptive_value_max', 140)
        self.declare_parameter('lane_adaptive_block_size', 81)
        self.declare_parameter('lane_adaptive_offset', 18)

        self.declare_parameter('alignment_max_angular_speed', 0.14)
        self.declare_parameter('alignment_min_angular_speed', 0.08)
        self.declare_parameter('alignment_gain', 0.30)
        self.declare_parameter('alignment_error_tolerance', 0.05)
        self.declare_parameter('alignment_heading_tolerance', 0.10)
        self.declare_parameter('alignment_min_confidence', 0.35)
        self.declare_parameter('alignment_confirm_frames', 12)
        self.declare_parameter('alignment_timeout', 20.0)

        self.declare_parameter('tracking_linear_speed', 0.060)
        self.declare_parameter('tracking_min_linear_speed', 0.020)
        self.declare_parameter('tracking_max_angular_speed', 0.075)
        self.declare_parameter('tracking_heading_gain', 0.35)
        self.declare_parameter('tracking_steering_alpha', 0.20)
        self.declare_parameter('tracking_loss_stop_frames', 4)
        # Arka kamera hareket yonunun tersine baktigi icin on kamera
        # denetleyicisinin direksiyon isareti ters cevrilir.
        self.declare_parameter('steering_sign', -1.0)

    def _read_parameters(self):
        def value(name):
            return self.get_parameter(name).value

        self.output_topic = str(value('output_topic'))
        self.odom_topic = str(value('odom_topic'))
        self.control_rate = float(value('control_rate'))
        self.turn_angle = math.radians(float(value('turn_angle_degrees')))
        self.direction = 1.0 if int(value('turn_direction')) >= 0 else -1.0
        self.turn_max = float(value('turn_max_angular_speed'))
        self.turn_min = float(value('turn_min_angular_speed'))
        self.turn_gain = float(value('turn_angular_gain'))
        self.turn_acceleration = float(value('turn_angular_acceleration'))
        self.turn_deceleration = float(value('turn_angular_deceleration'))
        self.turn_tolerance = math.radians(
            float(value('turn_tolerance_degrees')))
        self.turn_settle = float(value('turn_settle_duration'))
        self.turn_timeout = float(value('turn_timeout'))
        self.odom_timeout = float(value('odom_timeout'))
        self.camera_device = str(value('camera_device'))
        self.frame_width = int(value('frame_width'))
        self.frame_height = int(value('frame_height'))
        self.frame_rate = float(value('frame_rate'))
        self.mask_value_max = int(value('lane_adaptive_value_max'))
        self.mask_block_size = int(value('lane_adaptive_block_size'))
        self.mask_offset = int(value('lane_adaptive_offset'))
        self.align_max = float(value('alignment_max_angular_speed'))
        self.align_min = float(value('alignment_min_angular_speed'))
        self.align_gain = float(value('alignment_gain'))
        self.align_error_tolerance = float(
            value('alignment_error_tolerance'))
        self.align_heading_tolerance = float(
            value('alignment_heading_tolerance'))
        self.align_min_confidence = float(value('alignment_min_confidence'))
        self.align_confirm_frames = int(value('alignment_confirm_frames'))
        self.align_timeout = float(value('alignment_timeout'))
        self.tracking_speed = float(value('tracking_linear_speed'))
        self.tracking_min_speed = float(value('tracking_min_linear_speed'))
        self.tracking_max_angular = float(
            value('tracking_max_angular_speed'))
        self.tracking_heading_gain = float(value('tracking_heading_gain'))
        self.tracking_alpha = float(value('tracking_steering_alpha'))
        self.loss_stop_frames = int(value('tracking_loss_stop_frames'))
        self.steering_sign = float(value('steering_sign'))

    def _now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _odom_cb(self, msg):
        yaw = quaternion_yaw(msg.pose.pose.orientation)
        self.current_yaw = yaw
        self.last_odom_time = self._now()
        if self.state is StartState.TURNING:
            if self.previous_yaw is not None:
                step = self.direction * normalize_angle(
                    yaw - self.previous_yaw)
                self.turned_angle += max(0.0, step)
            self.previous_yaw = yaw

    def _command_cb(self, msg):
        if msg.data.strip().upper() == 'STOP':
            self.state = StartState.STOPPED
            self._stop()
            self.get_logger().error(
                '=== DURDURULDU === STOP komutu alindi')

    def _odom_fresh(self, now):
        return (self.last_odom_time is not None
                and now - self.last_odom_time <= self.odom_timeout)

    def _control(self):
        now = self._now()
        if self.state is StartState.STOPPED:
            self._stop()
            return

        if self.state is StartState.WAIT_ODOM:
            self._stop()
            if not self._odom_fresh(now):
                return
            self.state = StartState.SETTLING
            self.state_started = now
            self.get_logger().warning(
                '=== 180 DERECE DONUS HAZIR === Arac sabitleniyor')
            return

        if self.state is StartState.SETTLING:
            self._stop()
            if now - self.state_started < self.turn_settle:
                return
            if not self._odom_fresh(now):
                self.state = StartState.WAIT_ODOM
                return
            self.previous_yaw = self.current_yaw
            self.turned_angle = 0.0
            self.commanded_angular = 0.0
            self.state = StartState.TURNING
            self.state_started = now
            self.get_logger().warning(
                '=== 180 DERECE DONUS BASLADI === Kamera halen kapali')
            return

        if self.state is StartState.TURNING:
            self._turn_control(now)
            return

        if self.state is StartState.CAMERA_START:
            self._stop()
            if not self._open_camera():
                self.state = StartState.STOPPED
                return
            self.state = StartState.ALIGNING
            self.state_started = now
            self.get_logger().warning(
                '=== KAMERA ACILDI === Arka/lift kamerasi serit '
                'hizalamasina basladi')
            return

        self._camera_control(now)

    def _turn_control(self, now):
        if not self._odom_fresh(now):
            self._stop()
            self.get_logger().error(
                'Donus bekletiliyor: guncel odometri yok',
                throttle_duration_sec=2.0)
            return
        if now - self.state_started >= self.turn_timeout:
            self.state = StartState.STOPPED
            self._stop()
            self.get_logger().error('Donus zaman asimi; arac durduruldu')
            return
        remaining = self.turn_angle - self.turned_angle
        if remaining <= self.turn_tolerance:
            self._stop()
            self.state = StartState.CAMERA_START
            self.state_started = now
            self.get_logger().warning(
                f'=== 180 DERECE TAMAMLANDI === '
                f'Olculen={math.degrees(self.turned_angle):.1f} derece')
            return
        target = angular_command(
            remaining, self.turn_gain, self.turn_min, self.turn_max)
        self.commanded_angular = slew_limited_speed(
            self.commanded_angular, target, self.turn_acceleration,
            self.control_period, self.turn_deceleration)
        self._publish(0.0, self.direction * self.commanded_angular)

    def _open_camera(self):
        source = (int(self.camera_device) if self.camera_device.isdigit()
                  else self.camera_device)
        self.cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
        if not self.cap.isOpened():
            self.get_logger().error(
                f'Arka/lift kamerasi acilamadi: {self.camera_device}')
            return False
        self.detector = LaneDetector(
            use_opencl=False, value_max=self.mask_value_max,
            block_size=self.mask_block_size,
            adaptive_offset=self.mask_offset)
        return True

    def _camera_control(self, now):
        ok, frame = self.cap.read()
        if not ok:
            self._stop()
            self.get_logger().error(
                'Kamera karesi okunamadi; arac duruyor',
                throttle_duration_sec=2.0)
            return
        center_x = frame.shape[1] // 2
        cv2.line(frame, (center_x, 0), (center_x, frame.shape[0]),
                 (255, 0, 0), 2)
        found, pixel_error = self.detector.process(frame, center_x)
        combined_error = 0.0
        heading_error = 0.0
        if found:
            _, position_error, _ = scale_lane_error(
                pixel_error, center_x, 1.0, 0.0)
            heading_error = self.detector.last_heading_error
            combined_error, _ = combine_lane_errors(
                position_error, heading_error,
                self.tracking_heading_gain, 1.0)

        if self.state is StartState.ALIGNING:
            self._alignment_control(
                now, found, combined_error, heading_error)
            label = 'HIZALANIYOR'
        else:
            self._tracking_control(found, combined_error)
            label = 'ARKA KAMERA SERIT TAKIBI'
        cv2.putText(frame, label, (10, 28), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (0, 255, 255), 2)
        self._publish_debug(frame)

    def _alignment_control(self, now, found, combined_error, heading_error):
        confirmed = alignment_confirmed(
            found, self.detector.last_confidence, combined_error,
            heading_error, self.align_min_confidence,
            self.align_error_tolerance, self.align_heading_tolerance)
        self.aligned_frames = self.aligned_frames + 1 if confirmed else 0
        if self.aligned_frames >= max(1, self.align_confirm_frames):
            self._stop()
            self.filtered_lane_angular = 0.0
            self.missed_frames = 0
            self.state = StartState.TRACKING
            self.state_started = now
            self.get_logger().warning(
                '=== SERIT ORTALANDI === Hizalama dogrulandi; '
                'arka kamera ile ileri serit takibi basladi')
            return
        if now - self.state_started >= self.align_timeout:
            self.state = StartState.STOPPED
            self._stop()
            self.get_logger().error(
                'Serit hizalama zaman asimi; arac guvenli bicimde durduruldu')
            return
        if not found:
            self._stop()
            self.get_logger().warning(
                'Arka kamera serit bekliyor; hareket yok',
                throttle_duration_sec=1.0)
            return
        magnitude = min(self.align_max, max(
            self.align_min, self.align_gain * abs(combined_error)))
        angular = camera_steering_command(
            math.copysign(1.0, combined_error), magnitude,
            self.steering_sign)
        self._publish(0.0, angular)

    def _tracking_control(self, found, combined_error):
        if not found:
            self.missed_frames += 1
            # Kamera kaybinda eski hiz komutunun surucu zaman asimina kadar
            # devam etmesine izin verme; her kayip karede aktif dur komutu ver.
            self._stop()
            if self.missed_frames >= max(1, self.loss_stop_frames):
                self.get_logger().warning(
                    'Takipte serit kaybedildi; arac seridi bekliyor',
                    throttle_duration_sec=1.0)
            return
        self.missed_frames = 0
        target = camera_steering_command(
            combined_error, self.tracking_max_angular,
            self.steering_sign)
        alpha = max(0.0, min(1.0, self.tracking_alpha))
        self.filtered_lane_angular += alpha * (
            target - self.filtered_lane_angular)
        turn_ratio = min(
            1.0, abs(self.filtered_lane_angular)
            / max(1e-6, self.tracking_max_angular))
        fast = abs(self.tracking_speed)
        slow = min(fast, abs(self.tracking_min_speed))
        speed = fast - (fast - slow) * turn_ratio
        linear = math.copysign(speed, self.tracking_speed)
        self._publish(linear, self.filtered_lane_angular)

    def _publish_debug(self, frame):
        if self.debug_pub.get_subscription_count() == 0:
            return
        mask = self.detector.last_mask
        output = frame
        if mask is not None:
            output = cv2.hconcat([
                frame, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
        ok, encoded = cv2.imencode(
            '.jpg', output, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            return
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.format = 'jpeg'
        msg.data = encoded.tobytes()
        self.debug_pub.publish(msg)

    def _publish(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_pub.publish(msg)

    def _stop(self):
        self._publish(0.0, 0.0)

    def destroy_node(self):
        if rclpy.ok():
            self._stop()
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TurnThenRearLaneNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
