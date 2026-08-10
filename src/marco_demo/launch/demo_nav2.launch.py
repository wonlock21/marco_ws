"""Mevcut AMCL/harita ustunde yalniz Nav2 hareket sunucularini baslatir."""

import importlib.util
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import SetRemap


def _compose_module(navigation_share):
    path = os.path.join(navigation_share, "launch", "rpp_compose.py")
    spec = importlib.util.spec_from_file_location("marco_demo_rpp_compose", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_launch_description() -> LaunchDescription:
    navigation_share = get_package_share_directory("marco_navigation")
    nav2_share = get_package_share_directory("nav2_bringup")
    params_source = os.path.join(
        navigation_share, "config", "nav2_params.yaml"
    )
    params_file = "/tmp/marco_demo_nav2_params.yaml"
    behavior_tree = os.path.join(
        navigation_share, "behavior_trees", "navigate_to_pose_wait.xml"
    )
    _compose_module(navigation_share).compose_nav2_params_file(
        nav_share=navigation_share,
        profile="real",
        params_src=params_source,
        params_dst=params_file,
        text_replacements=[
            (
                'default_nav_to_pose_bt_xml: ""',
                f'default_nav_to_pose_bt_xml: "{behavior_tree}"',
            ),
            # Demo hareketinde dinamik engeli collision_monitor durdurur.
            # Kisa Nav2 tahmini action'i erken abort etmeden footprint'i korur.
            ("simulate_ahead_time: 2.0", "simulate_ahead_time: 0.5"),
            ("max_rotational_vel: 0.6", "max_rotational_vel: 0.3"),
            # Demo davranislari icin dinamik engelin tek sahibi disaridaki
            # collision_monitor'dur. Yerel costmap ayni LiDAR'i ikinci kez
            # yorumlayip Spin/DriveOnHeading'i erken abort etmesin.
            (
                "      obstacle_layer:\n"
                "        plugin: \"nav2_costmap_2d::ObstacleLayer\"\n"
                "        enabled: True",
                "      obstacle_layer:\n"
                "        plugin: \"nav2_costmap_2d::ObstacleLayer\"\n"
                "        enabled: False",
            ),
        ],
    )

    nav2 = GroupAction(actions=[
        SetRemap(src="cmd_vel", dst="cmd_vel_nav"),
        SetRemap(src="cmd_vel_smoothed", dst="/cmd_vel_raw"),
        # localization_launch bilerek yok: map_server ve AMCL zaten
        # /localization/start tarafindan calistiriliyor.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_share, "launch", "navigation_launch.py")
            ),
            launch_arguments={
                "use_sim_time": "false",
                "params_file": params_file,
                "autostart": "true",
                "use_composition": "False",
            }.items(),
        ),
    ])
    return LaunchDescription([
        LogInfo(msg=f"Demo Nav2 davranis sunuculari; BT: {behavior_tree}"),
        LogInfo(msg="Demo hiz zinciri: Nav2 -> /cmd_vel_raw -> safety -> /cmd_vel"),
        nav2,
    ])
