#!/usr/bin/env python3
"""Kayitli A/B rota grafini Nav2 Route ve FollowPath ile yuruten demo."""

import json
import math
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Pose2D
from lifecycle_msgs.msg import State
from lifecycle_msgs.srv import GetState
from marco_msgs.msg import DemoStatus, LocalizationStatus
from marco_msgs.srv import StartDemoScenario
from nav2_msgs.action import ComputeRoute, FollowPath
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


def _same_position(first: Pose2D, second: Pose2D, tolerance: float = 0.02) -> bool:
    return math.hypot(first.x - second.x, first.y - second.y) <= tolerance


def _build_route_graph(
    point_a: Pose2D,
    point_b: Pose2D,
    route_a: list[Pose2D],
    route_b: list[Pose2D],
) -> tuple[dict, dict[str, int]]:
    """A rotasi -> A -> B rotasi -> B sirali ve cift yonlu grafi uret."""
    entries = [
        *((f"A_ARA_{index}", "transit", point) for index, point in enumerate(route_a, 1)),
        ("A", "task", point_a),
        *((f"B_ARA_{index}", "transit", point) for index, point in enumerate(route_b, 1)),
        ("B", "task", point_b),
    ]
    compact = []
    for name, role, point in entries:
        if compact and _same_position(compact[-1][2], point):
            if role == "task":
                compact[-1] = (name, role, point)
            continue
        compact.append((name, role, point))
    if len(compact) < 2:
        raise DemoAbort("Rota grafi icin en az iki farkli nokta gerekli")

    features = []
    goal_ids = {}
    for node_id, (name, role, point) in enumerate(compact):
        properties = {
            "id": node_id,
            "frame": "map",
            "name": name,
            "metadata": {"role": role},
        }
        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Point",
                "coordinates": [point.x, point.y],
            },
        })
        if name in ("A", "B"):
            goal_ids[name] = node_id

    if set(goal_ids) != {"A", "B"}:
        raise DemoAbort("A ve B ayni konuma kaydedilemez")

    edge_id = 100
    for start_id in range(len(compact) - 1):
        end_id = start_id + 1
        start = compact[start_id][2]
        end = compact[end_id][2]
        for directed_start, directed_end, coordinates in (
            (start_id, end_id, [[start.x, start.y], [end.x, end.y]]),
            (end_id, start_id, [[end.x, end.y], [start.x, start.y]]),
        ):
            features.append({
                "type": "Feature",
                "properties": {
                    "id": edge_id,
                    "startid": directed_start,
                    "endid": directed_end,
                    "cost": 1.0,
                    "metadata": {"abs_speed_limit": 0.18},
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [coordinates],
                },
            })
            edge_id += 1

    return {
        "type": "FeatureCollection",
        "name": "marco_saved_demo_route",
        "crs": {"type": "name", "properties": {"name": "map"}},
        "features": features,
    }, goal_ids


