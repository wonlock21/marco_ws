#!/usr/bin/env python3
"""Headless-only action doubles for Phase-10 orchestration fault testing."""

import time

import rclpy
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionServer, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String

from marco_msgs.action import DockToStation, LiftLoad


class TestInterfaces(Node):
    """Exercise actual ROS actions while injecting deterministic outcomes."""

    def __init__(self) -> None:
        super().__init__('phase10_test_interfaces')
        self._fault = ''
        self._cb = ReentrantCallbackGroup()
        self.create_subscription(String, '/phase10/test_fault', self._set_fault, 10,
                                 callback_group=self._cb)
        self._servers = [
            ActionServer(self, NavigateToPose, 'navigate_to_pose', self._navigation,
                         cancel_callback=self._cancel, callback_group=self._cb),
            ActionServer(self, DockToStation, '/dock_to_station', self._dock,
                         cancel_callback=self._cancel, callback_group=self._cb),
            ActionServer(self, LiftLoad, '/lift_load', self._lift,
                         cancel_callback=self._cancel, callback_group=self._cb),
        ]
        self.get_logger().warning(
            'PHASE10 TEST-ONLY NavigateToPose/dock/lift action doubles active')

    def _set_fault(self, msg: String) -> None:
        self._fault = msg.data

    @staticmethod
    def _cancel(_request):
        return CancelResponse.ACCEPT

    def _wait(self, handle, kind: str) -> bool:
        end = time.monotonic() + (1.0 if self._fault == f'hold_{kind}' else 0.06)
        while time.monotonic() < end:
            if handle.is_cancel_requested:
                handle.canceled()
                return False
            time.sleep(0.01)
        return True

    def _navigation(self, handle):
        result = NavigateToPose.Result()
        if not self._wait(handle, 'navigation'):
            return result
        # Eski 'route' arizasi da navigasyon zincirini bozar.
        if self._fault in ('navigation', 'route'):
            handle.abort()
        else:
            handle.succeed()
        return result

    def _dock(self, handle):
        result = DockToStation.Result()
        if not self._wait(handle, 'docking'):
            result.message = 'test cancellation'
            return result
        if self._fault == 'docking':
            result.success = False
            result.result_code = DockToStation.Result.RESULT_LANE_LOST
            result.message = 'injected docking failure'
            handle.abort()
        else:
            result.success = True
            result.result_code = DockToStation.Result.RESULT_OK
            result.message = 'TEST-ONLY docking success'
            handle.succeed()
        return result

    def _lift(self, handle):
        result = LiftLoad.Result()
        if not self._wait(handle, 'lift'):
            result.message = 'test cancellation'
            return result
        if self._fault == 'lift':
            result.success = False
            result.result_code = LiftLoad.Result.RESULT_HARDWARE_FAULT
            result.message = 'injected lift failure'
            handle.abort()
        else:
            result.success = True
            result.result_code = LiftLoad.Result.RESULT_OK
            result.message = 'TEST-ONLY lift success'
            handle.succeed()
        return result


def main() -> None:
    rclpy.init()
    node = TestInterfaces()
    executor = MultiThreadedExecutor(num_threads=6)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
