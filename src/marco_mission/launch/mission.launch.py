"""Gorev katmani + sahte PLC (Faz 10 arayuz).

  ros2 launch marco_mission mission.launch.py
  ros2 service call /mission/start marco_msgs/srv/StartMission "{}"
  ros2 topic echo /robot_status
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    simulate = LaunchConfiguration("simulate_steps")
    step_delay = LaunchConfiguration("step_delay_s")

    return LaunchDescription(
        [
            DeclareLaunchArgument("simulate_steps", default_value="true"),
            DeclareLaunchArgument("step_delay_s", default_value="0.5"),
            LogInfo(msg=["mission launch simulate_steps=", simulate]),
            Node(
                package="marco_mission",
                executable="mock_plc",
                name="mock_plc",
                output="screen",
            ),
            Node(
                package="marco_mission",
                executable="mission_manager",
                name="mission_manager",
                output="screen",
                parameters=[
                    {
                        "simulate_steps": simulate,
                        "step_delay_s": step_delay,
                        "status_rate_hz": 5.0,
                        "gate_node": "kapi_q5",
                    }
                ],
            ),
        ]
    )
