#!/usr/bin/env python3
"""Simulation-only LiftLoad server; never a production hardware substitute."""

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node

from marco_msgs.action import LiftLoad


class SimulationLiftServer(Node):
    """Model lift limit-switch completion for Phase-10 simulation tests only."""

    def __init__(self) -> None:
        super().__init__('test_only_lift_server')
        self.declare_parameter('test_only', True)
        self.declare_parameter('result', 'success')
        if not bool(self.get_parameter('test_only').value):
            raise RuntimeError('test lift server requires test_only:=true')
        self._result = str(self.get_parameter('result').value)
        self._server = ActionServer(self, LiftLoad, '/lift_load', self._execute,
                                    goal_callback=self._goal,
                                    cancel_callback=lambda _: CancelResponse.ACCEPT)
        self.get_logger().warning(
            'TEST-ONLY lift action: simulated limit-switch result; not hardware evidence')

    def _goal(self, goal: LiftLoad.Goal) -> GoalResponse:
        valid = goal.command in (LiftLoad.Goal.COMMAND_PICKUP,
                                 LiftLoad.Goal.COMMAND_DROPOFF)
        return GoalResponse.ACCEPT if valid else GoalResponse.REJECT

    def _execute(self, handle):
        result = LiftLoad.Result()
        if handle.is_cancel_requested:
            handle.canceled()
            result.result_code = LiftLoad.Result.RESULT_ABORTED
            result.message = 'test lift canceled'
            return result
        feedback = LiftLoad.Feedback()
        feedback.phase = 'simulated_limit_switch'
        feedback.position = (1.0 if handle.request.command ==
                             LiftLoad.Goal.COMMAND_PICKUP else 0.0)
        handle.publish_feedback(feedback)
        if self._result == 'success':
            result.success = True
            result.result_code = LiftLoad.Result.RESULT_OK
            result.message = 'TEST-ONLY simulated limit switch reached'
            handle.succeed()
        else:
            result.success = False
            result.result_code = LiftLoad.Result.RESULT_HARDWARE_FAULT
            result.message = 'TEST-ONLY injected lift fault'
            handle.abort()
        return result


def main() -> None:
    rclpy.init()
    node = SimulationLiftServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
