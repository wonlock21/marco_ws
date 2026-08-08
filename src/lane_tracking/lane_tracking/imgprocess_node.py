"""Kamera tabanli QR hizalama ve serit takip dugumu."""

from enum import Enum
import os

import cv2
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool, String

from .lane_detector import LaneDetector
from .qr_detector import QRDetector


class ProcessState(Enum):
    IDLE = 1
    QR_ALIGNMENT = 2
    LANE_TRACKING = 3


def scale_lane_error(
        error, half_frame_width, max_angular_speed,
        center_deadband_ratio=0.01):
    """Kamera merkez/kenar araligini tam donus komutuna olcekle."""
    if half_frame_width <= 0 or max_angular_speed <= 0.0:
        return 0.0, 0.0, 0.0
    normalized_error = max(
        -1.0, min(1.0, float(error) / float(half_frame_width)))
    deadband = max(0.0, min(0.95, float(center_deadband_ratio)))
    magnitude = abs(normalized_error)
    if magnitude <= deadband:
        scaled_error = 0.0
    else:
        scaled_magnitude = (magnitude - deadband) / (1.0 - deadband)
        scaled_error = scaled_magnitude
        if normalized_error < 0.0:
            scaled_error = -scaled_error
    target_angular = -scaled_error * float(max_angular_speed)
    return normalized_error, scaled_error, target_angular


def enforce_minimum_wheel_speed(
        linear_speed, angular_speed, wheel_separation,
        minimum_wheel_speed):
    """Iki tekeri de motorun fiziksel kalkis esiginin ustunde tut."""
    if linear_speed <= 0.0 or minimum_wheel_speed <= 0.0:
        return max(0.0, float(linear_speed))
    required_linear = float(minimum_wheel_speed) + (
        abs(float(angular_speed)) * float(wheel_separation) * 0.5)
    return max(float(linear_speed), required_linear)


def combine_lane_errors(
        position_error, heading_error, heading_gain, max_angular_speed):
    """Yanal konum ve ilerideki serit yonunu lineer olarak birlestir."""
    combined_error = max(-1.0, min(
        1.0,
        float(position_error) + float(heading_gain) * float(heading_error),
    ))
    return combined_error, -combined_error * float(max_angular_speed)


