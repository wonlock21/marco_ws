"""Publish QR payloads read from the physical serial scanner."""

from __future__ import annotations

import time

import rclpy
import serial
from rclpy.node import Node

from marco_msgs.msg import QrReaderDetection


COMPETITION_QR_VALUES = frozenset({
    'BASLA',
    'ALIM1',
    'ALIM2',
    'ALIM3',
    'KAPI1',
    'KAPI2',
    'BIRAK1',
    'BIRAK2',
    'BIRAK3',
})


def normalize_qr_payload(payload: bytes | str) -> str:
    """Return the scanner payload in the competition's canonical form."""
    if isinstance(payload, bytes):
        value = payload.decode('utf-8', errors='ignore')
    else:
        value = str(payload)
    return value.strip().upper()


class QrSerialReader(Node):
    """Own the QR scanner serial port and publish exact-match detections."""

    def __init__(self) -> None:
        super().__init__('qr_serial_reader')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('read_timeout_s', 0.05)
        self.declare_parameter('reconnect_delay_s', 1.0)
        self.declare_parameter('output_topic', '/qr_reader/qr_detection')
        self.declare_parameter('reader_frame', 'qr_reader_front')

        self._port = str(self.get_parameter('port').value)
        self._baud = int(self.get_parameter('baud').value)
        self._read_timeout = float(
            self.get_parameter('read_timeout_s').value)
        self._reconnect_delay = float(
            self.get_parameter('reconnect_delay_s').value)
        output_topic = str(self.get_parameter('output_topic').value)
        self._reader_frame = str(self.get_parameter('reader_frame').value)
        if self._baud <= 0:
            raise ValueError('baud pozitif olmali')
        if self._read_timeout <= 0.0 or self._reconnect_delay <= 0.0:
            raise ValueError('seri port zaman asimlari pozitif olmali')

        self._publisher = self.create_publisher(
            QrReaderDetection, output_topic, 10)
        self._serial = None
        self._next_connect_at = 0.0
        self._timer = self.create_timer(0.01, self._poll)
        self.get_logger().info(
            f'QR seri okuyucu hazir | port={self._port} | '
            f'baud={self._baud} | cikis={output_topic}')

    def _connect(self) -> None:
        now = time.monotonic()
        if self._serial is not None or now < self._next_connect_at:
            return
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baud,
                timeout=self._read_timeout,
            )
            self._serial.reset_input_buffer()
            self.get_logger().info(f'QR okuyucu baglandi: {self._port}')
        except (OSError, serial.SerialException) as error:
            self._serial = None
            self._next_connect_at = now + self._reconnect_delay
            self.get_logger().warning(
                f'QR okuyucu baglanamadi: {error}',
                throttle_duration_sec=5.0)

    def _disconnect(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except (OSError, serial.SerialException):
                pass
        self._serial = None
        self._next_connect_at = time.monotonic() + self._reconnect_delay

    def _poll(self) -> None:
        self._connect()
        if self._serial is None:
            return
        try:
            if self._serial.in_waiting <= 0:
                return
            payload = self._serial.readline(256)
        except (OSError, serial.SerialException) as error:
            self.get_logger().error(f'QR okuyucu baglantisi koptu: {error}')
            self._disconnect()
            return

        value = normalize_qr_payload(payload)
        if not value:
            return
        valid = value in COMPETITION_QR_VALUES
        message = QrReaderDetection()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self._reader_frame
        message.qr_id = value
        message.valid = valid
        message.confidence = 1.0 if valid else 0.0
        message.reader_frame = self._reader_frame
        self._publisher.publish(message)
        if valid:
            self.get_logger().info(f'QR okundu: {value}')
        else:
            self.get_logger().warning(f'Gecersiz QR verisi reddedildi: {value!r}')

    def destroy_node(self):
        self._disconnect()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = QrSerialReader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
