"""Kamera tabanli QR hizalama ve serit takip dugumu."""

from enum import Enum
import os

import cv2
from geometry_msgs.msg import Twist
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import Bool, String

from .lane_detector import LaneDetector
from .qr_detector import QRDetector


class ProcessState(Enum):
    IDLE = 1
    QR_ALIGNMENT = 2
    LANE_TRACKING = 3
    TURNAROUND = 4


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


def apply_deadband(value, deadband_ratio=0.01):
    """Normalize edilmis sinyalde kucuk merkez hatalarini sifirla."""
    deadband = max(0.0, min(0.95, float(deadband_ratio)))
    magnitude = abs(float(value))
    if magnitude <= deadband:
        return 0.0
    scaled_magnitude = (magnitude - deadband) / (1.0 - deadband)
    return -scaled_magnitude if float(value) < 0.0 else scaled_magnitude


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


def compute_lane_turn_command(
        control_mode, normalized_error, scaled_error, heading_error,
        offset_gain, heading_gain, center_deadband_ratio,
        max_angular_speed):
    """Serit hatalarindan hedef acisal hiz uret."""
    mode = str(control_mode).strip().lower()
    if mode == 'legacy':
        combined_error, target_angular = combine_lane_errors(
            scaled_error, heading_error, heading_gain, max_angular_speed)
        return 'legacy', scaled_error, combined_error, target_angular

    offset_term = apply_deadband(normalized_error, center_deadband_ratio)
    combined_error = max(-1.0, min(
        1.0,
        float(offset_gain) * float(offset_term)
        + float(heading_gain) * float(heading_error),
    ))
    target_angular = -combined_error * float(max_angular_speed)
    return 'offset_heading', offset_term, combined_error, target_angular


def lane_end_confirmed(
        seen_frames, missed_frames, minimum_seen_frames,
        missing_frames, loss_hold_frames, enabled=True):
    """Baslangic/gecici kayiplari ele, kalici serit sonunu dogrula."""
    if not enabled:
        return False
    required_missing = max(
        int(loss_hold_frames) + 1, int(missing_frames))
    return (
        int(seen_frames) >= max(1, int(minimum_seen_frames))
        and int(missed_frames) >= required_missing
    )


def image_message_to_bgr(msg):
    """Convert common raw ROS image encodings to an owned BGR array."""
    channels_by_encoding = {
        'bgr8': 3,
        'rgb8': 3,
        'bgra8': 4,
        'rgba8': 4,
        'mono8': 1,
    }
    encoding = str(msg.encoding).lower()
    channels = channels_by_encoding.get(encoding)
    if channels is None:
        raise ValueError(f'desteklenmeyen kamera kodlamasi: {msg.encoding}')
    row_bytes = int(msg.width) * channels
    if int(msg.step) < row_bytes:
        raise ValueError('kamera mesaji step degeri satir genisliginden kucuk')
    raw = np.frombuffer(msg.data, dtype=np.uint8)
    required = int(msg.step) * int(msg.height)
    if raw.size < required:
        raise ValueError('kamera mesaji beklenenden kisa')
    rows = raw[:required].reshape(int(msg.height), int(msg.step))
    pixels = rows[:, :row_bytes]
    if channels == 1:
        image = pixels.reshape(int(msg.height), int(msg.width))
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    image = pixels.reshape(int(msg.height), int(msg.width), channels)
    if encoding == 'rgb8':
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if encoding == 'rgba8':
        return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    if encoding == 'bgra8':
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image.copy()


