#!/usr/bin/env python3
"""RViz markers for Phase 9 camera measurements and Gazebo ground truth."""

import math

import rclpy
from marco_msgs.msg import LaneOffset, QrDetection
from rclpy.node import Node
from std_msgs.msg import ColorRGBA
from tf2_msgs.msg import TFMessage
from visualization_msgs.msg import Marker, MarkerArray


class Phase9Visualizer(Node):
    """Render measured lane/QR errors and ground-truth pose."""

    def __init__(self):
        super().__init__('phase9_visualizer')
        self._lane = self._qr = self._truth = None
        self._pub = self.create_publisher(MarkerArray, '/phase9/markers', 10)
        self.create_subscription(LaneOffset, '/lane/offset',
                                 lambda msg: setattr(self, '_lane', msg), 10)
        self.create_subscription(QrDetection, '/qr/detection',
                                 lambda msg: setattr(self, '_qr', msg), 10)
        self.create_subscription(TFMessage, '/world/marco_test/dynamic_pose/info',
                                 self._on_tf, 10)
        self.create_timer(0.1, self._tick)

    def _on_tf(self, msg):
        for transform in msg.transforms:
            if transform.child_frame_id == 'marco':
                self._truth = transform.transform

    def _marker(self, number, kind, frame, color):
        marker = Marker()
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.header.frame_id, marker.ns, marker.id = frame, 'phase9', number
        marker.type, marker.action = kind, Marker.ADD
        marker.color = ColorRGBA(r=color[0], g=color[1], b=color[2], a=1.0)
        marker.pose.orientation.w = 1.0
        return marker

    def _tick(self):
        markers = MarkerArray()
        if self._lane and self._lane.detected:
            lane = self._marker(1, Marker.CUBE, 'base_footprint', (1.0, 0.8, 0.0))
            lane.pose.position.x, lane.pose.position.y = 0.75, self._lane.lateral_offset
            lane.pose.orientation.z = math.sin(self._lane.heading_error / 2.0)
            lane.pose.orientation.w = math.cos(self._lane.heading_error / 2.0)
            lane.scale.x, lane.scale.y, lane.scale.z = 1.5, 0.04, 0.02
            markers.markers.append(lane)
        if self._qr and self._qr.detected:
            qr = self._marker(2, Marker.CUBE, 'camera_front_link', (0.1, 0.9, 0.2))
            qr.pose.position.x, qr.pose.position.y = (
                self._qr.pose_in_camera.x, self._qr.pose_in_camera.y)
            qr.scale.x, qr.scale.y, qr.scale.z = 0.03, 0.24, 0.24
            markers.markers.append(qr)
            text = self._marker(3, Marker.TEXT_VIEW_FACING, 'base_footprint',
                                (1.0, 1.0, 1.0))
            text.pose.position.z = 1.4
            text.scale.z = 0.12
            text.text = ('QR=%s  lane=%.3fm yaw=%.3frad  longitudinal=%.3fm' %
                         (self._qr.data,
                          self._lane.lateral_offset if self._lane else float('nan'),
                          self._lane.heading_error if self._lane else float('nan'),
                          self._qr.pose_in_camera.x - 0.75))
            markers.markers.append(text)
        if self._truth:
            truth = self._marker(4, Marker.ARROW, 'odom', (0.0, 0.6, 1.0))
            truth.pose.position = self._truth.translation
            truth.pose.orientation = self._truth.rotation
            truth.scale.x, truth.scale.y, truth.scale.z = 0.6, 0.08, 0.08
            markers.markers.append(truth)
        self._pub.publish(markers)


def main():
    rclpy.init()
    node = Phase9Visualizer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
