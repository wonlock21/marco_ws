"""Safe ROS-node test for mission manager localization health wiring."""

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.qos import (DurabilityPolicy, QoSCompatibility, QoSProfile,
                       ReliabilityPolicy, qos_check_compatible)
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

from marco_msgs.msg import QrDetection, QrReaderDetection

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
        assert node._plc_auto_start is False
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


def test_scan_subscription_is_compatible_with_real_lidar_qos():
    """The real LiDAR publishes volatile scans with best-effort delivery."""
    rclpy.init()
    node = MissionManager()
    try:
        scan_subscription = next(
            subscription for subscription in node.subscriptions
            if subscription.topic_name == '/scan')
        lidar_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        compatibility, reason = qos_check_compatible(
            lidar_qos, scan_subscription.qos_profile)

        assert compatibility != QoSCompatibility.ERROR, reason
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_qr_gui_telemetry_keeps_full_detection_contract():
    """Retain QR pose, confidence and camera for RobotStatus fields."""
    rclpy.init()
    node = MissionManager()
    try:
        detection = QrDetection()
        detection.detected = True
        detection.data = 'A1'
        detection.pose_in_camera.x = 1.2
        detection.pose_in_camera.y = -0.1
        detection.pose_in_camera.theta = 0.2
        detection.confidence = 0.91
        detection.camera_frame = 'front'
        node._on_qr(detection)

        assert node._last_qr == 'A1'
        assert node._last_qr_detected
        assert node._last_qr_pose.x == 1.2
        assert node._last_qr_confidence == 0.91
        assert node._last_qr_camera == 'front'
        assert node._last_qr_seen > 0.0
        assert node._station_phase == node._STATION_IDLE
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_serial_qr_is_telemetry_only_without_camera_pose():
    """A physical reader payload updates telemetry but not station flow."""
    rclpy.init()
    node = MissionManager()
    try:
        node._begin_station_approach('A1')
        phase = node._station_phase
        detection = QrReaderDetection()
        detection.header.stamp = node.get_clock().now().to_msg()
        detection.qr_id = 'ALIM1'
        detection.valid = True
        detection.confidence = 1.0
        detection.reader_frame = 'qr_reader_front'

        node._on_qr_reader(detection)

        assert node._station_phase == phase
        assert node._last_qr == 'ALIM1'
        assert node._last_qr_detected
        assert node._last_qr_pose.x == 0.0
        assert node._last_qr_camera == 'qr_reader_front'
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_wrong_and_expected_qr_do_not_trigger_station_state():
    """Neither a wrong nor expected QR can advance the station flow."""
    rclpy.init()
    node = MissionManager()
    try:
        node._begin_station_approach('A3')
        phase = node._station_phase
        for value in ('YANLIS', 'q4'):
            detection = QrDetection()
            detection.detected = True
            detection.data = value
            detection.confidence = 1.0
            detection.camera_frame = 'front'
            node._on_qr(detection)
            assert node._station_phase == phase
            assert node._last_qr == value
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_production_mission_requires_fresh_stm32_communication():
    """A task cannot start from a missing, false or stale UART health state."""
    rclpy.init()
    node = MissionManager()
    try:
        assert not node._base_communication_healthy()

        node._on_base_communication(Bool(data=True))
        assert node._base_communication_healthy()

        node._base_communication_seen -= node._base_communication_timeout + 0.1
        assert not node._base_communication_healthy()
    finally:
        node.destroy_node()
        rclpy.shutdown()
