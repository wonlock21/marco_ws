#!/usr/bin/env python3
"""Kayitli A/B noktalarina dik segmentlerle giden hareket demosu."""

import math
import os
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Pose2D
from marco_msgs.msg import DemoStatus, LocalizationStatus
from marco_msgs.srv import StartDemoScenario
from nav2_msgs.action import DriveOnHeading, Spin
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformException, TransformListener


class DemoAbort(RuntimeError):
    pass


def _normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def _axis_heading(axis: str, delta: float) -> float:
    if axis == "x":
        return 0.0 if delta >= 0.0 else math.pi
    return math.pi / 2.0 if delta >= 0.0 else -math.pi / 2.0


def _preferred_axis_order(
    x: float,
    y: float,
    yaw: float,
    target_x: float,
    target_y: float,
    tolerance: float,
) -> list[str]:
    """Ilk donusu en az yapan Manhattan segment sirasini sec."""
    deltas = {"x": target_x - x, "y": target_y - y}
    candidates = [
        axis for axis in ("x", "y") if abs(deltas[axis]) > tolerance
    ]
    if len(candidates) < 2:
        return candidates
    candidates.sort(
        key=lambda axis: (
            abs(_normalize_angle(_axis_heading(axis, deltas[axis]) - yaw)),
            -abs(deltas[axis]),
        )
    )
    return candidates


