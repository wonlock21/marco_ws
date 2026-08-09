#!/usr/bin/env python3
"""Kaydedilmis saha haritasi ile tek bir AMCL surecini yonetir."""

import math
import os
import re
import shutil
import signal
import stat
import subprocess
import time
from pathlib import Path

import rclpy
import yaml
from geometry_msgs.msg import PoseWithCovarianceStamped
from marco_msgs.msg import FieldInfo, LocalizationStatus, MappingStatus
from marco_msgs.srv import ListFields, StartLocalization
from nav_msgs.msg import OccupancyGrid
from rclpy.executors import ExternalShutdownException
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from std_srvs.srv import Trigger


FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class LocalizationManager(Node):
    def __init__(self) -> None:
        super().__init__("localization_manager")
        self.declare_parameter("fake_hardware", False)
        self.declare_parameter("use_imu", False)
        self.declare_parameter("serial_port", "/dev/marco_stm32")
        self.declare_parameter("lidar_port", "/dev/ttyUSB0")
        self.declare_parameter("data_root", "~/marco_data/fields")
        self.declare_parameter("startup_timeout", 30.0)
        self.declare_parameter("initial_pose_timeout", 35.0)
        self.declare_parameter("initial_pose_xy_std", 0.25)
        self.declare_parameter("initial_pose_yaw_std", math.radians(10.0))

        latched = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._status_pub = self.create_publisher(
            LocalizationStatus, "/localization/status", latched
        )
        initial_pose_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        self._initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, "/initialpose", initial_pose_qos
        )
        self.create_subscription(OccupancyGrid, "/map", self._on_map, latched)
        self.create_subscription(
            PoseWithCovarianceStamped, "/amcl_pose", self._on_amcl_pose, 10
        )
        self.create_subscription(
            MappingStatus, "/mapping/status", self._on_mapping_status, latched
        )
        self.create_service(
            StartLocalization, "/localization/start", self._on_start
        )
        self.create_service(ListFields, "/fields/list", self._on_list_fields)
        self.create_service(Trigger, "/localization/stop", self._on_stop)
        self.create_timer(0.5, self._monitor_process)
        self.create_timer(0.5, self._publish_initial_pose)

        self._process = None
        self._field_name = ""
        self._map_yaml = ""
        self._state = LocalizationStatus.STATE_IDLE
        self._mapping_state = MappingStatus.STATE_IDLE
        self._started_at = 0.0
        self._initializing_at = 0.0
        self._saved_pose = None
        self._initial_pose_attempts = 0
        self._publish_status("Lokalizasyon hazir")

    def _data_root(self) -> Path:
        configured = str(self.get_parameter("data_root").value)
        return Path(os.path.expanduser(configured)).resolve()

    def _publish_status(self, message: str) -> None:
        status = LocalizationStatus()
        status.header.stamp = self.get_clock().now().to_msg()
        status.state = self._state
        status.field_name = self._field_name
        status.message = message
        status.map_yaml = self._map_yaml
        status.process_id = self._process.pid if self._process is not None else 0
        self._status_pub.publish(status)

    def _on_mapping_status(self, msg: MappingStatus) -> None:
        self._mapping_state = msg.state

    def _validate_map(self, field_name: str) -> Path:
        root = self._data_root()
        field_dir = (root / field_name).resolve()
        if field_dir.parent != root:
            raise ValueError("Saha dizini data_root disina cikamaz")
        if not field_dir.is_dir():
            raise ValueError(f"Saha klasoru bulunamadi: {field_dir}")

        map_yaml = field_dir / "map.yaml"
        if not map_yaml.is_file() or not os.access(map_yaml, os.R_OK):
            raise ValueError(f"Okunabilir map.yaml bulunamadi: {map_yaml}")
        if map_yaml.resolve().parent != field_dir:
            raise ValueError("map.yaml saha klasoru disina yonlenemez")

        try:
            with map_yaml.open("r", encoding="utf-8") as stream:
                content = yaml.safe_load(stream) or {}
        except (OSError, yaml.YAMLError) as error:
            raise ValueError(f"map.yaml okunamadi: {error}") from error

        image_value = content.get("image")
        if not isinstance(image_value, str) or not image_value.strip():
            raise ValueError("map.yaml icinde image alani yok")
        image = Path(image_value)
        image_path = (
            image.resolve() if image.is_absolute() else (field_dir / image).resolve()
        )
        if field_dir not in image_path.parents:
            raise ValueError("Harita resmi saha klasoru disinda olamaz")
        if not image_path.is_file() or not os.access(image_path, os.R_OK):
            raise ValueError(f"Harita resmi bulunamadi/okunamadi: {image_path}")

        if not isinstance(content.get("resolution"), (int, float)):
            raise ValueError("map.yaml icinde gecerli resolution yok")
        origin = content.get("origin")
        if not isinstance(origin, list) or len(origin) != 3:
            raise ValueError("map.yaml icinde gecerli origin yok")
        return map_yaml.resolve()

    @staticmethod
    def _load_saved_pose(field_dir: Path) -> tuple[float, float, float]:
        pose_path = field_dir / "mapping_pose.yaml"
        if not pose_path.is_file() or not os.access(pose_path, os.R_OK):
            raise ValueError(f"Kayitli baslangic pozu bulunamadi: {pose_path}")
        if pose_path.resolve().parent != field_dir:
            raise ValueError("mapping_pose.yaml saha klasoru disina yonlenemez")
        try:
            with pose_path.open("r", encoding="utf-8") as stream:
                content = yaml.safe_load(stream) or {}
        except (OSError, yaml.YAMLError) as error:
            raise ValueError(f"mapping_pose.yaml okunamadi: {error}") from error

        if content.get("frame_id") != "map":
            raise ValueError("Kayitli baslangic pozu map cercevesinde degil")
        if content.get("child_frame_id") != "base_footprint":
            raise ValueError("Kayitli poz base_footprint icin degil")
        position = content.get("position")
        if not isinstance(position, dict):
            raise ValueError("mapping_pose.yaml position alani gecersiz")
        values = (position.get("x"), position.get("y"), content.get("yaw"))
        if not all(isinstance(value, (int, float)) for value in values):
            raise ValueError("Kayitli x, y veya yaw degeri gecersiz")
        pose = tuple(float(value) for value in values)
        if not all(math.isfinite(value) for value in pose):
            raise ValueError("Kayitli x, y veya yaw sonlu degil")
        return pose

    def _hardware_error(self):
        if bool(self.get_parameter("fake_hardware").value):
            return None
        devices = (
            (str(self.get_parameter("serial_port").value), "STM32"),
            (str(self.get_parameter("lidar_port").value), "LiDAR"),
        )
        for path, label in devices:
            try:
                mode = os.stat(path).st_mode
            except OSError as error:
                return f"{label} cihazi kullanilamiyor: {path}: {error}"
            if not stat.S_ISCHR(mode) or not os.access(path, os.R_OK | os.W_OK):
                return f"{label} yolu karakter cihazi/okunur-yazilir degil: {path}"
        return None

    def _field_info(self, field_dir: Path) -> FieldInfo:
        info = FieldInfo()
        info.field_name = field_dir.name
        info.field_directory = str(field_dir)
        info.map_yaml = str(field_dir / "map.yaml")
        preview = field_dir / "map.png"
        if preview.is_file() and preview.resolve().parent == field_dir:
            info.preview_png = str(preview)

        issues = []
        manifest = field_dir / "field.yaml"
        if manifest.is_file() and manifest.resolve().parent == field_dir:
            try:
                with manifest.open("r", encoding="utf-8") as stream:
                    metadata = yaml.safe_load(stream) or {}
                created_at = metadata.get("created_at", "")
                if isinstance(created_at, str):
                    info.created_at = created_at
                else:
                    issues.append("field.yaml created_at alani gecersiz")
            except (OSError, yaml.YAMLError) as error:
                issues.append(f"field.yaml okunamadi: {error}")

        try:
            self._validate_map(field_dir.name)
            info.map_ready = True
        except ValueError as error:
            issues.append(str(error))
        try:
            self._load_saved_pose(field_dir)
            info.initial_pose_ready = True
        except ValueError as error:
            issues.append(str(error))

        info.localization_ready = info.map_ready and info.initial_pose_ready
        if issues:
            info.message = "; ".join(issues)
        elif info.localization_ready:
            info.message = "Lokalizasyona hazir"
        else:
            info.message = "Saha kaydi tamamlanmamis"
        return info

    def _on_list_fields(self, _request, response):
        root = self._data_root()
        if not root.exists():
            response.success = True
            response.message = "Kayitli saha yok"
            return response
        if not root.is_dir():
            response.success = False
            response.message = f"Saha veri yolu klasor degil: {root}"
            return response
        try:
            candidates = sorted(root.iterdir(), key=lambda path: path.name.lower())
            response.fields = [
                self._field_info(path.resolve())
                for path in candidates
                if path.is_dir()
                and not path.is_symlink()
                and FIELD_NAME_PATTERN.fullmatch(path.name)
            ]
        except OSError as error:
            response.success = False
            response.message = f"Saha klasorleri okunamadi: {error}"
            return response
        response.success = True
        response.message = f"{len(response.fields)} saha bulundu"
        return response

    def _slam_toolbox_is_running(self) -> bool:
        return any(
            name.startswith("/slam_toolbox/")
            for name, _types in self.get_service_names_and_types()
        )

    def _on_start(self, request, response):
        field_name = request.field_name.strip()
        if not FIELD_NAME_PATTERN.fullmatch(field_name):
            response.accepted = False
            response.message = (
                "Saha adi 1-64 karakter olmali; yalnizca harf, rakam, _ ve - kullanin"
            )
            return response

        if self._process is not None and self._process.poll() is None:
            response.accepted = False
            response.message = f"Lokalizasyon zaten calisiyor: {self._field_name}"
            response.map_yaml = self._map_yaml
            return response

        mapping_active = self._mapping_state in (
            MappingStatus.STATE_STARTING,
            MappingStatus.STATE_MAPPING,
            MappingStatus.STATE_SAVING,
            MappingStatus.STATE_STOPPING,
        )
        if mapping_active or self._slam_toolbox_is_running():
            response.accepted = False
            response.message = "Haritalama calisirken AMCL baslatilamaz"
            return response

        try:
            map_yaml = self._validate_map(field_name)
            saved_pose = self._load_saved_pose(map_yaml.parent)
        except ValueError as error:
            response.accepted = False
            response.message = str(error)
            return response

        hardware_error = self._hardware_error()
        if hardware_error:
            response.accepted = False
            response.message = hardware_error
            return response

        ros2 = shutil.which("ros2")
        if ros2 is None:
            response.accepted = False
            response.message = "ros2 komutu PATH icinde bulunamadi"
            return response

        command = [
            ros2,
            "launch",
            "marco_localization",
            "localization_safe.launch.py",
            f"sahte:={str(bool(self.get_parameter('fake_hardware').value)).lower()}",
            "lidar:=true",
            f"imu:={str(bool(self.get_parameter('use_imu').value)).lower()}",
            f"serial_port:={self.get_parameter('serial_port').value}",
            f"lidar_port:={self.get_parameter('lidar_port').value}",
            f"harita:={map_yaml}",
            "rviz:=false",
        ]
        try:
            self._process = subprocess.Popen(command, start_new_session=True)
        except OSError as error:
            self._process = None
            self._state = LocalizationStatus.STATE_ERROR
            self._field_name = field_name
            self._map_yaml = str(map_yaml)
            response.accepted = False
            response.message = f"Lokalizasyon baslatilamadi: {error}"
            response.map_yaml = self._map_yaml
            self._publish_status(response.message)
            return response

        self._field_name = field_name
        self._map_yaml = str(map_yaml)
        self._state = LocalizationStatus.STATE_STARTING
        self._started_at = time.monotonic()
        self._initializing_at = 0.0
        self._saved_pose = saved_pose
        self._initial_pose_attempts = 0
        response.accepted = True
        response.message = f"Saha haritasi yukleniyor: {field_name}"
        response.map_yaml = self._map_yaml
        self._publish_status(response.message)
        return response

    def _on_map(self, msg: OccupancyGrid) -> None:
        if self._state != LocalizationStatus.STATE_STARTING:
            return
        if (
            msg.header.frame_id not in ("", "map")
            or msg.info.width <= 0
            or msg.info.height <= 0
            or len(msg.data) != msg.info.width * msg.info.height
        ):
            return
        self._state = LocalizationStatus.STATE_INITIALIZING
        self._initializing_at = time.monotonic()
        x, y, yaw = self._saved_pose
        self._publish_status(
            f"Harita yuklendi; kayitli poz aktariliyor: x={x:.2f}, y={y:.2f}, "
            f"yaw={math.degrees(yaw):.1f} derece"
        )

    def _publish_initial_pose(self) -> None:
        if (
            self._state != LocalizationStatus.STATE_INITIALIZING
            or self._saved_pose is None
            or self._initial_pose_attempts >= 10
            or self._initial_pose_pub.get_subscription_count() < 1
        ):
            return

        x, y, yaw = self._saved_pose
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = "map"
        msg.header.stamp = (
            self.get_clock().now() - Duration(seconds=0.25)
        ).to_msg()
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        xy_std = float(self.get_parameter("initial_pose_xy_std").value)
        yaw_std = float(self.get_parameter("initial_pose_yaw_std").value)
        msg.pose.covariance[0] = xy_std * xy_std
        msg.pose.covariance[7] = xy_std * xy_std
        msg.pose.covariance[35] = yaw_std * yaw_std
        self._initial_pose_pub.publish(msg)
        self._initial_pose_attempts += 1
        self.get_logger().info(
            f"Kayitli AMCL baslangic pozu gonderildi "
            f"({self._initial_pose_attempts}/10)"
        )

    def _on_amcl_pose(self, _msg: PoseWithCovarianceStamped) -> None:
        if self._state in (
            LocalizationStatus.STATE_WAITING_INITIAL_POSE,
            LocalizationStatus.STATE_INITIALIZING,
        ):
            self._state = LocalizationStatus.STATE_LOCALIZING
            self._publish_status("AMCL konum takibi aktif")

    def _on_stop(self, _request, response):
        if self._process is None or self._process.poll() is not None:
            response.success = False
            response.message = "Calisan lokalizasyon yok"
            return response
        self._state = LocalizationStatus.STATE_STOPPING
        self._publish_status("Lokalizasyon durduruluyor")
        if self._terminate_process():
            self._state = LocalizationStatus.STATE_IDLE
            response.success = True
            response.message = "Lokalizasyon durduruldu"
        else:
            self._state = LocalizationStatus.STATE_ERROR
            response.success = False
            response.message = "Lokalizasyon sureci kapatilamadi"
        self._publish_status(response.message)
        return response

    def _monitor_process(self) -> None:
        if self._process is None:
            return
        return_code = self._process.poll()
        if return_code is not None:
            if self._state not in (
                LocalizationStatus.STATE_IDLE,
                LocalizationStatus.STATE_STOPPING,
            ):
                self._state = LocalizationStatus.STATE_ERROR
                self._process = None
                self._publish_status(
                    f"Lokalizasyon sureci beklenmeden kapandi (kod {return_code})"
                )
            else:
                self._process = None
            return

        timeout = float(self.get_parameter("startup_timeout").value)
        if (
            self._state == LocalizationStatus.STATE_STARTING
            and time.monotonic() - self._started_at > timeout
        ):
            self._state = LocalizationStatus.STATE_ERROR
            stopped = self._terminate_process()
            suffix = "" if stopped else "; surec kapatilamadi"
            self._publish_status(f"{timeout:.0f} saniyede harita yuklenmedi{suffix}")
            return

        initial_timeout = float(self.get_parameter("initial_pose_timeout").value)
        if (
            self._state == LocalizationStatus.STATE_INITIALIZING
            and time.monotonic() - self._initializing_at > initial_timeout
        ):
            self._state = LocalizationStatus.STATE_ERROR
            stopped = self._terminate_process()
            suffix = "" if stopped else "; surec kapatilamadi"
            self._publish_status(
                f"Kayitli pozdan {initial_timeout:.0f} saniyede AMCL pozu "
                f"alinamadi{suffix}"
            )

    def _terminate_process(self) -> bool:
        process = self._process
        if process is None or process.poll() is not None:
            self._process = None
            return True
        try:
            os.killpg(process.pid, signal.SIGINT)
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self.get_logger().error(
                    f"Lokalizasyon sureci kapanmadi; PID={process.pid}"
                )
                return False
        except ProcessLookupError:
            pass
        self._process = None
        return True

    def close(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._terminate_process()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LocalizationManager()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
