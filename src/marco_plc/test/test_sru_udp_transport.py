"""Localhost integration tests for the persistent SRU UDP transport."""

import socket
import threading
import time

from marco_plc.transports.base import RobotStatusSnapshot
from marco_plc.transports.sru_udp import SruUdpTransport


class FakeUdpPlc:
    """Small local UDP peer that responds from the configured server port."""

    def __init__(self, response=b'\x01\x01\x01'):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('127.0.0.1', 0))
        self._socket.settimeout(0.05)
        self.port = self._socket.getsockname()[1]
        self.response = response
        self.respond = True
        self.packets = []
        self.times = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                payload, address = self._socket.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                return
            self.packets.append(payload)
            self.times.append(time.monotonic())
            if self.respond:
                self._socket.sendto(self.response, address)

    def close(self):
        self._stop.set()
        self._socket.close()
        self._thread.join(timeout=1.0)


def _wait_for(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def _transport(server, period=0.05, stale=0.2, request_timeout=0.8):
    transport = SruUdpTransport(
        server_host='127.0.0.1',
        server_port=server.port,
        local_host='127.0.0.1',
        tx_period_s=period,
        rx_stale_timeout_s=stale,
        request_timeout_s=request_timeout,
    )
    transport.update_robot_status(RobotStatusSnapshot(0, '', '', 0.0, 0.0))
    transport.connect()
    return transport


def test_one_hz_heartbeat_period_is_approximately_correct():
    """Send the production-default heartbeat at approximately one hertz."""
    server = FakeUdpPlc()
    transport = _transport(server, period=1.0, stale=2.5)
    try:
        assert _wait_for(lambda: len(server.times) >= 3, timeout=2.6)
        intervals = [b - a for a, b in zip(server.times, server.times[1:3])]
        assert all(0.85 <= interval <= 1.15 for interval in intervals)
        assert all(len(packet) == 7 for packet in server.packets[:3])
    finally:
        transport.disconnect()
        server.close()


def test_valid_rx_connects_and_stale_rx_disconnects():
    """Base connectivity solely on freshness of validated PLC responses."""
    server = FakeUdpPlc()
    transport = _transport(server, stale=0.12)
    try:
        assert _wait_for(transport.is_connected)
        server.respond = False
        time.sleep(0.16)
        assert transport.is_connected() is False
        assert transport.request_task().success is False
    finally:
        transport.disconnect()
        server.close()


def test_invalid_rx_never_sets_connected():
    """Ignore malformed responses even when they come from the correct peer."""
    server = FakeUdpPlc(response=b'\x01\x01\x02\x00')
    transport = _transport(server, stale=0.12)
    try:
        assert _wait_for(lambda: len(server.packets) >= 2)
        assert transport.is_connected() is False
    finally:
        transport.disconnect()
        server.close()


def test_assignment_requires_fresh_control_run_and_reuses_local_id():
    """Reject CONTROL=1 and generate one stable local ID for an assignment."""
    server = FakeUdpPlc(response=b'\x02\x03\x01')
    transport = _transport(server)
    try:
        assert _wait_for(transport.is_connected)
        assert transport.request_task().success is False

        server.response = b'\x02\x03\x02'
        assert _wait_for(lambda: transport.request_task().success)
        first = transport.request_task()
        assert first.pickup_node == 'A2'
        assert first.dropoff_node == 'B3'
        assert first.task_id.startswith('plc_udp_')
        time.sleep(0.08)
        second = transport.request_task()
        assert second.task_id == first.task_id

        completion = transport.report_task_complete(first.task_id, True, 'done')
        assert completion.acknowledged is False
    finally:
        transport.disconnect()
        server.close()


def test_gate_rejects_cached_control_until_waiting_tx_gets_new_response():
    """Require a post-request RX after a newly transmitted WAITING_PLC state."""
    server = FakeUdpPlc(response=b'\x01\x01\x02')
    transport = _transport(server, request_timeout=1.0)
    result = []
    try:
        assert _wait_for(transport.is_connected)
        worker = threading.Thread(
            target=lambda: result.append(transport.request_gate_permission(
                'task-1', 'cross-1', 'q5', 'outbound')),
            daemon=True,
        )
        worker.start()
        time.sleep(0.12)
        assert worker.is_alive(), 'cached CONTROL=2 must not grant the gate'

        server.response = b'\x01\x01\x01'
        transport.update_robot_status(
            RobotStatusSnapshot(4, 'A1', 'B1', 1.0, -1.0))
        time.sleep(0.12)
        assert worker.is_alive(), 'CONTROL=1 must keep the vehicle waiting'

        server.response = b'\x01\x01\x02'
        worker.join(timeout=1.0)
        assert result and result[0].granted is True
        assert result[0].crossing_id == 'cross-1'
        waiting_packets = [packet for packet in server.packets if packet[0] == 5]
        assert waiting_packets
    finally:
        transport.disconnect()
        server.close()
