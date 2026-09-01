#!/usr/bin/env python3
"""
Route Server hiz limitini tek sahip olarak controller'a aktar.

Uretimde /speed_limit konusunun tek yayincisi bu dugumdur. Route Server
/route_speed_limit uretir; Mission Manager ise yalniz sifirlama olayi ister.
"""

from nav2_msgs.msg import SpeedLimit
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty


class SpeedLimitManager(Node):
    def __init__(self):
        super().__init__('speed_limit_manager')
        self._route_limit = 0.0
        self._guard_limit = 0.0
        self._publisher = self.create_publisher(SpeedLimit, '/speed_limit', 10)
        self.create_subscription(
            SpeedLimit, '/route_speed_limit', self._forward, 10)
        self.create_subscription(
            SpeedLimit, '/route/guard_speed_limit', self._guard, 10)
        self.create_subscription(
            Empty, '/route/speed_limit_reset', self._reset, 10)

    def _forward(self, msg: SpeedLimit) -> None:
        self._route_limit = float(msg.speed_limit)
        self._publish_effective()

    def _guard(self, msg: SpeedLimit) -> None:
        self._guard_limit = float(msg.speed_limit)
        self._publish_effective()

    def _publish_effective(self) -> None:
        active = [value for value in (self._route_limit, self._guard_limit)
                  if value > 0.0]
        output = SpeedLimit()
        output.percentage = False
        output.speed_limit = min(active) if active else 0.0
        self._publisher.publish(output)

    def _reset(self, _msg: Empty) -> None:
        self._route_limit = 0.0
        self._guard_limit = 0.0
        self._publish_effective()


def main(args=None):
    rclpy.init(args=args)
    node = SpeedLimitManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