class ImgProcessNode(Node):
    def __init__(self):
        super().__init__('imgprocess_node')

        self._declare_parameters()
        self.current_state = self._initial_state()
        self.kp_qr = float(self.get_parameter('kp_qr').value)
        self.kp_lane = float(self.get_parameter('kp_lane').value)
        self.qr_linear_speed = float(
            self.get_parameter('qr_linear_speed').value)
        self.lane_linear_speed = float(
            self.get_parameter('lane_linear_speed').value)
        self.lane_min_linear_speed = float(
            self.get_parameter('lane_min_linear_speed').value)
        self.lane_steering_alpha = float(
            self.get_parameter('lane_steering_alpha').value)
        self.lane_steering_release_alpha = float(
            self.get_parameter('lane_steering_release_alpha').value)
        self.lane_center_deadband_ratio = float(
            self.get_parameter('lane_center_deadband_ratio').value)
        self.lane_heading_gain = float(
            self.get_parameter('lane_heading_gain').value)
        self.lane_loss_hold_frames = int(
            self.get_parameter('lane_loss_hold_frames').value)
        self.lane_min_wheel_speed = float(
            self.get_parameter('lane_min_wheel_speed').value)
        self.wheel_separation = float(
            self.get_parameter('wheel_separation').value)
        self.max_angular_speed = float(
            self.get_parameter('max_angular_speed').value)
        self.filtered_lane_angular = 0.0
        self.lane_missed_frames = 0
        self.last_lane_command = None
        self.show_debug_window = bool(
            self.get_parameter('show_debug_window').value)
        self.use_gpu = self._configure_gpu()

        output_topic = str(self.get_parameter('output_topic').value)
        self.pub_cmd_vel = self.create_publisher(Twist, output_topic, 10)
        self.pub_active = self.create_publisher(
            Bool, '/lane_tracking/active', 10)
        self.pub_debug_image = self.create_publisher(
            CompressedImage, '/lane_tracking/debug/compressed', 1)
        self.sub_command = self.create_subscription(
            String, '/task_command', self.command_callback, 10)

        self.qr_tracker = QRDetector()
        try:
            self.lane_tracker = LaneDetector(
                use_opencl=self.use_gpu,
                value_max=int(self.get_parameter(
                    'lane_adaptive_value_max').value),
                block_size=int(self.get_parameter(
                    'lane_adaptive_block_size').value),
                adaptive_offset=int(self.get_parameter(
                    'lane_adaptive_offset').value),
            )
        except Exception as exc:
            self.use_gpu = False
            self.get_logger().error(
                f'OpenCL baslatilamadi: {exc}; CPU kullaniliyor')
            self.lane_tracker = LaneDetector(
                use_opencl=False,
                value_max=int(self.get_parameter(
                    'lane_adaptive_value_max').value),
                block_size=int(self.get_parameter(
                    'lane_adaptive_block_size').value),
                adaptive_offset=int(self.get_parameter(
                    'lane_adaptive_offset').value),
            )
        self.cap = self._open_camera()

        frame_rate = float(self.get_parameter('frame_rate').value)
        self.timer = self.create_timer(1.0 / frame_rate, self.timer_callback)

        self.get_logger().info(
            f'Goruntu isleme hazir | durum={self.current_state.name} | '
            f'cikis={output_topic} | isleme={"OpenCL GPU" if self.use_gpu else "CPU"}')
        self._log_parameters()

    def _declare_parameters(self):
        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 320)
        self.declare_parameter('frame_height', 240)
        self.declare_parameter('frame_rate', 30.0)
        self.declare_parameter('show_debug_window', True)
        self.declare_parameter('use_gpu', True)
        self.declare_parameter('gpu_device', '/dev/mali0')
        self.declare_parameter('startup_mode', 'IDLE')
        self.declare_parameter('output_topic', '/cmd_vel_lane')
        self.declare_parameter('kp_qr', 0.005)
        self.declare_parameter('kp_lane', 0.00030)
        self.declare_parameter('qr_linear_speed', 0.1)
        self.declare_parameter('lane_linear_speed', 0.067)
        self.declare_parameter('lane_min_linear_speed', 0.016)
        self.declare_parameter('lane_steering_alpha', 0.25)
        self.declare_parameter('lane_steering_release_alpha', 0.60)
        self.declare_parameter('lane_center_deadband_ratio', 0.01)
        self.declare_parameter('lane_heading_gain', 0.35)
        self.declare_parameter('lane_loss_hold_frames', 3)
        self.declare_parameter('lane_adaptive_value_max', 140)
        self.declare_parameter('lane_adaptive_block_size', 81)
        self.declare_parameter('lane_adaptive_offset', 18)
        self.declare_parameter('lane_min_wheel_speed', 0.055)
        self.declare_parameter('wheel_separation', 0.460)
        self.declare_parameter('max_angular_speed', 0.075)

    def _configure_gpu(self):
        if not bool(self.get_parameter('use_gpu').value):
            return False

        device = str(self.get_parameter('gpu_device').value)
        if not os.access(device, os.R_OK | os.W_OK):
            self.get_logger().warning(
                f'GPU aygiti erisilebilir degil: {device}; CPU kullaniliyor')
            return False

        try:
            import pyopencl  # noqa: F401
        except ImportError:
            self.get_logger().warning(
                'python3-pyopencl kurulu degil; CPU kullaniliyor')
            return False
        return True

    def _initial_state(self):
        requested = str(self.get_parameter('startup_mode').value).upper()
        try:
            return ProcessState[requested]
        except KeyError:
            self.get_logger().warning(
                f'Gecersiz startup_mode={requested}; IDLE kullaniliyor')
            return ProcessState.IDLE

    def _open_camera(self):
        device = str(self.get_parameter('camera_device').value)
        source = int(device) if device.isdigit() else device
        cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,
                int(self.get_parameter('frame_width').value))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,
                int(self.get_parameter('frame_height').value))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS,
                float(self.get_parameter('frame_rate').value))
        if not cap.isOpened():
            self.get_logger().error(
                f'Kamera acilamadi: {device}; motor komutu sifir tutulacak')
        return cap

    def command_callback(self, msg):
        command = msg.data.strip().upper()
        if command == 'START_APPROACH':
            self._reset_lane_control()
            self.current_state = ProcessState.QR_ALIGNMENT
            self.get_logger().info('Durum: QR_ALIGNMENT')
        elif command in ('START_LANE', 'LANE_TRACKING'):
            self._reset_lane_control()
            self.current_state = ProcessState.LANE_TRACKING
            self.get_logger().info('Durum: LANE_TRACKING')
        elif command == 'STOP':
            self._reset_lane_control()
            self.current_state = ProcessState.IDLE
            self.stop_robot()
            self._publish_active()
            self.get_logger().info('Durum: IDLE')

    def timer_callback(self):
        self._publish_active()
        ret, frame = self.cap.read()
        if not ret:
            self.stop_robot()
            self.get_logger().warning(
                'Kamera goruntusu okunamadi; dur komutu yayinlandi',
                throttle_duration_sec=2.0)
            return

        height, width, _ = frame.shape
        center_x = width // 2
        cv2.line(frame, (center_x, 0), (center_x, height), (255, 0, 0), 2)

        if self.current_state == ProcessState.IDLE:
            self._draw_state(frame, 'IDLE', (0, 255, 255))
        elif self.current_state == ProcessState.QR_ALIGNMENT:
            self._draw_state(frame, 'QR HIZALANMA', (0, 165, 255))
            found, error = self.qr_tracker.process(frame, center_x)
            if not found:
                self.stop_robot()
            elif abs(error) < 15.0:
                self.stop_robot()
                self._reset_lane_control()
                self.current_state = ProcessState.LANE_TRACKING
                self.get_logger().info(
                    'QR ortalandi; LANE_TRACKING durumuna gecildi')
            else:
                self.publish_movement(
                    self.qr_linear_speed, -error * self.kp_qr)
        elif self.current_state == ProcessState.LANE_TRACKING:
            self._draw_state(frame, 'SERIT TAKIBI', (0, 255, 0))
            found, error = self.lane_tracker.process(frame, center_x)
            if found:
                self.publish_lane_movement(error, center_x)
            else:
                self._handle_lane_loss()

        debug_frame = self._compose_debug_frame(frame)
        if self.show_debug_window:
            cv2.imshow('Orange Pi Kamera Arayuzu', debug_frame)
            cv2.waitKey(1)
        self._publish_debug_image(debug_frame)

    @staticmethod
    def _draw_state(frame, text, color):
        cv2.putText(frame, f'DURUM: {text}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def publish_movement(self, linear_x, angular_z):
        angular_z = max(
            -self.max_angular_speed, min(self.max_angular_speed, angular_z))
        twist_msg = Twist()
        twist_msg.linear.x = float(linear_x)
        twist_msg.angular.z = float(angular_z)
        self.pub_cmd_vel.publish(twist_msg)

    def publish_lane_movement(self, error, half_frame_width):
        normalized_error, scaled_error, _ = scale_lane_error(
            error, half_frame_width, self.max_angular_speed,
            self.lane_center_deadband_ratio)
        heading_error = self.lane_tracker.last_heading_error
        combined_error, target_angular = combine_lane_errors(
            scaled_error, heading_error, self.lane_heading_gain,
            self.max_angular_speed)
        alpha = max(0.0, min(1.0, self.lane_steering_alpha))
        releasing = (
            abs(target_angular) < abs(self.filtered_lane_angular)
            or target_angular * self.filtered_lane_angular < 0.0
        )
        if releasing:
            release_alpha = max(
                0.0, min(1.0, self.lane_steering_release_alpha))
            alpha = max(alpha, release_alpha)
        self.filtered_lane_angular += alpha * (
            target_angular - self.filtered_lane_angular)

        turn_ratio = (
            abs(self.filtered_lane_angular) / self.max_angular_speed
            if self.max_angular_speed > 0.0 else 0.0
        )
        turn_ratio = max(0.0, min(1.0, turn_ratio))
        min_speed = max(
            0.0, min(self.lane_linear_speed, self.lane_min_linear_speed))
        linear_speed = self.lane_linear_speed - (
            self.lane_linear_speed - min_speed) * turn_ratio
        linear_speed = enforce_minimum_wheel_speed(
            linear_speed, self.filtered_lane_angular,
            self.wheel_separation, self.lane_min_wheel_speed)
        half_track = self.wheel_separation * 0.5
        left_target = linear_speed - (
            self.filtered_lane_angular * half_track)
        right_target = linear_speed + (
            self.filtered_lane_angular * half_track)
        self.publish_movement(linear_speed, self.filtered_lane_angular)
        self.lane_missed_frames = 0
        self.last_lane_command = (
            float(linear_speed), float(self.filtered_lane_angular))
        self.get_logger().info(
            f'[SERIT] hata={error:+.1f} px ({normalized_error:+.1%}) | '
            f'merkez={scaled_error:+.1%} | '
            f'yon={heading_error:+.1%} | '
            f'birlesik={combined_error:+.1%} | '
            f'hedef_w={target_angular:+.3f} rad/s | '
            f'filtre_w={self.filtered_lane_angular:+.3f} rad/s '
            f'(alpha={alpha:.2f}) | '
            f'cmd_vel: v={linear_speed:.3f} m/s '
            f'w={self.filtered_lane_angular:+.3f} rad/s | '
            f'teker hedef sol={left_target * 1000.0:+.0f} '
            f'sag={right_target * 1000.0:+.0f} mm/s',
            throttle_duration_sec=0.5)

    def _handle_lane_loss(self):
        self.lane_missed_frames += 1
        hold_frames = max(0, self.lane_loss_hold_frames)
        if (self.last_lane_command is not None
                and self.lane_missed_frames <= hold_frames):
            linear_speed, angular_speed = self.last_lane_command
            self.publish_movement(linear_speed, angular_speed)
            self.get_logger().warning(
                f'[SERIT] gecici kayip {self.lane_missed_frames}/'
                f'{hold_frames} | son komut korunuyor: '
                f'v={linear_speed:.3f} m/s w={angular_speed:+.3f} rad/s')
            return

        self._reset_lane_control()
        self.stop_robot()
        self.get_logger().warning(
            '[SERIT] bulunamadi | cmd_vel: v=0.000 m/s w=0.000 rad/s',
            throttle_duration_sec=0.5)

    def _reset_lane_control(self):
        self.filtered_lane_angular = 0.0
        self.lane_missed_frames = 0
        self.last_lane_command = None
        if hasattr(self, 'lane_tracker'):
            self.lane_tracker.reset_tracking()

    def _compose_debug_frame(self, frame):
        if (not self.show_debug_window
                and self.pub_debug_image.get_subscription_count() == 0):
            return frame
        if (self.current_state is not ProcessState.LANE_TRACKING
                or self.lane_tracker.last_mask is None):
            return frame
        mask_bgr = cv2.cvtColor(
            self.lane_tracker.last_mask, cv2.COLOR_GRAY2BGR)
        cv2.putText(frame, 'ALGILAMA', (10, frame.shape[0] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        cv2.putText(mask_bgr, 'ADAPTIF MASKE', (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        return cv2.hconcat([frame, mask_bgr])

    def stop_robot(self):
        self.publish_movement(0.0, 0.0)

    def _publish_active(self):
        self.pub_active.publish(Bool(
            data=self.current_state is not ProcessState.IDLE))

    def _log_parameters(self):
        rendered = ' | '.join(
            f'{name}={parameter.value}'
            for name, parameter in sorted(self._parameters.items())
        )
        self.get_logger().info(f'[PARAMETRELER imgprocess] {rendered}')

    def _publish_debug_image(self, frame):
        if self.pub_debug_image.get_subscription_count() == 0:
            return
        ok, encoded = cv2.imencode(
            '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            return
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.format = 'jpeg'
        msg.data = encoded.tobytes()
        self.pub_debug_image.publish(msg)

    def destroy_node(self):
        self.stop_robot()
        self.current_state = ProcessState.IDLE
        self._publish_active()
        self.cap.release()
        if self.show_debug_window:
            cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ImgProcessNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
