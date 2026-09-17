"""Localhost integration tests for the persistent SRU UDP transport."""

import socket
import threading
import time

import pytest

from marco_plc.transports.base import RobotStatusSnapshot
from marco_plc.transports import sru_udp
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


def _transport(
    server,
    period=0.05,
    stale=0.2,
    request_timeout=0.8,
    error_callback=None,
):
    transport = SruUdpTransport(
        server_host='127.0.0.1',
        server_port=server.port,
        local_host='127.0.0.1',
        tx_period_s=period,
        rx_stale_timeout_s=stale,
        request_timeout_s=request_timeout,
        error_callback=error_callback,
    )
    transport.update_robot_status(RobotStatusSnapshot(0, '', '', 0.0, 0.0))
    transport.connect()
    return transport


def test_tx_continues_without_any_rx_and_after_rx_becomes_stale():
    """RX freshness never gates periodic RobotStatus transmission."""
    server = FakeUdpPlc()
    server.respond = False
    transport = _transport(server, period=0.05, stale=0.08)
    try:
        assert _wait_for(lambda: len(server.packets) >= 5, timeout=0.5)
        assert transport.is_connected() is False
        count_without_rx = len(server.packets)

        server.respond = True
        assert _wait_for(transport.is_connected)
        server.respond = False
        time.sleep(0.12)
        assert transport.is_connected() is False
        assert _wait_for(
            lambda: len(server.packets) >= count_without_rx + 5,
            timeout=0.5,
        )
        assert all(len(packet) == 7 for packet in server.packets)
    finally:
        transport.disconnect()
        server.close()


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


def test_rx_recovery_preserves_assignment_id_without_duplicate_task():
    server = FakeUdpPlc(response=b'\x01\x02\x02')
    transport = _transport(server, period=0.03, stale=0.06)
    try:
        assert _wait_for(transport.is_connected)
        assignment = transport.request_task()
        assert assignment.success is True

        server.respond = False
        time.sleep(0.09)
        assert transport.is_connected() is False
        packets_at_loss = len(server.packets)
        assert _wait_for(lambda: len(server.packets) > packets_at_loss + 2)

        server.respond = True
        assert _wait_for(transport.is_connected)
        recovered = transport.request_task()
        assert recovered.success is True
        assert recovered.task_id == assignment.task_id

        transport.report_task_complete(assignment.task_id, True, 'done')
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


def test_invalid_peer_and_payload_do_not_refresh_rx_state():
    diagnostics = []
    transport = SruUdpTransport(
        server_host='127.0.0.1',
        server_port=1515,
        local_host='127.0.0.1',
        error_callback=diagnostics.append,
    )
    with transport._condition:
        transport._peer = ('127.0.0.1', 1515)
        transport._socket = object()

    transport._receive(b'\x01\x01\x02', ('127.0.0.1', 1516))
    transport._receive(b'\x01\x01\x02\x00', ('127.0.0.1', 1515))

    assert transport._last_rx is None
    assert transport._rx_sequence == 0
    assert any('beklenmeyen UDP peer' in item for item in diagnostics)
    assert any('PAKET_RX 3 byte olmali' in item for item in diagnostics)


def test_completion_during_rx_loss_blocks_duplicate_after_recovery():
    server = FakeUdpPlc(response=b'\x03\x01\x02')
    transport = _transport(server, period=0.03, stale=0.06)
    try:
        assert _wait_for(transport.is_connected)
        assignment = transport.request_task()
        server.respond = False
        time.sleep(0.09)
        assert transport.is_connected() is False

        transport.report_task_complete(assignment.task_id, True, 'done')

        server.respond = True
        assert _wait_for(transport.is_connected)
        duplicate = transport.request_task()
        assert duplicate.success is False
        assert 'tamamlanan gorev' in duplicate.message
    finally:
        transport.disconnect()
        server.close()


