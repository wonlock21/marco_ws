import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data

class SelfScanFilter(Node):

    def __init__(self):
        super().__init__('self_scan_filter')

        # YDLIDAR'dan gelen HAM veri
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan_raw',
            self.scan_callback,
            qos_profile_sensor_data
        )

        # Sistemin geri kalanına gidecek TEMİZ veri
        self.publisher = self.create_publisher(
            LaserScan,
            '/scan',
            qos_profile_sensor_data
        )

        # Araç üzerindeki demirlerin LiDAR'a göre açıları
        self.blocked_regions = [
            (-180.0, -174.0),
            (-164.0, -154.0),
        ]

        self.get_logger().info(
            'LiDAR self-filter aktif: /scan_raw -> /scan'
        )

    def scan_callback(self, msg):

        filtered = LaserScan()

        filtered.header = msg.header

        filtered.angle_min = msg.angle_min
        filtered.angle_max = msg.angle_max
        filtered.angle_increment = msg.angle_increment

        filtered.time_increment = msg.time_increment
        filtered.scan_time = msg.scan_time

        filtered.range_min = msg.range_min
        filtered.range_max = msg.range_max

        filtered.ranges = list(msg.ranges)
        filtered.intensities = list(msg.intensities)

        for i, distance in enumerate(filtered.ranges):

            angle_rad = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle_rad)

            for min_angle, max_angle in self.blocked_regions:

                if min_angle <= angle_deg <= max_angle:
                    filtered.ranges[i] = float('inf')

                    if i < len(filtered.intensities):
                        filtered.intensities[i] = 0.0

                    break

        self.publisher.publish(filtered)


def main(args=None):

    rclpy.init(args=args)

    node = SelfScanFilter()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
