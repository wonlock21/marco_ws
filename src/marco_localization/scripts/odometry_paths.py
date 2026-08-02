#!/usr/bin/env python3
"""Faz 3 odometri izlerini kabul metriklerinden ayri process'te yayinlar."""

from collections import deque
import math
import time

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

PATH_LIMIT = 500
SAMPLE_PERIOD = 0.1
PUBLISH_PERIOD = 0.5
DISTANCE_STEP = 0.01
YAW_STEP = math.radians(0.5)


def yaw_of(msg: Odometry) -> float:
    q = msg.pose.pose.orientation
    return math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)


def angle_delta(current: float, previous: float) -> float:
    return math.atan2(math.sin(current - previous), math.cos(current - previous))


class OdometryPaths(Node):
    """Uc odometri akisini seyrek ve sinirli Path mesajlarina cevirir."""

    TOPICS = {
        "raw": ("/odom", "/phase3/path/raw"),
        "filtered": ("/odometry/filtered", "/phase3/path/filtered"),
        "ground_truth": ("/base/ground_truth", "/phase3/path/ground_truth"),
    }

    def __init__(self) -> None:
        super().__init__("odometry_paths")
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.paths = {key: deque(maxlen=PATH_LIMIT) for key in self.TOPICS}
        self.last_sample = {key: 0.0 for key in self.TOPICS}
        self.last_pose = {key: None for key in self.TOPICS}
        self.path_pubs = {
            key: self.create_publisher(Path, path_topic, qos)
            for key, (_, path_topic) in self.TOPICS.items()
        }
        for key, (topic, _) in self.TOPICS.items():
            self.create_subscription(
                Odometry, topic, lambda msg, name=key: self._on_odom(name, msg), 10
            )
        self.create_timer(PUBLISH_PERIOD, self._publish)

    def _on_odom(self, key: str, msg: Odometry) -> None:
        now = time.monotonic()
        current = (msg.pose.pose.position.x, msg.pose.pose.position.y, yaw_of(msg))
        previous = self.last_pose[key]
        elapsed = now - self.last_sample[key]
        moved = previous is None or math.hypot(
            current[0] - previous[0], current[1] - previous[1]
        ) >= DISTANCE_STEP
        turned = previous is None or abs(angle_delta(current[2], previous[2])) >= YAW_STEP
        if previous is not None and (elapsed < SAMPLE_PERIOD or not (moved or turned)):
            return
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose
        self.paths[key].append(pose)
        self.last_pose[key] = current
        self.last_sample[key] = now

    def _publish(self) -> None:
        stamp = self.get_clock().now().to_msg()
        for key, poses in self.paths.items():
            if not poses:
                continue
            path = Path()
            path.header.stamp = stamp
            path.header.frame_id = "odom"
            path.poses = list(poses)
            self.path_pubs[key].publish(path)


def main() -> None:
    rclpy.init()
    node = OdometryPaths()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
