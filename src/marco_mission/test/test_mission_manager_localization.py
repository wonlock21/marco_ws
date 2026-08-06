"""Safe ROS-node test for mission manager localization health wiring."""

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.qos import (DurabilityPolicy, QoSCompatibility, QoSProfile,
                       ReliabilityPolicy, qos_check_compatible)
from sensor_msgs.msg import LaserScan

from marco_mission.mission_manager import MissionManager


def _transform(node, parent, child):
    transform = TransformStamped()
    transform.header.stamp = node.get_clock().now().to_msg()
    transform.header.frame_id = parent
    transform.child_frame_id = child
    transform.transform.rotation.w = 1.0
    node._tf_buffer.set_transform(transform, 'localization_health_test')


def test_mock_node_accepts_stationary_robot_health_inputs():
    """One AMCL pose remains valid while live TF, scan and odom continue."""
    rclpy.init()
    node = MissionManager()
    try:
        pose = PoseWithCovarianceStamped()
        pose.pose.pose.orientation.w = 1.0
        node._on_pose(pose)
        node._on_scan(LaserScan())
        node._on_odom(Odometry())
        _transform(node, 'map', 'odom')
        _transform(node, 'odom', 'base_footprint')

        assert node._localization_health().valid
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_scan_subscription_is_compatible_with_real_ydlidar_qos():
    """The real YDLidar publishes volatile scans with best-effort delivery."""
    rclpy.init()
    node = MissionManager()
    try:
        scan_subscription = next(
            subscription for subscription in node.subscriptions
            if subscription.topic_name == '/scan')
        ydlidar_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        compatibility, reason = qos_check_compatible(
            ydlidar_qos, scan_subscription.qos_profile)

        assert compatibility != QoSCompatibility.ERROR, reason
    finally:
        node.destroy_node()
        rclpy.shutdown()
