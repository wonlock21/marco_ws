"""Open the front V4L2 camera once and publish raw ROS images."""

import threading

import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from sensor_msgs.msg import CompressedImage


class FrontCameraPublisher(Node):
    """OpenCV-backed publisher for cameras that are unstable with usb_cam."""

    def __init__(self):
        super().__init__('front_camera_publisher')
        self.declare_parameter('video_device', '/dev/marco_front_camera')
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        self.declare_parameter('framerate', 25.0)
        self.declare_parameter('fourcc', 'MJPG')
        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter(
            'compressed_topic', '/camera/image_raw/compressed')
        self.declare_parameter('jpeg_quality', 75)
        self.declare_parameter('reconnect_interval', 1.0)

        self.device = str(self.get_parameter('video_device').value)
        self.width = int(self.get_parameter('image_width').value)
        self.height = int(self.get_parameter('image_height').value)
        self.framerate = float(self.get_parameter('framerate').value)
        self.fourcc = str(self.get_parameter('fourcc').value).upper()
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.jpeg_quality = max(
            1, min(100, int(self.get_parameter('jpeg_quality').value)))
        self.reconnect_interval = max(
            0.2, float(self.get_parameter('reconnect_interval').value))

        if len(self.fourcc) != 4:
            raise ValueError('fourcc tam olarak 4 karakter olmali')
        if self.width <= 0 or self.height <= 0 or self.framerate <= 0.0:
            raise ValueError('kamera boyutu ve FPS pozitif olmali')

        topic = str(self.get_parameter('compressed_topic').value)
        image_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        self.publisher = self.create_publisher(
            CompressedImage, topic, image_qos)
        self.capture = None
        self.capture_lock = threading.Lock()
        self.latest_encoded = None
        self.latest_width = 0
        self.latest_height = 0
        self.latest_sequence = 0
        self.published_sequence = 0
        self.published_frames = 0
        self.read_failure_reported = False
        self.stop_event = threading.Event()
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            name='front-camera-capture',
            daemon=True,
        )
        self.capture_thread.start()
        self.timer = self.create_timer(1.0 / self.framerate, self._on_timer)
        self.get_logger().info(
            f'On kamera yayincisi hazir: {self.device} -> {topic} '
            f'({self.width}x{self.height} {self.fourcc} '
            f'{self.framerate:.1f} FPS, JPEG kalite={self.jpeg_quality})')

    def _open_camera(self):
        self._release_camera()

        source = int(self.device) if self.device.isdigit() else self.device
        capture = cv2.VideoCapture(source, cv2.CAP_V4L2)
        # Konftel CAM10 icin format, boyuttan once secilmelidir.
        capture.set(
            cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.fourcc))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        capture.set(cv2.CAP_PROP_FPS, self.framerate)
        if not capture.isOpened():
            capture.release()
            self.get_logger().warning(
                f'Kamera acilamadi: {self.device}; yeniden denenecek',
                throttle_duration_sec=5.0)
            return False
        self.capture = capture
        self.read_failure_reported = False
        self.get_logger().info(f'Kamera acildi: {self.device}')
        return True

    def _capture_loop(self):
        while not self.stop_event.is_set():
            if self.capture is None and not self._open_camera():
                self.stop_event.wait(self.reconnect_interval)
                continue
            ok, frame = self.capture.read()
            if not ok or frame is None:
                if not self.read_failure_reported:
                    self.read_failure_reported = True
                    self.get_logger().warning(
                        'Kamera karesi okunamadi; kamera yeniden acilacak')
                self._release_camera()
                self.stop_event.wait(self.reconnect_interval)
                continue
            encoded_ok, encoded = cv2.imencode(
                '.jpg', frame,
                [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            if not encoded_ok:
                self.get_logger().warning(
                    'Kamera karesi JPEG olarak kodlanamadi',
                    throttle_duration_sec=2.0)
                continue
            with self.capture_lock:
                self.latest_encoded = encoded.tobytes()
                self.latest_width = int(frame.shape[1])
                self.latest_height = int(frame.shape[0])
                self.latest_sequence += 1
        self._release_camera()

    def _on_timer(self):
        with self.capture_lock:
            if self.latest_sequence == self.published_sequence:
                return
            encoded = self.latest_encoded
            width = self.latest_width
            height = self.latest_height
            self.published_sequence = self.latest_sequence
        if encoded is None:
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.format = 'jpeg'
        msg.data = encoded
        self.publisher.publish(msg)
        self.published_frames += 1
        if self.published_frames == 1:
            self.get_logger().info(
                f'Ilk kamera karesi yayinlandi: '
                f'{width}x{height} JPEG')

    def _release_camera(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def destroy_node(self):
        self.stop_event.set()
        if self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        self._release_camera()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = FrontCameraPublisher()
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
