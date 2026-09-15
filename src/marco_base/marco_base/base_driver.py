"""STM32 ile ROS 2 arasindaki koprü dugumu.

Sorumluluklari:
  /cmd_vel  -> ters kinematik -> tekerlek hiz komutu -> UART
  UART      -> encoder tick   -> odometri            -> /odom, /joint_states
  UART      -> imu_yaw        -> IMU yaw              -> /imu/data_raw
  UART      -> durum bayrak   -> /base/estop, /base/manual_mode, /base/battery
  UART      -> alis bayatligi -> /base/communication_ok

Bilincli olarak DAHIL EDILMEYENLER:
  - odom -> base_footprint TF yayini varsayilan olarak KAPALIDIR.
    Bu donusumu robot_localization EKF'i yayinlar; ikisi ayni anda yayinlarsa
    TF agacinda cakisma olusur ve Nav2 rastgele birini gorur.
  - Hiz duzeltmesi/filtreleme yapilmaz. Odometri ham kestirimdir; filtreleme
    EKF'in isidir.
"""

from __future__ import annotations

import csv
import math
import struct
import threading
import time
from datetime import datetime
from pathlib import Path

import rclpy
from geometry_msgs.msg import Quaternion, Twist, TransformStamped
from marco_msgs.action import LiftLoad
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import BatteryState, Imu, JointState
from std_msgs.msg import Bool
from tf2_ros import TransformBroadcaster

from . import protocol as p
from .fake_stm32 import FakeStm32, FakeStm32Transport
from .odometry import (
    DifferentialOdometry,
    timestamp_delta,
    twist_to_wheel_speeds,
    wheel_rpm_to_speed,
    wheel_speed_to_rpm,
)
from .transport import SerialTransport

HEARTBEAT_PERIOD = 0.1
FORK_COMMAND_LEASE_MS = 500
FORK_COMMAND_REFRESH_PERIOD = 0.2


def stabilize_wheel_rpm(
    previous: tuple[float, float],
    requested: tuple[float, float],
    deadband: float,
) -> tuple[float, float]:
    """Kablo hedefindeki anlamsiz float titresimini bastir.

    STM32 ayni yondeki her farkli float hedefte hiz rampasini yeniden
    baslatiyor. Nav2'nin sayisal gurultusu bu nedenle ilk PID cevrimini
    surekli erteleyebiliyor. Durus, ilk hareket ve yon degisimi gecikmeden
    uygulanir; yalniz iki teker de esigin altinda degistiyse onceki kablo
    hedefi korunur.
    """
    previous_left, previous_right = previous
    requested_left, requested_right = requested

    if deadband <= 0.0:
        return requested

    previous_stopped = previous_left == 0.0 and previous_right == 0.0
    requested_stopped = requested_left == 0.0 and requested_right == 0.0
    if previous_stopped or requested_stopped:
        return requested

    direction_changed = (
        previous_left * requested_left <= 0.0
        or previous_right * requested_right <= 0.0
    )
    if direction_changed:
        return requested

    if (
        abs(requested_left - previous_left) >= deadband
        or abs(requested_right - previous_right) >= deadband
    ):
        return requested

    return previous


