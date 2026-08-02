#!/usr/bin/env python3
"""Faz 3 odometri/EKF kabul ve geriye uyumlu UMBmark test araci."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import signal
import sys
import threading
import time

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.duration import Duration
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener

COMMAND_RATE = 50.0
LINEAR_LIMIT = 0.40
ANGULAR_LIMIT = 0.50


def normalize(angle: float) -> float:
    """Aciyi (-pi, pi] araligina getir."""
    return math.atan2(math.sin(angle), math.cos(angle))


def yaw_of(msg: Odometry) -> float:
    """Odometry quaternion'undan yaw dondur."""
    q = msg.pose.pose.orientation
    return math.atan2(2.0 * (q.w * q.z), 1.0 - 2.0 * q.z * q.z)


def finite_odom(msg: Odometry) -> bool:
    """Kabulde kullanilan odometri alanlarinin sonlu oldugunu denetle."""
    q = msg.pose.pose.orientation
    values = (
        msg.pose.pose.position.x, msg.pose.pose.position.y, q.x, q.y, q.z, q.w,
        msg.twist.twist.linear.x, msg.twist.twist.angular.z,
    )
    return all(math.isfinite(value) for value in values)


@dataclass
class Pose:
    """Duzlem pozu."""

    x: float
    y: float
    yaw: float

    @classmethod
    def from_msg(cls, msg: Odometry) -> "Pose":
        return cls(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw_of(msg))

    def relative(self, other: "Pose") -> tuple[float, float, float]:
        dx, dy = other.x - self.x, other.y - self.y
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return dx * c + dy * s, -dx * s + dy * c, normalize(other.yaw - self.yaw)


class OdometryCheck(Node):
    """Uc odometri akisini izler, path uretir ve guvenli manevra yaptirir."""

    TOPICS = {
        "raw": ("/odom", "/phase3/path/raw"),
        "filtered": ("/odometry/filtered", "/phase3/path/filtered"),
        "ground_truth": ("/base/ground_truth", "/phase3/path/ground_truth"),
    }

    def __init__(self) -> None:
        super().__init__("odometry_check")
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.messages: dict[str, Odometry | None] = {key: None for key in self.TOPICS}
        self.samples = {key: 0 for key in self.TOPICS}
        self.first_time: dict[str, float | None] = {key: None for key in self.TOPICS}
        self.last_time: dict[str, float | None] = {key: None for key in self.TOPICS}
        self.max_callback_gap = {key: 0.0 for key in self.TOPICS}
        self.max_stamp_age = {key: 0.0 for key in self.TOPICS}
        self.total_yaw = {key: 0.0 for key in self.TOPICS}
        self.last_yaw: dict[str, float | None] = {key: None for key in self.TOPICS}
        self.invalid = {key: 0 for key in self.TOPICS}
        self.frames_ok = {key: True for key in self.TOPICS}
        self.stop_requested = False
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        for key, (topic, _) in self.TOPICS.items():
            self.create_subscription(
                Odometry,
                topic,
                lambda msg, name=key: self._on_odom(name, msg),
                50,
            )

    def _on_odom(self, key: str, msg: Odometry) -> None:
        now = time.monotonic()
        self.samples[key] += 1
        self.first_time[key] = self.first_time[key] or now
        if self.last_time[key] is not None:
            self.max_callback_gap[key] = max(
                self.max_callback_gap[key], now - self.last_time[key]
            )
        self.last_time[key] = now
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        ros_now = self.get_clock().now().nanoseconds * 1e-9
        self.max_stamp_age[key] = max(self.max_stamp_age[key], max(0.0, ros_now - stamp))
        if not finite_odom(msg):
            self.invalid[key] += 1
            return
        expected_child = (
            "base_footprint_truth" if key == "ground_truth" else "base_footprint"
        )
        self.frames_ok[key] &= (
            msg.header.frame_id == "odom" and msg.child_frame_id == expected_child
        )
        yaw = yaw_of(msg)
        if self.last_yaw[key] is not None:
            self.total_yaw[key] += normalize(yaw - self.last_yaw[key])
        self.last_yaw[key] = yaw
        self.messages[key] = msg

    def pose(self, key: str) -> Pose:
        return Pose.from_msg(self.messages[key])

    def rates(self) -> dict[str, float]:
        result = {}
        for key in self.TOPICS:
            elapsed = (self.last_time[key] or 0.0) - (self.first_time[key] or 0.0)
            result[key] = (self.samples[key] - 1) / elapsed if elapsed > 0.0 else 0.0
        return result

    def timing_metrics(self) -> dict[str, dict[str, float | int]]:
        """Her odometri akisi icin alinan mesaj ve zamanlama sagligini raporla."""
        ros_now = self.get_clock().now().nanoseconds * 1e-9
        result = {}
        for key, msg in self.messages.items():
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            result[key] = {
                "received_messages": self.samples[key],
                "max_callback_gap_s": self.max_callback_gap[key],
                "max_stamp_age_s": self.max_stamp_age[key],
                "final_stamp_age_s": max(0.0, ros_now - stamp),
            }
        return result

    def wait_ready(self, timeout: float = 20.0) -> bool:
        """Topic, abone ve odom->base_footprint TF zincirini bekle."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self.stop_requested:
            topics = all(self.messages.values())
            subscriber = self.cmd_pub.get_subscription_count() > 0
            tf_ready = self.tf_buffer.can_transform(
                "odom", "base_footprint", rclpy.time.Time(), Duration(seconds=0.1)
            )
            if topics and subscriber and tf_ready:
                return True
            time.sleep(0.05)
        return False

    def publish_cmd(self, linear: float, angular: float) -> None:
        msg = Twist()
        msg.linear.x = max(-LINEAR_LIMIT, min(LINEAR_LIMIT, linear))
        msg.angular.z = max(-ANGULAR_LIMIT, min(ANGULAR_LIMIT, angular))
        self.cmd_pub.publish(msg)

    def halt(self, seconds: float = 0.7) -> None:
        """Motor rampasi ve Ctrl+C icin coklu sifir Twist yayinla."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and rclpy.ok():
            self.publish_cmd(0.0, 0.0)
            time.sleep(1.0 / COMMAND_RATE)

    def settle(self, seconds: float = 2.0) -> None:
        """Robot durduktan sonra EKF'in son olcumleri islemesini bekle."""
        self.halt(seconds)

    def drive(self, distance: float, timeout: float) -> bool:
        """Ham odometriye gore kapali cevrim duz sur."""
        start = self.pose("raw")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self.stop_requested:
            forward, _, heading = start.relative(self.pose("raw"))
            remaining = distance - forward
            if abs(remaining) < 0.004:
                self.halt()
                return True
            speed = math.copysign(min(0.35, max(0.04, abs(remaining))), remaining)
            self.publish_cmd(speed, max(-0.35, min(0.35, -2.0 * heading)))
            time.sleep(1.0 / COMMAND_RATE)
        self.halt()
        return False

    def turn(self, angle: float, timeout: float) -> bool:
        """Ham yaw farklarini biriktirerek kapali cevrim yerinde don."""
        start_total = self.total_yaw["raw"]
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self.stop_requested:
            remaining = angle - (self.total_yaw["raw"] - start_total)
            if abs(remaining) < math.radians(0.35):
                self.halt()
                return True
            speed = math.copysign(min(0.45, max(0.05, abs(remaining))), remaining)
            self.publish_cmd(0.0, speed)
            time.sleep(1.0 / COMMAND_RATE)
        self.halt()
        return False