def test_initial_socket_failure_is_retried_by_same_worker(monkeypatch):
    diagnostics = []
    recovered_socket = _WorkerSocket()
    attempts = 0
    transport = SruUdpTransport(
        server_host='127.0.0.1',
        server_port=1515,
        local_host='127.0.0.1',
        tx_period_s=0.02,
        reconnect_interval_s=1.0,
        error_callback=diagnostics.append,
    )
    transport.update_robot_status(RobotStatusSnapshot(0, '', '', 0.0, 0.0))

    def open_socket():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError('injected initial bind failure')
        return recovered_socket, ('127.0.0.1', 1515)

    def no_rx(_readable, _writeable, _exceptional, timeout):
        time.sleep(min(timeout, 0.002))
        return [], [], []

    monkeypatch.setattr(transport, '_open_socket', open_socket)
    monkeypatch.setattr(sru_udp.select, 'select', no_rx)
    try:
        assert transport.connect() is True
        worker = transport._worker
        assert _wait_for(lambda: attempts >= 2)
        assert _wait_for(lambda: recovered_socket.sent >= 1)
        assert transport._worker is worker
        assert worker.is_alive()
        assert diagnostics
    finally:
        transport.disconnect()


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
        assignment = transport.request_task()
        assert assignment.success is True
        worker = threading.Thread(
            target=lambda: result.append(transport.request_gate_permission(
                assignment.task_id, 'cross-1', 'q5', 'outbound')),
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


def test_repeated_control_wait_windows_are_nonfatal_then_matching_run_grants():
    """Model more than 10 production seconds without a slow wall-clock test."""
    server = FakeUdpPlc(response=b'\x01\x02\x02')
    transport = _transport(
        server, period=0.01, stale=0.08, request_timeout=0.06)
    try:
        assert _wait_for(transport.is_connected)
        assignment = transport.request_task()
        assert (assignment.pickup_node, assignment.dropoff_node) == ('A1', 'B2')
        transport.update_robot_status(
            RobotStatusSnapshot(4, 'A1', 'B2', 1.0, -1.0))
        server.response = b'\x01\x02\x01'

        # Four scaled polling windows represent >12 s at the production
        # request_timeout_s=3.0 setting. Every response remains a normal wait.
        for sequence in range(4):
            reply = transport.request_gate_permission(
                assignment.task_id, f'cross-{sequence}', 'q5', 'outbound')
            assert reply.granted is False
            assert reply.message.startswith('WAITING_PLC:')
            assert transport.is_connected() is True

        server.response = b'\x01\x02\x02'
        granted = transport.request_gate_permission(
            assignment.task_id, 'cross-grant', 'q5', 'outbound')
        assert granted.granted is True
    finally:
        transport.disconnect()
        server.close()


def test_mismatched_run_pair_cannot_grant_then_active_pair_can():
    """Keep the active assignment while ignoring another task's CONTROL=2."""
    diagnostics = []
    server = FakeUdpPlc(response=b'\x01\x02\x02')
    transport = _transport(
        server,
        period=0.01,
        stale=0.08,
        request_timeout=0.06,
        error_callback=diagnostics.append,
    )
    try:
        assert _wait_for(transport.is_connected)
        assignment = transport.request_task()
        assert (assignment.pickup_node, assignment.dropoff_node) == ('A1', 'B2')
        transport.update_robot_status(
            RobotStatusSnapshot(4, 'A1', 'B2', 1.0, -1.0))

        server.response = b'\x03\x01\x02'
        mismatch = transport.request_gate_permission(
            assignment.task_id, 'cross-mismatch', 'q5', 'outbound')
        assert mismatch.granted is False
        assert mismatch.message.startswith('WAITING_PLC:')
        assert 'beklenen=A1/B2 gelen=A3/B1' in mismatch.message
        assert any('beklenen=A1/B2 gelen=A3/B1' in item
                   for item in diagnostics)

        server.response = b'\x01\x02\x02'
        granted = transport.request_gate_permission(
            assignment.task_id, 'cross-correct', 'q5', 'outbound')
        assert granted.granted is True
        assert transport._active_pair == ('A1', 'B2')
    finally:
        transport.disconnect()
        server.close()


def test_gate_fails_closed_when_rx_becomes_stale():
    """Missing RX keeps the explicit gate closed in WAITING_PLC."""
    server = FakeUdpPlc(response=b'\x01\x02\x02')
    transport = _transport(
        server, period=0.01, stale=0.05, request_timeout=0.2)
    try:
        assert _wait_for(transport.is_connected)
        assignment = transport.request_task()
        transport.update_robot_status(
            RobotStatusSnapshot(4, 'A1', 'B2', 1.0, -1.0))
        server.respond = False

        denied = transport.request_gate_permission(
            assignment.task_id, 'cross-stale', 'q5', 'outbound')
        assert denied.granted is False
        assert denied.message.startswith('WAITING_PLC:')
        assert transport.is_connected() is False
    finally:
        transport.disconnect()
        server.close()


class _WorkerSocket:
    """Controllable socket double for worker recovery paths."""

    def __init__(self, send_error=False, recv_error=False):
        self.send_error = send_error
        self.recv_error = recv_error
        self.closed = False
        self.sent = 0

    def sendto(self, payload, _peer):
        if self.send_error:
            raise OSError('injected send failure')
        self.sent += 1
        return len(payload)

    def recvfrom(self, _size):
        if self.recv_error:
            raise OSError('injected recv failure')
        raise BlockingIOError

    def close(self):
        self.closed = True


@pytest.mark.parametrize('failure', ('send', 'recv', 'select'))
def test_worker_recreates_socket_after_io_failure(monkeypatch, failure):
    """send/recv/select failures all recycle the socket without restart."""
    diagnostics = []
    first = _WorkerSocket(
        send_error=failure == 'send', recv_error=failure == 'recv')
    replacement = _WorkerSocket()
    opened = []
    select_calls = 0
    transport = SruUdpTransport(
        server_host='127.0.0.1',
        server_port=1515,
        local_host='127.0.0.1',
        tx_period_s=0.01,
        rx_stale_timeout_s=0.05,
        request_timeout_s=0.05,
        reconnect_interval_s=0.01,
        error_callback=diagnostics.append,
    )
    transport.update_robot_status(RobotStatusSnapshot(0, '', '', 0.0, 0.0))

    def open_socket():
        value = first if not opened else replacement
        opened.append(value)
        return value, ('127.0.0.1', 1515)

    def select_once(readable, _writeable, _exceptional, timeout):
        nonlocal select_calls
        select_calls += 1
        if failure == 'select' and select_calls == 1:
            raise ValueError('injected select failure')
        if failure == 'recv' and readable[0] is first:
            return readable, [], []
        time.sleep(min(timeout, 0.002))
        return [], [], []

    monkeypatch.setattr(transport, '_open_socket', open_socket)
    monkeypatch.setattr(sru_udp.select, 'select', select_once)
    try:
        transport.connect()
        assert _wait_for(lambda: len(opened) >= 2, timeout=0.3)
        assert first.closed is True
        assert _wait_for(lambda: replacement.sent >= 1, timeout=0.3)
        assert transport._worker.is_alive()
        assert diagnostics
    finally:
        transport.disconnect()


def test_delayed_tx_tick_skips_missed_deadlines_without_burst(monkeypatch):
    """Absolute cadence skips missed slots after one delayed send."""
    server = FakeUdpPlc()
    transport = SruUdpTransport(
        server_host='127.0.0.1',
        server_port=server.port,
        local_host='127.0.0.1',
        tx_period_s=0.05,
        rx_stale_timeout_s=0.2,
        request_timeout_s=0.2,
    )
    transport.update_robot_status(RobotStatusSnapshot(0, '', '', 0.0, 0.0))
    original_send = transport._send_status
    first = True

    def delayed_once(udp_socket):
        nonlocal first
        if first:
            first = False
            time.sleep(0.12)
        return original_send(udp_socket)

    monkeypatch.setattr(transport, '_send_status', delayed_once)
    try:
        transport.connect()
        assert _wait_for(lambda: len(server.times) >= 3, timeout=0.5)
        intervals = [b - a for a, b in zip(server.times, server.times[1:])]
        assert min(intervals) >= 0.02
    finally:
        transport.disconnect()
        server.close()
