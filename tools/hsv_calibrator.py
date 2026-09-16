#!/usr/bin/env python3
"""Kameradan veya mevcut ROS goruntu yayinindan tiklamali HSV kalibrasyonu."""

import argparse

import cv2
import numpy as np


HUE_PERIOD = 180


def hue_intervals(hues, margin=5):
    """Ornekleri kapsayan en kisa dairesel OpenCV hue araliklarini dondur."""
    values = sorted({int(value) % HUE_PERIOD for value in hues})
    if not values:
        return []
    if len(values) == 1:
        arc_start = values[0]
        arc_length = 0
    else:
        gaps = [
            (values[(index + 1) % len(values)] - values[index]) % HUE_PERIOD
            for index in range(len(values))
        ]
        gap_index = int(np.argmax(gaps))
        arc_start = values[(gap_index + 1) % len(values)]
        arc_length = (
            values[gap_index] - arc_start) % HUE_PERIOD

    start = arc_start - int(margin)
    width = arc_length + 2 * int(margin)
    if width >= HUE_PERIOD - 1:
        return [(0, HUE_PERIOD - 1)]
    end = start + width
    start_mod = start % HUE_PERIOD
    end_mod = end % HUE_PERIOD
    if start // HUE_PERIOD == end // HUE_PERIOD:
        return [(start_mod, end_mod)]
    return [(start_mod, HUE_PERIOD - 1), (0, end_mod)]


def suggested_bounds(samples, hue_margin=5, saturation_margin=25,
                     value_margin=25):
    if not samples:
        return [], 0, 255, 0, 255
    sample_array = np.asarray(samples, dtype=np.int16)
    intervals = hue_intervals(sample_array[:, 0], hue_margin)
    sat_min = max(0, int(sample_array[:, 1].min()) - saturation_margin)
    sat_max = min(255, int(sample_array[:, 1].max()) + saturation_margin)
    val_min = max(0, int(sample_array[:, 2].min()) - value_margin)
    val_max = min(255, int(sample_array[:, 2].max()) + value_margin)
    return intervals, sat_min, sat_max, val_min, val_max


def build_mask(hsv_frame, bounds):
    intervals, sat_min, sat_max, val_min, val_max = bounds
    mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
    for hue_min, hue_max in intervals:
        part = cv2.inRange(
            hsv_frame,
            np.array([hue_min, sat_min, val_min], dtype=np.uint8),
            np.array([hue_max, sat_max, val_max], dtype=np.uint8),
        )
        mask = cv2.bitwise_or(mask, part)
    return mask


def format_bounds(bounds):
    intervals, sat_min, sat_max, val_min, val_max = bounds
    hue_text = ' U '.join(f'[{low},{high}]' for low, high in intervals)
    return f'H={hue_text} S=[{sat_min},{sat_max}] V=[{val_min},{val_max}]'


