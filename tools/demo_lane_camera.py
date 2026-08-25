#!/usr/bin/env python3
"""Publish a moving synthetic dark lane as a raw ROS 2 camera image."""

import argparse
import math

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class DemoLaneCamera(Node):
    def __init__(self, topic, width, height, fps):
        super().__init__('demo_lane_camera')
        self.publisher = self.create_publisher(Image, topic, 10)
        self.width = int(width)
        self.height = int(height)
        self.started = self.get_clock().now()
        self.create_timer(1.0 / float(fps), self.publish_frame)
        self.get_logger().info(
            f'Demo serit kamerasi: {topic} | '
            f'{self.width}x{self.height} @ {fps:.1f} FPS')

    def publish_frame(self):
        elapsed = (
            self.get_clock().now() - self.started).nanoseconds * 1e-9
        frame = self._make_frame(elapsed)
        message = Image()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'demo_camera'
        message.height = self.height
        message.width = self.width
        message.encoding = 'bgr8'
        message.is_bigendian = False
        message.step = self.width * 3
        message.data = frame.tobytes()
        self.publisher.publish(message)

    def _make_frame(self, elapsed):
        x_gradient = np.linspace(25.0, -15.0, self.width)
        y_gradient = np.linspace(25.0, -10.0, self.height)[:, None]
        illumination = 185.0 + x_gradient + y_gradient
        gray = np.clip(illumination, 0, 255).astype(np.uint8)
        frame = np.repeat(gray[:, :, None], 3, axis=2)

        offset = math.sin(elapsed * 0.55) * self.width * 0.16
        bend = math.sin(elapsed * 0.32) * self.width * 0.10
        points = []
        for y in range(int(self.height * 0.38), self.height + 1, 4):
            progress = (y - self.height * 0.38) / (self.height * 0.62)
            center = self.width * 0.5 + offset + bend * (1.0 - progress)
            points.append((int(round(center)), y))
        cv2.polylines(
            frame, [np.asarray(points, dtype=np.int32)], False,
            (38, 38, 38), thickness=max(10, self.width // 18),
            lineType=cv2.LINE_AA)

        cv2.putText(
            frame, 'SENTETIK KAMERA - MOTOR YOK', (8, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.43, (0, 0, 210), 1,
            cv2.LINE_AA)
        return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', default='/camera/image_raw')
    parser.add_argument('--width', type=int, default=320)
    parser.add_argument('--height', type=int, default=240)
    parser.add_argument('--fps', type=float, default=20.0)
    args = parser.parse_args()

    rclpy.init()
    node = DemoLaneCamera(args.topic, args.width, args.height, args.fps)
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