class DemoScenarioManager(Node):
    def __init__(self) -> None:
        super().__init__("demo_scenario_manager")
        self.declare_parameter("camera", "/dev/marco_front_camera")
        self.declare_parameter("odom_topic", "/odometry/filtered")
        self.declare_parameter("data_root", "~/marco_data/fields")
        self.declare_parameter("turn_direction", 1)
        self.declare_parameter("nav_startup_timeout", 60.0)
        self.declare_parameter("nav_goal_timeout", 180.0)
        self.declare_parameter("lane_phase_timeout", 120.0)
        self.declare_parameter("handoff_delay", 1.2)
        self.declare_parameter("position_tolerance", 0.10)
        self.declare_parameter("obstacle_clear_delay", 0.5)
        self.declare_parameter("obstacle_detection_enabled", True)

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
        self._compute_route = ActionClient(
            self,
            ComputeRoute,
            "/compute_route",
            callback_group=self._callbacks,
        )
        self._follow_path = ActionClient(
            self,
            FollowPath,
            "/follow_path",
            callback_group=self._callbacks,
        )
        # Action endpoint'i lifecycle CONFIGURING asamasinda gorunebilir ve bu
        # durumda hedefi reddeder. Navigation launch'indaki son yonetilen dugum
        # aktif oldugunda tum Nav2 zinciri kullanima hazirdir.
        self._nav_ready = self.create_client(
            GetState,
            "/velocity_smoother/get_state",
            callback_group=self._callbacks,
        )
        self._route_ready = self.create_client(
            GetState,
            "/route_server/get_state",
            callback_group=self._callbacks,
        )
        self._tf = Buffer()
        self._tf_listener = TransformListener(self._tf, self)

        self._lock = threading.RLock()
        self._state = DemoStatus.STATE_IDLE
        self._message = "Demo hazir"
        self._point_a = Pose2D()
        self._point_b = Pose2D()
        self._route_a = []
        self._route_b = []
        self._route_graph_file = ""
        self._route_goal_ids = {}
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

        if not self._obstacles_enabled():
            self.get_logger().warning(
                "DEMO ENGEL ALGILAMA BYPASS AKTIF; yalniz kontrollu test icin"
            )

    def _obstacles_enabled(self) -> bool:
        return bool(self.get_parameter("obstacle_detection_enabled").value)

    def _obstacle_active(self) -> bool:
        return self._obstacles_enabled() and self._obstacle_detected

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
        moving_states = (
            DemoStatus.STATE_STARTING,
            DemoStatus.STATE_NAVIGATING_A,
            DemoStatus.STATE_LANE_A,
            DemoStatus.STATE_TURNING_A,
            DemoStatus.STATE_NAVIGATING_B,
            DemoStatus.STATE_LANE_B,
            DemoStatus.STATE_TURNING_B,
        )
        state_changed = detected != self._obstacle_detected
        if state_changed:
            self._last_obstacle_at = time.monotonic()
        # Guvenlik durumunu demo bosken de takip et; boylece engel varken demo
        # baslatilamaz. Ancak haritalama/manuel surus sirasinda demo hareket
        # ediyormus gibi yaniltici olay mesaji uretme.
        if state_changed and self._state in moving_states:
            if detected:
                self.get_logger().warning(
                    "Engel algilandi; demo hareketi bekliyor"
                )
            else:
                self.get_logger().info(
                    "Engel kalkti; demo hareketi devam edecek"
                )
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
        if (
            not self._obstacles_enabled()
            or not msg.data
            or self._state not in moving_states
        ):
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

    @classmethod
    def _point_from_entry(cls, entry, label: str) -> Pose2D:
        if not isinstance(entry, dict):
            raise DemoAbort(f"{label} noktasi gecersiz")
        values = (entry.get("x"), entry.get("y"), entry.get("theta"))
        if not all(isinstance(value, (int, float)) for value in values):
            raise DemoAbort(f"{label} noktasi sayisal degil")
        point = Pose2D()
        point.x, point.y, point.theta = (float(value) for value in values)
        if not cls._valid_point(point):
            raise DemoAbort(f"{label} noktasi sonlu sayilar icermiyor")
        return point

    def _load_saved_points(
        self,
    ) -> tuple[Pose2D, Pose2D, list[Pose2D], list[Pose2D]]:
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
            if entry is None:
                raise DemoAbort(f"{name} noktasi kayitli degil")
            loaded.append(self._point_from_entry(entry, name))

        routes = content.get("routes", {})
        if routes is None:
            routes = {}
        if not isinstance(routes, dict):
            raise DemoAbort("demo_points.yaml routes alani gecersiz")
        loaded_routes = []
        for target_name in ("A", "B"):
            route = routes.get(target_name, [])
            if not isinstance(route, list):
                raise DemoAbort(f"{target_name} rotasi liste degil")
            loaded_routes.append([
                self._point_from_entry(entry, f"{target_name} rota {index + 1}")
                for index, entry in enumerate(route)
            ])
        return loaded[0], loaded[1], loaded_routes[0], loaded_routes[1]

    def _write_route_graph(
        self,
        point_a: Pose2D,
        point_b: Pose2D,
        route_a: list[Pose2D],
        route_b: list[Pose2D],
    ) -> tuple[str, dict[str, int]]:
        field_name = self._localization_field.strip()
        if not field_name or Path(field_name).name != field_name:
            raise DemoAbort("Aktif lokalizasyon saha adi gecersiz")
        root = self._data_root()
        field_dir = (root / field_name).resolve()
        if field_dir.parent != root or not field_dir.is_dir():
            raise DemoAbort(f"Aktif saha klasoru bulunamadi: {field_dir}")
        graph_path = field_dir / "demo_route.geojson"
        if graph_path.is_symlink():
            raise DemoAbort("demo_route.geojson sembolik bag olamaz")

        graph, goal_ids = _build_route_graph(
            point_a, point_b, route_a, route_b
        )
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".demo_route.", suffix=".tmp", dir=str(field_dir)
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(graph, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, graph_path)
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            temporary.unlink(missing_ok=True)
            raise
        return str(graph_path), goal_ids

    def _begin_demo(
        self,
        point_a: Pose2D,
        point_b: Pose2D,
        route_a: list[Pose2D] | None = None,
        route_b: list[Pose2D] | None = None,
    ) -> str:
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
            if self._obstacle_active():
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
            self._route_a = [self._copy_point(point) for point in route_a or []]
            self._route_b = [self._copy_point(point) for point in route_b or []]
            try:
                self._route_graph_file, self._route_goal_ids = (
                    self._write_route_graph(
                        self._point_a,
                        self._point_b,
                        self._route_a,
                        self._route_b,
                    )
                )
            except (OSError, TypeError, ValueError) as error:
                raise DemoAbort(f"Demo rota grafi yazilamadi: {error}") from error
            self._cancel_requested = False
            self._turn_finishing = False
            self._start_nav_process(self._route_graph_file)
            self._set_state(
                DemoStatus.STATE_STARTING, "Demo Nav2 sunuculari baslatiliyor"
            )
            threading.Thread(
                target=self._navigate_then_lane,
                args=("A", self._point_a),
                daemon=True,
            ).start()
            return (
                "A/B kayitli rota demo senaryosu baslatildi; "
                f"A ara nokta={len(self._route_a)}, "
                f"B ara nokta={len(self._route_b)}"
            )

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
            point_a, point_b, route_a, route_b = self._load_saved_points()
            response.message = self._begin_demo(
                point_a, point_b, route_a, route_b
            )
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
            if self._obstacle_active():
                response.success = False
                response.message = "Devam etmeden once engel alanini temizleyin"
                return response
            self._cancel_requested = False
            self._set_state(
                DemoStatus.STATE_NAVIGATING_B,
                "B noktasina Nav2 rota hareketi hazirlaniyor",
                "B",
            )
            threading.Thread(
                target=self._navigate_then_lane,
                args=("B", self._point_b),
                daemon=True,
            ).start()
            response.success = True
            response.message = "Yuk onayi alindi; B Nav2 rotasi basladi"
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

    def _start_nav_process(self, graph_file: str) -> None:
        try:
            self._nav_process = subprocess.Popen(
                [
                    self._ros2(),
                    "launch",
                    "marco_demo",
                    "demo_nav2.launch.py",
                    f"graph:={graph_file}",
                ],
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

    def _wait_nav2_active(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        pending = {
            "Nav2": self._nav_ready,
            "Route Server": self._route_ready,
        }
        while pending and time.monotonic() < deadline:
            if self._cancel_requested:
                raise DemoAbort("Demo iptal edildi")
            for label, client in list(pending.items()):
                remaining = deadline - time.monotonic()
                if not client.wait_for_service(
                    timeout_sec=min(0.25, max(0.0, remaining))
                ):
                    continue
                future = client.call_async(GetState.Request())
                query_deadline = min(deadline, time.monotonic() + 5.0)
                while not future.done() and time.monotonic() < query_deadline:
                    if self._cancel_requested:
                        future.cancel()
                        raise DemoAbort("Demo iptal edildi")
                    time.sleep(0.05)
                if not future.done():
                    # Lifecycle dugumu configure gecisindeyken get_state yaniti
                    # gecikebilir. Tek bir yavas sorgu tum Nav2 baslatmayi iptal
                    # etmemeli; genel nav_startup_timeout dolana kadar yeniden dene.
                    future.cancel()
                    continue
                try:
                    response = future.result()
                except Exception as error:  # noqa: BLE001 - ROS future hatasi
                    self.get_logger().warning(
                        f"{label} lifecycle durumu okunamadi; tekrar denenecek: "
                        f"{error}"
                    )
                    continue
                if response.current_state.id == State.PRIMARY_STATE_ACTIVE:
                    pending.pop(label)
            if pending:
                time.sleep(0.1)
        if pending:
            names = ", ".join(pending)
            raise DemoAbort(f"ACTIVE durumuna gecemeyen dugumler: {names}")

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

    def _wait_obstacle_clear(self) -> None:
        if not self._obstacles_enabled():
            return
        delay = max(0.0, float(
            self.get_parameter("obstacle_clear_delay").value
        ))
        while True:
            while self._obstacle_active():
                if self._cancel_requested:
                    raise DemoAbort("Demo iptal edildi")
                time.sleep(0.05)
            clear_since = time.monotonic()
            while time.monotonic() - clear_since < delay:
                if self._cancel_requested:
                    raise DemoAbort("Demo iptal edildi")
                if self._obstacle_active():
                    break
                time.sleep(0.05)
            else:
                return

    def _run_action_wrapped(self, client, goal, label: str):
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
        return wrapped

    def _run_action(self, client, goal, label: str) -> int:
        return self._run_action_wrapped(client, goal, label).status

    def _move_nav2_route(self, target_name: str, point: Pose2D) -> None:
        self._wait_obstacle_clear()
        goal_id = self._route_goal_ids.get(target_name)
        if goal_id is None:
            raise DemoAbort(f"{target_name} rota hedefi graf icinde yok")

        route_goal = ComputeRoute.Goal()
        route_goal.goal_id = int(goal_id)
        route_goal.use_start = False
        route_goal.use_poses = False
        route_result = self._run_action_wrapped(
            self._compute_route,
            route_goal,
            f"{target_name} rota hesaplama",
        )
        if route_result.status != GoalStatus.STATUS_SUCCEEDED:
            raise DemoAbort(
                f"{target_name} rotasi hesaplanamadi; "
                f"action status={route_result.status}"
            )

        path = route_result.result.path
        if path.header.frame_id not in ("", "map") or len(path.poses) < 2:
            raise DemoAbort(f"{target_name} icin gecerli rota yolu uretilmedi")
        path.header.frame_id = "map"
        for pose in path.poses:
            pose.header.frame_id = "map"
        path.poses[-1].pose.orientation.x = 0.0
        path.poses[-1].pose.orientation.y = 0.0
        path.poses[-1].pose.orientation.z = math.sin(point.theta / 2.0)
        path.poses[-1].pose.orientation.w = math.cos(point.theta / 2.0)

        node_count = len(route_result.result.route.nodes)
        edge_count = len(route_result.result.route.edges)
        self._set_state(
            self._state,
            f"{target_name} Nav2 rotasi izleniyor: "
            f"{node_count} dugum, {edge_count} kenar",
            target_name,
        )
        follow_goal = FollowPath.Goal()
        follow_goal.path = path
        follow_goal.controller_id = "FollowPath"
        self._wait_obstacle_clear()
        status = self._run_action(
            self._follow_path,
            follow_goal,
            f"{target_name} rota takibi",
        )
        if status != GoalStatus.STATUS_SUCCEEDED:
            raise DemoAbort(
                f"{target_name} rotasi takip edilemedi; action status={status}"
            )

        x, y, _yaw = self._lookup_map_pose()
        tolerance = float(self.get_parameter("position_tolerance").value)
        error = math.hypot(point.x - x, point.y - y)
        if error > tolerance * 1.5:
            raise DemoAbort(
                f"{target_name} konum toleransina ulasamadi: {error:.3f} m"
            )

    def _navigate_then_lane(self, target_name: str, point: Pose2D) -> None:
        try:
            startup_timeout = float(
                self.get_parameter("nav_startup_timeout").value
            )
            self._wait_nav2_active(startup_timeout)
            if not self._compute_route.wait_for_server(
                timeout_sec=startup_timeout
            ):
                raise DemoAbort("compute_route action sunucusu hazir olmadi")
            if not self._follow_path.wait_for_server(timeout_sec=startup_timeout):
                raise DemoAbort("follow_path action sunucusu hazir olmadi")
            state = (
                DemoStatus.STATE_NAVIGATING_A
                if target_name == "A"
                else DemoStatus.STATE_NAVIGATING_B
            )
            self._set_state(
                state,
                f"{target_name} noktasina Nav2 rota grafi ile gidiliyor",
                target_name,
            )
            self._move_nav2_route(target_name, point)
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
