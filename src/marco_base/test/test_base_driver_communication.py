"""STM32 communication-health publication tests."""

import time

import rclpy
from rclpy.parameter import Parameter

from marco_base.base_driver import BaseDriver


class Recorder:
    """Capture publisher output without a ROS executor."""

    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


def test_valid_frames_become_healthy_and_stale_frames_become_unhealthy():
    """UART health follows valid decoded frames and their monotonic age."""
    rclpy.init()
    node = BaseDriver(parameter_overrides=[
        Parameter("use_fake_hardware", value=True),
        Parameter("wheel_measurement_log_enabled", value=False),
        Parameter("communication_timeout", value=0.05),
    ])
    node._communication_pub = Recorder()
    try:
        deadline = time.monotonic() + 0.5
        while node._last_valid_frame_wall is None and time.monotonic() < deadline:
            node._read_transport()
            time.sleep(0.01)

        node._publish_communication_health()
        assert node._last_valid_frame_wall is not None
        assert node._communication_pub.messages[-1].data

        node._last_valid_frame_wall = time.monotonic() - 1.0
        node._publish_communication_health()
        assert not node._communication_pub.messages[-1].data
    finally:
        node.destroy_node()
        rclpy.shutdown()
