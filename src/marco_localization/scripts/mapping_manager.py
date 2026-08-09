#!/usr/bin/env python3
"""GUI servisleriyle tek bir guvenli haritalama surecini yonetir."""

import binascii
import math
import os
import re
import shutil
import signal
import stat
import struct
import subprocess
import tempfile
import threading
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path

import rclpy
import yaml
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from marco_msgs.msg import MappingStatus
from marco_msgs.srv import SaveMapping, StartMapping
from nav_msgs.msg import OccupancyGrid
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from std_srvs.srv import Trigger
from slam_toolbox.srv import SaveMap, SerializePoseGraph


FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return (
        struct.pack(">I", len(payload))
        + body
        + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)
    )


def _occupancy_grid_png(msg: OccupancyGrid) -> bytes:
    width = msg.info.width
    height = msg.info.height
    if width <= 0 or height <= 0 or len(msg.data) != width * height:
        raise ValueError("gecersiz OccupancyGrid")

    rows = bytearray()
    for source_y in range(height - 1, -1, -1):
        rows.append(0)
        offset = source_y * width
        for value in msg.data[offset:offset + width]:
            if value < 0:
                rows.append(205)
            else:
                rows.append(254 - round(min(100, int(value)) * 254 / 100))
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=3))
        + _png_chunk(b"IEND", b"")
    )


def _yaw_of(orientation) -> float:
    siny = 2.0 * (
        orientation.w * orientation.z + orientation.x * orientation.y
    )
    cosy = 1.0 - 2.0 * (
        orientation.y * orientation.y + orientation.z * orientation.z
    )
    return math.atan2(siny, cosy)


