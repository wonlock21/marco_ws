#!/usr/bin/env python3
"""OpenCV kamerayi yerel agda MJPEG olarak yayinlar."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import threading
import time
from urllib.parse import parse_qs, urlparse

import cv2

from lane_tracking.lane_detector import LaneDetector


INDEX_HTML = """<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MarCO Kamera</title>
  <style>
    html,body{margin:0;background:#111;height:100%;display:grid;place-items:center}
    img{display:block;max-width:100vw;max-height:100vh;width:auto;height:auto}
  </style>
</head>
<body><img src="/stream.mjpg?token={token}" alt="MarCO canli kamera"></body>
</html>
"""


class Camera:
    def __init__(self, device, width, height, fps, quality, lane_overlay):
        self.quality = quality
        self.lane_detector = LaneDetector(use_opencl=True) if lane_overlay else None
        self.condition = threading.Condition()
        self.frame = None
        self.sequence = 0
        self.running = True

        source = int(device) if device.isdigit() else device
        self.capture = cv2.VideoCapture(source, cv2.CAP_V4L2)
        self.capture.set(
            cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.capture.isOpened():
            raise RuntimeError(f'Kamera acilamadi: {device}')

        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.05)
                continue
            if self.lane_detector is not None:
                height, width, _ = frame.shape
                center_x = width // 2
                cv2.line(
                    frame, (center_x, 0), (center_x, height),
                    (255, 0, 0), 2)
                found, error = self.lane_detector.process(frame, center_x)
                status = (
                    f'SERIT TAKIBI | HATA: {error:+.0f}px'
                    if found else 'SERIT BULUNAMADI'
                )
                color = (0, 255, 0) if found else (0, 0, 255)
                cv2.putText(
                    frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, color, 2)
            with self.condition:
                self.frame = frame
                self.sequence += 1
                self.condition.notify_all()

    def jpeg_after(self, previous_sequence):
        with self.condition:
            self.condition.wait_for(
                lambda: self.sequence != previous_sequence or not self.running,
                timeout=1.0,
            )
            if self.frame is None:
                return previous_sequence, None
            sequence = self.sequence
            frame = self.frame.copy()
        ok, encoded = cv2.imencode(
            '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        return sequence, encoded.tobytes() if ok else None

    def close(self):
        self.running = False
        with self.condition:
            self.condition.notify_all()
        self.thread.join(timeout=1.0)
        self.capture.release()


class RosCamera:
    def __init__(self, topic):
        import rclpy
        from sensor_msgs.msg import CompressedImage

        self.rclpy = rclpy
        self.condition = threading.Condition()
        self.frame = None
        self.sequence = 0
        self.running = True
        rclpy.init(args=None)
        self.node = rclpy.create_node('lane_web_stream')
        self.subscription = self.node.create_subscription(
            CompressedImage, topic, self._image_callback, 1)
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        self.rclpy.spin(self.node)

    def _image_callback(self, msg):
        with self.condition:
            self.frame = bytes(msg.data)
            self.sequence += 1
            self.condition.notify_all()

    def jpeg_after(self, previous_sequence):
        with self.condition:
            self.condition.wait_for(
                lambda: self.sequence != previous_sequence or not self.running,
                timeout=1.0,
            )
            return self.sequence, self.frame

    def close(self):
        self.running = False
        with self.condition:
            self.condition.notify_all()
        self.rclpy.shutdown()
        self.thread.join(timeout=1.0)
        self.node.destroy_node()


class StreamHandler(BaseHTTPRequestHandler):
    camera = None
    token = ''

    def do_GET(self):
        request = urlparse(self.path)
        supplied = parse_qs(request.query).get('token', [''])[0]
        if not hmac.compare_digest(supplied, self.token):
            self.send_error(403)
            return

        if request.path in ('/', '/index.html'):
            page = INDEX_HTML.replace('{token}', self.token).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(page)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(page)
            return
        if request.path != '/stream.mjpg':
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header(
            'Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        sequence = -1
        try:
            while True:
                sequence, jpeg = self.camera.jpeg_after(sequence)
                if jpeg is None:
                    continue
                self.wfile.write(b'--frame\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n')
                self.wfile.write(
                    f'Content-Length: {len(jpeg)}\r\n\r\n'.encode('ascii'))
                self.wfile.write(jpeg)
                self.wfile.write(b'\r\n')
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, _format, *_args):
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', default='/dev/video0')
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--token', required=True)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=360)
    parser.add_argument('--fps', type=float, default=25.0)
    parser.add_argument('--quality', type=int, default=80)
    parser.add_argument('--lane-overlay', action='store_true')
    parser.add_argument('--ros-topic')
    args = parser.parse_args()

    if args.ros_topic:
        camera = RosCamera(args.ros_topic)
    else:
        camera = Camera(
            args.device, args.width, args.height, args.fps, args.quality,
            args.lane_overlay)
    StreamHandler.camera = camera
    StreamHandler.token = args.token
    server = ThreadingHTTPServer((args.host, args.port), StreamHandler)
    print(f'Kamera yayini: http://{args.host}:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        camera.close()


if __name__ == '__main__':
    main()
