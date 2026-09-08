"""TEKNOFEST SRU PLC simulator UDP transport."""

from __future__ import annotations

import math
import select
import socket
import struct
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from marco_plc.transports.base import (
    CompletionResult,
    GatePermissionResult,
    PlcTransport,
    RobotStatusSnapshot,
    TaskAssignmentResult,
)


TX_PACKET_LENGTH = 7
RX_PACKET_LENGTH = 3
NO_ASSIGNMENT_CODE = 0
CONTROL_WAIT = 1
CONTROL_RUN = 2
WAITING_PLC_TX_STATUS = 5

# RobotStatus uses zero-based values; the SRU wire protocol uses 1..8.
MISSION_STATE_TO_TX_STATUS = {
    0: 1,
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 7,
    7: 8,
}
PICKUP_TO_CODE = {'A1': 1, 'A2': 2, 'A3': 3}
DROPOFF_TO_CODE = {'B1': 1, 'B2': 2, 'B3': 3}
CODE_TO_PICKUP = {value: key for key, value in PICKUP_TO_CODE.items()}
CODE_TO_DROPOFF = {value: key for key, value in DROPOFF_TO_CODE.items()}


class SruPacketError(ValueError):
    """Reject malformed or non-representable SRU packets."""


@dataclass(frozen=True)
class SruRxPacket:
    """Validated three-byte PLC response."""

    pickup_node: str
    dropoff_node: str
    control: int


def _station_code(value: str, mapping, label: str) -> int:
    """Map a station name, reserving zero only for no active assignment."""
    if not value:
        # The specification leaves startup/no-task TX station bytes undefined.
        # Zero is centralized here as an unknown placeholder and is never
        # accepted as a real A/B assignment in PAKET_RX.
        return NO_ASSIGNMENT_CODE
    try:
        return mapping[value]
    except KeyError as error:
        raise SruPacketError(f'gecersiz {label} istasyonu: {value!r}') from error


def _map_frame_coordinates(x_m: float, y_m: float):
    """Apply the current map-frame-to-wire coordinate policy in one place."""
    # The specification does not define a physical origin or axis direction.
    # Until the organizer confirms it, Nav2 map-frame x/y are used unchanged.
    return x_m, y_m


def _encode_coordinate(value_m: float, axis: str) -> int:
    """Convert metres to signed centimetres without wrapping invalid values."""
    if not math.isfinite(value_m):
        raise SruPacketError(f'{axis} koordinati NaN/Inf olamaz')
    encoded = int(value_m * 100.0)
    if not -32768 <= encoded <= 32767:
        raise SruPacketError(f'{axis} koordinati Int16 araligi disinda: {value_m}')
    return encoded


def encode_tx_packet(status: RobotStatusSnapshot) -> bytes:
    """Encode one exact seven-byte little-endian PAKET_TX."""
    try:
        wire_state = MISSION_STATE_TO_TX_STATUS[int(status.mission_state)]
    except (KeyError, TypeError, ValueError) as error:
        raise SruPacketError(
            f'gecersiz RobotStatus mission_state: {status.mission_state!r}'
        ) from error
    pickup = _station_code(status.pickup_node, PICKUP_TO_CODE, 'pickup')
    dropoff = _station_code(status.dropoff_node, DROPOFF_TO_CODE, 'dropoff')
    map_x, map_y = _map_frame_coordinates(status.x_m, status.y_m)
    packet = struct.pack(
        '<BBBhh',
        wire_state,
        pickup,
        dropoff,
        _encode_coordinate(map_x, 'x'),
        _encode_coordinate(map_y, 'y'),
    )
    if len(packet) != TX_PACKET_LENGTH:
        raise SruPacketError(f'PAKET_TX uzunlugu gecersiz: {len(packet)}')
    return packet


def decode_rx_packet(payload: bytes) -> SruRxPacket:
    """Validate and decode one exact three-byte PAKET_RX."""
    if len(payload) != RX_PACKET_LENGTH:
        raise SruPacketError(f'PAKET_RX 3 byte olmali: {len(payload)}')
    pickup_code, dropoff_code = payload[0], payload[1]
    # The specification table accidentally labels CONTROL as Byte3. PAKET_RX
    # and its header are explicitly three bytes, so the third physical byte,
    # payload[2] (Byte2), is the CONTROL field.
    control = payload[2]
    try:
        pickup = CODE_TO_PICKUP[pickup_code]
        dropoff = CODE_TO_DROPOFF[dropoff_code]
    except KeyError as error:
        raise SruPacketError(
            f'PAKET_RX istasyon kodu gecersiz: {pickup_code}/{dropoff_code}'
        ) from error
    if control not in (CONTROL_WAIT, CONTROL_RUN):
        raise SruPacketError(f'PAKET_RX control kodu gecersiz: {control}')
    return SruRxPacket(pickup, dropoff, control)


