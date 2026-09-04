"""Mevcut AMCL/harita ustunde Nav2 FollowPath ve Route Server'i baslatir."""

import importlib.util
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap


def _compose_module(navigation_share):
    path = os.path.join(navigation_share, "launch", "rpp_compose.py")
    spec = importlib.util.spec_from_file_location("marco_demo_rpp_compose", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_demo_nav_params(navigation_share: str) -> str:
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
            # Dinamik engelin sahibi disaridaki collision_monitor olarak kalir.
            # Route Server statik haritayi global costmap uzerinden denetler.
            (
                "      obstacle_layer:\n"
                '        plugin: "nav2_costmap_2d::ObstacleLayer"\n'
                "        enabled: True",
                "      obstacle_layer:\n"
                '        plugin: "nav2_costmap_2d::ObstacleLayer"\n'
                "        enabled: False",
            ),
        ],
    )
    with open(params_file, encoding="utf-8") as stream:
        params = yaml.safe_load(stream)
    follow = params["controller_server"]["ros__parameters"]["FollowPath"]
    # Fiziksel demo profili: ilk saha degerlerinin iki kati. Degerler genel
    # Nav2 profilini degistirmeden yalniz kayitli A/B demosuna uygulanir.
    follow["desired_linear_vel"] = 0.60
    follow["lookahead_dist"] = 0.30
    follow["min_lookahead_dist"] = 0.20
    follow["max_lookahead_dist"] = 0.45
    follow["min_approach_linear_velocity"] = 0.10
    follow["rotate_to_heading_angular_vel"] = 0.60
    smoother = params["velocity_smoother"]["ros__parameters"]
    smoother["max_velocity"] = [0.60, 0.0, 0.80]
    smoother["min_velocity"] = [-0.30, 0.0, -0.80]
    with open(params_file, "w", encoding="utf-8") as stream:
        yaml.safe_dump(params, stream, sort_keys=False, allow_unicode=True)
    return params_file


def _write_route_params(navigation_share: str, graph_file: str) -> str:
    if not os.path.isabs(graph_file) or not os.path.isfile(graph_file):
        raise RuntimeError(f"Demo rota grafi bulunamadi: {graph_file}")
    source = os.path.join(
        navigation_share, "config", "route_server.yaml"
    )
    with open(source, encoding="utf-8") as stream:
        params = yaml.safe_load(stream)
    route = params["route_server"]["ros__parameters"]
    route["graph_filepath"] = graph_file
    output = "/tmp/marco_demo_route_server.yaml"
    with open(output, "w", encoding="utf-8") as stream:
        yaml.safe_dump(params, stream, sort_keys=False, allow_unicode=True)
    return output


def _launch_setup(context):
    navigation_share = get_package_share_directory("marco_navigation")
    nav2_share = get_package_share_directory("nav2_bringup")
    graph_file = os.path.abspath(LaunchConfiguration("graph").perform(context))
    nav_params = _write_demo_nav_params(navigation_share)
    route_params = _write_route_params(navigation_share, graph_file)

    nav2 = GroupAction(actions=[
        SetRemap(src="cmd_vel", dst="cmd_vel_nav"),
        SetRemap(src="cmd_vel_smoothed", dst="/cmd_vel_raw"),
        # map_server ve AMCL /localization/start tarafindan zaten calisiyor.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_share, "launch", "navigation_launch.py")
            ),
            launch_arguments={
                "use_sim_time": "false",
                "params_file": nav_params,
                "autostart": "true",
                "use_composition": "False",
            }.items(),
        ),
    ])
    route_server = Node(
        package="nav2_route",
        executable="route_server",
        name="route_server",
        output="screen",
        parameters=[route_params],
        remappings=[("tf", "/tf"), ("tf_static", "/tf_static")],
    )
    lifecycle_route = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_demo_route",
        output="screen",
        parameters=[{
            "use_sim_time": False,
            "autostart": True,
            "node_names": ["route_server"],
        }],
    )
    return [
        LogInfo(msg=f"Demo Nav2 rota grafi: {graph_file}"),
        LogInfo(msg="Demo hareketi: ComputeRoute -> FollowPath/RPP"),
        LogInfo(msg="Demo hiz zinciri: Nav2 -> /cmd_vel_raw -> safety -> /cmd_vel"),
        nav2,
        route_server,
        lifecycle_route,
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "graph", description="Mutlak demo_route.geojson yolu"
        ),
        OpaqueFunction(function=_launch_setup),
    ])