def snapshot(node: OdometryCheck) -> tuple[dict[str, Pose], dict[str, float]]:
    return ({key: node.pose(key) for key in node.TOPICS}, dict(node.total_yaw))


def straight_test(node: OdometryCheck, distance: float) -> dict:
    print(f"\n[ASAMA 1] {distance:.2f} metre duz surus basliyor.", flush=True)
    poses0, _ = snapshot(node)
    completed = node.drive(distance, max(30.0, abs(distance) / 0.20 + 15.0))
    node.settle()
    poses1, _ = snapshot(node)
    rel = {key: poses0[key].relative(poses1[key]) for key in node.TOPICS}
    truth_distance = math.hypot(rel["ground_truth"][0], rel["ground_truth"][1])
    raw_error = math.hypot(
        rel["raw"][0] - rel["ground_truth"][0],
        rel["raw"][1] - rel["ground_truth"][1],
    )
    filtered_error = math.hypot(
        rel["filtered"][0] - rel["ground_truth"][0],
        rel["filtered"][1] - rel["ground_truth"][1],
    )
    percent = 100.0 * raw_error / truth_distance if truth_distance else math.inf
    result = {
        "completed": completed,
        "ground_truth_distance_m": truth_distance,
        "raw_distance_m": math.hypot(rel["raw"][0], rel["raw"][1]),
        "filtered_distance_m": math.hypot(rel["filtered"][0], rel["filtered"][1]),
        "raw_position_error_m": raw_error,
        "raw_position_error_percent": percent,
        "filtered_final_position_error_m": filtered_error,
        "raw_lateral_drift_m": rel["raw"][1],
        "filtered_lateral_drift_m": rel["filtered"][1],
        "pass": completed and percent < 2.0,
    }
    print(
        f"  Gercek={truth_distance:.4f} m, ham hata=%{percent:.3f}, "
        f"EKF son hata={filtered_error:.4f} m, yanal={rel['raw'][1]:+.4f} m"
    )
    print(f"  SONUC: {'PASS' if result['pass'] else 'FAIL'}", flush=True)
    return result


