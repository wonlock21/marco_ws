#!/usr/bin/env python3
"""Phase-10 headless acceptance; writes raw JSON under /tmp/marco_phase10."""

import json
import os
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String

from marco_msgs.msg import RobotStatus
from marco_msgs.srv import (CancelMission, ResetMissionSafety, StartMission,
                            SubmitManualTask)


class Acceptance(Node):
    """Drive public mission interfaces and validate observable invariants."""

    def __init__(self) -> None:
        super().__init__('phase10_acceptance')
        self.events = []
        self.status = None
        self.cmd = Twist()
        self.create_subscription(String, '/mission/events', self._event, 100)
        self.create_subscription(RobotStatus, '/robot_status',
                                 lambda m: setattr(self, 'status', m), 20)
        self.create_subscription(Twist, '/cmd_vel', lambda m: setattr(self, 'cmd', m), 50)
        self.fault = self.create_publisher(String, '/phase10/test_fault', 10)
        self.estop = self.create_publisher(Bool, '/base/estop', 10)
        self.safety = self.create_publisher(Bool, '/safety/navigation_abort', 10)
        self.plc_connected = self.create_publisher(Bool, '/plc/test_connected', 10)
        self.gate = self.create_publisher(Bool, '/plc/test_gate_granted', 10)
        self.gate_delay = self.create_publisher(Float32, '/plc/test_gate_delay', 10)
        self.start = self.create_client(StartMission, '/mission/start')
        self.manual = self.create_client(SubmitManualTask,
                                         '/mission/submit_manual_task')
        self.cancel = self.create_client(CancelMission, '/mission/cancel')
        self.reset = self.create_client(ResetMissionSafety, '/mission/reset_safety')

    def _event(self, msg: String) -> None:
        self.events.append(json.loads(msg.data))

    def call(self, client, req, timeout=3.0):
        assert client.wait_for_service(timeout_sec=2.0)
        future = client.call_async(req)
        end = time.monotonic() + timeout
        while not future.done() and time.monotonic() < end:
            time.sleep(0.01)
        return future.result()

    def wait_complete(self, previous: int, timeout=8.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            complete = [e for e in self.events if e['event'] == 'mission_complete']
            if len(complete) > previous:
                time.sleep(0.1)
                return complete[-1]
            time.sleep(0.02)
        return None

    def set_fault(self, value: str) -> None:
        self.fault.publish(String(data=value))
        time.sleep(0.08)

    def start_plc(self):
        count = len([e for e in self.events if e['event'] == 'mission_complete'])
        response = self.call(self.start, StartMission.Request())
        return response, count

    def gui(self, task_id: str, pickup='alma_1', dropoff='birak_1'):
        req = SubmitManualTask.Request()
        req.task_id, req.pickup_node, req.dropoff_node = task_id, pickup, dropoff
        count = len([e for e in self.events if e['event'] == 'mission_complete'])
        return self.call(self.manual, req), count

    def invariant(self, start_index: int) -> dict:
        subset = self.events[start_index:]
        active = 0
        max_active = 0
        for event in subset:
            if event['event'] == 'action_started':
                active += 1
                max_active = max(max_active, active)
            elif event['event'] == 'action_finished':
                active = max(0, active - 1)
            elif event['event'] in ('mission_failed', 'mission_complete'):
                active = 0
        zero = abs(self.cmd.linear.x) < 1e-6 and abs(self.cmd.angular.z) < 1e-6
        return {'single_action_owner': max_active <= 1, 'active_action_final': active,
                'final_twist_zero': zero}

    def run(self) -> dict:
        results = {}
        time.sleep(0.7)
        self.gate_delay.publish(Float32(data=0.02))
        pairs = set()
        for index in range(3):
            begin = len(self.events)
            response, count = self.start_plc()
            done = self.wait_complete(count)
            accepted = next((e for e in self.events[begin:]
                             if e['event'] == 'task_accepted'), {})
            pairs.add((accepted.get('pickup'), accepted.get('dropoff')))
            results[f'mock_nominal_{index + 1}'] = {
                'pass': bool(response.accepted and done and done['success']),
                'task': accepted, **self.invariant(begin)}
        results['three_random_tasks'] = {'pass': len(pairs) == 3,
                                         'pairs': sorted([list(x) for x in pairs])}

        begin = len(self.events)
        response, count = self.gui('gui_nominal', 'alma_2', 'birak_3')
        done = self.wait_complete(count)
        results['gui_nominal'] = {'pass': bool(response.accepted and done and
                                               done['success']),
                                  **self.invariant(begin)}

        response, _ = self.gui('invalid', 'not_a_node', 'birak_1')
        results['invalid_node'] = {'pass': not response.accepted,
                                   'message': response.message}

        self.set_fault('hold_navigation')
        begin = len(self.events)
        first, count = self.gui('busy_first')
        second, _ = self.gui('busy_second')
        canceled = self.call(self.cancel, CancelMission.Request())
        done = self.wait_complete(count)
        results['second_task_and_cancel'] = {
            'pass': bool(first.accepted and not second.accepted and canceled.accepted and
                         done and not done['success']), **self.invariant(begin)}
        self.set_fault('')

        for name, fault in (('navigation_failure', 'navigation'),
                            ('docking_failure', 'docking'), ('lift_failure', 'lift')):
            self.set_fault(fault)
            begin = len(self.events)
            response, count = self.gui(name)
            done = self.wait_complete(count)
            results[name] = {'pass': bool(response.accepted and done and
                                          not done['success']), **self.invariant(begin)}
        self.set_fault('')

        self.gate.publish(Bool(data=False))
        time.sleep(0.05)
        begin = len(self.events)
        response, count = self.gui('gate_reject')
        done = self.wait_complete(count)
        results['gate_rejection'] = {'pass': bool(response.accepted and done and
                                                  not done['success']),
                                     **self.invariant(begin)}
        self.gate.publish(Bool(data=True))
        time.sleep(0.05)
        self.gate_delay.publish(Float32(data=1.0))
        time.sleep(0.05)
        begin = len(self.events)
        response, count = self.gui('gate_timeout')
        done = self.wait_complete(count)
        results['gate_timeout'] = {'pass': bool(response.accepted and done and
                                                not done['success']),
                                   **self.invariant(begin)}
        self.gate_delay.publish(Float32(data=0.02))
        time.sleep(1.0)

        self.set_fault('hold_navigation')
        begin = len(self.events)
        response, count = self.start_plc()
        time.sleep(0.15)
        self.plc_connected.publish(Bool(data=False))
        done = self.wait_complete(count)
        results['plc_loss'] = {'pass': bool(response.accepted and done and
                                            not done['success']), **self.invariant(begin)}
        self.plc_connected.publish(Bool(data=True))
        self.set_fault('')
        time.sleep(0.2)

        for name, publisher in (('safety_abort', self.safety), ('estop', self.estop)):
            self.set_fault('hold_navigation')
            begin = len(self.events)
            response, count = self.gui(name)
            time.sleep(0.15)
            publisher.publish(Bool(data=True))
            done = self.wait_complete(count)
            publisher.publish(Bool(data=False))
            time.sleep(0.1)
            blocked, _ = self.gui(f'{name}_must_not_resume')
            reset = self.call(self.reset, ResetMissionSafety.Request())
            results[name] = {'pass': bool(response.accepted and done and
                                          not done['success'] and not blocked.accepted and
                                          reset.accepted), 'no_auto_resume': not blocked.accepted,
                             **self.invariant(begin)}
            self.set_fault('')

        plc_states = [e['state'] for e in self.events if e['event'] ==
                      'state_transition' and e['source'] == 'mock_plc']
        gui_states = [e['state'] for e in self.events if e['event'] ==
                      'state_transition' and e['source'] == 'gui']
        nominal_chain = [1, 2, 3, 4, 3, 5, 2, 0]
        results['shared_state_machine'] = {
            'pass': (all(x in plc_states for x in nominal_chain) and
                     all(x in gui_states for x in nominal_chain)),
            'plc_states': plc_states[:16], 'gui_states': gui_states[:16]}
        required = [value.get('pass', False) for value in results.values()]
        return {'passed': all(required), 'results': results,
                'event_count': len(self.events), 'events': self.events}


def main() -> None:
    rclpy.init()
    node = Acceptance()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    thread = __import__('threading').Thread(target=executor.spin, daemon=True)
    thread.start()
    result = node.run()
    os.makedirs('/tmp/marco_phase10', exist_ok=True)
    path = '/tmp/marco_phase10/headless_acceptance.json'
    with open(path, 'w', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print(('PASS' if result['passed'] else 'FAIL') + f' Phase 10: {path}')
    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()
    raise SystemExit(0 if result['passed'] else 1)