class BaseDriver(Node):
    """Alt seviye kontrolcu koprusu."""

    def __init__(self, **kwargs) -> None:
        super().__init__("marco_base_driver", **kwargs)

        self._declare_parameters()

        self.wheel_separation = self.get_parameter("wheel_separation").value
        self.wheel_radius = self.get_parameter("wheel_radius").value
        self.max_wheel_speed = self.get_parameter("max_wheel_speed").value
        self.command_rpm_scale = float(
            self.get_parameter("command_rpm_scale").value
        )
        if not math.isfinite(self.command_rpm_scale) or self.command_rpm_scale <= 0.0:
            raise ValueError("command_rpm_scale sonlu ve 0'dan buyuk olmali")
        self.rpm_command_deadband = float(
            self.get_parameter("rpm_command_deadband").value
        )
        if (
            not math.isfinite(self.rpm_command_deadband)
            or self.rpm_command_deadband < 0.0
        ):
            raise ValueError("rpm_command_deadband sonlu ve negatif olmamali")
        self.cmd_timeout = self.get_parameter("cmd_vel_timeout").value
        self.communication_timeout = float(
            self.get_parameter("communication_timeout").value
        )
        if self.communication_timeout <= 0.0:
            raise ValueError("communication_timeout sifirdan buyuk olmali")
        self.lift_pickup_duration_s = float(
            self.get_parameter("lift_pickup_duration_s").value
        )
        self.lift_dropoff_duration_s = float(
            self.get_parameter("lift_dropoff_duration_s").value
        )
        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        self.publish_tf = self.get_parameter("publish_tf").value
        self.imu_frame = str(self.get_parameter("imu_frame_id").value)
        self.imu_angle_sign = float(self.get_parameter("imu_angle_sign").value)

        self.odometry = DifferentialOdometry(
            wheel_radius=self.wheel_radius,
            wheel_separation=self.wheel_separation,
            ticks_per_rev=self.get_parameter("ticks_per_revolution").value,
            max_tick_delta=self.get_parameter("max_tick_delta").value,
            max_consecutive_rejects=self.get_parameter(
                "max_consecutive_tick_rejects"
            ).value,
        )

        self._transport_lock = threading.RLock()
        self._lift_goal_lock = threading.Lock()
        self._lift_goal_active = False
        self._shutdown_requested = threading.Event()
        self._transport = self._create_transport()

        self._parser = p.FrameParser()
        self._target = (0.0, 0.0)
        self._last_sent_target_rpm = (0.0, 0.0)
        self._last_command_enabled = False
        self._last_cmd_time = self.get_clock().now()
        self._last_heartbeat = 0.0
        self._last_wheel_log_time = 0.0
        self._status: p.StatusFrame | None = None
        self._last_valid_frame_wall: float | None = None
        self._last_status_wall: float | None = None
        self._communication_ok = False
        self._odom_frames_received = 0
        self._odom_len_warned = False
        self._imu_previous: tuple[int, float, int] | None = None
        self._imu_invalid_warned = False
        self._wheel_csv_file = None
        self._wheel_csv_writer = None
        self._wheel_csv_rows_since_flush = 0
        self._open_wheel_measurement_log()

        qos = QoSPresetProfiles.SENSOR_DATA.value
        self._odom_pub = self.create_publisher(Odometry, "odom", 10)
        self._joint_pub = self.create_publisher(JointState, "joint_states", 10)
        self._estop_pub = self.create_publisher(Bool, "base/estop", 10)
        self._manual_pub = self.create_publisher(Bool, "base/manual_mode", 10)
        self._communication_pub = self.create_publisher(
            Bool, "base/communication_ok", 10
        )
        self._battery_pub = self.create_publisher(BatteryState, "base/battery", qos)
        self._imu_pub = self.create_publisher(Imu, "imu/data_raw", qos)

        self._tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None

        # Sahte donanimda taklit gercek pozu bilir. Onu yayinlamak odometri
        # hatasini sayisal olarak olcmeyi saglar; Faz 3 ve Faz 5 kabul
        # kriterleri bu karsilastirmaya dayanir. Gercek donanimda boyle bir
        # referans olmadigi icin topik hic olusturulmaz.
        self._ground_truth_pub = (
            self.create_publisher(Odometry, "base/ground_truth", 10)
            if self.fake is not None
            else None
        )

        self.create_subscription(Twist, "cmd_vel", self._on_cmd_vel, 10)

        self._lift_server = None
        if self.get_parameter("lift_action_server_enabled").value:
            self._lift_server = ActionServer(
                self,
                LiftLoad,
                "/lift_load",
                self._execute_lift,
                callback_group=ReentrantCallbackGroup(),
                goal_callback=self._lift_goal_callback,
                cancel_callback=self._lift_cancel_callback,
            )

        command_rate = self.get_parameter("command_rate").value
        read_rate = self.get_parameter("read_rate").value
        self.create_timer(1.0 / command_rate, self._send_command)
        self.create_timer(1.0 / read_rate, self._read_transport)
        self.create_timer(0.1, self._publish_communication_health)

        # Acilis dizisi (protokol §6): once varsa kilitli hatayi temizle.
        self._write_transport(p.encode_safety(p.SafetyCommand.CLEAR_FAULT))

        source = (
            "SAHTE DONANIM"
            if self.get_parameter("use_fake_hardware").value
            else self.get_parameter("serial_port").value
        )
        self.get_logger().info(
            f"marco_base_driver hazir | {source} | "
            f"teker aras\u0131={self.wheel_separation:.3f} m | "
            f"metre/tick={self.odometry.meters_per_tick * 1000:.4f} mm | "
            f"IMU={self.imu_frame} imu_yaw isareti {self.imu_angle_sign:+.0f} | "
            f"TF yayini={'acik' if self.publish_tf else 'kapali (EKF yayinlayacak)'}"
        )

    # ------------------------------------------------------------------ kurulum

    def _declare_parameters(self) -> None:
        self.declare_parameter("serial_port", "/dev/marco_stm32")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("use_fake_hardware", False)

        # Etkin yaricap properties.xacro ile ayni tutulur. Etkin odometri
        # araligi ise URDF'deki fiziksel teker merkez araligindan farklidir.
        self.declare_parameter("wheel_radius", 0.1177)
        self.declare_parameter("wheel_separation", 0.423)
        self.declare_parameter("ticks_per_revolution", 360)
        self.declare_parameter("max_wheel_speed", 0.838)
        # Gecici saha kalibrasyonu icin komut RPM carpani. Normal kullanimda
        # 1.0 kalir; testte --ros-args -p command_rpm_scale:=2.0 verilebilir.
        self.declare_parameter("command_rpm_scale", 1.0)
        # Nav2'nin mikroskobik float titresiminin STM32 hiz rampasini her
        # pakette yeniden baslatmasini engeller. Float protokolu korunur.
        self.declare_parameter("rpm_command_deadband", 0.01)
        # Encoder int32'de sarar. Tek orneklemede bundan buyuk |Δtick| islenmez.
        self.declare_parameter("max_tick_delta", 2000)
        self.declare_parameter("max_consecutive_tick_rejects", 3)

        self.declare_parameter("command_rate", 50.0)
        self.declare_parameter("read_rate", 200.0)
        self.declare_parameter("cmd_vel_timeout", 0.5)
        self.declare_parameter("communication_timeout", 0.5)
        self.declare_parameter("lift_action_server_enabled", True)
        self.declare_parameter("lift_pickup_duration_s", 0.0)
        self.declare_parameter("lift_dropoff_duration_s", 0.0)

        # STM32 encoder geri bildirimini hedef komutla birlikte kalici kaydet.
        self.declare_parameter("wheel_measurement_log_enabled", True)
        self.declare_parameter(
            "wheel_measurement_log_directory", "~/.ros/marco_wheel_logs"
        )
        self.declare_parameter("wheel_measurement_terminal_rate_hz", 2.0)

        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("imu_frame_id", "imu_link")
        self.declare_parameter("imu_angle_sign", 1.0)
        self.declare_parameter("imu_yaw_stddev_deg", 3.0)
        self.declare_parameter("imu_yaw_rate_stddev", 0.08)

        # Odometri gurultu modeli. Kovaryans kat edilen mesafeyle olceklenir;
        # duran robot icin sabit buyuk bir kovaryans vermek EKF'i yaniltir.
        self.declare_parameter("linear_noise_ratio", 0.02)
        self.declare_parameter("angular_noise_ratio", 0.05)
        self.declare_parameter("min_noise", 0.001)

        # Sahte donanim hata enjeksiyonu (yalnizca use_fake_hardware=true iken)
        self.declare_parameter("fake_slip_factor", 0.0)
        self.declare_parameter("fake_wheel_scale_error_left", 0.0)
        self.declare_parameter("fake_wheel_scale_error_right", 0.0)
        # Taklidin gercek teker aras\u0131 mesafesi. 0.0 ise wheel_separation ile
        # ayni alinir. Farkli verilirse mekanik ekibin bildirdigi olcunun
        # yanlis oldugu durum benzetilir; kalibrasyon testinin bu hatayi
        # ayirt edip edemedigi boyle dogrulanir.
        self.declare_parameter("fake_wheel_separation_actual", 0.0)

    def _create_transport(self):
        if self.get_parameter("use_fake_hardware").value:
            override = self.get_parameter("fake_wheel_separation_actual").value
            actual_separation = override if override > 0.0 else self.wheel_separation
            fake = FakeStm32(
                wheel_radius=self.get_parameter("wheel_radius").value,
                wheel_separation=actual_separation,
                ticks_per_rev=self.get_parameter("ticks_per_revolution").value,
                max_wheel_speed=self.max_wheel_speed,
                slip_factor=self.get_parameter("fake_slip_factor").value,
                wheel_scale_error_left=self.get_parameter("fake_wheel_scale_error_left").value,
                wheel_scale_error_right=self.get_parameter("fake_wheel_scale_error_right").value,
            )
            self.fake = fake
            return FakeStm32Transport(fake, lambda: self._now_seconds())

        self.fake = None
        return SerialTransport(
            port=self.get_parameter("serial_port").value,
            baudrate=self.get_parameter("baudrate").value,
        )

    def _now_seconds(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9

    def _write_transport(self, data: bytes) -> None:
        """Serialize writes to the one STM32 transport shared by this node."""
        with self._transport_lock:
            self._transport.write(data)

    def _open_wheel_measurement_log(self) -> None:
        if not self.get_parameter("wheel_measurement_log_enabled").value:
            return

        directory = Path(
            str(self.get_parameter("wheel_measurement_log_directory").value)
        ).expanduser()
        try:
            directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = directory / f"wheel_measurements_{timestamp}.csv"
            self._wheel_csv_file = path.open("w", newline="", encoding="utf-8")
            fieldnames = [
                "ros_time_s",
                "stm32_timestamp_us",
                "command_enabled",
                "target_left_rpm",
                "target_right_rpm",
                "target_left_equivalent_mm_s",
                "target_right_equivalent_mm_s",
                "measured_left_mm_s",
                "measured_right_mm_s",
                "error_left_mm_s",
                "error_right_mm_s",
                "left_ticks",
                "right_ticks",
                "status_flags",
            ]
            self._wheel_csv_writer = csv.DictWriter(
                self._wheel_csv_file, fieldnames=fieldnames
            )
            self._wheel_csv_writer.writeheader()
            self._wheel_csv_file.flush()
            self.get_logger().info(f"Teker olcum CSV kaydi: {path}")
        except OSError as exc:
            self._wheel_csv_file = None
            self._wheel_csv_writer = None
            self.get_logger().error(f"Teker olcum CSV dosyasi acilamadi: {exc}")

    # ------------------------------------------------------------------ komut yolu

    def _on_cmd_vel(self, msg: Twist) -> None:
        if not math.isfinite(msg.linear.x) or not math.isfinite(msg.angular.z):
            self.get_logger().error("NaN/Inf /cmd_vel reddedildi; guvenli durus uygulanıyor")
            self._target = (0.0, 0.0)
            return
        self._target = twist_to_wheel_speeds(
            linear=msg.linear.x,
            angular=msg.angular.z,
            wheel_separation=self.wheel_separation,
            max_wheel_speed=self.max_wheel_speed,
        )
        self._last_cmd_time = self.get_clock().now()

    def _send_command(self) -> None:
        age = (self.get_clock().now() - self._last_cmd_time).nanoseconds * 1e-9

        # /cmd_vel susarsa arac durur. STM32 watchdog'u son savunma hatti;
        # burasi normal isleyisteki ilk hattir.
        if age > self.cmd_timeout:
            left, right = 0.0, 0.0
        else:
            left, right = self._target

        blocked = self._status is not None and (
            p.StatusFlag.ESTOP_ACTIVE in self._status.flags
            or p.StatusFlag.MODE_MANUAL in self._status.flags
        )

        # Guvenlik bayragi etkinken sayisal hedef de sifirlanir. Boylece STM32
        # enable bitini uygulamasa bile hareket komutu tasinmaz.
        if blocked:
            left, right = 0.0, 0.0

        left_rpm = (
            wheel_speed_to_rpm(left, self.wheel_radius) * self.command_rpm_scale
        )
        right_rpm = (
            wheel_speed_to_rpm(right, self.wheel_radius) * self.command_rpm_scale
        )

        left_rpm, right_rpm = stabilize_wheel_rpm(
            self._last_sent_target_rpm,
            (left_rpm, right_rpm),
            self.rpm_command_deadband,
        )

        try:
            self._write_transport(
                p.encode_wheel_rpm(
                    left_rpm=left_rpm,
                    right_rpm=right_rpm,
                    enabled=not blocked,
                )
            )
        except OSError as exc:
            self._mark_communication_lost(f"seri port yazma hatasi: {exc}")
            return
        self._last_sent_target_rpm = (left_rpm, right_rpm)
        self._last_command_enabled = not blocked

        now = self._now_seconds()
        if now - self._last_heartbeat >= HEARTBEAT_PERIOD:
            self._last_heartbeat = now
            try:
                self._write_transport(p.encode_heartbeat())
            except OSError as exc:
                self._mark_communication_lost(f"heartbeat yazma hatasi: {exc}")

    # ------------------------------------------------------------------ okuma yolu

    def _read_transport(self) -> None:
        try:
            data = self._transport.read()
        except OSError as exc:
            self._mark_communication_lost(f"seri port okuma hatasi: {exc}")
            return

        if not data:
            return

        for msg_id, payload in self._parser.feed(data):
            try:
                if msg_id is p.MsgId.STATE_ODOMETRY:
                    if len(payload) not in p.ODOMETRY_SUPPORTED_PAYLOAD_LENS:
                        raise ValueError(
                            f"desteklenmeyen odometri boyutu: {len(payload)}"
                        )
                    if (
                        len(payload) != p.ODOMETRY_PAYLOAD_LEN
                        and not self._odom_len_warned
                    ):
                        self._odom_len_warned = True
                        self.get_logger().warn(
                            f"STM32 odometri {len(payload)} bayt gonderiyor "
                            f"(IMU'lu protokol {p.ODOMETRY_PAYLOAD_LEN}). "
                            "Odometri alinir fakat bu pakette IMU kullanilamaz."
                        )
                    self._on_odometry(p.decode_odometry(payload))
                    self._last_valid_frame_wall = time.monotonic()
                elif msg_id is p.MsgId.STATE_STATUS:
                    self._on_status(p.decode_status(payload))
                    now = time.monotonic()
                    self._last_valid_frame_wall = now
                    self._last_status_wall = now
            except (struct.error, ValueError) as exc:
                self.get_logger().warn(
                    f"protokol uyumsuzlugu msg=0x{int(msg_id):02X} "
                    f"len={len(payload)} (desteklenen odom="
                    f"{sorted(p.ODOMETRY_SUPPORTED_PAYLOAD_LENS)}, "
                    f"status={p.STATUS_PAYLOAD_LEN}): {exc} | "
                    f"payload={payload[:32].hex()}"
                )

    def _mark_communication_lost(self, message: str) -> None:
        if self._communication_ok:
            self.get_logger().error(message)
        self._communication_ok = False

    def _publish_communication_health(self) -> None:
        now = time.monotonic()
        healthy = (
            self._last_valid_frame_wall is not None
            and now - self._last_valid_frame_wall <= self.communication_timeout
        )
        if healthy != self._communication_ok:
            self._communication_ok = healthy
            if healthy:
                self.get_logger().info("STM32/UART iletisimi saglikli")
            else:
                self.get_logger().error("STM32/UART verisi bayat veya kayip")
        self._communication_pub.publish(Bool(data=healthy))

    def _on_odometry(self, frame: p.OdometryFrame) -> None:
        self._record_wheel_measurement(frame)
        updated = self.odometry.update(
            left_ticks=frame.left_ticks,
            right_ticks=frame.right_ticks,
            timestamp_us=frame.timestamp_us,
            timestamp_bits=frame.timestamp_bits,
        )
        self._odom_frames_received += 1
        stamp = self.get_clock().now().to_msg()
        self._publish_imu(frame, stamp)
        if not updated:
            return

        self._publish_odometry(stamp)
        self._publish_joint_states(stamp, frame)
        self._publish_ground_truth(stamp)

    def _record_wheel_measurement(self, frame: p.OdometryFrame) -> None:
        """Hedef ve STM32 olculen teker hizlarini logla."""
        now = self._now_seconds()
        target_left_rpm, target_right_rpm = self._last_sent_target_rpm
        target_left = wheel_rpm_to_speed(
            target_left_rpm, self.wheel_radius
        ) * 1000.0
        target_right = wheel_rpm_to_speed(
            target_right_rpm, self.wheel_radius
        ) * 1000.0
        measured_left = int(frame.left_mm_s)
        measured_right = int(frame.right_mm_s)
        error_left = target_left - measured_left
        error_right = target_right - measured_right

        if self._wheel_csv_writer is not None:
            flags = int(self._status.flags) if self._status is not None else 0
            self._wheel_csv_writer.writerow(
                {
                    "ros_time_s": f"{now:.6f}",
                    "stm32_timestamp_us": frame.timestamp_us,
                    "command_enabled": int(self._last_command_enabled),
                    "target_left_rpm": f"{target_left_rpm:.6f}",
                    "target_right_rpm": f"{target_right_rpm:.6f}",
                    "target_left_equivalent_mm_s": f"{target_left:.6f}",
                    "target_right_equivalent_mm_s": f"{target_right:.6f}",
                    "measured_left_mm_s": measured_left,
                    "measured_right_mm_s": measured_right,
                    "error_left_mm_s": f"{error_left:.6f}",
                    "error_right_mm_s": f"{error_right:.6f}",
                    "left_ticks": frame.left_ticks,
                    "right_ticks": frame.right_ticks,
                    "status_flags": flags,
                }
            )
            self._wheel_csv_rows_since_flush += 1
            if self._wheel_csv_rows_since_flush >= 25:
                self._wheel_csv_file.flush()
                self._wheel_csv_rows_since_flush = 0

        rate = float(
            self.get_parameter("wheel_measurement_terminal_rate_hz").value
        )
        period = 1.0 / rate if rate > 0.0 else math.inf
        if now - self._last_wheel_log_time >= period:
            self._last_wheel_log_time = now
            self.get_logger().info(
                "[TEKER OLCUM] "
                f"hedef sol={target_left_rpm:+.3f} "
                f"sag={target_right_rpm:+.3f} RPM "
                f"(karsilik {target_left:+.3f}/{target_right:+.3f} mm/s) | "
                f"olculen sol={measured_left:+d} sag={measured_right:+d} mm/s | "
                f"hata sol={error_left:+.3f} sag={error_right:+.3f} mm/s | "
                f"aktif={self._last_command_enabled}"
            )

    def _publish_imu(self, frame: p.OdometryFrame, stamp) -> None:
        """Firmware imu_yaw alanini ROS ENU yaw mesaji olarak yayinla."""
        if frame.imu_yaw_deg is None:
            return
        angle_deg = float(frame.imu_yaw_deg)
        if not math.isfinite(angle_deg):
            if not self._imu_invalid_warned:
                self._imu_invalid_warned = True
                self.get_logger().warn("STM32 imu_yaw NaN/Inf; IMU mesaji reddedildi")
            return

        yaw = math.radians(angle_deg) * self.imu_angle_sign
        yaw = math.atan2(math.sin(yaw), math.cos(yaw))
        yaw_rate = 0.0
        if self._imu_previous is not None:
            previous_stamp, previous_yaw, previous_bits = self._imu_previous
            dt_us = (
                timestamp_delta(
                    previous_stamp,
                    frame.timestamp_us,
                    bits=frame.timestamp_bits,
                )
                if previous_bits == frame.timestamp_bits
                else 0
            )
            if dt_us > 0:
                delta = math.atan2(
                    math.sin(yaw - previous_yaw),
                    math.cos(yaw - previous_yaw),
                )
                yaw_rate = delta / (dt_us * 1e-6)
        self._imu_previous = (
            frame.timestamp_us,
            yaw,
            frame.timestamp_bits,
        )

        msg = Imu()
        msg.header.stamp = stamp
        msg.header.frame_id = self.imu_frame
        msg.orientation.z = math.sin(yaw / 2.0)
        msg.orientation.w = math.cos(yaw / 2.0)
        msg.angular_velocity.z = yaw_rate

        yaw_std = math.radians(
            float(self.get_parameter("imu_yaw_stddev_deg").value)
        )
        yaw_rate_std = float(
            self.get_parameter("imu_yaw_rate_stddev").value
        )
        # Roll/pitch olculmuyor. Paket ivme tasimadigi icin -1 "olcum yok".
        msg.orientation_covariance[0] = 1e6
        msg.orientation_covariance[4] = 1e6
        msg.orientation_covariance[8] = yaw_std * yaw_std
        msg.angular_velocity_covariance[0] = 1e6
        msg.angular_velocity_covariance[4] = 1e6
        msg.angular_velocity_covariance[8] = yaw_rate_std * yaw_rate_std
        msg.linear_acceleration_covariance[0] = -1.0
        self._imu_pub.publish(msg)

    def _publish_ground_truth(self, stamp) -> None:
        if self._ground_truth_pub is None:
            return
        msg = Odometry()
        msg.header.stamp = stamp
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = "base_footprint_truth"
        msg.pose.pose.position.x = self.fake.true_x
        msg.pose.pose.position.y = self.fake.true_y
        msg.pose.pose.orientation = _yaw_to_quaternion(self.fake.true_theta)
        self._ground_truth_pub.publish(msg)

    def _on_status(self, frame: p.StatusFrame) -> None:
        previous = self._status
        self._status = frame

        if previous is None or previous.flags != frame.flags:
            self._log_flag_changes(previous, frame)

        self._estop_pub.publish(Bool(data=p.StatusFlag.ESTOP_ACTIVE in frame.flags))
        self._manual_pub.publish(Bool(data=p.StatusFlag.MODE_MANUAL in frame.flags))

        battery = BatteryState()
        battery.header.stamp = self.get_clock().now().to_msg()
        battery.voltage = frame.battery_mv / 1000.0
        battery.current = -(frame.current_ma_left + frame.current_ma_right) / 1000.0
        battery.temperature = float(frame.temperature_c)
        battery.present = True
        self._battery_pub.publish(battery)

    # --------------------------------------------------------------- lift action

    def _lift_hardware_error(self) -> str:
        """Return a fail-closed reason when lift control is not currently safe."""
        if self._shutdown_requested.is_set():
            return "base driver kapaniyor"
        now = time.monotonic()
        if (
            self._last_valid_frame_wall is None
            or now - self._last_valid_frame_wall > self.communication_timeout
            or self._last_status_wall is None
            or now - self._last_status_wall > self.communication_timeout
            or self._status is None
        ):
            return "STM32/UART status iletisimi yok veya bayat"
        if p.StatusFlag.ESTOP_ACTIVE in self._status.flags:
            return "e-stop aktif"
        if p.StatusFlag.MODE_MANUAL in self._status.flags:
            return "manuel mod aktif"
        if p.StatusFlag.OVERCURRENT in self._status.flags:
            return "fork asiri akim bayragi aktif"
        return ""

    def _lift_movement_duration(self, command: int) -> tuple[float, str]:
        if command == LiftLoad.Goal.COMMAND_PICKUP:
            return self.lift_pickup_duration_s, "lift_pickup_duration_s"
        return self.lift_dropoff_duration_s, "lift_dropoff_duration_s"

    def _lift_goal_error(self, goal: LiftLoad.Goal) -> str:
        if goal.command not in (
            LiftLoad.Goal.COMMAND_PICKUP,
            LiftLoad.Goal.COMMAND_DROPOFF,
        ):
            return f"gecersiz lift komutu: {goal.command}"
        if not str(goal.station_id).strip():
            return "station_id bos olamaz"
        timeout = float(goal.timeout)
        if not math.isfinite(timeout) or timeout <= 0.0:
            return "lift timeout sonlu ve sifirdan buyuk olmali"
        if timeout > 65.535:
            return "lift timeout STM32 uint16 araligini asiyor (en fazla 65.535 s)"
        duration, parameter_name = self._lift_movement_duration(goal.command)
        if not math.isfinite(duration) or duration <= 0.0:
            return f"{parameter_name} yapılandırılmamış"
        if duration >= timeout:
            return (
                f"{parameter_name} goal.timeout degerinden kucuk olmali"
            )
        return ""

    def _lift_goal_callback(self, goal: LiftLoad.Goal) -> GoalResponse:
        error = self._lift_goal_error(goal)
        if not error:
            error = self._lift_hardware_error()
        with self._lift_goal_lock:
            if self._lift_goal_active:
                error = "baska bir lift goal halen aktif"
            if error:
                self.get_logger().error(f"/lift_load goal reddedildi: {error}")
                return GoalResponse.REJECT
            self._lift_goal_active = True
        return GoalResponse.ACCEPT

    @staticmethod
    def _lift_cancel_callback(_goal_handle) -> CancelResponse:
        return CancelResponse.ACCEPT

    @staticmethod
    def _lift_result(success: bool, result_code: int, message: str):
        result = LiftLoad.Result()
        result.success = success
        result.result_code = result_code
        result.message = message
        return result

    def _send_fork_stop(self) -> bool:
        try:
            self._write_transport(p.encode_fork(p.ForkAction.STOP, 0))
            return True
        except (OSError, ValueError) as exc:
            self._mark_communication_lost(f"fork STOP gonderilemedi: {exc}")
            return False

    def _execute_lift(self, goal_handle):
        """Run a configured fork motion and verify pickup load after STOP."""
        goal = goal_handle.request
        command_name = (
            "pickup" if goal.command == LiftLoad.Goal.COMMAND_PICKUP else "dropoff"
        )
        fork_action = (
            p.ForkAction.UP
            if goal.command == LiftLoad.Goal.COMMAND_PICKUP
            else p.ForkAction.DOWN
        )
        phase = "moving_up" if fork_action is p.ForkAction.UP else "moving_down"

        try:
            error = self._lift_goal_error(goal) or self._lift_hardware_error()
            if error:
                goal_handle.abort()
                return self._lift_result(
                    False, LiftLoad.Result.RESULT_HARDWARE_FAULT, error
                )

            movement_duration, _ = self._lift_movement_duration(goal.command)
            started = time.monotonic()
            movement_deadline = started + movement_duration
            overall_deadline = started + float(goal.timeout)
            next_refresh = 0.0

            while rclpy.ok() and not self._shutdown_requested.is_set():
                if goal_handle.is_cancel_requested:
                    self._send_fork_stop()
                    goal_handle.canceled()
                    return self._lift_result(
                        False,
                        LiftLoad.Result.RESULT_ABORTED,
                        f"{command_name} operator tarafindan iptal edildi; STOP gonderildi",
                    )

                error = self._lift_hardware_error()
                if error:
                    self._send_fork_stop()
                    goal_handle.abort()
                    return self._lift_result(
                        False,
                        LiftLoad.Result.RESULT_HARDWARE_FAULT,
                        f"{command_name} guvenli durduruldu: {error}",
                    )

                now = time.monotonic()
                if now >= overall_deadline:
                    self._send_fork_stop()
                    goal_handle.abort()
                    return self._lift_result(
                        False,
                        LiftLoad.Result.RESULT_TIMEOUT,
                        f"{command_name} overall timeout; STOP gonderildi",
                    )

                if now >= movement_deadline:
                    if not self._send_fork_stop():
                        goal_handle.abort()
                        return self._lift_result(
                            False,
                            LiftLoad.Result.RESULT_HARDWARE_FAULT,
                            f"{command_name} hareketi bitti ancak STOP gonderilemedi",
                        )
                    stop_sent_wall = time.monotonic()
                    if stop_sent_wall >= overall_deadline:
                        goal_handle.abort()
                        return self._lift_result(
                            False,
                            LiftLoad.Result.RESULT_TIMEOUT,
                            f"{command_name} overall timeout; STOP gonderildi",
                        )
                    if fork_action is p.ForkAction.DOWN:
                        goal_handle.succeed()
                        return self._lift_result(
                            True,
                            LiftLoad.Result.RESULT_OK,
                            "dropoff hareket suresi tamamlandi; STOP gonderildi",
                        )

                    feedback = LiftLoad.Feedback()
                    feedback.phase = "verifying_load"
                    feedback.position = math.nan
                    goal_handle.publish_feedback(feedback)
                    verification_deadline = min(
                        overall_deadline,
                        stop_sent_wall + self.communication_timeout,
                    )
                    while rclpy.ok() and not self._shutdown_requested.is_set():
                        if goal_handle.is_cancel_requested:
                            self._send_fork_stop()
                            goal_handle.canceled()
                            return self._lift_result(
                                False,
                                LiftLoad.Result.RESULT_ABORTED,
                                "pickup yuk kontrolunde iptal edildi; STOP gonderildi",
                            )
                        status_wall = self._last_status_wall
                        if (
                            status_wall is not None
                            and status_wall > stop_sent_wall
                        ):
                            error = self._lift_hardware_error()
                            if error:
                                self._send_fork_stop()
                                goal_handle.abort()
                                return self._lift_result(
                                    False,
                                    LiftLoad.Result.RESULT_HARDWARE_FAULT,
                                    f"pickup yuk kontrolu basarisiz: {error}",
                                )
                            if p.StatusFlag.LOAD_DETECTED in self._status.flags:
                                goal_handle.succeed()
                                return self._lift_result(
                                    True,
                                    LiftLoad.Result.RESULT_OK,
                                    "pickup STOP sonrasi fresh status ile yuk algilandi",
                                )
                            goal_handle.abort()
                            return self._lift_result(
                                False,
                                LiftLoad.Result.RESULT_HARDWARE_FAULT,
                                "pickup tamamlandi ancak yuk algilanmadi",
                            )
                        verify_now = time.monotonic()
                        if verify_now >= overall_deadline:
                            self._send_fork_stop()
                            goal_handle.abort()
                            return self._lift_result(
                                False,
                                LiftLoad.Result.RESULT_TIMEOUT,
                                "pickup overall timeout; STOP gonderildi",
                            )
                        if verify_now >= verification_deadline:
                            self._send_fork_stop()
                            goal_handle.abort()
                            return self._lift_result(
                                False,
                                LiftLoad.Result.RESULT_HARDWARE_FAULT,
                                "pickup STOP sonrasi fresh STM32 status gelmedi",
                            )
                        time.sleep(0.02)

                    self._send_fork_stop()
                    goal_handle.abort()
                    return self._lift_result(
                        False,
                        LiftLoad.Result.RESULT_ABORTED,
                        "pickup yuk kontrolu base driver kapanisi nedeniyle durdu",
                    )

                if now >= next_refresh:
                    remaining_ms = max(
                        1,
                        int(math.ceil((movement_deadline - now) * 1000.0)),
                    )
                    lease_ms = min(FORK_COMMAND_LEASE_MS, remaining_ms)
                    try:
                        self._write_transport(p.encode_fork(fork_action, lease_ms))
                    except (OSError, ValueError) as exc:
                        self._mark_communication_lost(
                            f"fork {command_name} komutu gonderilemedi: {exc}"
                        )
                        self._send_fork_stop()
                        goal_handle.abort()
                        return self._lift_result(
                            False,
                            LiftLoad.Result.RESULT_HARDWARE_FAULT,
                            f"{command_name} UART yazma hatasi: {exc}",
                        )
                    next_refresh = now + FORK_COMMAND_REFRESH_PERIOD

                feedback = LiftLoad.Feedback()
                feedback.phase = phase
                feedback.position = math.nan
                goal_handle.publish_feedback(feedback)
                time.sleep(0.02)

            self._send_fork_stop()
            goal_handle.abort()
            return self._lift_result(
                False,
                LiftLoad.Result.RESULT_ABORTED,
                f"{command_name} base driver kapanisi nedeniyle durduruldu",
            )
        except Exception as exc:
            self._send_fork_stop()
            goal_handle.abort()
            self.get_logger().error(
                f"/lift_load {command_name} beklenmeyen exception: {exc}"
            )
            return self._lift_result(
                False,
                LiftLoad.Result.RESULT_HARDWARE_FAULT,
                f"{command_name} beklenmeyen hata; STOP gonderildi: {exc}",
            )
        finally:
            self._send_fork_stop()
            with self._lift_goal_lock:
                self._lift_goal_active = False

    def _log_flag_changes(self, previous: p.StatusFrame | None, current: p.StatusFrame) -> None:
        old = previous.flags if previous else p.StatusFlag(0)
        for flag, message in (
            (p.StatusFlag.ESTOP_ACTIVE, "ACIL STOP"),
            (p.StatusFlag.MODE_MANUAL, "MANUEL MOD"),
            (p.StatusFlag.OVERCURRENT, "ASIRI AKIM"),
            (p.StatusFlag.WATCHDOG_TRIGGERED, "WATCHDOG"),
            (p.StatusFlag.ENCODER_FAULT, "ENCODER HATASI"),
        ):
            if flag in current.flags and flag not in old:
                self.get_logger().warn(f"{message} aktif")
            elif flag not in current.flags and flag in old:
                self.get_logger().info(f"{message} temizlendi")

    # ------------------------------------------------------------------ yayin

    def _publish_odometry(self, stamp) -> None:
        state = self.odometry.state

        values = (
            state.x, state.y, state.theta,
            state.linear_velocity, state.angular_velocity,
        )
        if not all(math.isfinite(value) for value in values):
            self.get_logger().error("NaN/Inf odometri durumu reddedildi")
            return

        msg = Odometry()
        msg.header.stamp = stamp
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame

        msg.pose.pose.position.x = state.x
        msg.pose.pose.position.y = state.y
        msg.pose.pose.orientation = _yaw_to_quaternion(state.theta)

        msg.twist.twist.linear.x = state.linear_velocity
        msg.twist.twist.angular.z = state.angular_velocity

        self._fill_covariance(msg)
        self._odom_pub.publish(msg)

        if self._tf_broadcaster is not None:
            tf = TransformStamped()
            tf.header.stamp = stamp
            tf.header.frame_id = self.odom_frame
            tf.child_frame_id = self.base_frame
            tf.transform.translation.x = state.x
            tf.transform.translation.y = state.y
            tf.transform.rotation = msg.pose.pose.orientation
            self._tf_broadcaster.sendTransform(tf)

    def _fill_covariance(self, msg: Odometry) -> None:
        """Kovaryansi anlik harekete gore olceklendirir.

        EKF mutlak pose'u degil encoderdan hesaplanan vx/vyaw alanlarini
        tuketir. Bu yuzden twist kovaryansi anlik hizla olceklenir; robot
        durdugunda olcum belirsizligi taban degerine iner.
        """
        linear_ratio = self.get_parameter("linear_noise_ratio").value
        angular_ratio = self.get_parameter("angular_noise_ratio").value
        floor = self.get_parameter("min_noise").value

        state = self.odometry.state
        linear_std = linear_ratio * abs(state.linear_velocity) + floor
        angular_std = angular_ratio * abs(state.angular_velocity) + floor

        large = 1e6
        msg.pose.covariance[0] = linear_std ** 2
        msg.pose.covariance[7] = linear_std ** 2
        msg.pose.covariance[14] = large
        msg.pose.covariance[21] = large
        msg.pose.covariance[28] = large
        msg.pose.covariance[35] = angular_std ** 2

        msg.twist.covariance[0] = linear_std ** 2
        msg.twist.covariance[7] = large
        msg.twist.covariance[14] = large
        msg.twist.covariance[21] = large
        msg.twist.covariance[28] = large
        msg.twist.covariance[35] = angular_std ** 2

    def _publish_joint_states(self, stamp, frame: p.OdometryFrame) -> None:
        msg = JointState()
        msg.header.stamp = stamp
        msg.name = ["left_wheel_joint", "right_wheel_joint", "fork_lift_joint"]
        msg.position = [
            self.odometry.left_wheel_angle,
            self.odometry.right_wheel_angle,
            self._fork_position(),
        ]
        msg.velocity = [
            (frame.left_mm_s / 1000.0) / self.wheel_radius,
            (frame.right_mm_s / 1000.0) / self.wheel_radius,
            0.0,
        ]
        self._joint_pub.publish(msg)

    def _fork_position(self) -> float:
        """Catal eklemi icin kaba konum.

        STM32 yalnizca limit switch durumu bildirir, surekli konum olcmez.
        Bu yuzden ara konum bilinemez; gorsellestirme icin son bilinen
        uc noktaya yuvarlanir.
        """
        if self._status is None:
            return 0.0
        return 0.100 if self._status.fork_state == 2 else 0.0

    def destroy_node(self) -> bool:
        self._shutdown_requested.set()
        try:
            self._send_fork_stop()
            # UART tamponu/tek-kare kaybi ihtimaline karsi kapanista birden
            # fazla devre-disinda sifir komutu gonderilir.
            for _ in range(5):
                self._write_transport(p.encode_wheel_rpm(0.0, 0.0, False))
            with self._transport_lock:
                self._transport.close()
        except OSError:
            pass
        finally:
            if self._wheel_csv_file is not None:
                self._wheel_csv_file.flush()
                self._wheel_csv_file.close()
                self._wheel_csv_file = None
        return super().destroy_node()


def _yaw_to_quaternion(yaw: float) -> Quaternion:
    return Quaternion(z=math.sin(yaw * 0.5), w=math.cos(yaw * 0.5))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BaseDriver()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node._shutdown_requested.set()
        node._send_fork_stop()
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