class SruUdpTransport(PlcTransport):
    """Exchange SRU packets on one persistent UDP socket and fail closed."""

    def __init__(
        self,
        server_host: str,
        server_port: int,
        local_host: str,
        tx_period_s: float = 1.0,
        rx_stale_timeout_s: float = 2.5,
        request_timeout_s: float = 3.0,
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        if not server_host:
            raise ValueError('server_host bos olamaz')
        if not 1 <= int(server_port) <= 65535:
            raise ValueError('server_port 1..65535 araliginda olmali')
        if tx_period_s <= 0.0 or rx_stale_timeout_s <= 0.0:
            raise ValueError('TX periodu ve RX stale timeout pozitif olmali')
        if request_timeout_s <= 0.0:
            raise ValueError('request_timeout_s pozitif olmali')
        self._server_host = server_host
        self._server_port = int(server_port)
        self._local_host = local_host
        self._tx_period = float(tx_period_s)
        self._rx_stale_timeout = float(rx_stale_timeout_s)
        self._request_timeout = float(request_timeout_s)
        self._error_callback = error_callback

        self._condition = threading.Condition(threading.RLock())
        self._socket: Optional[socket.socket] = None
        self._peer = None
        self._worker: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._status: Optional[RobotStatusSnapshot] = None
        self._last_rx: Optional[SruRxPacket] = None
        self._last_rx_time = 0.0
        self._rx_sequence = 0
        self._waiting_tx_sequence = 0
        self._waiting_tx_time = 0.0
        self._gate_rx_sequence_consumed = 0
        self._active_pair = None
        self._active_task_id = ''
        self._assignment_completed = False
        self._last_error = ''

    def connect(self) -> bool:
        """Open the persistent UDP socket without claiming PLC connectivity."""
        with self._condition:
            if self._socket is not None:
                return True
            peer_ip = socket.gethostbyname(self._server_host)
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                udp_socket.bind((self._local_host, 0))
                udp_socket.setblocking(False)
            except Exception:
                udp_socket.close()
                raise
            self._peer = (peer_ip, self._server_port)
            self._socket = udp_socket
            self._stop.clear()
            self._worker = threading.Thread(
                target=self._io_worker,
                args=(udp_socket,),
                name='sru_udp_io',
                daemon=True,
            )
            self._worker.start()
            return True

    def disconnect(self) -> None:
        """Stop the worker and close its persistent UDP socket."""
        with self._condition:
            self._stop.set()
            udp_socket = self._socket
            self._socket = None
            worker = self._worker
            self._condition.notify_all()
        if udp_socket is not None:
            udp_socket.close()
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=1.0)

    def is_connected(self) -> bool:
        """Require a live socket and at least one fresh validated response."""
        with self._condition:
            return self._fresh_rx_locked(time.monotonic())

    def update_robot_status(self, status: RobotStatusSnapshot) -> None:
        """Atomically replace the telemetry used by the next heartbeat."""
        with self._condition:
            self._status = status
            self._condition.notify_all()

    def request_task(self) -> TaskAssignmentResult:
        """Expose a fresh CONTROL=2 assignment through the ROS contract."""
        with self._condition:
            if not self._fresh_rx_locked(time.monotonic()):
                return TaskAssignmentResult(False, message='PLC RX bayat/yok')
            packet = self._last_rx
            if packet.control != CONTROL_RUN:
                return TaskAssignmentResult(
                    False, message='PLC CONTROL=Bekle; gorev baslatilmadi')
            pair = (packet.pickup_node, packet.dropoff_node)
            if self._active_pair == pair and self._active_task_id:
                if self._assignment_completed:
                    return TaskAssignmentResult(
                        False,
                        message='tamamlanan gorev icin yeni CONTROL gecisi bekleniyor',
                    )
            else:
                self._active_pair = pair
                self._active_task_id = f'plc_udp_{uuid.uuid4().hex[:12]}'
                self._assignment_completed = False
            return TaskAssignmentResult(
                True,
                task_id=self._active_task_id,
                pickup_node=packet.pickup_node,
                dropoff_node=packet.dropoff_node,
                message='fresh PLC UDP gorevi',
            )

    def request_gate_permission(
        self,
        task_id: str,
        crossing_id: str,
        node_id: str,
        direction: str,
    ) -> GatePermissionResult:
        """Wait for CONTROL=2 received after a new WAITING_PLC heartbeat."""
        del task_id, node_id, direction  # These ROS identities are not on wire.
        started = time.monotonic()
        deadline = started + self._request_timeout
        with self._condition:
            initial_rx_sequence = self._rx_sequence
            initial_waiting_sequence = self._waiting_tx_sequence
            while True:
                if self._socket is None:
                    return GatePermissionResult(
                        False, crossing_id, 'PLC UDP socket hazir degil')
                waiting_sent = (
                    self._waiting_tx_sequence > initial_waiting_sequence
                    and self._waiting_tx_time >= started
                )
                new_rx_after_waiting = (
                    waiting_sent
                    and self._rx_sequence > initial_rx_sequence
                    and self._rx_sequence > self._gate_rx_sequence_consumed
                    and self._last_rx_time >= self._waiting_tx_time
                    and self._fresh_rx_locked(time.monotonic())
                )
                if new_rx_after_waiting:
                    if self._last_rx.control == CONTROL_RUN:
                        self._gate_rx_sequence_consumed = self._rx_sequence
                        return GatePermissionResult(
                            True, crossing_id, 'fresh PLC gate izni')
                    # CONTROL=1 means keep waiting for a later response.
                    initial_rx_sequence = self._rx_sequence
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return GatePermissionResult(
                        False, crossing_id, 'fresh PLC gate izni timeout')
                self._condition.wait(timeout=remaining)

    def report_task_complete(
        self, task_id: str, success: bool, message: str
    ) -> CompletionResult:
        """Record local lifecycle state without inventing a UDP ACK packet."""
        del success, message
        with self._condition:
            if task_id and task_id == self._active_task_id:
                self._assignment_completed = True
        # The SRU protocol has no completion message or acknowledgement. The
        # RETURNING RobotStatus is already represented by PAKET_TX status=6.
        return CompletionResult(
            acknowledged=False,
            message='SRU UDP protokolunde task-complete ACK tanimli degil',
        )

    def _fresh_rx_locked(self, now: float) -> bool:
        return (
            self._socket is not None
            and self._last_rx is not None
            and now - self._last_rx_time <= self._rx_stale_timeout
        )

    def _io_worker(self, udp_socket: socket.socket) -> None:
        next_tx = time.monotonic()
        try:
            while not self._stop.is_set():
                now = time.monotonic()
                if now >= next_tx:
                    self._send_status(udp_socket)
                    next_tx = now + self._tx_period
                wait_s = min(0.2, max(0.0, next_tx - time.monotonic()))
                try:
                    readable, _, _ = select.select(
                        [udp_socket], [], [], wait_s)
                except (OSError, ValueError) as error:
                    if not self._stop.is_set():
                        self._report_error(f'UDP select hatasi: {error}')
                    return
                if not readable:
                    continue
                try:
                    payload, address = udp_socket.recvfrom(65535)
                except BlockingIOError:
                    continue
                except OSError as error:
                    if not self._stop.is_set():
                        self._report_error(f'UDP recv hatasi: {error}')
                    return
                self._receive(payload, address)
        finally:
            with self._condition:
                if self._socket is udp_socket:
                    self._socket = None
                self._condition.notify_all()
            try:
                udp_socket.close()
            except OSError:
                pass

    def _send_status(self, udp_socket: socket.socket) -> None:
        with self._condition:
            status = self._status
            peer = self._peer
        if status is None or peer is None:
            return
        try:
            payload = encode_tx_packet(status)
            sent = udp_socket.sendto(payload, peer)
            if sent != TX_PACKET_LENGTH:
                raise OSError(f'eksik UDP gonderimi: {sent}/{TX_PACKET_LENGTH}')
        except (OSError, SruPacketError) as error:
            self._report_error(f'PAKET_TX gonderilemedi: {error}')
            return
        sent_at = time.monotonic()
        if payload[0] == WAITING_PLC_TX_STATUS:
            with self._condition:
                self._waiting_tx_sequence += 1
                self._waiting_tx_time = sent_at
                self._condition.notify_all()

    def _receive(self, payload: bytes, address) -> None:
        with self._condition:
            peer = self._peer
        if peer is None or address[0] != peer[0] or address[1] != peer[1]:
            self._report_error(f'beklenmeyen UDP peer reddedildi: {address}')
            return
        try:
            packet = decode_rx_packet(payload)
        except SruPacketError as error:
            self._report_error(str(error))
            return
        received_at = time.monotonic()
        with self._condition:
            self._last_rx = packet
            self._last_rx_time = received_at
            self._rx_sequence += 1
            if packet.control == CONTROL_WAIT and self._assignment_completed:
                self._active_pair = None
                self._active_task_id = ''
                self._assignment_completed = False
            self._condition.notify_all()
        self._clear_error()

    def _report_error(self, message: str) -> None:
        callback = None
        with self._condition:
            if message != self._last_error:
                self._last_error = message
                callback = self._error_callback
        if callback is not None:
            callback(message)

    def _clear_error(self) -> None:
        with self._condition:
            self._last_error = ''