class MappingManager(Node):
    def __init__(self) -> None:
        super().__init__("mapping_manager")
        self.declare_parameter("fake_hardware", False)
        self.declare_parameter("use_imu", False)
        self.declare_parameter("serial_port", "/dev/marco_stm32")
        self.declare_parameter("lidar_port", "/dev/ttyUSB0")
        self.declare_parameter("startup_timeout", 30.0)
        self.declare_parameter("data_root", "~/marco_data/fields")
        self.declare_parameter("save_timeout", 30.0)

        self._service_group = MutuallyExclusiveCallbackGroup()
        self._worker_group = ReentrantCallbackGroup()

        status_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._status_pub = self.create_publisher(
            MappingStatus, "/mapping/status", status_qos
        )
        self.create_subscription(
            OccupancyGrid,
            "/map",
            self._on_map,
            status_qos,
            callback_group=self._worker_group,
        )
        self.create_subscription(
            PoseWithCovarianceStamped,
            "/pose",
            self._on_pose,
            10,
            callback_group=self._worker_group,
        )
        self.create_service(
            StartMapping,
            "/mapping/start",
            self._on_start,
            callback_group=self._service_group,
        )
        self.create_service(
            SaveMapping,
            "/mapping/save",
            self._on_save,
            callback_group=self._service_group,
        )
        self.create_service(
            Trigger,
            "/mapping/stop",
            self._on_stop,
            callback_group=self._service_group,
        )
        self._save_map_client = self.create_client(
            SaveMap,
            "/slam_toolbox/save_map",
            callback_group=self._worker_group,
        )
        self._serialize_client = self.create_client(
            SerializePoseGraph,
            "/slam_toolbox/serialize_map",
            callback_group=self._worker_group,
        )
        self._manual_cmd_pub = self.create_publisher(Twist, "/cmd_vel_manual", 10)
        self.create_timer(
            0.5, self._monitor_process, callback_group=self._worker_group
        )

        self._process = None
        self._field_name = ""
        self._state = MappingStatus.STATE_IDLE
        self._started_at = 0.0
        self._latest_map = None
        self._latest_pose = None
        self._publish_status("Haritalama hazir")

    def _data_root(self) -> Path:
        configured = str(self.get_parameter("data_root").value)
        return Path(os.path.expanduser(configured)).resolve()

    def _publish_status(self, message: str) -> None:
        status = MappingStatus()
        status.header.stamp = self.get_clock().now().to_msg()
        status.state = self._state
        status.field_name = self._field_name
        status.message = message
        status.process_id = self._process.pid if self._process is not None else 0
        self._status_pub.publish(status)

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
            response.message = f"Haritalama zaten calisiyor: {self._field_name}"
            return response

        target = self._data_root() / field_name
        if target.exists():
            response.accepted = False
            response.message = f"Saha klasoru zaten var, ezilmeyecek: {target}"
            return response

        if not bool(self.get_parameter("fake_hardware").value):
            devices = (
                (str(self.get_parameter("serial_port").value), "STM32"),
                (str(self.get_parameter("lidar_port").value), "LiDAR"),
            )
            for path, label in devices:
                try:
                    mode = os.stat(path).st_mode
                except OSError as error:
                    response.accepted = False
                    response.message = f"{label} cihazi kullanilamiyor: {path}: {error}"
                    return response
                if not stat.S_ISCHR(mode) or not os.access(path, os.R_OK | os.W_OK):
                    response.accepted = False
                    response.message = f"{label} yolu karakter cihazi/okunur-yazilir degil: {path}"
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
            "mapping_safe.launch.py",
            f"sahte:={str(bool(self.get_parameter('fake_hardware').value)).lower()}",
            "lidar:=true",
            f"imu:={str(bool(self.get_parameter('use_imu').value)).lower()}",
            f"serial_port:={self.get_parameter('serial_port').value}",
            f"lidar_port:={self.get_parameter('lidar_port').value}",
            "rviz:=false",
        ]

        try:
            self._process = subprocess.Popen(command, start_new_session=True)
        except OSError as error:
            self._process = None
            self._state = MappingStatus.STATE_ERROR
            self._field_name = field_name
            response.accepted = False
            response.message = f"Haritalama baslatilamadi: {error}"
            self._publish_status(response.message)
            return response

        self._field_name = field_name
        self._state = MappingStatus.STATE_STARTING
        self._started_at = time.monotonic()
        self._latest_map = None
        self._latest_pose = None
        response.accepted = True
        response.message = f"Haritalama baslatiliyor: {field_name}"
        self._publish_status(response.message)
        return response

    def _on_map(self, msg: OccupancyGrid) -> None:
        if (
            msg.info.width <= 0
            or msg.info.height <= 0
            or len(msg.data) != msg.info.width * msg.info.height
        ):
            return
        self._latest_map = msg
        if self._state == MappingStatus.STATE_STARTING:
            self._state = MappingStatus.STATE_MAPPING
            self._publish_status("Canli harita uretiliyor")

    def _on_pose(self, msg: PoseWithCovarianceStamped) -> None:
        if msg.header.frame_id and msg.header.frame_id != "map":
            self.get_logger().warning(
                f"SLAM pozu map cercevesinde degil: {msg.header.frame_id}"
            )
            return
        if self._state in (
            MappingStatus.STATE_STARTING,
            MappingStatus.STATE_MAPPING,
            MappingStatus.STATE_SAVING,
        ):
            self._latest_pose = msg

    def _call_service(self, client, request, label: str):
        timeout = float(self.get_parameter("save_timeout").value)
        deadline = time.monotonic() + timeout
        if not client.wait_for_service(timeout_sec=min(timeout, 5.0)):
            raise RuntimeError(f"{label} servisi bulunamadi")

        future = client.call_async(request)
        completed = threading.Event()
        future.add_done_callback(lambda _future: completed.set())
        remaining = max(0.0, deadline - time.monotonic())
        if not completed.wait(remaining):
            raise TimeoutError(f"{label} {timeout:.0f} saniyede tamamlanmadi")
        error = future.exception()
        if error is not None:
            raise RuntimeError(f"{label} hatasi: {error}")
        return future.result()

    @staticmethod
    def _write_yaml(path: Path, content) -> None:
        with path.open("w", encoding="utf-8") as stream:
            yaml.safe_dump(content, stream, sort_keys=False, allow_unicode=True)

    def _write_metadata(self, staging: Path, map_msg, pose_msg) -> None:
        map_yaml_path = staging / "map.yaml"
        with map_yaml_path.open("r", encoding="utf-8") as stream:
            map_yaml = yaml.safe_load(stream) or {}
        map_yaml["image"] = "map.pgm"
        self._write_yaml(map_yaml_path, map_yaml)

        pose = pose_msg.pose.pose
        pose_data = {
            "frame_id": pose_msg.header.frame_id or "map",
            "child_frame_id": "base_footprint",
            "stamp": {
                "sec": pose_msg.header.stamp.sec,
                "nanosec": pose_msg.header.stamp.nanosec,
            },
            "position": {
                "x": float(pose.position.x),
                "y": float(pose.position.y),
                "z": float(pose.position.z),
            },
            "orientation": {
                "x": float(pose.orientation.x),
                "y": float(pose.orientation.y),
                "z": float(pose.orientation.z),
                "w": float(pose.orientation.w),
            },
            "yaw": float(_yaw_of(pose.orientation)),
            "covariance": [float(value) for value in pose_msg.pose.covariance],
        }
        self._write_yaml(staging / "mapping_pose.yaml", pose_data)

        info = map_msg.info
        manifest = {
            "version": 1,
            "field_name": self._field_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "map": {
                "yaml": "map.yaml",
                "image": "map.pgm",
                "preview": "map.png",
                "width": int(info.width),
                "height": int(info.height),
                "resolution": float(info.resolution),
            },
            "slam_toolbox": {
                "posegraph": "map.posegraph",
                "data": "map.data",
            },
            "mapping_pose": "mapping_pose.yaml",
        }
        self._write_yaml(staging / "field.yaml", manifest)

    def _on_save(self, _request, response):
        if self._state != MappingStatus.STATE_MAPPING:
            response.success = False
            response.message = "Kaydetmek icin aktif ve hazir bir haritalama gerekli"
            return response
        if self._process is None or self._process.poll() is not None:
            response.success = False
            response.message = "Haritalama sureci calismiyor"
            return response
        if self._latest_map is None:
            response.success = False
            response.message = "Kaydedilecek /map verisi yok"
            return response
        if self._latest_pose is None:
            response.success = False
            response.message = "Kaydedilecek map -> base_footprint pozu yok"
            return response

        root = self._data_root()
        target = root / self._field_name
        if target.exists():
            response.success = False
            response.message = f"Saha klasoru zaten var, ezilmeyecek: {target}"
            response.field_directory = str(target)
            return response

        staging = None
        self._state = MappingStatus.STATE_SAVING
        self._publish_status("Harita ve son konum kaydediliyor")
        self._manual_cmd_pub.publish(Twist())
        map_msg = self._latest_map
        pose_msg = self._latest_pose

        try:
            root.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(
                prefix=f".{self._field_name}.saving-", dir=str(root)
            ))
            stem = staging / "map"

            save_request = SaveMap.Request()
            save_request.name.data = str(stem)
            save_result = self._call_service(
                self._save_map_client, save_request, "Harita kaydetme"
            )
            if save_result.result != SaveMap.Response.RESULT_SUCCESS:
                raise RuntimeError(
                    f"Harita kaydetme sonuc kodu: {save_result.result}"
                )

            graph_request = SerializePoseGraph.Request()
            graph_request.filename = str(stem)
            graph_result = self._call_service(
                self._serialize_client, graph_request, "Pose graph kaydetme"
            )
            if graph_result.result != SerializePoseGraph.Response.RESULT_SUCCESS:
                raise RuntimeError(
                    f"Pose graph kaydetme sonuc kodu: {graph_result.result}"
                )

            required = ("map.yaml", "map.pgm", "map.posegraph", "map.data")
            missing = [
                name for name in required
                if not (staging / name).is_file()
                or (staging / name).stat().st_size == 0
            ]
            if missing:
                raise RuntimeError(f"Eksik/bos kayit dosyalari: {', '.join(missing)}")

            (staging / "map.png").write_bytes(_occupancy_grid_png(map_msg))
            self._write_metadata(staging, map_msg, pose_msg)
            staging.rename(target)
        except Exception as error:
            self._state = MappingStatus.STATE_MAPPING
            response.success = False
            response.message = f"Harita kaydedilemedi: {error}"
            response.field_directory = str(staging) if staging else ""
            self._publish_status(response.message)
            self.get_logger().error(response.message)
            return response

        self._state = MappingStatus.STATE_STOPPING
        self._publish_status("Kayit tamamlandi, haritalama durduruluyor")
        stopped = self._terminate_process()
        response.success = True
        response.field_directory = str(target)
        response.map_yaml = str(target / "map.yaml")
        if stopped:
            self._state = MappingStatus.STATE_SAVED
            response.message = f"Harita kaydedildi: {target}"
        else:
            self._state = MappingStatus.STATE_ERROR
            response.message = (
                f"Harita kaydedildi fakat haritalama sureci durdurulamadi: {target}"
            )
        self._publish_status(response.message)
        return response

    def _on_stop(self, _request, response):
        if self._process is None or self._process.poll() is not None:
            response.success = False
            response.message = "Calisan haritalama yok"
            return response

        self._state = MappingStatus.STATE_STOPPING
        self._publish_status("Haritalama durduruluyor")
        if self._terminate_process():
            self._state = MappingStatus.STATE_IDLE
            response.success = True
            response.message = "Haritalama durduruldu"
        else:
            self._state = MappingStatus.STATE_ERROR
            response.success = False
            response.message = "Haritalama sureci kapatilamadi"
        self._publish_status(response.message)
        return response

    def _monitor_process(self) -> None:
        if self._process is None:
            return

        return_code = self._process.poll()
        if return_code is not None:
            if self._state not in (
                MappingStatus.STATE_IDLE,
                MappingStatus.STATE_STOPPING,
            ):
                self._state = MappingStatus.STATE_ERROR
                self._process = None
                self._publish_status(
                    f"Haritalama sureci beklenmeden kapandi (kod {return_code})"
                )
            else:
                self._process = None
            return

        timeout = float(self.get_parameter("startup_timeout").value)
        if (
            self._state == MappingStatus.STATE_STARTING
            and time.monotonic() - self._started_at > timeout
        ):
            self._state = MappingStatus.STATE_ERROR
            stopped = self._terminate_process()
            suffix = "" if stopped else "; surec kapatilamadi"
            self._publish_status(f"{timeout:.0f} saniyede /map gelmedi{suffix}")

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
                    f"Haritalama sureci kapanmadi; PID={process.pid}"
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
    node = MappingManager()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.close()
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
