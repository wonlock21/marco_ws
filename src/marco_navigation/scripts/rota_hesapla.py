#!/usr/bin/env python3
"""ComputeRoute smoke test — dugum ID veya pose ile rota hesapla.

Ornek:
  ros2 run marco_navigation rota_hesapla.py --start 0 --goal 8
  ros2 run marco_navigation rota_hesapla.py --sx -2 --sy -2 --gx 2 --gy 2
"""

from __future__ import annotations

import argparse
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputeRoute
from rclpy.action import ActionClient
from rclpy.node import Node


class RotaHesapla(Node):
    def __init__(self) -> None:
        super().__init__("rota_hesapla")
        self._client = ActionClient(self, ComputeRoute, "compute_route")

    def hesapla(
        self,
        *,
        start_id: int | None,
        goal_id: int | None,
        start_xy: tuple[float, float] | None,
        goal_xy: tuple[float, float] | None,
    ) -> int:
        if not self._client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("compute_route action server yok")
            return 2

        goal = ComputeRoute.Goal()
        if start_id is not None and goal_id is not None:
            goal.start_id = start_id
            goal.goal_id = goal_id
            goal.use_poses = False
            goal.use_start = True
        else:
            assert start_xy is not None and goal_xy is not None
            goal.use_poses = True
            goal.use_start = True
            goal.start = self._pose(start_xy[0], start_xy[1])
            goal.goal = self._pose(goal_xy[0], goal_xy[1])

        future = self._client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        handle = future.result()
        if handle is None or not handle.accepted:
            self.get_logger().error("hedef reddedildi")
            return 3

        result_fut = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_fut)
        wrapped = result_fut.result()
        if wrapped is None:
            self.get_logger().error("sonuc yok")
            return 4

        result = wrapped.result
        route = result.route
        path = result.path
        node_ids = [n.nodeid for n in route.nodes]
        edge_ids = [e.edgeid for e in route.edges]
        length = 0.0
        if len(path.poses) >= 2:
            for a, b in zip(path.poses[:-1], path.poses[1:]):
                dx = b.pose.position.x - a.pose.position.x
                dy = b.pose.position.y - a.pose.position.y
                length += (dx * dx + dy * dy) ** 0.5

        self.get_logger().info(
            f"SUCCEEDED cost={route.route_cost:.3f} "
            f"nodes={node_ids} edges={edge_ids} "
            f"path_poses={len(path.poses)} length≈{length:.2f}m "
            f"plan_time={result.planning_time.sec}."
            f"{result.planning_time.nanosec // 1_000_000:03d}s"
        )
        return 0

    @staticmethod
    def _pose(x: float, y: float) -> PoseStamped:
        p = PoseStamped()
        p.header.frame_id = "map"
        p.pose.position.x = x
        p.pose.position.y = y
        p.pose.orientation.w = 1.0
        return p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=None, help="baslangic dugum id")
    parser.add_argument("--goal", type=int, default=None, help="hedef dugum id")
    parser.add_argument("--sx", type=float, default=None)
    parser.add_argument("--sy", type=float, default=None)
    parser.add_argument("--gx", type=float, default=None)
    parser.add_argument("--gy", type=float, default=None)
    args = parser.parse_args(argv)

    use_ids = args.start is not None and args.goal is not None
    use_poses = all(v is not None for v in (args.sx, args.sy, args.gx, args.gy))
    if use_ids == use_poses:
        parser.error("Ya --start/--goal ya da --sx/--sy/--gx/--gy ver")

    rclpy.init()
    node = RotaHesapla()
    try:
        code = node.hesapla(
            start_id=args.start if use_ids else None,
            goal_id=args.goal if use_ids else None,
            start_xy=(args.sx, args.sy) if use_poses else None,
            goal_xy=(args.gx, args.gy) if use_poses else None,
        )
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return code


if __name__ == "__main__":
    sys.exit(main())
