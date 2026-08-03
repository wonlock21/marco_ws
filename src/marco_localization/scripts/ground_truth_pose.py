#!/usr/bin/env python3
"""Convert Gazebo's model world pose to measurement-only ROS odometry/paths."""

import math

import rclpy
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from tf2_msgs.msg import TFMessage


class GroundTruthPose(Node):
    def __init__(self):
        super().__init__('ground_truth_pose')
        self.declare_parameter('map_world_x', 0.0)
        self.declare_parameter('map_world_y', 0.0)
        self.declare_parameter('map_world_yaw', 0.0)
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.sub = self.create_subscription(
            TFMessage, '/world/marco_test/dynamic_pose/info', self.cb, qos)
        self.odom_pub = self.create_publisher(Odometry, '/ground_truth/odom', 10)
        self.gt_path_pub = self.create_publisher(Path, '/ground_truth/path', qos)
        self.amcl_path_pub = self.create_publisher(Path, '/amcl/path', qos)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_cb, 10)
        self.gt_path = Path()
        self.amcl_path = Path()

    def append_path(self, path, pub, stamp, pose):
        item = PoseStamped()
        item.header.stamp = stamp
        item.header.frame_id = 'map'
        item.pose = pose
        path.header = item.header
        path.poses.append(item)
        if len(path.poses) > 1200:
            del path.poses[:200]
        pub.publish(path)

    def cb(self, msg):
        if not msg.transforms:
            return
        # The robot-scoped PosePublisher emits exactly the model world pose.
        candidates = [t for t in msg.transforms
                      if t.child_frame_id == 'marco' or
                      t.child_frame_id.endswith('/marco')]
        if not candidates:
            return
        tf = candidates[0]
        x0 = self.get_parameter('map_world_x').value
        y0 = self.get_parameter('map_world_y').value
        yaw0 = self.get_parameter('map_world_yaw').value
        c, s = math.cos(yaw0), math.sin(yaw0)
        wx, wy = tf.transform.translation.x, tf.transform.translation.y
        odom = Odometry()
        odom.header.stamp = tf.header.stamp
        if odom.header.stamp.sec == 0 and odom.header.stamp.nanosec == 0:
            odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'map'
        odom.child_frame_id = 'base_footprint_ground_truth'
        odom.pose.pose.position.x = x0 + c * wx - s * wy
        odom.pose.pose.position.y = y0 + s * wx + c * wy
        q = tf.transform.rotation
        extra = yaw0 * 0.5
        odom.pose.pose.orientation.x = q.x * math.cos(extra) - q.y * math.sin(extra)
        odom.pose.pose.orientation.y = q.x * math.sin(extra) + q.y * math.cos(extra)
        odom.pose.pose.orientation.z = q.z * math.cos(extra) + q.w * math.sin(extra)
        odom.pose.pose.orientation.w = q.w * math.cos(extra) - q.z * math.sin(extra)
        self.odom_pub.publish(odom)
        self.append_path(self.gt_path, self.gt_path_pub, odom.header.stamp, odom.pose.pose)

    def amcl_cb(self, msg):
        self.append_path(self.amcl_path, self.amcl_path_pub,
                         msg.header.stamp, msg.pose.pose)


def main(args=None):
    rclpy.init(args=args)
    node = GroundTruthPose()
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
