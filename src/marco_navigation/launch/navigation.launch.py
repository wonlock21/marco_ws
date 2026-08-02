"""AMCL + Nav2 temel navigasyon (Faz 6).

Zincir:
  amcl.launch.py          (robot + LiDAR + EKF + map + AMCL)
  + nav2 navigation_launch (controller, planner, bt_navigator, ...)

Sartnameye uygun BT: engelde Wait (Spin/BackUp ile kacinma YOK).
Rota agi icin: route.launch.py (nav2_route + ComputeRoute BT).

Ornekler:
  ros2 launch marco_navigation navigation.launch.py \\
      sahte:=true lidar:=true harita:=oda_test baslangic:=true

  # Hedef (map cercevesinde):
  ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \\
    "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0},
     orientation: {w: 1.0}}}}"

Orange Pi'de rviz:=true VERME — CPU LiDAR'i acliga sokar.
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
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _kur(context, *args, **kwargs):
    nav_share = get_package_share_directory("marco_navigation")
    loc_share = get_package_share_directory("marco_localization")
    bringup_share = get_package_share_directory("nav2_bringup")

    params_src = os.path.join(nav_share, "config", "nav2_params.yaml")
    bt_xml = os.path.join(
        nav_share, "behavior_trees", "navigate_to_pose_wait.xml"
    )
    rviz_config = os.path.join(loc_share, "config", "amcl.rviz")

    # BT yolunu yaml'e yaz. navigation_launch params_file olarak string yol
    # bekliyor; RewrittenYaml Substitution'i IncludeLaunchDescription'a
    # vermek guvenilir degil.
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
    params_file = "/tmp/marco_nav2_params.yaml"
    with open(params_file, "w", encoding="utf-8") as f:
        f.write(metin)

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

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    return [
        LogInfo(msg=f"Nav2 BT: {bt_xml}"),
        LogInfo(msg=f"Nav2 params: {params_file}"),
        LogInfo(msg="Hedef icin RViz Nav2 Goal veya navigate_to_pose action"),
        amcl,
        nav2,
        rviz,
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
            DeclareLaunchArgument("harita", default_value="oda_test"),
            DeclareLaunchArgument("baslangic", default_value="true"),
            DeclareLaunchArgument("x", default_value="0.0"),
            DeclareLaunchArgument("y", default_value="0.0"),
            DeclareLaunchArgument("yaw", default_value="0.0"),
            DeclareLaunchArgument(
                "rviz",
                default_value="false",
                description="Orange Pi'de KAPALI tut",
            ),
            OpaqueFunction(function=_kur),
        ]
    )