def compute_pd_angular(
        error_px, half_frame_width, previous_error, dt, kp, kd,
        max_angular_speed, previous_derivative=0.0,
        derivative_alpha=0.25):
    """Compute bounded PD steering from camera-minus-lane pixel error."""
    if half_frame_width <= 0.0 or max_angular_speed <= 0.0:
        return 0.0, 0.0, 0.0
    error = max(-1.0, min(
        1.0, float(error_px) / float(half_frame_width)))
    raw_derivative = 0.0
    if previous_error is not None and dt is not None and 0.001 <= dt <= 0.25:
        raw_derivative = (error - float(previous_error)) / float(dt)
    alpha = max(0.0, min(1.0, float(derivative_alpha)))
    derivative = float(previous_derivative) + alpha * (
        raw_derivative - float(previous_derivative))
    angular = float(kp) * error + float(kd) * derivative
    angular = max(
        -float(max_angular_speed),
        min(float(max_angular_speed), angular))
    return angular, error, derivative


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
        self.lane_control_mode = str(
            self.get_parameter('lane_control_mode').value).strip().lower()
        self.lane_offset_gain = float(
            self.get_parameter('lane_offset_gain').value)
        self.lane_heading_gain = float(
            self.get_parameter('lane_heading_gain').value)
        self.lane_loss_hold_frames = int(
            self.get_parameter('lane_loss_hold_frames').value)
        self.lane_end_min_seen_frames = int(
            self.get_parameter('lane_end_min_seen_frames').value)
        self.lane_end_missing_frames = int(
            self.get_parameter('lane_end_missing_frames').value)
        self.lane_end_detection_enabled = bool(
            self.get_parameter('lane_end_detection_enabled').value)
        self.lane_min_wheel_speed = float(
            self.get_parameter('lane_min_wheel_speed').value)
        self.wheel_separation = float(
            self.get_parameter('wheel_separation').value)
        self.max_angular_speed = float(
            self.get_parameter('max_angular_speed').value)
        self.pd_kp = float(self.get_parameter('lane_pd_kp').value)
        self.pd_kd = float(self.get_parameter('lane_pd_kd').value)
        self.pd_derivative_alpha = float(
            self.get_parameter('lane_pd_derivative_alpha').value)
        self._pd_previous_error = None
        self._pd_previous_time = None
        self._pd_derivative = 0.0
        self.filtered_lane_angular = 0.0
        self.lane_missed_frames = 0
        self.lane_seen_frames = 0
        self.lane_end_reported = False
        self.last_lane_command = None
        self.show_debug_window = bool(
            self.get_parameter('show_debug_window').value)
        self.use_gpu = self._configure_gpu()
        self.camera_input = str(
            self.get_parameter('camera_input').value).strip().lower()
        self.camera_topic = str(self.get_parameter('camera_topic').value)
        self.camera_compressed_topic = str(
            self.get_parameter('camera_compressed_topic').value)
        self.camera_timeout = float(
            self.get_parameter('camera_timeout').value)
        self._last_camera_time = None
        self._camera_timed_out = False

        output_topic = str(self.get_parameter('output_topic').value)
        self.pub_cmd_vel = self.create_publisher(Twist, output_topic, 10)
        self.pub_active = self.create_publisher(
            Bool, '/lane_tracking/active', 10)
        self.pub_lane_end = self.create_publisher(
            Bool, '/lane_tracking/end_detected', 10)
        self.pub_debug_image = self.create_publisher(
            CompressedImage, '/lane_tracking/debug/compressed', 1)
        self.sub_command = self.create_subscription(
            String, '/task_command', self.command_callback, 10)
        self.sub_turn_complete = self.create_subscription(
            Bool, '/lane_tracking/turn_complete',
            self.turn_complete_callback, 10)

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
                ipm_enabled=bool(self.get_parameter(
                    'lane_ipm_enabled').value),
                ipm_source_points=list(self.get_parameter(
                    'lane_ipm_source_points').value),
                ipm_destination_points=list(self.get_parameter(
                    'lane_ipm_destination_points').value),
                lookahead_y=int(self.get_parameter(
                    'lane_lookahead_y').value),
                lookahead_band_half_height=int(self.get_parameter(
                    'lane_lookahead_band_half_height').value),
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
                ipm_enabled=bool(self.get_parameter(
                    'lane_ipm_enabled').value),
                ipm_source_points=list(self.get_parameter(
                    'lane_ipm_source_points').value),
                ipm_destination_points=list(self.get_parameter(
                    'lane_ipm_destination_points').value),
                lookahead_y=int(self.get_parameter(
                    'lane_lookahead_y').value),
                lookahead_band_half_height=int(self.get_parameter(
                    'lane_lookahead_band_half_height').value),
            )
        self.cap = None
        self.timer = None
        self.camera_subscription = None
        if self.camera_input == 'ros_topic':
            qos = QoSPresetProfiles.SENSOR_DATA.value
            self.camera_subscription = self.create_subscription(
                Image, self.camera_topic, self._camera_callback, qos)
            self.camera_watchdog = self.create_timer(
                min(0.1, max(0.02, self.camera_timeout * 0.5)),
                self._camera_watchdog_callback)
        elif self.camera_input == 'ros_compressed':
            qos = QoSPresetProfiles.SENSOR_DATA.value
            self.camera_subscription = self.create_subscription(
                CompressedImage,
                self.camera_compressed_topic,
                self._compressed_camera_callback,
                qos)
            self.camera_watchdog = self.create_timer(
                min(0.1, max(0.02, self.camera_timeout * 0.5)),
                self._camera_watchdog_callback)
        elif self.camera_input == 'v4l2':
            self.cap = self._open_camera()
            frame_rate = float(self.get_parameter('frame_rate').value)
            self.timer = self.create_timer(
                1.0 / frame_rate, self.timer_callback)
        else:
            raise ValueError(
                'camera_input yalnizca ros_topic, ros_compressed '
                'veya v4l2 olabilir')

        camera_source = (
            self.camera_topic if self.camera_input == 'ros_topic'
            else self.camera_compressed_topic
            if self.camera_input == 'ros_compressed'
            else self.get_parameter('camera_device').value)
        self.get_logger().info(
            f'Goruntu isleme hazir | durum={self.current_state.name} | '
            f'cikis={output_topic} | '
            f'kamera={self.camera_input}:{camera_source} | '
            f'isleme={"OpenCL GPU" if self.use_gpu else "CPU"}')
        self._log_parameters()

    def _declare_parameters(self):
        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('camera_input', 'v4l2')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter(
            'camera_compressed_topic', '/camera/image_raw/compressed')
        self.declare_parameter('camera_timeout', 0.5)
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
        self.declare_parameter('lane_control_mode', 'offset_heading')
        self.declare_parameter('lane_offset_gain', 0.85)
        self.declare_parameter('lane_heading_gain', 0.35)
        self.declare_parameter('lane_pd_kp', 0.080)
        self.declare_parameter('lane_pd_kd', 0.012)
        self.declare_parameter('lane_pd_derivative_alpha', 0.25)
        self.declare_parameter('lane_loss_hold_frames', 3)
        # Serit, yeni bir takip oturumunda yeterince gorulmeden "son" karari
        # verilmez. Boylece kamera acilisindaki bos kareler donusu tetiklemez.
        self.declare_parameter('lane_end_min_seen_frames', 15)
        self.declare_parameter('lane_end_missing_frames', 9)
        self.declare_parameter('lane_end_detection_enabled', True)
        self.declare_parameter('lane_adaptive_value_max', 140)
        self.declare_parameter('lane_adaptive_block_size', 81)
        self.declare_parameter('lane_adaptive_offset', 18)
        self.declare_parameter('lane_ipm_enabled', False)
        self.declare_parameter(
            'lane_ipm_source_points',
            [0.20, 0.95, 0.42, 0.45, 0.58, 0.45, 0.80, 0.95])
        self.declare_parameter(
            'lane_ipm_destination_points',
            [0.20, 1.00, 0.20, 0.00, 0.80, 0.00, 0.80, 1.00])
        self.declare_parameter('lane_lookahead_y', 160)
        self.declare_parameter('lane_lookahead_band_half_height', 5)
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
        # Bu kamera 640x480 icin yalniz MJPEG destekliyor. Formati boyuttan
        # once secmek OpenCV'nin desteklenmeyen YUYV kipine dusmesini engeller.
        cap.set(
            cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
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

    def turn_complete_callback(self, msg):
        """180 derece manevra bittiginde serit takibini yeniden devral."""
        if (msg.data
                and self.current_state is ProcessState.TURNAROUND):
            self._reset_lane_control(new_session=True)
            self.current_state = ProcessState.LANE_TRACKING
            self.get_logger().info(
                '180 derece donus tamamlandi; LANE_TRACKING devam ediyor')

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.stop_robot()
            self.get_logger().warning(
                'Kamera goruntusu okunamadi; dur komutu yayinlandi',
                throttle_duration_sec=2.0)
            return
        self._process_frame(frame)

    def _camera_callback(self, msg):
        try:
            frame = image_message_to_bgr(msg)
        except (ValueError, cv2.error) as exc:
            self.stop_robot()
            self.get_logger().error(
                f'Kamera mesaji islenemedi: {exc}',
                throttle_duration_sec=2.0)
            return
        self._last_camera_time = self.get_clock().now()
        self._camera_timed_out = False
        self._process_frame(frame)

    def _compressed_camera_callback(self, msg):
        encoded = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            self.stop_robot()
            self.get_logger().error(
                'Sikistirilmis kamera mesaji JPEG olarak acilamadi',
                throttle_duration_sec=2.0)
            return
        self._last_camera_time = self.get_clock().now()
        self._camera_timed_out = False
        self._process_frame(frame)

    def _camera_watchdog_callback(self):
        now = self.get_clock().now()
        stale = self._last_camera_time is None
        if self._last_camera_time is not None:
            age = (now - self._last_camera_time).nanoseconds * 1e-9
            stale = age > self.camera_timeout
        if stale:
            self.stop_robot()
            if not self._camera_timed_out:
                self._camera_timed_out = True
                source_topic = (
                    self.camera_compressed_topic
                    if self.camera_input == 'ros_compressed'
                    else self.camera_topic)
                self.get_logger().warning(
                    f'{source_topic} goruntusu yok; '
                    'dur komutu yayinlandi')

    def _process_frame(self, frame):
        self._publish_active()

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
                if self.lane_control_mode == 'pd_lookahead':
                    lane_x = self.lane_tracker.last_lookahead_x
                    if lane_x is None:
                        self._handle_lane_loss()
                    else:
                        self.lane_seen_frames += 1
                        pd_error = float(center_x) - float(lane_x)
                        self.publish_pd_lane_movement(pd_error, center_x)
                else:
                    self.lane_seen_frames += 1
                    self.publish_lane_movement(error, center_x)
            else:
                self._handle_lane_loss()
        elif self.current_state == ProcessState.TURNAROUND:
            self._draw_state(frame, '180 DERECE DONUS', (255, 0, 255))
            # Donus dugumu /cmd_vel cikisinin tek sahibidir. Bu sifir komutu,
            # eski bir serit komutunun yeniden kullanilmasini da engeller.
            self.stop_robot()

        debug_frame = self._compose_debug_frame(frame)
        if self.show_debug_window:
            cv2.imshow('Orange Pi Kamera Arayuzu', debug_frame)
            cv2.waitKey(1)
        self._publish_debug_image(debug_frame)

    def publish_pd_lane_movement(self, error, half_frame_width):
        now = self.get_clock().now()
        dt = None
        if self._pd_previous_time is not None:
            dt = (now - self._pd_previous_time).nanoseconds * 1e-9
        angular, normalized_error, derivative = compute_pd_angular(
            error_px=error,
            half_frame_width=half_frame_width,
            previous_error=self._pd_previous_error,
            dt=dt,
            kp=self.pd_kp,
            kd=self.pd_kd,
            max_angular_speed=self.max_angular_speed,
            previous_derivative=self._pd_derivative,
            derivative_alpha=self.pd_derivative_alpha,
        )
        self._pd_previous_error = normalized_error
        self._pd_previous_time = now
        self._pd_derivative = derivative

        linear_speed = max(0.0, self.lane_linear_speed)
        half_track = self.wheel_separation * 0.5
        left_target = linear_speed - angular * half_track
        right_target = linear_speed + angular * half_track
        self.publish_movement(linear_speed, angular)
        self.lane_missed_frames = 0
        self.last_lane_command = (linear_speed, angular)
        self.get_logger().info(
            f'[SERIT PD] lookahead_hata={error:+.1f}px '
            f'({normalized_error:+.1%}) | dt='
            f'{dt if dt is not None else 0.0:.4f}s | '
            f'P={self.pd_kp * normalized_error:+.4f} | '
            f'D={self.pd_kd * derivative:+.4f} | '
            f'cmd_vel: v={linear_speed:.3f} w={angular:+.3f} rad/s | '
            f'teker hedef sol={left_target * 1000.0:+.0f} '
            f'sag={right_target * 1000.0:+.0f} mm/s',
            throttle_duration_sec=0.5)

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
        control_mode, position_term, combined_error, target_angular = (
            compute_lane_turn_command(
                self.lane_control_mode, normalized_error, scaled_error,
                heading_error, self.lane_offset_gain,
                self.lane_heading_gain,
                self.lane_center_deadband_ratio,
                self.max_angular_speed,
            )
        )
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
            f'mod={control_mode} | '
            f'merkez={position_term:+.1%} | '
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

        if (not self.lane_end_reported and lane_end_confirmed(
                self.lane_seen_frames, self.lane_missed_frames,
                self.lane_end_min_seen_frames, self.lane_end_missing_frames,
                hold_frames, self.lane_end_detection_enabled)):
            self.lane_end_reported = True
            self.last_lane_command = None
            self.filtered_lane_angular = 0.0
            self.stop_robot()
            self.current_state = ProcessState.TURNAROUND
            self.pub_lane_end.publish(Bool(data=True))
            self.get_logger().info(
                f'[SERIT SONU] {self.lane_seen_frames} gorulen ve '
                f'{self.lane_missed_frames} kayip kare sonrasi 180 derece '
                'donus istendi')
            return

        # Gecici kayip sayaci burada korunur; aksi halde art arda kayip kareler
        # hicbir zaman serit sonu esigine ulasamaz.
        self.filtered_lane_angular = 0.0
        self.last_lane_command = None
        self.stop_robot()
        self.get_logger().warning(
            '[SERIT] bulunamadi | cmd_vel: v=0.000 m/s w=0.000 rad/s',
            throttle_duration_sec=0.5)

    def _reset_lane_control(self, new_session=True):
        self.filtered_lane_angular = 0.0
        self._pd_previous_error = None
        self._pd_previous_time = None
        self._pd_derivative = 0.0
        self.lane_missed_frames = 0
        self.last_lane_command = None
        if new_session:
            self.lane_seen_frames = 0
            self.lane_end_reported = False
        if hasattr(self, 'lane_tracker'):
            self.lane_tracker.reset_tracking()

    def _compose_debug_frame(self, frame):
        if (not self.show_debug_window
                and self.pub_debug_image.get_subscription_count() == 0):
            return frame
        if (self.current_state is not ProcessState.LANE_TRACKING
                or self.lane_tracker.last_mask is None):
            return frame
        detection_frame = self.lane_tracker.last_debug_frame
        if detection_frame is None:
            detection_frame = frame
        mask_bgr = cv2.cvtColor(
            self.lane_tracker.last_mask, cv2.COLOR_GRAY2BGR)
        label = (
            'IPM ALGILAMA'
            if self.lane_tracker.ipm_enabled else 'ALGILAMA')
        cv2.putText(
            detection_frame, label, (10, detection_frame.shape[0] - 12),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        cv2.putText(mask_bgr, 'ADAPTIF MASKE', (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        return cv2.hconcat([detection_frame, mask_bgr])

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
        # launch SIGINT sirasinda ROS baglami dugumden once kapanmis olabilir.
        if rclpy.ok():
            self.stop_robot()
        self.current_state = ProcessState.IDLE
        if rclpy.ok():
            self._publish_active()
        if self.cap is not None:
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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
