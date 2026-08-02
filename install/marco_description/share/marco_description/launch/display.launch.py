"""Robot modelini RViz2'de goruntuler.

Faz 1 dogrulama araci: URDF'in dogru genisledigini, TF agacinin kopuksuz
oldugunu ve eklem limitlerinin makul oldugunu gozle kontrol etmek icin.

    ros2 launch marco_description display.launch.py
    ros2 launch marco_description display.launch.py gui:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare("marco_description")

    use_gui = LaunchConfiguration("gui")
    use_rviz = LaunchConfiguration("rviz")

    robot_description = ParameterValue(
        Command([
            "xacro ",
            PathJoinSubstitution([pkg, "urdf", "marco.urdf.xacro"]),
        ]),
        value_type=str,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "gui", default_value="true",
            description="Eklemleri elle oynatmak icin joint_state_publisher_gui baslat.",
        ),
        DeclareLaunchArgument(
            "rviz", default_value="true",
            description="RViz2'yi baslat.",
        ),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
            output="screen",
        ),

        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
            condition=IfCondition(use_gui),
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            condition=UnlessCondition(use_gui),
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", PathJoinSubstitution([pkg, "rviz", "model.rviz"])],
            condition=IfCondition(use_rviz),
        ),
    ])
