"""Fail-closed ROS facade for a future production PLC transport."""

from __future__ import annotations

from typing import Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

from marco_msgs.srv import AssignTask, GatePermission, TaskComplete
from marco_plc.transports import PlcTransport, UnconfiguredTransport


class PlcBridgeNode(Node):
    """Keep the stable ROS PLC contract independent from the field protocol."""

    def __init__(self, transport: Optional[PlcTransport] = None) -> None:
        super().__init__('real_plc_bridge')
        defaults = (
            ('protocol', 'unset'),
            ('host', ''),
            ('port', 0),
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
        self._connect_timeout = float(
            self.get_parameter('connect_timeout_s').value)
        self._request_timeout = float(
            self.get_parameter('request_timeout_s').value)
        self._retry_count = int(self.get_parameter('retry_count').value)
        self._reconnect_enabled = bool(
            self.get_parameter('reconnect_enabled').value)
        self._reconnect_interval = max(
            0.1, float(self.get_parameter('reconnect_interval_s').value))

        if transport is None:
            self._transport, self._transport_available = self._create_transport()
        else:
            self._transport = transport
            self._transport_available = True

        self._connected_pub = self.create_publisher(Bool, '/plc/connected', 10)
        self.create_service(AssignTask, '/plc/assign_task', self._on_assign)
        self.create_service(
            GatePermission, '/plc/gate_permission', self._on_gate)
        self.create_service(
            TaskComplete, '/plc/task_complete', self._on_complete)
        self.create_timer(0.2, self._publish_connected)
        self.create_timer(self._reconnect_interval, self._on_reconnect_timer)
        self._publish_connected()

        if not self._transport_available:
            self.get_logger().warning(self._transport.reason)

    def _create_transport(self) -> Tuple[PlcTransport, bool]:
        """Create only implemented transports; currently none exist."""
        if self._protocol in ('', 'unset'):
            reason = 'PLC transport yapilandirilmadi (protocol=unset)'
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

    def _on_reconnect_timer(self) -> None:
        """Attempt at most once per timer tick when a real transport exists."""
        if (
            not self._reconnect_enabled
            or not self._transport_available
            or self.connected
        ):
            return
        try:
            self._transport.connect()
        except Exception as error:  # transport boundary must fail closed
            self.get_logger().error(f'PLC reconnect hatasi: {error}')

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
