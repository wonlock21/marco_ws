#!/usr/bin/env python3
"""Evidence-oriented simulation AMCL acceptance; never uses /odom as truth."""

import json
import math
import os
import statistics
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from lifecycle_msgs.srv import GetState
from nav2_msgs.msg import ParticleCloud
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, QoSProfile, ReliabilityPolicy,
                       qos_profile_sensor_data)
from ros_gz_interfaces.msg import WorldStatistics
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformListener


def angle(q):
    return math.atan2(2*(q.w*q.z + q.x*q.y), 1-2*(q.y*q.y + q.z*q.z))


def wrap(v): return math.atan2(math.sin(v), math.cos(v))


def percentile(values, q):
    if not values: return None
    s = sorted(values); k = (len(s)-1)*q; lo = int(k); hi = min(lo+1, len(s)-1)
    return s[lo] + (s[hi]-s[lo])*(k-lo)


def metric(values):
    return {'mean': statistics.fmean(values) if values else None,
            'p95': percentile(values, .95), 'max': max(values) if values else None,
            'final': values[-1] if values else None, 'samples': len(values)}


class Acceptance(Node):
    def __init__(self):
        super().__init__('amcl_acceptance')
        self.declare_parameter('result_path', '/tmp/marco_phase5_acceptance.json')
        self.declare_parameter('timeout', 300.0)
        self.declare_parameter('require_drive', True)
        self.start = time.monotonic(); self.first_initial = None; self.first_amcl = None
        self.converged = None; self.stable_since = None; self.finished = False
        self.map = None; self.truth = None; self.last_cmd = Twist(); self.drive_done = None
        self.drive_done_wall = None; self.particles = 0; self.covariances = []
        self.times = {k: [] for k in ('scan', 'odom', 'amcl', 'tf')}
        self.ages = {k: [] for k in ('scan', 'odom', 'amcl', 'tf')}
        self.pos = []; self.yaw = []; self.moving_pos = []; self.moving_yaw = []
        self.stopped_pos = []; self.stopped_yaw = []
        self.tf_exact_ok = 0; self.tf_drop = 0; self.tf_extrapolation = 0
        self.tf_exact_seen = False
        self.laser_tf_seen = False
        self.dynamic_edges = {}; self.rtf = []; self.lifecycle = {}
        self.buffer = Buffer(cache_time=Duration(seconds=20)); self.listener = TransformListener(self.buffer, self)
        sensor = qos_profile_sensor_data
        transient = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                               reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, '/map', self.map_cb, transient)
        self.create_subscription(LaserScan, '/scan', lambda m: self.timed('scan', m), sensor)
        self.create_subscription(Odometry, '/odom', lambda m: self.timed('odom', m), 30)
        self.create_subscription(Odometry, '/ground_truth/odom', self.truth_cb, 30)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_cb, 30)
        self.create_subscription(ParticleCloud, '/particle_cloud', self.cloud_cb, sensor)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 20)
        self.create_subscription(Bool, '/amcl_test/completed', self.done_cb, 1)
        self.create_subscription(PoseWithCovarianceStamped, '/initialpose', self.initial_cb, 10)
        self.create_subscription(Bool, '/amcl_test/initial_pose_sent', self.initial_event_cb,
                                 transient)
        self.create_subscription(TFMessage, '/tf', self.tf_cb, 100)
        self.create_subscription(WorldStatistics, '/world/marco_test/stats', self.stats_cb, 10)
        self.stop_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.lifecycle_clients = {n: self.create_client(GetState, '/%s/get_state' % n)
                                  for n in ('map_server', 'amcl')}
        self.pending = {}
        self.timer = self.create_timer(.5, self.tick)

    def msg_age(self, msg):
        stamp = rclpy.time.Time.from_msg(msg.header.stamp)
        return max(0.0, (self.get_clock().now()-stamp).nanoseconds/1e9)

    def timed(self, key, msg):
        self.times[key].append(time.monotonic()); self.ages[key].append(self.msg_age(msg))
        if key == 'scan':
            try:
                self.buffer.lookup_transform('base_footprint', msg.header.frame_id,
                                             rclpy.time.Time.from_msg(msg.header.stamp),
                                             timeout=Duration(seconds=.02))
                self.laser_tf_seen = True
            except Exception:
                pass

    def map_cb(self, msg): self.map = msg
    def truth_cb(self, msg): self.truth = msg
    def initial_cb(self, _msg):
        if self.first_initial is None: self.first_initial = time.monotonic()-self.start
    def initial_event_cb(self, msg):
        if msg.data and self.first_initial is None:
            self.first_initial = time.monotonic()-self.start
    def cloud_cb(self, msg): self.particles = len(msg.particles)
    def cmd_cb(self, msg): self.last_cmd = msg
    def done_cb(self, msg):
        self.drive_done = msg.data; self.drive_done_wall = time.monotonic()

    def stats_cb(self, msg):
        self.rtf.append(msg.real_time_factor)

    def tf_cb(self, msg):
        now = time.monotonic(); self.times['tf'].append(now)
        for t in msg.transforms:
            edge = '%s->%s' % (t.header.frame_id, t.child_frame_id)
            self.dynamic_edges[edge] = self.dynamic_edges.get(edge, 0)+1
            self.ages['tf'].append(self.msg_age(t))

    def amcl_cb(self, msg):
        self.timed('amcl', msg)
        if self.first_amcl is None: self.first_amcl = time.monotonic()-self.start
        self.covariances.append({'position': msg.pose.covariance[0]+msg.pose.covariance[7],
                                 'yaw': msg.pose.covariance[35]})
        if self.truth is None: return
        p, g = msg.pose.pose, self.truth.pose.pose
        pe = math.hypot(p.position.x-g.position.x, p.position.y-g.position.y)
        ye = abs(wrap(angle(p.orientation)-angle(g.orientation)))
        self.pos.append(pe); self.yaw.append(ye)
        moving = abs(self.last_cmd.linear.x) > .01 or abs(self.last_cmd.angular.z) > .01
        (self.moving_pos if moving else self.stopped_pos).append(pe)
        (self.moving_yaw if moving else self.stopped_yaw).append(ye)
        if pe < .05 and ye < math.radians(3):
            if self.stable_since is None: self.stable_since = time.monotonic()
            if self.converged is None and time.monotonic()-self.stable_since >= 2:
                self.converged = time.monotonic()-self.start
        else: self.stable_since = None
        try:
            stamp = rclpy.time.Time.from_msg(msg.header.stamp)
            self.buffer.lookup_transform('map', 'odom', stamp, timeout=Duration(seconds=.03))
            self.tf_exact_ok += 1
            self.tf_exact_seen = True
        except Exception as exc:
            # The first /amcl_pose and map->odom can arrive in either DDS order.
            # Drops are meaningful only after the exact-time chain was established.
            if self.tf_exact_seen:
                self.tf_drop += 1
                if 'extrapolation' in str(exc).lower(): self.tf_extrapolation += 1

    def lifecycle_poll(self):
        for name, client in self.lifecycle_clients.items():
            if name in self.pending or not client.service_is_ready(): continue
            future = client.call_async(GetState.Request()); self.pending[name] = future
            future.add_done_callback(lambda f, n=name: self.lifecycle_done(n, f))

    def lifecycle_done(self, name, future):
        try: self.lifecycle[name] = future.result().current_state.label
        except Exception: self.lifecycle[name] = 'error'
        self.pending.pop(name, None)

    @staticmethod
    def hz(v): return (len(v)-1)/(v[-1]-v[0]) if len(v)>1 and v[-1]>v[0] else 0.0

    def process_metrics(self):
        found = []
        for entry in os.listdir('/proc'):
            if not entry.isdigit(): continue
            try:
                cmd = open('/proc/%s/cmdline' % entry, 'rb').read().replace(b'\0', b' ').decode()
                if '/nav2_amcl/amcl' in cmd or cmd.rstrip().endswith(' amcl'):
                    stat = open('/proc/%s/stat' % entry).read().split()
                    found.append({'pid': int(entry), 'cpu_ticks': int(stat[13])+int(stat[14]),
                                  'rss_mb': int(stat[23])*os.sysconf('SC_PAGE_SIZE')/1048576})
            except (OSError, ValueError): pass
        return found

    def tick(self):
        if self.finished: return
        self.lifecycle_poll(); elapsed = time.monotonic()-self.start
        if self.drive_done_wall and time.monotonic()-self.drive_done_wall > 5: self.finalize()
        elif elapsed > self.get_parameter('timeout').value: self.finalize('acceptance timeout')

    def finalize(self, extra=None):
        if self.finished: return
        self.finished = True
        zero = Twist()
        for _ in range(10): self.stop_pub.publish(zero)
        stopped = abs(self.last_cmd.linear.x)<1e-4 and abs(self.last_cmd.angular.z)<1e-4
        pm, ym = metric(self.pos), metric(self.yaw)
        failures = []
        if self.map is None or not self.map.data: failures.append('/map missing or invalid')
        for n in ('map_server','amcl'):
            if self.lifecycle.get(n) != 'active': failures.append('%s lifecycle is not active' % n)
        for key, minimum in [('scan',10),('odom',20),('amcl',1)]:
            if self.hz(self.times[key]) < minimum: failures.append('/%s rate missing/low' % key)
        if not self.particles: failures.append('/particle_cloud missing')
        if self.times['scan'] and not self.laser_tf_seen:
            failures.append('laser_link TF missing')
        if self.first_initial is None: failures.append('initial pose was never observed')
        if self.converged is None: failures.append('AMCL did not converge')
        if self.tf_exact_ok == 0: failures.append('map->odom exact timestamp unavailable')
        if self.tf_drop or self.tf_extrapolation: failures.append('TF drop/extrapolation nonzero')
        if self.get_parameter('require_drive').value and self.drive_done is not True:
            failures.append('controlled drive did not complete')
        if not stopped: failures.append('final cmd_vel is not zero')
        if pm['p95'] is None or pm['p95'] >= .05: failures.append('p95 position >= 0.05 m')
        if ym['p95'] is None or ym['p95'] >= math.radians(3): failures.append('p95 yaw >= 3 deg')
        if pm['final'] is None or pm['final'] >= .05: failures.append('final position >= 0.05 m')
        if ym['final'] is None or ym['final'] >= math.radians(3): failures.append('final yaw >= 3 deg')
        if extra: failures.append(extra)
        publishers = {}
        for topic in ('/tf','/scan','/odom','/amcl_pose','/particle_cloud'):
            publishers[topic] = sorted('%s/%s' % (i.node_namespace.strip('/'), i.node_name)
                                       for i in self.get_publishers_info_by_topic(topic))
        nodes = sorted(name for name, _namespace in self.get_node_names_and_namespaces())
        if 'slam_toolbox' in nodes:
            failures.append('multiple map->odom owner: slam_toolbox is running')
        if len(publishers['/tf']) > 3:
            failures.append('unexpected additional dynamic TF publisher')
        result = {'pass': not failures, 'failure_reasons': failures,
                  'lifecycle_states': self.lifecycle, 'topic_hz': {k:self.hz(v) for k,v in self.times.items()},
                  'timestamp_age_sec': {k:metric(v) for k,v in self.ages.items()},
                  'tf': {'dynamic_edges': self.dynamic_edges, 'publishers': publishers['/tf'],
                         'exact_timestamp_successes': self.tf_exact_ok,
                         'drop_count': self.tf_drop, 'extrapolation_count': self.tf_extrapolation},
                  'initial_pose_sec': self.first_initial, 'first_amcl_pose_sec': self.first_amcl,
                  'convergence_sec': self.converged, 'position_error_m': pm,
                  'yaw_error_rad': ym, 'yaw_error_deg': {k:(math.degrees(v) if v is not None else None)
                                                        for k,v in ym.items() if k!='samples'} | {'samples':ym['samples']},
                  'moving_position_error_m': metric(self.moving_pos),
                  'moving_yaw_error_rad': metric(self.moving_yaw),
                  'stopped_position_error_m': metric(self.stopped_pos),
                  'stopped_yaw_error_rad': metric(self.stopped_yaw),
                  'covariance': {'initial': self.covariances[0] if self.covariances else None,
                                 'final': self.covariances[-1] if self.covariances else None},
                  'particle_count': self.particles, 'gazebo_rtf': metric(self.rtf),
                  'amcl_process': self.process_metrics(), 'topic_publishers': publishers,
                  'ground_truth_source': 'Gazebo world dynamic_pose/info model pose; map<-world fixed transform [0,0,0]',
                  'map_world_transform': {'x':0.0,'y':0.0,'yaw':0.0},
                  'final_cmd_vel': {'linear_x':self.last_cmd.linear.x,'angular_z':self.last_cmd.angular.z}}
        path = self.get_parameter('result_path').value; os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path,'w',encoding='utf-8') as f: json.dump(result,f,indent=2,ensure_ascii=False)
        log = self.get_logger().info if result['pass'] else self.get_logger().error
        log('Faz 5 simulation acceptance %s: %s' % ('PASS' if result['pass'] else 'FAIL', path))


def main(args=None):
    rclpy.init(args=args); node=Acceptance()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        if not node.finished and rclpy.ok(): node.finalize('interrupted')
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == '__main__': main()
