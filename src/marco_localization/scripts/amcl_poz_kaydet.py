#!/usr/bin/env python3
"""AMCL pozunu periyodik kaydeder — lokalizasyon dogrulugu icin ham veri.

Referans poz (ground truth) olmadan mutlak hata olculemez; bu arac yalnizca
/amcl_pose zaman serisini CSV'ye yazar. Sahada serit metre / bilinen noktalarla
karsilastirmak icin kullanilir.

Kullanim:
  ros2 run marco_localization amcl_poz_kaydet.py [--sure 60] [--cikti /tmp/amcl.csv]
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node


def yaw_of(q) -> float:
    """Quaternion'dan duzlemsel yaw (rad)."""
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


class Kayitci(Node):
    """ /amcl_pose abonesi; satirlari bellekte tutar. """

    def __init__(self) -> None:
        super().__init__("amcl_poz_kaydet")
        self.satirlar: list[tuple] = []
        self.create_subscription(
            PoseWithCovarianceStamped, "/amcl_pose", self._cb, 10
        )

    def _cb(self, msg: PoseWithCovarianceStamped) -> None:
        p = msg.pose.pose.position
        yaw = yaw_of(msg.pose.pose.orientation)
        # Kovaryans: xx=0, yy=7, yawyaw=35
        c = msg.pose.covariance
        self.satirlar.append(
            (
                msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
                p.x,
                p.y,
                yaw,
                math.degrees(yaw),
                math.sqrt(max(c[0], 0.0)),
                math.sqrt(max(c[7], 0.0)),
                math.sqrt(max(c[35], 0.0)),
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sure", type=float, default=60.0, help="saniye")
    parser.add_argument(
        "--cikti",
        default=str(Path.home() / "kayitlar" / f"amcl_{int(time.time())}.csv"),
    )
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    dugum = Kayitci()
    yol = Path(args.cikti)
    yol.parent.mkdir(parents=True, exist_ok=True)

    dugum.get_logger().info(
        f"{args.sure:.0f} sn boyunca /amcl_pose kaydediliyor → {yol}"
    )
    bitis = time.time() + args.sure
    try:
        while time.time() < bitis and rclpy.ok():
            rclpy.spin_once(dugum, timeout_sec=0.2)
    except KeyboardInterrupt:
        pass

    with yol.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["t", "x", "y", "yaw_rad", "yaw_deg", "std_x", "std_y", "std_yaw"]
        )
        w.writerows(dugum.satirlar)

    n = len(dugum.satirlar)
    dugum.get_logger().info(f"{n} ornek yazildi: {yol}")
    if n >= 2:
        x0, y0 = dugum.satirlar[0][1], dugum.satirlar[0][2]
        x1, y1 = dugum.satirlar[-1][1], dugum.satirlar[-1][2]
        dugum.get_logger().info(
            f"yer degisimi: dx={x1-x0:+.3f} dy={y1-y0:+.3f} "
            f"(|d|={math.hypot(x1-x0, y1-y0):.3f} m)"
        )

    dugum.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
