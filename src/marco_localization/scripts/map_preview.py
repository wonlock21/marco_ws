#!/usr/bin/env python3
"""OccupancyGrid'i PNG'ye, harita pozunu ekran pikseline cevirir."""

import binascii
import math
import struct
import zlib

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from marco_msgs.msg import MapPixelPose
from nav_msgs.msg import MapMetaData, OccupancyGrid
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from sensor_msgs.msg import CompressedImage
from tf2_ros import Buffer, TransformException, TransformListener


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    crc = binascii.crc32(body) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", crc)


def occupancy_grid_to_png(width: int, height: int, data) -> bytes:
    """ROS OccupancyGrid verisini ustten baslayan 8-bit gri PNG'ye cevir."""
    expected = width * height
    if width <= 0 or height <= 0 or len(data) != expected:
        raise ValueError(
            f"gecersiz harita boyutu: {width}x{height}, veri={len(data)}"
        )

    rows = bytearray()
    for source_y in range(height - 1, -1, -1):
        rows.append(0)  # PNG filter: None
        offset = source_y * width
        for value in data[offset:offset + width]:
            if value < 0:
                gray = 205
            else:
                occupancy = min(100, int(value))
                gray = 254 - round(occupancy * 254 / 100)
            rows.append(gray)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=3))
        + _png_chunk(b"IEND", b"")
    )


def _yaw_of(orientation) -> float:
    siny = 2.0 * (
        orientation.w * orientation.z + orientation.x * orientation.y
    )
    cosy = 1.0 - 2.0 * (
        orientation.y * orientation.y + orientation.z * orientation.z
    )
    return math.atan2(siny, cosy)


def pose_to_pixel(info: MapMetaData, pose) -> tuple[float, float, float, bool]:
    """Map pozunu PNG pikseline ve ekran yonune cevir."""
    if info.resolution <= 0.0 or info.width == 0 or info.height == 0:
        raise ValueError("harita metadata'si gecersiz")

    origin = info.origin
    origin_yaw = _yaw_of(origin.orientation)
    dx = pose.position.x - origin.position.x
    dy = pose.position.y - origin.position.y

    cosine = math.cos(origin_yaw)
    sine = math.sin(origin_yaw)
    map_x = cosine * dx + sine * dy
    map_y = -sine * dx + cosine * dy

    pixel_x = map_x / info.resolution
    pixel_y = float(info.height - 1) - map_y / info.resolution
    relative_yaw = _yaw_of(pose.orientation) - origin_yaw
    screen_yaw = math.atan2(-math.sin(relative_yaw), math.cos(relative_yaw))
    inside = (
        0.0 <= pixel_x < float(info.width)
        and 0.0 <= pixel_y < float(info.height)
    )
    return pixel_x, pixel_y, screen_yaw, inside


class MapPreview(Node):
    def __init__(self) -> None:
        super().__init__("map_preview")
        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("slam_pose_topic", "/pose")
        self.declare_parameter("amcl_pose_topic", "/amcl_pose")
        self.declare_parameter("tf_pose_source", "tf")

        latched = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._image_pub = self.create_publisher(
            CompressedImage, "/map_preview/compressed", latched
        )
        self._metadata_pub = self.create_publisher(
            MapMetaData, "/map_preview/metadata", latched
        )
        self._pixel_pub = self.create_publisher(
            MapPixelPose, "/map_preview/robot_pixel", latched
        )

        self._info = None
        self._latest_pose = None
        self._latest_source = ""
        self._map_count = 0
        self._tf = Buffer()
        self._tf_listener = TransformListener(self._tf, self)

        self.create_subscription(
            OccupancyGrid,
            str(self.get_parameter("map_topic").value),
            self._on_map,
            latched,
        )
        self.create_subscription(
            PoseWithCovarianceStamped,
            str(self.get_parameter("slam_pose_topic").value),
            lambda msg: self._on_pose(msg, "slam_toolbox"),
            10,
        )
        self.create_subscription(
            PoseWithCovarianceStamped,
            str(self.get_parameter("amcl_pose_topic").value),
            lambda msg: self._on_pose(msg, "amcl"),
            10,
        )
        # AMCL, robot hareket esiklerini asmadiginda yeni /amcl_pose mesaji
        # yayinlamayabilir. Flutter sayfasi da ilk mesajdan sonra acilabilir.
        # Guncel ve kanonik robot pozunu TF'den duzenli okuyarak pikseli
        # yeniden yayinla; transient-local QoS son degeri gec aboneye saklar.
        self.create_timer(0.2, self._publish_tf_pixel)

    def _on_map(self, msg: OccupancyGrid) -> None:
        try:
            png = occupancy_grid_to_png(msg.info.width, msg.info.height, msg.data)
        except ValueError as error:
            self.get_logger().error(str(error))
            return

        self._info = msg.info
        image = CompressedImage()
        image.header = msg.header
        image.format = "png"
        image.data = png
        self._image_pub.publish(image)
        self._metadata_pub.publish(msg.info)
        self._map_count += 1
        if self._map_count == 1:
            self.get_logger().info(
                f"Harita onizlemesi hazir: {msg.info.width}x{msg.info.height}"
            )
        self._publish_pixel()

    def _on_pose(self, msg: PoseWithCovarianceStamped, source: str) -> None:
        if msg.header.frame_id and msg.header.frame_id != "map":
            self.get_logger().warning(
                f"{source} pozu map cercevesinde degil: {msg.header.frame_id}"
            )
            return
        self._latest_pose = msg
        self._latest_source = source
        self._publish_pixel()

    def _publish_tf_pixel(self) -> None:
        if self._info is None:
            return
        try:
            transform = self._tf.lookup_transform(
                "map", "base_footprint", rclpy.time.Time()
            )
        except TransformException:
            return

        pose = PoseWithCovarianceStamped()
        pose.header = transform.header
        pose.header.frame_id = "map"
        # Bu mesaj TF'nin olculme zamani degil, pikselin yayinlanma zamanidir.
        # Flutter tazelik kontrolu yaparken hareketsiz pozu eski sanmamalidir.
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.pose.position.x = transform.transform.translation.x
        pose.pose.pose.position.y = transform.transform.translation.y
        pose.pose.pose.position.z = transform.transform.translation.z
        pose.pose.pose.orientation = transform.transform.rotation
        self._latest_pose = pose
        self._latest_source = str(self.get_parameter("tf_pose_source").value)
        self._publish_pixel()

    def _publish_pixel(self) -> None:
        if self._info is None or self._latest_pose is None:
            return
        try:
            x, y, yaw, inside = pose_to_pixel(
                self._info, self._latest_pose.pose.pose
            )
        except ValueError as error:
            self.get_logger().error(str(error))
            return

        output = MapPixelPose()
        output.header = self._latest_pose.header
        output.pixel_x = float(x)
        output.pixel_y = float(y)
        output.screen_yaw = float(yaw)
        output.map_width = self._info.width
        output.map_height = self._info.height
        output.inside_map = inside
        output.source = self._latest_source
        self._pixel_pub.publish(output)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MapPreview()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