def rotation_test(node: OdometryCheck, degrees: float) -> dict:
    print(f"\n[ASAMA 2] {degrees:.1f} derece yerinde donus basliyor.", flush=True)
    poses0, yaw0 = snapshot(node)
    completed = node.turn(math.radians(degrees), max(30.0, abs(math.radians(degrees)) / 0.30 + 15.0))
    node.settle()
    poses1, yaw1 = snapshot(node)
    turns = {key: yaw1[key] - yaw0[key] for key in node.TOPICS}
    raw_error = abs(math.degrees(turns["raw"] - turns["ground_truth"]))
    filtered_error = abs(math.degrees(turns["filtered"] - turns["ground_truth"]))
    final_orientation_error = abs(math.degrees(normalize(
        poses0["filtered"].relative(poses1["filtered"])[2]
        - poses0["ground_truth"].relative(poses1["ground_truth"])[2]
    )))
    configured = 0.460
    correction = configured * turns["raw"] / turns["ground_truth"] if abs(turns["ground_truth"]) > 1e-9 else math.nan
    result = {
        "completed": completed,
        "ground_truth_turn_deg": math.degrees(turns["ground_truth"]),
        "raw_turn_deg": math.degrees(turns["raw"]),
        "filtered_turn_deg": math.degrees(turns["filtered"]),
        "raw_yaw_error_deg": raw_error,
        "filtered_yaw_error_deg": filtered_error,
        "filtered_final_orientation_error_deg": final_orientation_error,
        "suggested_wheel_separation_m": correction,
        "pass": (
            completed and raw_error < 5.0
            and filtered_error < 5.0 and final_orientation_error < 5.0
        ),
    }
    print(
        f"  Gercek={result['ground_truth_turn_deg']:.3f}°, ham hata={raw_error:.3f}°, "
        f"EKF birikimli hata={filtered_error:.3f}°, "
        f"EKF son yonelim hata={final_orientation_error:.3f}°"
    )
    if not result["pass"]:
        print(f"  Onerilen wheel_separation: {correction:.5f} m")
    print(f"  SONUC: {'PASS' if result['pass'] else 'FAIL'}", flush=True)
    return result


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", default="kabul", choices=["duz", "donus", "kabul", "hepsi"])
    parser.add_argument("--distance", "--mesafe", dest="distance", type=float, default=10.0)
    parser.add_argument("--turn-deg", dest="turn_deg", type=float, default=360.0)
    parser.add_argument("--tur", type=float, default=None, help="geriye uyumlu tur sayisi")
    parser.add_argument("--scenario", default="nominal")
    parser.add_argument("--result-file", default="/tmp/marco_phase3_acceptance.json")
    return parser.parse_known_args()


def main() -> None:
    args, ros_args = parse_args()
    if args.tur is not None:
        args.turn_deg = args.tur * 360.0
    rclpy.init(args=ros_args)
    node = OdometryCheck()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spinner = threading.Thread(target=executor.spin, daemon=True)
    spinner.start()
    signal.signal(signal.SIGINT, lambda *_: setattr(node, "stop_requested", True))
    result = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "scenario": args.scenario}
    exit_code = 1
    try:
        print("Topic'ler, /cmd_vel abonesi ve TF zinciri bekleniyor...", flush=True)
        if not node.wait_ready():
            raise RuntimeError("Hazirlik zaman asimi: /odom, EKF, ground truth, TF veya cmd_vel eksik")
        for remaining in range(5, 0, -1):
            print(f"Kabul testi {remaining} saniye sonra baslayacak...", flush=True)
            time.sleep(1.0)
        if args.test in ("duz", "kabul", "hepsi"):
            result["straight"] = straight_test(node, args.distance)
        if args.test in ("donus", "kabul", "hepsi"):
            result["rotation"] = rotation_test(node, args.turn_deg)
        node.halt(1.0)
        result["rates_hz"] = node.rates()
        result["timing"] = node.timing_metrics()
        result["frames_valid"] = node.frames_ok
        result["invalid_odometry_samples"] = node.invalid
        result["cmd_vel_final"] = {"linear_x": 0.0, "angular_z": 0.0, "zero_burst": True}
        checks = [value["pass"] for key, value in result.items() if key in ("straight", "rotation")]
        result["pass"] = bool(checks) and all(checks) and all(node.frames_ok.values()) and not any(node.invalid.values())
        result["ekf_note"] = (
            "Odom-only EKF bagimsiz sensor icermedigi icin sistematik encoder hatasini "
            "duzeltemez; yapay dogruluk iyilesmesi iddia edilmez."
        )
        exit_code = 0 if result["pass"] else 1
    except (RuntimeError, KeyboardInterrupt) as exc:
        result["error"] = str(exc) or "Ctrl+C"
        result["pass"] = False
        print(f"HATA: {result['error']}", flush=True)
    finally:
        node.halt(0.8)
        with open(args.result_file, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"Sonuc dosyasi: {args.result_file}", flush=True)
        executor.shutdown(timeout_sec=2.0)
        spinner.join(timeout=2.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
