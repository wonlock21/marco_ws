"""Adapt a hardware-independent front QR reader topic to MarCO QR telemetry."""

import rclpy
from rclpy.node import Node

from marco_msgs.msg import QrDetection, QrReaderDetection


class QrReaderAdapter(Node):
    """Bridge `/qr_reader/qr_detection` to canonical `/qr/detection`."""

    def __init__(self) -> None:
        super().__init__("qr_reader_adapter")
        self.declare_parameter("input_topic", "/qr_reader/qr_detection")
        self.declare_parameter("output_topic", "/qr/detection")
        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        self._publisher = self.create_publisher(QrDetection, output_topic, 10)
        self.create_subscription(
            QrReaderDetection, input_topic, self._on_detection, 10
        )

    def _on_detection(self, source: QrReaderDetection) -> None:
        output = QrDetection()
        output.header = source.header
        output.detected = bool(source.valid and source.qr_id.strip())
        output.data = source.qr_id.strip() if output.detected else ""
        output.confidence = float(source.confidence)
        output.camera_frame = source.reader_frame.strip() or source.header.frame_id
        self._publisher.publish(output)


def main() -> None:
    rclpy.init()
    node = QrReaderAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
