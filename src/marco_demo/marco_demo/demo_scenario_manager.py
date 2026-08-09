#!/usr/bin/env python3
"""A/B Nav2 hedefleri ile iki serit-donus fazli hareket demosu."""

import math
import os
import shutil
import signal
import subprocess
import threading
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Pose2D, PoseStamped
from marco_msgs.msg import DemoStatus, LocalizationStatus
from marco_msgs.srv import StartDemoScenario
from nav2_msgs.action import NavigateToPose
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


class DemoAbort(RuntimeError):
    pass


class DemoScenarioManager(Node):
    def __init__(self) -> None:
        super().__init__("demo_scenario_manager")
        self.declare_parameter("camera", "/dev/video0")
        self.declare_parameter("odom_topic", "/odometry/filtered")
        self.declare_parameter("turn_direction", 1)
        self.declare_parameter("nav_startup_timeout", 60.0)
        self.declare_parameter("nav_goal_timeout", 180.0)
        self.declare_parameter("lane_phase_timeout", 120.0)
        self.declare_parameter("handoff_delay", 1.2)

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
        self.create_service(
            StartDemoScenario,
            "/demo/start",
            self._on_start,
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
        self._navigation = ActionClient(
            self,
            NavigateToPose,
            "/navigate_to_pose",
            callback_group=self._callbacks,
        )

        self._lock = threading.RLock()
        self._state = DemoStatus.STATE_IDLE
        self._message = "Demo hazir"
        self._point_a = Pose2D()
        self._point_b = Pose2D()
        self._active_target = ""
        self._localization_state = LocalizationStatus.STATE_IDLE
        self._nav_process = None
        self._lane_process = None
        self._active_goal = None
        self._cancel_requested = False
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

    def _on_start(self, request, response):
        with self._lock:
            if self._state not in (
                DemoStatus.STATE_IDLE,
                DemoStatus.STATE_COMPLETE,
                DemoStatus.STATE_ERROR,
                DemoStatus.STATE_CANCELED,
            ):
                response.accepted = False
                response.message = "Demo zaten calisiyor"
                return response
            if self._localization_state != LocalizationStatus.STATE_LOCALIZING:
                response.accepted = False
                response.message = "Once lokalizasyonu baslatin ve LOCALIZING bekleyin"
                return response
            if not self._valid_point(request.point_a) or not self._valid_point(
                request.point_b
            ):
                response.accepted = False
                response.message = "A/B koordinatlari sonlu sayilar olmali"
                return response
            distance = math.hypot(
                request.point_b.x - request.point_a.x,
                request.point_b.y - request.point_a.y,
            )
            if distance < 0.20:
                response.accepted = False
                response.message = "A ve B en az 0.20 metre farkli olmali"
                return response

            if not self._cleanup_processes():
                response.accepted = False
                response.message = "Onceki demo surecleri kapatilamadi"
                self._state = DemoStatus.STATE_ERROR
                self._message = response.message
                self._publish_status()
                return response
            self._point_a = self._copy_point(request.point_a)
            self._point_b = self._copy_point(request.point_b)
            self._cancel_requested = False
            self._turn_finishing = False
            try:
                self._start_nav_process()
            except DemoAbort as error:
                response.accepted = False
                response.message = str(error)
                self._state = DemoStatus.STATE_ERROR
                self._message = response.message
                self._publish_status()
                return response
            self._set_state(
                DemoStatus.STATE_STARTING, "Demo Nav2 sunuculari baslatiliyor"
            )
            threading.Thread(
                target=self._navigate_then_lane,
                args=("A", self._point_a),
                daemon=True,
            ).start()
            response.accepted = True
            response.message = "A/B demo senaryosu baslatildi"
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
            self._cancel_requested = False
            self._set_state(
                DemoStatus.STATE_NAVIGATING_B,
                "Nav2 B noktasina hazirlaniyor",
                "B",
            )
            threading.Thread(
                target=self._navigate_then_lane,
                args=("B", self._point_b),
                daemon=True,
            ).start()
            response.success = True
            response.message = "Yuk onayi alindi; B noktasina gidiliyor"
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

    def _navigate_then_lane(self, target_name: str, point: Pose2D) -> None:
        try:
            startup_timeout = float(
                self.get_parameter("nav_startup_timeout").value
            )
            if not self._navigation.wait_for_server(timeout_sec=startup_timeout):
                raise DemoAbort("navigate_to_pose action sunucusu hazir olmadi")
            state = (
                DemoStatus.STATE_NAVIGATING_A
                if target_name == "A"
                else DemoStatus.STATE_NAVIGATING_B
            )
            self._set_state(state, f"Nav2 {target_name} noktasina gidiyor", target_name)
            goal = NavigateToPose.Goal()
            goal.pose = PoseStamped()
            goal.pose.header.frame_id = "map"
            goal.pose.header.stamp = self.get_clock().now().to_msg()
            goal.pose.pose.position.x = point.x
            goal.pose.pose.position.y = point.y
            goal.pose.pose.orientation.z = math.sin(point.theta / 2.0)
            goal.pose.pose.orientation.w = math.cos(point.theta / 2.0)
            deadline = time.monotonic() + float(
                self.get_parameter("nav_goal_timeout").value
            )
            handle = self._wait_future(
                self._navigation.send_goal_async(goal), deadline, f"Nav2 {target_name} goal"
            )
            if handle is None or not handle.accepted:
                raise DemoAbort(f"Nav2 {target_name} hedefini reddetti")
            self._active_goal = handle
            wrapped = self._wait_future(
                handle.get_result_async(), deadline, f"Nav2 {target_name} sonucu"
            )
            self._active_goal = None
            if wrapped.status != GoalStatus.STATUS_SUCCEEDED:
                raise DemoAbort(
                    f"Nav2 {target_name} basarisiz; action status={wrapped.status}"
                )
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
