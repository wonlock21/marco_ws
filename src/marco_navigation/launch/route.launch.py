"""AMCL + Nav2 + nav2_route (Faz 7).

Zincir:
  navigation.launch.py  (AMCL + controller/planner/bt_navigator)
  + route_server        (GeoJSON rota agi)
  + lifecycle_manager_route

BT: navigate_route_wait.xml — ComputeRoute + FollowPath + Wait
    (serbest NavFn yok; engelde Wait).

Ornekler:
  ros2 launch marco_navigation route.launch.py \\
      sahte:=true lidar:=true harita:=nav_test baslangic:=true

  # Dugum ID ile rota (smoke):
  ros2 run marco_navigation rota_hesapla.py --start 0 --goal 8

  # Pose ile NavigateToPose (graf uzerinde en yakin dugumler):
  ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \\
    "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 2.0},
     orientation: {w: 1.0}}}}"

Orange Pi'de rviz:=true VERME.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _kur(context, *args, **kwargs):
    nav_share = get_package_share_directory("marco_navigation")
    loc_share = get_package_share_directory("marco_localization")
    bringup_share = get_package_share_directory("nav2_bringup")

    params_src = os.path.join(nav_share, "config", "nav2_params.yaml")
    route_params_src = os.path.join(nav_share, "config", "route_server.yaml")
    bt_xml = os.path.join(
        nav_share, "behavior_trees", "navigate_route_wait.xml"
    )
    graph_file = LaunchConfiguration("graf").perform(context)
    if not graph_file:
        graph_file = os.path.join(nav_share, "graphs", "demo_rota.geojson")
    elif not os.path.isabs(graph_file):
        graph_file = os.path.join(nav_share, "graphs", graph_file)

    with open(params_src, encoding="utf-8") as f:
        metin = f.read()
    if 'default_nav_to_pose_bt_xml: ""' not in metin:
        raise RuntimeError(
            "nav2_params.yaml icinde default_nav_to_pose_bt_xml: \"\" yok"
        )
    metin = metin.replace(
        'default_nav_to_pose_bt_xml: ""',
        f'default_nav_to_pose_bt_xml: "{bt_xml}"',
    )
    params_file = "/tmp/marco_nav2_route_params.yaml"
    with open(params_file, "w", encoding="utf-8") as f:
        f.write(metin)

    # graph_filepath'i mutlak yaz
    with open(route_params_src, encoding="utf-8") as f:
        route_metin = f.read()
    route_metin = route_metin.replace(
        'graph_filepath: ""',
        f'graph_filepath: "{graph_file}"',
    )
    route_params_file = "/tmp/marco_route_server.yaml"
    with open(route_params_file, "w", encoding="utf-8") as f:
        f.write(route_metin)

    amcl = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(loc_share, "launch", "amcl.launch.py")
        ),
        launch_arguments={
            "sahte": LaunchConfiguration("sahte"),
            "lidar": LaunchConfiguration("lidar"),
            "imu": LaunchConfiguration("imu"),
            "harita": LaunchConfiguration("harita"),
            "baslangic": LaunchConfiguration("baslangic"),
            "x": LaunchConfiguration("x"),
            "y": LaunchConfiguration("y"),
            "yaw": LaunchConfiguration("yaw"),
            "rviz": "false",
        }.items(),
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": "false",
            "params_file": params_file,
            "autostart": "true",
            "use_composition": "False",
        }.items(),
    )

    route_server = Node(
        package="nav2_route",
        executable="route_server",
        name="route_server",
        output="screen",
        parameters=[route_params_file],
        remappings=[("tf", "/tf"), ("tf_static", "/tf_static")],
    )

    lifecycle_route = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_route",
        output="screen",
        parameters=[
            {
                "use_sim_time": False,
                "autostart": True,
                "node_names": ["route_server"],
            }
        ],
    )

    return [
        LogInfo(msg=f"Route BT: {bt_xml}"),
        LogInfo(msg=f"Route graf: {graph_file}"),
        LogInfo(msg=f"Nav2 params: {params_file}"),
        amcl,
        nav2,
        route_server,
        lifecycle_route,
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("sahte", default_value="true"),
            DeclareLaunchArgument("lidar", default_value="true"),
            DeclareLaunchArgument(
                "imu",
                default_value="false",
                description=(
                    "true ise EKF imu_imu.yaml + madgwick. "
                    "Donanim yoksa once fake_imu yayinla."
                ),
            ),
            DeclareLaunchArgument("harita", default_value="nav_test"),
            DeclareLaunchArgument("baslangic", default_value="true"),
            DeclareLaunchArgument("x", default_value="0.0"),
            DeclareLaunchArgument("y", default_value="0.0"),
            DeclareLaunchArgument("yaw", default_value="0.0"),
            DeclareLaunchArgument(
                "graf",
                default_value="",
                description=(
                    "GeoJSON yolu (bos = graphs/demo_rota.geojson). "
                    "Goreli ise share/graphs/ altinda aranir."
                ),
            ),
            OpaqueFunction(function=_kur),
        ]
    )