class HsvCalibrator:
    def __init__(self, roi_radius, hue_margin, saturation_margin, value_margin):
        self.roi_radius = max(0, int(roi_radius))
        self.hue_margin = max(0, int(hue_margin))
        self.saturation_margin = max(0, int(saturation_margin))
        self.value_margin = max(0, int(value_margin))
        self.frame = None
        self.hsv_frame = None
        self.samples = []
        self.points = []

    @property
    def bounds(self):
        return suggested_bounds(
            self.samples, self.hue_margin,
            self.saturation_margin, self.value_margin)

    def mouse_callback(self, event, x, y, _flags, _userdata):
        if event == cv2.EVENT_RBUTTONDOWN:
            self.clear()
            return
        if event != cv2.EVENT_LBUTTONDOWN or self.hsv_frame is None:
            return
        height, width = self.hsv_frame.shape[:2]
        if not (0 <= x < width and 0 <= y < height):
            return
        radius = self.roi_radius
        x0, x1 = max(0, x - radius), min(width, x + radius + 1)
        y0, y1 = max(0, y - radius), min(height, y + radius + 1)
        median = np.median(
            self.hsv_frame[y0:y1, x0:x1].reshape(-1, 3), axis=0)
        sample = tuple(int(round(value)) for value in median)
        self.samples.append(sample)
        self.points.append((x, y, sample))
        print(f'Ornek {len(self.samples)}: x={x} y={y} HSV={sample}')
        self.print_suggestion()

    def clear(self):
        self.samples.clear()
        self.points.clear()
        print('Ornekler temizlendi.')

    def print_suggestion(self):
        if self.samples:
            print(f'Onerilen maske: {format_bounds(self.bounds)}')

    def draw(self, frame):
        display = frame.copy()
        for index, (x, y, sample) in enumerate(self.points, start=1):
            cv2.circle(display, (x, y), 6, (0, 255, 0), 2)
            cv2.putText(
                display, f'{index}: H{sample[0]} S{sample[1]} V{sample[2]}',
                (min(x + 8, max(0, display.shape[1] - 180)), max(18, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.43, (0, 255, 0), 1,
                cv2.LINE_AA)
        if self.samples:
            cv2.putText(
                display, format_bounds(self.bounds), (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1,
                cv2.LINE_AA)
        return display


def open_camera(args):
    source = int(args.device) if args.device.isdigit() else args.device
    capture = cv2.VideoCapture(source, cv2.CAP_V4L2)
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*args.fourcc))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    capture.set(cv2.CAP_PROP_FPS, args.fps)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not capture.isOpened():
        raise RuntimeError(
            f'Kamera acilamadi: {args.device}. Kamerayi kullanan node varsa kapat.')
    return capture


class RosCompressedSource:
    """Kamerayi tekrar acmadan mevcut CompressedImage yayini alir."""

    def __init__(self, topic):
        import rclpy
        from rclpy.qos import (
            QoSDurabilityPolicy,
            QoSHistoryPolicy,
            QoSProfile,
            QoSReliabilityPolicy,
        )
        from sensor_msgs.msg import CompressedImage

        self.rclpy = rclpy
        self.frame = None
        rclpy.init(args=None)
        self.node = rclpy.create_node('hsv_calibrator')
        sensor_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        self.subscription = self.node.create_subscription(
            CompressedImage, topic, self._on_image, sensor_qos)
        self.node.get_logger().info(f'Goruntu bekleniyor: {topic}')

    def _on_image(self, message):
        encoded = np.frombuffer(message.data, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is not None:
            self.frame = frame

    def read(self):
        self.rclpy.spin_once(self.node, timeout_sec=0.05)
        return None if self.frame is None else self.frame.copy()

    def close(self):
        self.node.destroy_node()
        if self.rclpy.ok():
            self.rclpy.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description='Tiklamali canli HSV kalibrasyonu')
    parser.add_argument('--device', default='/dev/marco_front_camera')
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--fps', type=float, default=25.0)
    parser.add_argument('--fourcc', default='MJPG')
    parser.add_argument(
        '--ros-topic',
        help='Mevcut CompressedImage yayini. Verilirse kamera aygiti acilmaz.')
    parser.add_argument('--roi-radius', type=int, default=4)
    parser.add_argument('--hue-margin', type=int, default=5)
    parser.add_argument('--saturation-margin', type=int, default=25)
    parser.add_argument('--value-margin', type=int, default=25)
    args = parser.parse_args()

    if not args.ros_topic and len(args.fourcc) != 4:
        parser.error('--fourcc tam olarak dort karakter olmali')

    calibrator = HsvCalibrator(
        args.roi_radius, args.hue_margin,
        args.saturation_margin, args.value_margin)
    capture = None if args.ros_topic else open_camera(args)
    ros_source = RosCompressedSource(args.ros_topic) if args.ros_topic else None
    window = 'HSV Kalibrasyon'
    mask_window = 'Onerilen HSV Maskesi'
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.namedWindow(mask_window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, calibrator.mouse_callback)
    print('Sol tik: ornek ekle | Sag tik/C: temizle | S: yazdir | Q/ESC: cik')

    try:
        while True:
            if ros_source is not None:
                frame = ros_source.read()
                if frame is None:
                    key = cv2.waitKey(1) & 0xFF
                    if key in (27, ord('q')):
                        break
                    continue
            else:
                ok, frame = capture.read()
                if not ok or frame is None:
                    print('Kamera karesi okunamadi.')
                    break
            calibrator.frame = frame
            calibrator.hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = build_mask(calibrator.hsv_frame, calibrator.bounds)
            cv2.imshow(window, calibrator.draw(frame))
            cv2.imshow(mask_window, mask)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                break
            if key == ord('c'):
                calibrator.clear()
            elif key == ord('s'):
                calibrator.print_suggestion()
    finally:
        if capture is not None:
            capture.release()
        if ros_source is not None:
            ros_source.close()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
