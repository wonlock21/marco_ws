"""Fail-closed ROS facade for a future production PLC transport."""

from __future__ import annotations

from typing import Optional, Tuple

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool

from marco_msgs.msg import RobotStatus
from marco_msgs.srv import AssignTask, GatePermission, TaskComplete
from marco_plc.transports import (
    PlcTransport,
    RobotStatusSnapshot,
    UnconfiguredTransport,
)
from marco_plc.transports.sru_udp import SruUdpTransport


class PlcBridgeNode(Node):
    """Keep the stable ROS PLC contract independent from the field protocol."""

    def __init__(self, transport: Optional[PlcTransport] = None) -> None:
        super().__init__('real_plc_bridge')
        defaults = (
            ('protocol', 'unset'),
            ('host', ''),
            ('port', 0),
            ('server_host', '192.168.100.100'),
            ('server_port', 1515),
            ('local_host', '192.168.100.10'),
            ('tx_period_s', 1.0),
            ('rx_stale_timeout_s', 2.5),
            ('connect_timeout_s', 3.0),
            ('request_timeout_s', 3.0),
            ('retry_count', 2),
            ('reconnect_enabled', True),
            ('reconnect_interval_s', 2.0),
        )
        for name, default in defaults:
            self.declare_parameter(name, default)

        self._protocol = str(self.get_parameter('protocol').value).strip().lower()
        self._host = str(self.get_parameter('host').value).strip()
        self._port = int(self.get_parameter('port').value)
        self._server_host = str(
            self.get_parameter('server_host').value).strip()
        self._server_port = int(self.get_parameter('server_port').value)
        self._local_host = str(self.get_parameter('local_host').value).strip()
        self._tx_period = float(self.get_parameter('tx_period_s').value)
        self._rx_stale_timeout = float(
            self.get_parameter('rx_stale_timeout_s').value)
        self._connect_timeout = float(
            self.get_parameter('connect_timeout_s').value)
        self._request_timeout = float(
            self.get_parameter('request_timeout_s').value)
        self._retry_count = int(self.get_parameter('retry_count').value)
        self._reconnect_enabled = bool(
            self.get_parameter('reconnect_enabled').value)
        self._reconnect_interval = max(
            0.1, float(self.get_parameter('reconnect_interval_s').value))
        self._callback_group = ReentrantCallbackGroup()
        self._last_connect_error = ''
        self._last_status_error = ''

        if transport is None:
            self._transport, self._transport_available = self._create_transport()
        else:
            self._transport = transport
            self._transport_available = True

        self._connected_pub = self.create_publisher(
            Bool, '/plc/connected', 10)
        self.create_subscription(
            RobotStatus, '/robot_status', self._on_robot_status, 10,
            callback_group=self._callback_group)
        self.create_service(
            AssignTask, '/plc/assign_task', self._on_assign,
            callback_group=self._callback_group)
        self.create_service(
            GatePermission, '/plc/gate_permission', self._on_gate,
            callback_group=self._callback_group)
        self.create_service(
            TaskComplete, '/plc/task_complete', self._on_complete,
            callback_group=self._callback_group)
        self.create_timer(
            0.2, self._publish_connected,
            callback_group=self._callback_group)
        self.create_timer(
            self._reconnect_interval, self._on_reconnect_timer,
            callback_group=self._callback_group)
        self._publish_connected()

        if not self._transport_available:
            self.get_logger().warning(self._transport.reason)
        else:
            self._connect_transport()

    def _create_transport(self) -> Tuple[PlcTransport, bool]:
        """Create the explicitly selected transport or remain fail closed."""
        if self._protocol in ('', 'unset'):
            reason = 'PLC transport yapilandirilmadi (protocol=unset)'
        elif self._protocol == 'sru_udp':
            try:
                transport = SruUdpTransport(
                    server_host=self._server_host,
                    server_port=self._server_port,
                    local_host=self._local_host,
                    tx_period_s=self._tx_period,
                    rx_stale_timeout_s=self._rx_stale_timeout,
                    request_timeout_s=self._request_timeout,
                    error_callback=self._on_transport_error,
                )
            except ValueError as error:
                reason = f'SRU UDP yapilandirmasi gecersiz: {error}'
            else:
                return transport, True
        elif not self._host or self._port <= 0:
            reason = 'PLC protocol/host/port yapilandirmasi eksik'
        else:
            reason = f'PLC transport implementasyonu yok: {self._protocol}'
        return UnconfiguredTransport(reason), False

    @property
    def connected(self) -> bool:
        """Return a fail-closed connection state for ROS consumers."""
        if not self._transport_available:
            return False
        try:
            return bool(self._transport.is_connected())
        except Exception:
            return False

    def _connection_message(self) -> Bool:
        """Build the exact std_msgs/Bool heartbeat consumed by Mission Manager."""
        return Bool(data=self.connected)

    def _publish_connected(self) -> None:
        """Publish connection health with the legacy depth-10 QoS."""
        self._connected_pub.publish(self._connection_message())

    def _on_robot_status(self, message: RobotStatus) -> None:
        """Cache map-frame RobotStatus data without doing network I/O."""
        frame = message.pose.header.frame_id or message.header.frame_id
        if frame != 'map':
            error = f'PLC TX icin map-frame pose gerekli: {frame or "bos"}'
            if error != self._last_status_error:
                self._last_status_error = error
                self.get_logger().error(error)
            return
        self._last_status_error = ''
        position = message.pose.pose.pose.position
        self._transport.update_robot_status(RobotStatusSnapshot(
            mission_state=int(message.mission_state),
            pickup_node=message.pickup_node,
            dropoff_node=message.dropoff_node,
            x_m=float(position.x),
            y_m=float(position.y),
        ))

    def _connect_transport(self) -> None:
        """Prepare UDP I/O without treating socket creation as connectivity."""
        try:
            opened = bool(self._transport.connect())
        except Exception as error:
            detail = f'PLC transport acilamadi: {error}'
            if detail != self._last_connect_error:
                self._last_connect_error = detail
                self.get_logger().error(detail)
            return
        if opened:
            self._last_connect_error = ''

    def _on_transport_error(self, detail: str) -> None:
        """Log each distinct worker error once."""
        self.get_logger().error(detail)

    def _on_reconnect_timer(self) -> None:
        """Attempt at most once per timer tick when a real transport exists."""
        if (
            not self._reconnect_enabled
            or not self._transport_available
            or self.connected
        ):
            return
        self._connect_transport()

    def _mark_transport_failed(self, operation: str, error: Exception) -> None:
        """Disconnect after a transport exception without granting anything."""
        try:
            self._transport.disconnect()
        except Exception:
            pass
        self.get_logger().error(f'PLC {operation} hatasi: {error}')

    def _on_assign(
        self, _request: AssignTask.Request, response: AssignTask.Response
    ) -> AssignTask.Response:
        """Forward task assignment requests or reject while disconnected."""
        if not self.connected:
            response.success = False
            response.message = 'PLC baglantisi/transport hazir degil'
            return response
        try:
            result = self._transport.request_task()
        except Exception as error:  # transport boundary must fail closed
            self._mark_transport_failed('assign_task', error)
            response.success = False
            response.message = f'PLC assign_task hatasi: {error}'
            return response
        response.success = bool(result.success)
        response.task_id = result.task_id
        response.pickup_node = result.pickup_node
        response.dropoff_node = result.dropoff_node
        response.message = result.message
        return response

    def _on_gate(
        self, request: GatePermission.Request, response: GatePermission.Response
    ) -> GatePermission.Response:
        """Forward all crossing identity fields and deny on every failure."""
        response.crossing_id = request.crossing_id
        if not self.connected:
            response.granted = False
            response.message = 'PLC baglantisi/transport hazir degil'
            return response
        try:
            result = self._transport.request_gate_permission(
                request.task_id,
                request.crossing_id,
                request.node_id,
                request.direction,
            )
        except Exception as error:  # transport boundary must fail closed
            self._mark_transport_failed('gate_permission', error)
            response.granted = False
            response.message = f'PLC gate_permission hatasi: {error}'
            return response
        response.granted = bool(result.granted)
        response.crossing_id = result.crossing_id
        response.message = result.message
        return response

    def _on_complete(
        self, request: TaskComplete.Request, response: TaskComplete.Response
    ) -> TaskComplete.Response:
        """Forward completion reports or leave them unacknowledged."""
        if not self.connected:
            response.acknowledged = False
            return response
        try:
            result = self._transport.report_task_complete(
                request.task_id, request.success, request.message)
        except Exception as error:  # transport boundary must fail closed
            self._mark_transport_failed('task_complete', error)
            response.acknowledged = False
            return response
        response.acknowledged = bool(result.acknowledged)
        return response

    def destroy_node(self) -> None:
        """Release a future transport before destroying the ROS node."""
        try:
            self._transport.disconnect()
        except Exception:
            pass
        super().destroy_node()


def main() -> None:
    """Run the production PLC bridge."""
    rclpy.init()
    node = PlcBridgeNode()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
