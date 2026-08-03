#!/usr/bin/env python3
"""Phase 9 negative action/freshness/safety acceptance matrix."""

import json
import os
import threading
import time

import rclpy
from marco_docking.phase9_acceptance import Phase9Acceptance
from marco_msgs.action import DockToStation
from rclpy.executors import MultiThreadedExecutor
from rclpy.parameter import Parameter
from rcl_interfaces.srv import SetParameters
from std_msgs.msg import Bool


class NegativeAcceptance(Phase9Acceptance):
    """Inject explicit perception faults and exercise action safety exits."""

    def __init__(self):
        super().__init__()
        self._sim_params = self.create_client(
            SetParameters, '/phase9_sim_inputs/set_parameters')
        self._estop_pub = self.create_publisher(Bool, '/base/estop', 10)
        self._obstacle_pub = self.create_publisher(
            Bool, '/safety/obstacle_detected', 10)
        self._force_estop = self._force_obstacle = False
        self.create_timer(0.02, self._publish_faults)

    def _publish_faults(self):
        if self._force_estop:
            self._estop_pub.publish(Bool(data=True))
        if self._force_obstacle:
            self._obstacle_pub.publish(Bool(data=True))

    def fault(self, lane='', qr=''):
        if not self._sim_params.wait_for_service(timeout_sec=5.0):
            raise RuntimeError('simulation input parameter service unavailable')
        request = SetParameters.Request()
        request.parameters = [
            Parameter('lane_fault_mode', value=lane).to_parameter_msg(),
            Parameter('qr_fault_mode', value=qr).to_parameter_msg()]
        response = self._wait(self._sim_params.call_async(request), 5.0)
        if not all(item.successful for item in response.results):
            raise RuntimeError('simulation input parameter update rejected')
        time.sleep(0.7)

    def send(self, station='istasyon_A', timeout=8.0):
        goal = DockToStation.Goal()
        goal.station_id, goal.timeout = station, timeout
        goal.position_tolerance, goal.yaw_tolerance = 0.075, 0.087
        goal.approach_type = DockToStation.Goal.APPROACH_DROPOFF
        return self._wait(self._action.send_goal_async(goal), 5.0)

    def stopped(self):
        time.sleep(0.7)
        return (self._zero(self._last_cmd['cmd_vel']) and
                self._zero(self._last_cmd['cmd_vel_dock']))

    def run_negative(self):
        self._action.wait_for_server(timeout_sec=10.0)
        self._pose_client.wait_for_service(timeout_sec=10.0)
        rows = []

        def finish(name, wrapped, expected, action_status=None):
            result = wrapped.result
            rows.append({'scenario': name, 'result_code': int(result.result_code),
                         'message': result.message, 'expected_code': expected,
                         'action_status': int(wrapped.status if action_status is None
                                              else action_status),
                         'zero_twist': self.stopped(),
                         'pass': (
                             int(result.result_code) == expected and
                             self._zero(self._last_cmd['cmd_vel']) and
                             self._zero(self._last_cmd['cmd_vel_dock']))})

        self.set_pose(0.0, 0.0, 0.0)
        self.fault()
        handle = self.send(station='yanlis_istasyon')
        finish('qr_mismatch', self._wait(handle.get_result_async(), 10.0),
               DockToStation.Result.RESULT_QR_MISMATCH)

        for name, lane, qr, expected in (
                ('qr_stale_lost', '', 'stale', DockToStation.Result.RESULT_CAMERA_LOST),
                ('lane_stale_lost', 'stale', '', DockToStation.Result.RESULT_LANE_LOST),
                ('camera_loss', 'camera_lost', 'camera_lost',
                 DockToStation.Result.RESULT_LANE_LOST),
                ('low_confidence', 'low_confidence', 'low_confidence',
                 DockToStation.Result.RESULT_LANE_LOST)):
            self.fault(lane, qr)
            handle = self.send()
            finish(name, self._wait(handle.get_result_async(), 10.0), expected)

        self.fault()
        self.set_pose(-0.05, 0.0, 0.0)
        handle = self.send(timeout=10.0)
        time.sleep(0.25)
        self._wait(handle.cancel_goal_async(), 5.0)
        finish('action_cancel', self._wait(handle.get_result_async(), 5.0),
               DockToStation.Result.RESULT_ABORTED)

        handle = self.send(timeout=0.1)
        finish('timeout', self._wait(handle.get_result_async(), 5.0),
               DockToStation.Result.RESULT_TIMEOUT)

        self._force_estop = True
        handle = self.send()
        finish('estop', self._wait(handle.get_result_async(), 5.0),
               DockToStation.Result.RESULT_ABORTED)
        self._force_estop = False
        self._estop_pub.publish(Bool(data=False))
        time.sleep(1.0)

        self._force_obstacle = True
        handle = self.send()
        finish('obstacle', self._wait(handle.get_result_async(), 5.0),
               DockToStation.Result.RESULT_OBSTACLE)
        self._force_obstacle = False
        self._obstacle_pub.publish(Bool(data=False))

        self.set_pose(-0.05, 0.0, 0.0)
        first = self.send(timeout=10.0)
        second = self.send(timeout=10.0)
        rejected = not second.accepted
        self._wait(first.cancel_goal_async(), 5.0)
        first_result = self._wait(first.get_result_async(), 5.0)
        rows.append({'scenario': 'simultaneous_second_goal',
                     'second_goal_rejected': rejected,
                     'first_result_code': int(first_result.result.result_code),
                     'zero_twist': self.stopped(),
                     'pass': rejected and self.stopped()})

        # Clearing a fault must not restart motion without a fresh goal.
        time.sleep(1.0)
        rows.append({'scenario': 'no_auto_resume', 'zero_twist': self.stopped(),
                     'pass': self.stopped()})
        evidence = {'schema': 'marco.phase9.negative.v1', 'scenarios': rows,
                    'pass': all(row['pass'] for row in rows)}
        path = '/tmp/marco_phase9/negative_final.json'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as stream:
            json.dump(evidence, stream, indent=2, sort_keys=True)
        return evidence


def main():
    rclpy.init()
    node = NegativeAcceptance()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    try:
        result = node.run_negative()
        print(json.dumps({'pass': result['pass'], 'count': len(result['scenarios'])}))
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