class DemoScenarioManager(Node):
    def __init__(self) -> None:
        super().__init__("demo_scenario_manager")
        self.declare_parameter("camera", "/dev/video0")
        self.declare_parameter("odom_topic", "/odometry/filtered")
        self.declare_parameter("data_root", "~/marco_data/fields")
        self.declare_parameter("turn_direction", 1)
        self.declare_parameter("nav_startup_timeout", 60.0)
        self.declare_parameter("nav_goal_timeout", 180.0)
        self.declare_parameter("lane_phase_timeout", 120.0)
        self.declare_parameter("handoff_delay", 1.2)
        self.declare_parameter("linear_speed", 0.18)
        self.declare_parameter("position_tolerance", 0.10)
        self.declare_parameter("yaw_tolerance", math.radians(5.0))
        self.declare_parameter("obstacle_clear_delay", 0.5)

        self._callbacks = ReentrantCallbackGroup()
        latched = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._status_pub = self.create_publisher(
            DemoStatus, "/demo/status", latched
        )
        self._task_pub = self.create_publisher(String, "/task_command", 10)
        self.create_subscription(
            LocalizationStatus,
            "/localization/status",
            self._on_localization_status,
            latched,
            callback_group=self._callbacks,
        )
        self.create_subscription(
            Bool,
            "/lane_tracking/end_detected",
            self._on_lane_end,
            10,
            callback_group=self._callbacks,
        )
        self.create_subscription(
            Bool,
            "/lane_tracking/turn_complete",
            self._on_turn_complete,
            10,
            callback_group=self._callbacks,
        )
        self.create_subscription(
            Bool,
            "/safety/obstacle_detected",
            self._on_obstacle,
            10,
            callback_group=self._callbacks,
        )
        self.create_subscription(
            Bool,
            "/safety/navigation_abort",
            self._on_navigation_abort,
            10,
            callback_group=self._callbacks,
        )
        self.create_subscription(
            Bool,
            "/base/manual_mode",
            self._on_manual_mode,
            10,
            callback_group=self._callbacks,
        )
        self.create_service(
            StartDemoScenario,
            "/demo/start",
            self._on_start,
            callback_group=self._callbacks,
        )
        self.create_service(
            Trigger,
            "/demo/start_saved",
            self._on_start_saved,
            callback_group=self._callbacks,
        )
        self.create_service(
            Trigger,
            "/demo/continue",
            self._on_continue,
            callback_group=self._callbacks,
        )
        self.create_service(
            Trigger,
            "/demo/cancel",
            self._on_cancel,
            callback_group=self._callbacks,
        )
        self.create_timer(0.5, self._monitor, callback_group=self._callbacks)
        self._drive = ActionClient(
            self,
            DriveOnHeading,
            "/drive_on_heading",
            callback_group=self._callbacks,
        )
        self._spin = ActionClient(
            self,
            Spin,
            "/spin",
            callback_group=self._callbacks,
        )
        self._tf = Buffer()
        self._tf_listener = TransformListener(self._tf, self)

        self._lock = threading.RLock()
        self._state = DemoStatus.STATE_IDLE
        self._message = "Demo hazir"
        self._point_a = Pose2D()
        self._point_b = Pose2D()
        self._active_target = ""
        self._localization_state = LocalizationStatus.STATE_IDLE
        self._localization_field = ""
        self._manual_mode = False
        self._nav_process = None
        self._lane_process = None
        self._active_goal = None
        self._cancel_requested = False
        self._obstacle_detected = False
        self._last_obstacle_at = 0.0
        self._turn_finishing = False
        self._phase_started = 0.0
        self._publish_status()

    def _publish_status(self) -> None:
        status = DemoStatus()
        status.header.stamp = self.get_clock().now().to_msg()
        status.header.frame_id = "map"
        status.state = self._state
        status.message = self._message
        status.point_a = self._point_a
        status.point_b = self._point_b
        status.active_target = self._active_target
        status.navigation_process_id = (
            self._nav_process.pid if self._nav_process is not None else 0
        )
        status.lane_process_id = (
            self._lane_process.pid if self._lane_process is not None else 0
        )
        self._status_pub.publish(status)

    def _set_state(self, state: int, message: str, target: str = "") -> None:
        with self._lock:
            self._state = state
            self._message = message
            self._active_target = target
            self._phase_started = time.monotonic()
            self._publish_status()
        self.get_logger().info(message)

    def _on_localization_status(self, msg: LocalizationStatus) -> None:
        self._localization_state = msg.state
        self._localization_field = msg.field_name
        if (
            self._state not in (
                DemoStatus.STATE_IDLE,
                DemoStatus.STATE_COMPLETE,
                DemoStatus.STATE_ERROR,
                DemoStatus.STATE_CANCELED,
            )
            and msg.state != LocalizationStatus.STATE_LOCALIZING
        ):
            self._fail("Demo sirasinda lokalizasyon kaybedildi")

    def _on_obstacle(self, msg: Bool) -> None:
        detected = bool(msg.data)
        if detected and not self._obstacle_detected:
            self._last_obstacle_at = time.monotonic()
            self.get_logger().warning("Engel algilandi; demo hareketi bekliyor")
        elif not detected and self._obstacle_detected:
            self._last_obstacle_at = time.monotonic()
            self.get_logger().info("Engel kalkti; demo hareketi devam edecek")
        self._obstacle_detected = detected

    def _on_navigation_abort(self, msg: Bool) -> None:
        moving_states = (
            DemoStatus.STATE_STARTING,
            DemoStatus.STATE_NAVIGATING_A,
            DemoStatus.STATE_LANE_A,
            DemoStatus.STATE_TURNING_A,
            DemoStatus.STATE_NAVIGATING_B,
            DemoStatus.STATE_LANE_B,
            DemoStatus.STATE_TURNING_B,
        )
        if not msg.data or self._state not in moving_states:
            return
        threading.Thread(
            target=self._fail,
            args=("Guvenlik engel bekleme zaman asimi verdi",),
            daemon=True,
        ).start()

    def _on_manual_mode(self, msg: Bool) -> None:
        active = bool(msg.data)
        self._manual_mode = active
        if active and self._state not in (
            DemoStatus.STATE_IDLE,
            DemoStatus.STATE_COMPLETE,
            DemoStatus.STATE_ERROR,
            DemoStatus.STATE_CANCELED,
        ):
            threading.Thread(
                target=self._fail,
                args=("Manuel mod acildi; demo iptal edildi",),
                daemon=True,
            ).start()

    @staticmethod
    def _valid_point(point: Pose2D) -> bool:
        return all(math.isfinite(value) for value in (point.x, point.y, point.theta))

    @staticmethod
    def _copy_point(source: Pose2D) -> Pose2D:
        point = Pose2D()
        point.x = float(source.x)
        point.y = float(source.y)
        point.theta = float(source.theta)
        return point

    def _data_root(self) -> Path:
        configured = str(self.get_parameter("data_root").value)
        return Path(os.path.expanduser(configured)).resolve()

    def _load_saved_points(self) -> tuple[Pose2D, Pose2D]:
        field_name = self._localization_field.strip()
        if not field_name or Path(field_name).name != field_name:
            raise DemoAbort("Aktif lokalizasyon saha adi gecersiz")
        root = self._data_root()
        field_dir = (root / field_name).resolve()
        if field_dir.parent != root or not field_dir.is_dir():
            raise DemoAbort(f"Aktif saha klasoru bulunamadi: {field_dir}")
        points_file = field_dir / "demo_points.yaml"
        if points_file.is_symlink():
            raise DemoAbort("demo_points.yaml sembolik bag olamaz")
        if not points_file.is_file():
            raise DemoAbort(f"Kayitli A/B noktalari bulunamadi: {points_file}")
        try:
            with points_file.open("r", encoding="utf-8") as stream:
                content = yaml.safe_load(stream) or {}
        except (OSError, yaml.YAMLError) as error:
            raise DemoAbort(f"demo_points.yaml okunamadi: {error}") from error
        if not isinstance(content, dict):
            raise DemoAbort("demo_points.yaml kok alani gecersiz")
        if content.get("frame_id") != "map":
            raise DemoAbort("A/B noktalari map cercevesinde degil")
        if content.get("field_name") != field_name:
            raise DemoAbort("A/B noktalari aktif sahaya ait degil")
        entries = content.get("points")
        if not isinstance(entries, dict):
            raise DemoAbort("demo_points.yaml points alani gecersiz")

        loaded = []
        for name in ("A", "B"):
            entry = entries.get(name)
            if not isinstance(entry, dict):
                raise DemoAbort(f"{name} noktasi kayitli degil")
            values = (entry.get("x"), entry.get("y"), entry.get("theta"))
            if not all(isinstance(value, (int, float)) for value in values):
                raise DemoAbort(f"{name} noktasi sayisal degil")
            point = Pose2D()
            point.x, point.y, point.theta = (float(value) for value in values)
            if not self._valid_point(point):
                raise DemoAbort(f"{name} noktasi sonlu sayilar icermiyor")
            loaded.append(point)
        return loaded[0], loaded[1]

    def _begin_demo(self, point_a: Pose2D, point_b: Pose2D) -> str:
        with self._lock:
            if self._state not in (
                DemoStatus.STATE_IDLE,
                DemoStatus.STATE_COMPLETE,
                DemoStatus.STATE_ERROR,
                DemoStatus.STATE_CANCELED,
            ):
                raise DemoAbort("Demo zaten calisiyor")
            if self._localization_state != LocalizationStatus.STATE_LOCALIZING:
                raise DemoAbort(
                    "Once lokalizasyonu baslatin ve LOCALIZING bekleyin"
                )
            if self._manual_mode:
                raise DemoAbort("Demo baslamadan once manuel modu kapatin")
            if self._obstacle_detected:
                raise DemoAbort("Demo baslamadan once engel alanini temizleyin")
            if not self._valid_point(point_a) or not self._valid_point(point_b):
                raise DemoAbort("A/B koordinatlari sonlu sayilar olmali")
            distance = math.hypot(
                point_b.x - point_a.x,
                point_b.y - point_a.y,
            )
            if distance < 0.20:
                raise DemoAbort("A ve B en az 0.20 metre farkli olmali")

            if not self._cleanup_processes():
                self._state = DemoStatus.STATE_ERROR
                self._message = "Onceki demo surecleri kapatilamadi"
                self._publish_status()
                raise DemoAbort(self._message)
            self._point_a = self._copy_point(point_a)
            self._point_b = self._copy_point(point_b)
            self._cancel_requested = False
            self._turn_finishing = False
            self._start_nav_process()
            self._set_state(
                DemoStatus.STATE_STARTING, "Demo Nav2 sunuculari baslatiliyor"
            )
            threading.Thread(
                target=self._navigate_then_lane,
                args=("A", self._point_a),
                daemon=True,
            ).start()
            return "A/B dik hareket demo senaryosu baslatildi"

    def _on_start(self, request, response):
        try:
            response.message = self._begin_demo(request.point_a, request.point_b)
            response.accepted = True
        except DemoAbort as error:
            response.accepted = False
            response.message = str(error)
            if self._state == DemoStatus.STATE_STARTING:
                self._state = DemoStatus.STATE_ERROR
                self._message = response.message
                self._publish_status()
        return response

    def _on_start_saved(self, _request, response):
        try:
            point_a, point_b = self._load_saved_points()
            response.message = self._begin_demo(point_a, point_b)
            response.success = True
        except DemoAbort as error:
            response.success = False
            response.message = str(error)
        return response

    def _on_continue(self, _request, response):
        with self._lock:
            if self._state != DemoStatus.STATE_WAITING_LOAD:
                response.success = False
                response.message = "Demo yuk onayi beklemiyor"
                return response
            if self._localization_state != LocalizationStatus.STATE_LOCALIZING:
                response.success = False
                response.message = "Lokalizasyon aktif degil"
                return response
            if self._obstacle_detected:
                response.success = False
                response.message = "Devam etmeden once engel alanini temizleyin"
                return response
            self._cancel_requested = False
            self._set_state(
                DemoStatus.STATE_NAVIGATING_B,
                "B noktasina dik hareket hazirlaniyor",
                "B",
            )
            threading.Thread(
                target=self._navigate_then_lane,
                args=("B", self._point_b),
                daemon=True,
            ).start()
            response.success = True
            response.message = "Yuk onayi alindi; B noktasina dik rota basladi"
            return response

    def _on_cancel(self, _request, response):
        self._cancel_requested = True
        goal = self._active_goal
        if goal is not None:
            goal.cancel_goal_async()
        self._publish_stop()
        stopped = self._cleanup_processes()
        if stopped:
            self._set_state(
                DemoStatus.STATE_CANCELED, "Demo operator tarafindan iptal edildi"
            )
            response.success = True
            response.message = "Demo iptal edildi"
        else:
            self._set_state(
                DemoStatus.STATE_ERROR, "Demo sureclerinden biri kapatilamadi"
            )
            response.success = False
            response.message = self._message
        return response

    def _ros2(self) -> str:
        executable = shutil.which("ros2")
        if executable is None:
            raise DemoAbort("ros2 komutu PATH icinde bulunamadi")
        return executable

    def _start_nav_process(self) -> None:
        try:
            self._nav_process = subprocess.Popen(
                [self._ros2(), "launch", "marco_demo", "demo_nav2.launch.py"],
                start_new_session=True,
            )
        except OSError as error:
            self._nav_process = None
            raise DemoAbort(f"Demo Nav2 baslatilamadi: {error}") from error

    def _start_lane_process(self) -> None:
        command = [
            self._ros2(),
            "launch",
            "marco_demo",
            "demo_lane_segment.launch.py",
            f"camera:={self.get_parameter('camera').value}",
            f"odom_topic:={self.get_parameter('odom_topic').value}",
            f"turn_direction:={self.get_parameter('turn_direction').value}",
        ]
        try:
            self._lane_process = subprocess.Popen(command, start_new_session=True)
        except OSError as error:
            self._lane_process = None
            raise DemoAbort(f"Serit takip sureci baslatilamadi: {error}") from error

    def _wait_future(self, future, deadline: float, label: str):
        completed = threading.Event()
        future.add_done_callback(lambda _future: completed.set())
        while not completed.wait(0.05):
            if self._cancel_requested:
                raise DemoAbort("Demo iptal edildi")
            if time.monotonic() >= deadline:
                raise DemoAbort(f"{label} zaman asimi")
        error = future.exception()
        if error is not None:
            raise DemoAbort(f"{label} hatasi: {error}")
        return future.result()

    def _lookup_map_pose(self, timeout: float = 3.0) -> tuple[float, float, float]:
        deadline = time.monotonic() + timeout
        last_error = ""
        while time.monotonic() < deadline:
            if self._cancel_requested:
                raise DemoAbort("Demo iptal edildi")
            try:
                transform = self._tf.lookup_transform(
                    "map", "base_footprint", rclpy.time.Time()
                )
                translation = transform.transform.translation
                rotation = transform.transform.rotation
                yaw = math.atan2(
                    2.0 * (
                        rotation.w * rotation.z
                        + rotation.x * rotation.y
                    ),
                    1.0 - 2.0 * (
                        rotation.y * rotation.y
                        + rotation.z * rotation.z
                    ),
                )
                values = (translation.x, translation.y, yaw)
                if all(math.isfinite(value) for value in values):
                    return tuple(float(value) for value in values)
                last_error = "TF sonlu sayilar icermiyor"
            except TransformException as error:
                last_error = str(error)
            time.sleep(0.05)
        raise DemoAbort(f"map -> base_footprint TF alinamadi: {last_error}")

    @staticmethod
    def _set_allowance(goal, seconds: float) -> None:
        whole = max(1, int(math.ceil(seconds)))
        goal.time_allowance.sec = whole
        goal.time_allowance.nanosec = 0

    def _wait_obstacle_clear(self) -> None:
        delay = max(0.0, float(
            self.get_parameter("obstacle_clear_delay").value
        ))
        while True:
            while self._obstacle_detected:
                if self._cancel_requested:
                    raise DemoAbort("Demo iptal edildi")
                time.sleep(0.05)
            clear_since = time.monotonic()
            while time.monotonic() - clear_since < delay:
                if self._cancel_requested:
                    raise DemoAbort("Demo iptal edildi")
                if self._obstacle_detected:
                    break
                time.sleep(0.05)
            else:
                return

    def _run_action(self, client, goal, label: str) -> int:
        timeout = float(self.get_parameter("nav_goal_timeout").value)
        deadline = time.monotonic() + timeout
        handle = self._wait_future(
            client.send_goal_async(goal), deadline, f"{label} goal"
        )
        if handle is None or not handle.accepted:
            raise DemoAbort(f"{label} hedefi reddedildi")
        self._active_goal = handle
        try:
            wrapped = self._wait_future(
                handle.get_result_async(), deadline, f"{label} sonucu"
            )
        finally:
            self._active_goal = None
        return wrapped.status

    def _spin_to(self, target_yaw: float, label: str) -> None:
        tolerance = float(self.get_parameter("yaw_tolerance").value)
        for attempt in range(4):
            self._wait_obstacle_clear()
            _x, _y, current_yaw = self._lookup_map_pose()
            delta = _normalize_angle(target_yaw - current_yaw)
            if abs(delta) <= tolerance:
                return
            goal = Spin.Goal()
            goal.target_yaw = float(delta)
            self._set_allowance(
                goal, float(self.get_parameter("nav_goal_timeout").value)
            )
            status = self._run_action(self._spin, goal, label)
            if status == GoalStatus.STATUS_SUCCEEDED:
                continue
            recent_obstacle = (
                self._obstacle_detected
                or time.monotonic() - self._last_obstacle_at < 2.0
            )
            if not recent_obstacle:
                raise DemoAbort(f"{label} basarisiz; action status={status}")
            self._wait_obstacle_clear()
        _x, _y, current_yaw = self._lookup_map_pose()
        error = abs(_normalize_angle(target_yaw - current_yaw))
        if error > tolerance:
            raise DemoAbort(f"{label} yon toleransina ulasamadi")

    def _drive_axis(
        self, axis: str, target_coordinate: float, target_name: str
    ) -> None:
        tolerance = float(self.get_parameter("position_tolerance").value)
        speed = float(self.get_parameter("linear_speed").value)
        if not math.isfinite(speed) or speed <= 0.0:
            raise DemoAbort("Demo linear_speed pozitif olmali")
        for attempt in range(4):
            self._wait_obstacle_clear()
            x, y, _yaw = self._lookup_map_pose()
            current = x if axis == "x" else y
            delta = target_coordinate - current
            if abs(delta) <= tolerance:
                return
            heading = _axis_heading(axis, delta)
            axis_name = "X" if axis == "x" else "Y"
            self._spin_to(
                heading, f"{target_name} {axis_name} eksenine donus"
            )
            x, y, _yaw = self._lookup_map_pose()
            current = x if axis == "x" else y
            remaining = abs(target_coordinate - current)
            if remaining <= tolerance:
                return

            goal = DriveOnHeading.Goal()
            goal.target.x = float(remaining)
            goal.speed = float(speed)
            allowance = max(
                float(self.get_parameter("nav_goal_timeout").value),
                remaining / speed + 30.0,
            )
            self._set_allowance(goal, allowance)
            status = self._run_action(
                self._drive,
                goal,
                f"{target_name} {axis_name} duz segment",
            )
            if status == GoalStatus.STATUS_SUCCEEDED:
                continue
            recent_obstacle = (
                self._obstacle_detected
                or time.monotonic() - self._last_obstacle_at < 2.0
            )
            if not recent_obstacle:
                raise DemoAbort(
                    f"{target_name} {axis_name} segmenti basarisiz; "
                    f"action status={status}"
                )
            self._wait_obstacle_clear()
        x, y, _yaw = self._lookup_map_pose()
        error = abs(target_coordinate - (x if axis == "x" else y))
        if error > tolerance:
            raise DemoAbort(
                f"{target_name} {axis.upper()} ekseni toleransina ulasamadi"
            )

    def _move_orthogonal(self, target_name: str, point: Pose2D) -> None:
        tolerance = float(self.get_parameter("position_tolerance").value)
        x, y, yaw = self._lookup_map_pose()
        order = _preferred_axis_order(
            x, y, yaw, point.x, point.y, tolerance
        )
        if order:
            self.get_logger().info(
                f"{target_name} dik rota sirasi: "
                + " -> ".join(axis.upper() for axis in order)
            )
        else:
            self.get_logger().info(
                f"{target_name} konumu zaten tolerans icinde"
            )
        for axis in order:
            coordinate = point.x if axis == "x" else point.y
            self._drive_axis(axis, coordinate, target_name)

        # Diferansiyel suruste kalan kucuk eksen hatasini en fazla iki kez duzelt.
        for _attempt in range(2):
            x, y, _yaw = self._lookup_map_pose()
            errors = {"x": point.x - x, "y": point.y - y}
            if math.hypot(errors["x"], errors["y"]) <= tolerance:
                break
            axis = max(errors, key=lambda name: abs(errors[name]))
            coordinate = point.x if axis == "x" else point.y
            self._drive_axis(axis, coordinate, target_name)

        x, y, _yaw = self._lookup_map_pose()
        error = math.hypot(point.x - x, point.y - y)
        if error > tolerance * 1.5:
            raise DemoAbort(
                f"{target_name} konum toleransina ulasamadi: {error:.3f} m"
            )
        self._spin_to(point.theta, f"{target_name} serit yonune donus")

    def _navigate_then_lane(self, target_name: str, point: Pose2D) -> None:
        try:
            startup_timeout = float(
                self.get_parameter("nav_startup_timeout").value
            )
            if not self._drive.wait_for_server(timeout_sec=startup_timeout):
                raise DemoAbort("drive_on_heading action sunucusu hazir olmadi")
            if not self._spin.wait_for_server(timeout_sec=startup_timeout):
                raise DemoAbort("spin action sunucusu hazir olmadi")
            state = (
                DemoStatus.STATE_NAVIGATING_A
                if target_name == "A"
                else DemoStatus.STATE_NAVIGATING_B
            )
            self._set_state(
                state,
                f"{target_name} noktasina dik segmentlerle gidiliyor",
                target_name,
            )
            self._move_orthogonal(target_name, point)
            delay = max(0.0, float(self.get_parameter("handoff_delay").value))
            end = time.monotonic() + delay
            while time.monotonic() < end:
                if self._cancel_requested:
                    raise DemoAbort("Demo iptal edildi")
                time.sleep(0.05)
            self._start_lane_process()
            lane_state = (
                DemoStatus.STATE_LANE_A
                if target_name == "A"
                else DemoStatus.STATE_LANE_B
            )
            self._set_state(
                lane_state,
                f"{target_name} noktasinda kamera serit takibi aktif",
                target_name,
            )
        except DemoAbort as error:
            if not self._cancel_requested:
                self._fail(str(error))
        except Exception as error:
            self._fail(f"Demo beklenmeyen hata: {error}")

    def _on_lane_end(self, msg: Bool) -> None:
        if not msg.data:
            return
        if self._state == DemoStatus.STATE_LANE_A:
            self._set_state(
                DemoStatus.STATE_TURNING_A, "A seridi bitti; 180 derece donuluyor", "A"
            )
        elif self._state == DemoStatus.STATE_LANE_B:
            self._set_state(
                DemoStatus.STATE_TURNING_B, "B seridi bitti; 180 derece donuluyor", "B"
            )

    def _on_turn_complete(self, msg: Bool) -> None:
        if not msg.data or self._turn_finishing:
            return
        if self._state not in (
            DemoStatus.STATE_TURNING_A,
            DemoStatus.STATE_TURNING_B,
        ):
            return
        self._turn_finishing = True
        completed_state = self._state
        threading.Thread(
            target=self._finish_turn, args=(completed_state,), daemon=True
        ).start()

    def _finish_turn(self, completed_state: int) -> None:
        self._publish_stop()
        if not self._terminate_lane():
            self._turn_finishing = False
            self._fail("Serit takip sureci guvenli bicimde kapatilamadi")
            return
        if completed_state == DemoStatus.STATE_TURNING_A:
            self._set_state(
                DemoStatus.STATE_WAITING_LOAD,
                "A tamamlandi; yuk yerlestirin ve Devam'a basin",
            )
        else:
            if not self._terminate_nav():
                self._turn_finishing = False
                self._fail("Demo Nav2 sureci guvenli bicimde kapatilamadi")
                return
            self._set_state(
                DemoStatus.STATE_COMPLETE, "A/B hareket demosu tamamlandi"
            )
        self._turn_finishing = False

    def _publish_stop(self) -> None:
        self._task_pub.publish(String(data="STOP"))

    @staticmethod
    def _terminate(process) -> bool:
        if process is None or process.poll() is not None:
            return True
        try:
            os.killpg(process.pid, signal.SIGINT)
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    return False
        except ProcessLookupError:
            pass
        return True

    def _terminate_lane(self) -> bool:
        process = self._lane_process
        if self._terminate(process):
            self._lane_process = None
            return True
        return False

    def _terminate_nav(self) -> bool:
        process = self._nav_process
        if self._terminate(process):
            self._nav_process = None
            return True
        return False

    def _cleanup_processes(self) -> bool:
        self._publish_stop()
        lane_stopped = self._terminate_lane()
        nav_stopped = self._terminate_nav()
        return lane_stopped and nav_stopped

    def _fail(self, message: str) -> None:
        with self._lock:
            if self._state in (
                DemoStatus.STATE_ERROR,
                DemoStatus.STATE_CANCELED,
                DemoStatus.STATE_COMPLETE,
            ):
                return
            self._cancel_requested = True
        goal = self._active_goal
        if goal is not None:
            goal.cancel_goal_async()
        self._cleanup_processes()
        self._set_state(DemoStatus.STATE_ERROR, message)
        self.get_logger().error(message)

    def _monitor(self) -> None:
        if (
            self._nav_process is not None
            and self._nav_process.poll() is not None
            and not self._turn_finishing
            and self._state not in (
                DemoStatus.STATE_IDLE,
                DemoStatus.STATE_COMPLETE,
                DemoStatus.STATE_ERROR,
                DemoStatus.STATE_CANCELED,
            )
        ):
            self._nav_process = None
            self._fail("Demo Nav2 sureci beklenmeden kapandi")
            return
        if (
            self._lane_process is not None
            and self._lane_process.poll() is not None
            and not self._turn_finishing
            and self._state in (
                DemoStatus.STATE_LANE_A,
                DemoStatus.STATE_TURNING_A,
                DemoStatus.STATE_LANE_B,
                DemoStatus.STATE_TURNING_B,
            )
        ):
            self._lane_process = None
            self._fail("Serit takip sureci beklenmeden kapandi")
            return
        if self._state in (
            DemoStatus.STATE_LANE_A,
            DemoStatus.STATE_TURNING_A,
            DemoStatus.STATE_LANE_B,
            DemoStatus.STATE_TURNING_B,
        ):
            timeout = float(self.get_parameter("lane_phase_timeout").value)
            if time.monotonic() - self._phase_started > timeout:
                self._fail(f"Serit/donus fazi {timeout:.0f} saniyede tamamlanmadi")

    def close(self) -> None:
        self._cancel_requested = True
        self._cleanup_processes()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DemoScenarioManager()
    executor = MultiThreadedExecutor(num_threads=4)
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
