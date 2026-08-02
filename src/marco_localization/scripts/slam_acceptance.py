#!/usr/bin/env python3
import json
import math
import os
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import LaserScan
from slam_toolbox.srv import SaveMap
from std_msgs.msg import Bool, String
from tf2_ros import Buffer, TransformListener


class SlamAcceptance(Node):
    def __init__(self):
        super().__init__('slam_acceptance')
        self.declare_parameter('result_path', '/tmp/marco_phase4_acceptance.json')
        self.declare_parameter('map_output', '/tmp/marco_phase4/marco_test')
        self.declare_parameter('save_map', True)
        self.declare_parameter('timeout', 240.0)
        self.declare_parameter('finish_grace', 4.0)
        self.start_wall = time.monotonic()
        self.first_map_wall = None
        self.map_msg = None
        self.initial_known = None
        self.max_known = 0
        self.scan_times = []
        self.odom_times = []
        self.map_updates = 0
        self.finite_scan_count = 0
        self.tf_drop_count = 0
        self.tf_seen = False
        self.last_cmd = Twist()
        self.drive_result = None
        self.drive_done_wall = None
        self.finished = False
        self.saving = False
        self.save_future = None
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.create_subscription(OccupancyGrid, '/map', self.map_cb, 2)
        self.create_subscription(LaserScan, '/scan', self.scan_cb,
                                 qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 20)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 20)
        self.create_subscription(Bool, '/slam_test/completed', self.done_cb, 1)
        self.status_pub = self.create_publisher(String, '/slam_test/status', 1)
        self.save_client = self.create_client(SaveMap, '/slam_toolbox/save_map')
        self.timer = self.create_timer(0.5, self.tick)
        self.get_logger().info('Faz 4 kabul metrikleri toplanıyor.')

    def map_cb(self, msg):
        if self.first_map_wall is None:
            self.first_map_wall = time.monotonic()
        self.map_msg = msg
        self.map_updates += 1
        known = sum(v >= 0 for v in msg.data)
        if self.initial_known is None:
            self.initial_known = known
        self.max_known = max(self.max_known, known)

    def scan_cb(self, msg):
        self.scan_times.append(time.monotonic())
        self.finite_scan_count += sum(math.isfinite(v) for v in msg.ranges)

    def odom_cb(self, _msg):
        self.odom_times.append(time.monotonic())

    def cmd_cb(self, msg):
        self.last_cmd = msg

    def done_cb(self, msg):
        self.drive_result = msg.data
        self.drive_done_wall = time.monotonic()

    @staticmethod
    def hz(times):
        if len(times) < 2 or times[-1] <= times[0]:
            return 0.0
        return (len(times) - 1) / (times[-1] - times[0])

    def tf_check(self):
        try:
            self.buffer.lookup_transform('map', 'odom', rclpy.time.Time(),
                                         timeout=Duration(seconds=0.05))
            self.tf_seen = True
        except Exception:
            if self.tf_seen:
                self.tf_drop_count += 1

    def start_save(self):
        if self.saving:
            return
        self.saving = True
        output = self.get_parameter('map_output').value
        os.makedirs(os.path.dirname(output), exist_ok=True)
        if not self.get_parameter('save_map').value:
            self.finalize()
            return
        if not self.save_client.wait_for_service(timeout_sec=5.0):
            self.finalize('map saver servisi yok')
            return
        request = SaveMap.Request()
        request.name.data = output
        self.save_future = self.save_client.call_async(request)
        self.save_future.add_done_callback(self.save_done)

    def save_done(self, future):
        try:
            response = future.result()
            if getattr(response, 'result', 1) not in (0, True):
                self.finalize('map saver servis sonucu basarisiz')
                return
        except Exception as exc:
            self.finalize('map saver exception: %s' % exc)
            return
        self.finalize()

    def tick(self):
        if self.finished:
            return
        self.tf_check()
        elapsed = time.monotonic() - self.start_wall
        if self.drive_done_wall is not None and not self.saving:
            if time.monotonic() - self.drive_done_wall >= self.get_parameter(
                    'finish_grace').value:
                self.start_save()
        elif elapsed >= self.get_parameter('timeout').value and not self.saving:
            self.start_save()

    def finalize(self, extra_failure=None):
        if self.finished:
            return
        self.finished = True
        elapsed = time.monotonic() - self.start_wall
        data = list(self.map_msg.data) if self.map_msg else []
        known = sum(v >= 0 for v in data)
        unknown = sum(v < 0 for v in data)
        free = sum(0 <= v < 50 for v in data)
        occupied = sum(v >= 50 for v in data)
        width = self.map_msg.info.width if self.map_msg else 0
        height = self.map_msg.info.height if self.map_msg else 0
        resolution = self.map_msg.info.resolution if self.map_msg else 0.0
        output = self.get_parameter('map_output').value
        yaml_path = output + '.yaml'
        pgm_path = output + '.pgm'
        stopped = abs(self.last_cmd.linear.x) < 1e-4 and abs(
            self.last_cmd.angular.z) < 1e-4
        failures = []
        if self.map_msg is None:
            failures.append('/map gelmedi')
        if not (0.049 <= resolution <= 0.051):
            failures.append('harita cozunurlugu 0.05 m degil')
        if known < 1000 or free == 0 or occupied == 0:
            failures.append('harita yeterli bos/dolu bilinen hucre icermiyor')
        growth = self.max_known - (self.initial_known or 0)
        if growth <= 0:
            failures.append('bilinen alan buyumedi')
        if self.hz(self.scan_times) < 5.0:
            failures.append('/scan hizi dusuk veya yok')
        if self.hz(self.odom_times) < 10.0:
            failures.append('/odom hizi dusuk veya yok')
        if not self.tf_seen:
            failures.append('map -> odom TF yok')
        if self.drive_result is not True:
            failures.append('otomatik surus tamamlanmadi')
        if not stopped:
            failures.append('son /cmd_vel sifir degil')
        if self.get_parameter('save_map').value:
            if not (os.path.getsize(yaml_path) > 0 if os.path.isfile(yaml_path) else False):
                failures.append('kayitli YAML yok/bos')
            if not (os.path.getsize(pgm_path) > 0 if os.path.isfile(pgm_path) else False):
                failures.append('kayitli PGM yok/bos')
        if extra_failure:
            failures.append(extra_failure)
        result = {
            'pass': not failures, 'duration_sec': round(elapsed, 3),
            'first_map_sec': (round(self.first_map_wall - self.start_wall, 3)
                              if self.first_map_wall else None),
            'map_resolution': resolution, 'width': width, 'height': height,
            'known_cells': known, 'unknown_cells': unknown,
            'free_cells': free, 'occupied_cells': occupied,
            'known_ratio': known / len(data) if data else 0.0,
            'known_growth': growth, 'scan_hz': self.hz(self.scan_times),
            'odom_hz': self.hz(self.odom_times), 'map_updates': self.map_updates,
            'map_to_odom_available': self.tf_seen,
            'tf_drop_count': self.tf_drop_count,
            'finite_scan_count': self.finite_scan_count,
            'final_cmd_vel': {'linear_x': self.last_cmd.linear.x,
                              'angular_z': self.last_cmd.angular.z},
            'map_yaml_path': yaml_path if os.path.isfile(yaml_path) else '',
            'map_image_path': pgm_path if os.path.isfile(pgm_path) else '',
            'failure_reasons': failures,
            'thresholds': {'occupied_cell_min': 50, 'free_cell_max_exclusive': 50,
                           'min_known_cells': 1000, 'min_scan_hz': 5.0,
                           'min_odom_hz': 10.0},
        }
        path = self.get_parameter('result_path').value
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        self.status_pub.publish(String(data=json.dumps(result, ensure_ascii=False)))
        if result['pass']:
            self.get_logger().info('Faz 4 simülasyon kabulü PASS: ' + path)
            self.get_logger().info('Faz 4 simülasyon haritalama testi tamamlandı. '
                                   'Robot durduruldu; harita RViz incelemesi için '
                                   'açık bırakıldı. Ctrl+C ile kapatabilirsiniz.')
        else:
            self.get_logger().error('Faz 4 simülasyon kabulü FAIL: ' + '; '.join(failures))


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = SlamAcceptance()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, RuntimeError):
        pass
    finally:
        try:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
        except (KeyboardInterrupt, RuntimeError):
            # Tolerate a second launch SIGINT during rclpy entity teardown.
            pass


if __name__ == '__main__':
    main()
