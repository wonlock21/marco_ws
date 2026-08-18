"""Mask robot self-occlusion rays without clearing space behind the robot."""

import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def parse_blocked_regions(values):
    """Convert a flat degree array into validated ``(min, max)`` pairs."""
    if len(values) % 2:
        raise ValueError('blocked_regions_deg cift sayida deger icermeli')

    regions = []
    for index in range(0, len(values), 2):
        minimum = float(values[index])
        maximum = float(values[index + 1])
        if not math.isfinite(minimum) or not math.isfinite(maximum):
            raise ValueError('blocked_regions_deg sonlu acilar icermeli')
        if minimum > maximum:
            raise ValueError(
                'blocked_regions_deg icinde minimum maksimumdan buyuk olamaz'
            )
        regions.append((minimum, maximum))
    return regions


class SelfScanFilter(Node):
    """Replace configured self-occluded LiDAR rays with invalid measurements."""

    def __init__(self):
        super().__init__('self_scan_filter')

        # Flat array: [min_deg_0, max_deg_0, min_deg_1, max_deg_1, ...].
        # Yeni 45 cm montajda lift direklerinin acilari /scan_raw ile yeniden
        # olculene kadar bos kalir; eski montaja ait acilar kullanilmaz.
        blocked_parameter = self.declare_parameter(
            'blocked_regions_deg', Parameter.Type.DOUBLE_ARRAY
        )
        self.blocked_regions = parse_blocked_regions(
            blocked_parameter.value or []
        )

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

        self.get_logger().info(
            'LiDAR self-filter aktif: /scan_raw -> /scan | '
            f'kapali bolge sayisi={len(self.blocked_regions)}'
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

        for i, _distance in enumerate(filtered.ranges):

            angle_rad = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle_rad)

            for min_angle, max_angle in self.blocked_regions:

                if min_angle <= angle_deg <= max_angle:
                    # NaN LaserScan icin gecersiz/olcumsuz isindir. +inf
                    # kullanmak Nav2 obstacle layer'da inf_is_valid=true iken
                    # isin boyunca ray-clearing yaparak liftin arkasini kesin
                    # bos gosterebilirdi; self-occlusion icin bu guvenli degil.
                    filtered.ranges[i] = float('nan')

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
