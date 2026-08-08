#!/usr/bin/env python3
"""Fiziksel rota sapmasından RPP override önerisi üretir.

FollowPath aktifken /plan veya /received_global_plan ve
map→base_footprint pozunu örnekler; cross-track mean/p95/max hesaplar.
Opsiyonel /route/cross_track_error varsa onu da kaydeder.

Override yazmak için en az 50 geçerli pose örneği ve finite p95/max şarttır.
--yaz-override kullanılıyorsa --override-yol zorunludur; aksi halde dosyaya
dokunulmaz.

Örnek:
  ros2 run marco_navigation rpp_calibrate.py \\
    --sure 60 --limit-m 0.10 \\
    --cikti /tmp/marco_rpp_calib.json \\
    --yaz-override --override-yol src/marco_navigation/config/rpp_override_real.yaml
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone

import rclpy
import yaml
from nav_msgs.msg import Path
from rclpy.node import Node
from std_msgs.msg import Float32
from tf2_ros import Buffer, TransformListener

MIN_POSE_SAMPLES = 50
PATH_TOPICS = ("/plan", "/received_global_plan")


def _seg_dist(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return math.hypot(point[0] - a[0], point[1] - a[1])
    t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denom))
    return math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)


def _percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    x = (len(ordered) - 1) * q
    lo = int(x)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (x - lo)


def _path_points(path: Path):
    return [(p.pose.position.x, p.pose.position.y) for p in path.poses]


def _cross_track(point, pts):
    if len(pts) < 2:
        return None
    return min(_seg_dist(point, a, b) for a, b in zip(pts[:-1], pts[1:]))


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


class RppCalibrate(Node):
    def __init__(self):
        super().__init__("rpp_calibrate")
        self.path = None
        self.path_topic = None
        self.path_received = False
        self.topic_cte = []
        self.pose_cte = []
        self.tf = Buffer()
        self._tf_listener = TransformListener(self.tf, self)
        for topic in PATH_TOPICS:
            self.create_subscription(Path, topic, self._make_path_cb(topic), 10)
        self.create_subscription(Float32, "/route/cross_track_error", self._on_cte, 20)
        self.create_timer(0.1, self._sample_pose)

    def _make_path_cb(self, topic: str):
        def _cb(msg: Path):
            if not msg.poses:
                return
            self.path = msg
            self.path_topic = topic
            self.path_received = True

        return _cb

    def _on_cte(self, msg: Float32):
        if math.isfinite(msg.data):
            self.topic_cte.append(abs(float(msg.data)))

    def _sample_pose(self):
        if self.path is None or len(self.path.poses) < 2:
            return
        try:
            tf = self.tf.lookup_transform("map", "base_footprint", rclpy.time.Time())
        except Exception:
            return
        point = (tf.transform.translation.x, tf.transform.translation.y)
        cte = _cross_track(point, _path_points(self.path))
        if cte is not None and math.isfinite(cte):
            self.pose_cte.append(float(cte))


def _suggest(limit_m: float, p95: float, maximum: float) -> dict:
    """Sapmaya göre gerçek override için muhafazakâr öneri."""
    follow = {
        "desired_linear_vel": 0.35,
        "lookahead_dist": 0.50,
        "min_lookahead_dist": 0.25,
        "max_lookahead_dist": 0.75,
        "approach_velocity_scaling_dist": 0.55,
        "max_allowed_time_to_collision_up_to_carrot": 1.0,
        "regulated_linear_scaling_min_speed": 0.10,
        "cost_scaling_dist": 0.30,
    }
    smoother = {
        "max_velocity": [0.35, 0.0, 0.50],
        "min_velocity": [-0.25, 0.0, -0.50],
        "max_accel": [0.40, 0.0, 0.80],
        "max_decel": [-1.20, 0.0, -1.50],
    }
    ref = p95
    if ref > limit_m or maximum > limit_m:
        scale = max(0.55, limit_m / max(ref, maximum, 1e-3))
        follow["desired_linear_vel"] = round(0.35 * scale, 3)
        follow["lookahead_dist"] = round(max(0.35, 0.50 * scale), 3)
        follow["max_lookahead_dist"] = round(max(0.55, 0.75 * scale), 3)
        follow["max_allowed_time_to_collision_up_to_carrot"] = 1.2
        smoother["max_velocity"] = [follow["desired_linear_vel"], 0.0, 0.45]
        smoother["max_accel"] = [round(0.40 * scale, 3), 0.0, 0.70]
    elif ref < 0.5 * limit_m:
        follow["desired_linear_vel"] = 0.40
        follow["lookahead_dist"] = 0.55
        follow["max_lookahead_dist"] = 0.80
        smoother["max_velocity"] = [0.40, 0.0, 0.55]
        smoother["max_accel"] = [0.45, 0.0, 0.90]
    return {"FollowPath": follow, "velocity_smoother": smoother}


def _write_override(path: str, suggestion: dict, metrics: dict) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(path):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(path, f"{path}.bak-{stamp}")
    header = (
        "# Gerçek araç RPP farkları (rpp_calibrate.py ile yazıldı).\n"
        f"# tarih_utc: {metrics['timestamp_utc']}\n"
        f"# cross_track_p95_m: {metrics.get('pose_cross_track_p95_m')}\n"
        f"# cross_track_max_m: {metrics.get('pose_cross_track_max_m')}\n"
        f"# pose_samples: {metrics.get('pose_samples')}\n"
        f"# limit_m: {metrics.get('limit_m')}\n"
        f"# pass: {metrics.get('pass')}\n\n"
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(header)
        yaml.safe_dump(suggestion, handle, default_flow_style=False, sort_keys=False)


def _pack(samples):
    if not samples:
        return {"count": 0, "mean_m": None, "p95_m": None, "max_m": None}
    return {
        "count": len(samples),
        "mean_m": statistics.fmean(samples),
        "p95_m": _percentile(samples, 0.95),
        "max_m": max(samples),
    }


def _samples_ok(pose: dict) -> tuple[bool, str]:
    if pose["count"] < MIN_POSE_SAMPLES:
        return (
            False,
            f"yetersiz pose ornegi: {pose['count']} < {MIN_POSE_SAMPLES}",
        )
    if not _is_finite_number(pose["p95_m"]) or not _is_finite_number(pose["max_m"]):
        return False, "pose cross-track p95/max finite degil"
    return True, ""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sure", type=float, default=60.0, help="ornekleme suresi (s)")
    parser.add_argument("--limit-m", type=float, default=0.10, help="max sapma limiti")
    parser.add_argument("--cikti", default="/tmp/marco_rpp_calib.json")
    parser.add_argument(
        "--yaz-override",
        action="store_true",
        help="yeterli ornek varsa --override-yol dosyasina yazar (yedek alir)",
    )
    parser.add_argument(
        "--override-yol",
        default=None,
        help="--yaz-override ile zorunlu; yazilacak rpp_override_real.yaml yolu",
    )
    args = parser.parse_args(argv)

    if args.yaz_override and not args.override_yol:
        print(
            "HATA: --yaz-override icin --override-yol zorunlu "
            "(otomatik/sabit yol yok).",
            file=sys.stderr,
        )
        return 2

    rclpy.init(args=None)
    node = RppCalibrate()
    end = time.monotonic() + max(1.0, args.sure)
    try:
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        path_received = node.path_received
        path_topic = node.path_topic
        samples_pose = list(node.pose_cte)
        samples_topic = list(node.topic_cte)
        node.destroy_node()
        rclpy.shutdown()

    if not path_received:
        print(
            "HATA: aktif rota path topic'i gelmedi. "
            f"Dinlenen: {', '.join(PATH_TOPICS)}. "
            "FollowPath / NavigateToPose / route takibi ayakta ve rota yayinlaniyor mu?",
            file=sys.stderr,
        )
        return 2

    pose = _pack(samples_pose)
    topic = _pack(samples_topic)
    ok, reason = _samples_ok(pose)
    limit_pass = (
        ok
        and pose["max_m"] <= args.limit_m
    )
    suggestion = (
        _suggest(args.limit_m, float(pose["p95_m"]), float(pose["max_m"]))
        if ok
        else None
    )
    metrics = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": args.sure,
        "limit_m": args.limit_m,
        "path_topic": path_topic,
        "samples_ok": ok,
        "fail_reason": None if ok else reason,
        "pass": limit_pass,
        "pose_cross_track_mean_m": pose["mean_m"],
        "pose_cross_track_p95_m": pose["p95_m"],
        "pose_cross_track_max_m": pose["max_m"],
        "pose_samples": pose["count"],
        "min_pose_samples": MIN_POSE_SAMPLES,
        "topic_cross_track_mean_m": topic["mean_m"],
        "topic_cross_track_p95_m": topic["p95_m"],
        "topic_cross_track_max_m": topic["max_m"],
        "topic_samples": topic["count"],
        "suggested_override": suggestion,
        "override_written": False,
    }

    out_dir = os.path.dirname(args.cikti)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.cikti, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
        handle.write("\n")

    print(
        json.dumps(
            {
                "pass": metrics["pass"],
                "samples_ok": metrics["samples_ok"],
                "fail_reason": metrics["fail_reason"],
                "path_topic": metrics["path_topic"],
                "pose_cross_track_p95_m": metrics["pose_cross_track_p95_m"],
                "pose_cross_track_max_m": metrics["pose_cross_track_max_m"],
                "pose_samples": metrics["pose_samples"],
                "topic_samples": metrics["topic_samples"],
            },
            indent=2,
        )
    )
    print(f"kanit: {args.cikti}")

    if not ok:
        print(f"FAIL: {reason}; override yazilmadi.", file=sys.stderr)
        return 2

    if args.yaz_override:
        _write_override(args.override_yol, suggestion, metrics)
        metrics["override_written"] = True
        with open(args.cikti, "w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2)
            handle.write("\n")
        print(f"override yazildi: {args.override_yol}")

    return 0 if limit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
