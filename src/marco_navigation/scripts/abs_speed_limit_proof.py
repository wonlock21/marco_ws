#!/usr/bin/env python3
"""abs_speed_limit → /speed_limit → cmd zinciri kanıtı (Faz 12).

Statik (hazirlik kontrolu; tek basina kabul kaniti degildir):
  - navigate_route_wait.xml ilk ComputeRoute + ComputeAndTrackRoute + Parallel kullanır
  - route_server.yaml AdjustSpeedLimit + speed_tag=abs_speed_limit

Dinamik (--sure > 0, stack ayaktayken):
  - /speed_limit üzerinde percentage=false ve graf metadata aralığında mesaj
  - /cmd_vel_raw (yoksa /cmd_vel) |linear.x| o anki limitin üstüne çıkmaz

Örnek:
  ros2 run marco_navigation abs_speed_limit_proof.py \\
    --graf src/marco_navigation/graphs/demo_rota.geojson \\
    --sure 45 --cikti /tmp/marco_abs_speed_limit_proof.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import yaml


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def static_checks(nav_share: str) -> dict:
    bt = os.path.join(nav_share, "behavior_trees", "navigate_route_wait.xml")
    route_yaml = os.path.join(nav_share, "config", "route_server.yaml")
    errors = []
    tree = ET.parse(bt)
    tags = {el.tag.split("}")[-1] for el in tree.iter()}
    if "ComputeAndTrackRoute" not in tags:
        errors.append("BT ComputeAndTrackRoute kullanmiyor")
    if "ComputeRoute" not in tags:
        errors.append("BT FollowPath oncesi ilk ComputeRoute kullanmiyor")
    if "FollowPath" not in tags:
        errors.append("BT FollowPath yok")
    if "Parallel" not in tags:
        errors.append("BT Parallel yok (Track+Follow eşzamanlı olmalı)")

    params = yaml.safe_load(_read_text(route_yaml))
    rs = params["route_server"]["ros__parameters"]
    if "AdjustSpeedLimit" not in rs.get("operations", []):
        errors.append("route_server operations AdjustSpeedLimit icermiyor")
    adj = rs.get("AdjustSpeedLimit", {})
    if adj.get("speed_tag") != "abs_speed_limit":
        errors.append(f"speed_tag abs_speed_limit degil: {adj.get('speed_tag')}")
    topic = adj.get("speed_limit_topic", "")
    if topic not in ("speed_limit", "/speed_limit"):
        errors.append(f"speed_limit_topic beklenen degil: {topic}")

    return {
        "bt_path": bt,
        "route_server_yaml": route_yaml,
        "bt_has_compute_and_track_route": "ComputeAndTrackRoute" in tags,
        "bt_has_parallel": "Parallel" in tags,
        "bt_has_follow_path": "FollowPath" in tags,
        "adjust_speed_limit": adj,
        "errors": errors,
        "passed": not errors,
    }


def _graph_limits(graph_path: str) -> list[float]:
    with open(graph_path, encoding="utf-8") as handle:
        data = json.load(handle)
    limits = []
    for feature in data.get("features", []):
        if feature.get("geometry", {}).get("type") != "MultiLineString":
            continue
        meta = feature.get("properties", {}).get("metadata") or {}
        if "abs_speed_limit" in meta:
            limits.append(float(meta["abs_speed_limit"]))
    return limits


def runtime_checks(duration_s: float, cmd_topics: list[str], limits: list[float]) -> dict:
    import rclpy
    from geometry_msgs.msg import Twist
    from nav2_msgs.msg import SpeedLimit
    from rclpy.node import Node

    class Probe(Node):
        def __init__(self):
            super().__init__("abs_speed_limit_proof")
            self.speeds = []
            self.cmds = []
            self.create_subscription(SpeedLimit, "/speed_limit", self._on_speed, 20)
            for topic in cmd_topics:
                self.create_subscription(
                    Twist, topic, lambda m, t=topic: self._on_cmd(m, t), 50
                )

        def _on_speed(self, msg: SpeedLimit):
            self.speeds.append(
                {
                    "t": time.monotonic(),
                    "speed_limit": float(msg.speed_limit),
                    "percentage": bool(msg.percentage),
                }
            )

        def _on_cmd(self, msg: Twist, topic: str):
            self.cmds.append(
                {
                    "t": time.monotonic(),
                    "topic": topic,
                    "linear_x": float(msg.linear.x),
                    "angular_z": float(msg.angular.z),
                }
            )

    rclpy.init(args=None)
    node = Probe()
    end = time.monotonic() + max(0.0, duration_s)
    try:
        while rclpy.ok() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
    finally:
        speeds = list(node.speeds)
        cmds = list(node.cmds)
        node.destroy_node()
        rclpy.shutdown()

    abs_msgs = [s for s in speeds if not s["percentage"] and s["speed_limit"] > 0.0]
    meta_min = min(limits) if limits else None
    meta_max = max(limits) if limits else None
    unique_limits = sorted(set(limits))
    in_meta = [
        s
        for s in abs_msgs
        if any(abs(s["speed_limit"] - value) <= 1e-3 for value in unique_limits)
    ]

    violations = []
    if abs_msgs and cmds:
        # Her cmd için o ana kadarki son pozitif abs limit.
        for cmd in cmds:
            prior = [s for s in abs_msgs if s["t"] <= cmd["t"] + 0.05]
            if not prior:
                continue
            limit = prior[-1]["speed_limit"]
            if abs(cmd["linear_x"]) > limit + 0.02:
                violations.append(
                    {
                        "topic": cmd["topic"],
                        "linear_x": cmd["linear_x"],
                        "limit": limit,
                    }
                )

    errors = []
    if duration_s > 0 and not abs_msgs:
        errors.append("/speed_limit üzerinde abs (percentage=false, >0) mesaj yok")
    if limits and abs_msgs and len(in_meta) != len(abs_msgs):
        errors.append("gelen speed_limit graf abs_speed_limit değerlerinden biri değil")
    cmd_topic_used = sorted({c["topic"] for c in cmds})
    if duration_s > 0 and "/cmd_vel_raw" not in cmd_topic_used:
        errors.append("/cmd_vel_raw üzerinde örnek alınamadı")
    if violations:
        errors.append(f"cmd limit asimi: {len(violations)} ornek")

    return {
        "duration_s": duration_s,
        "speed_limit_messages": len(speeds),
        "abs_speed_limit_messages": len(abs_msgs),
        "abs_in_graph_metadata": len(in_meta),
        "graph_limit_min": meta_min,
        "graph_limit_max": meta_max,
        "cmd_samples": len(cmds),
        "cmd_topics_seen": cmd_topic_used,
        "cmd_limit_violations": violations[:20],
        "errors": errors,
        "passed": not errors,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nav-share",
        default="",
        help="marco_navigation share; bossa ament_index",
    )
    parser.add_argument("--graf", default="", help="GeoJSON (dinamik meta aralığı)")
    parser.add_argument("--sure", type=float, default=0.0, help="dinamik ornekleme s")
    parser.add_argument(
        "--cmd-topic",
        action="append",
        default=[],
        help="dinlenecek cmd topic (tekrarlanabilir); varsayilan /cmd_vel_raw ve /cmd_vel",
    )
    parser.add_argument("--cikti", default="/tmp/marco_abs_speed_limit_proof.json")
    args = parser.parse_args(argv)

    if args.nav_share:
        nav_share = args.nav_share
    else:
        from ament_index_python.packages import get_package_share_directory

        nav_share = get_package_share_directory("marco_navigation")

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "static": static_checks(nav_share),
    }

    if args.sure > 0:
        limits = _graph_limits(args.graf) if args.graf else []
        cmd_topics = args.cmd_topic or ["/cmd_vel_raw", "/cmd_vel"]
        report["runtime"] = runtime_checks(args.sure, cmd_topics, limits)
    else:
        report["runtime"] = {
            "skipped": True,
            "reason": "--sure 0; yalnız statik hazırlık kontrolü, kabul kanıtı değil",
            "passed": False,
            "errors": ["dinamik /speed_limit ve /cmd_vel_raw kanıtı çalıştırılmadı"],
        }

    report["passed"] = report["static"]["passed"] and report["runtime"].get(
        "passed", False
    )

    out_dir = os.path.dirname(args.cikti)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.cikti, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    print(json.dumps({"passed": report["passed"], "cikti": args.cikti,
                      "static_errors": report["static"]["errors"],
                      "runtime_errors": report["runtime"].get("errors", [])},
                     indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
