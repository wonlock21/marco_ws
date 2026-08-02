"""Serit takibi PWM koprusunu baslatir.

/pwm_left + /pwm_right -> CMD_MOTOR_PWM -> UART. base_driver ILE AYNI ANDA
CALISTIRILAMAZ; ikisi ayni seri porta yazar.

Ornekler:
  ros2 launch marco_base pwm_bridge.launch.py
  ros2 launch marco_base pwm_bridge.launch.py sahte:=true
  ros2 launch marco_base pwm_bridge.launch.py port:=/dev/ttyACM0
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = os.path.join(
        get_package_share_directory("marco_base"), "config", "pwm_bridge.yaml"
    )

    arguments = [
        DeclareLaunchArgument(
            "sahte",
            default_value="false",
            description="Gercek STM32 yerine yazilim taklidini kullan",
        ),
        DeclareLaunchArgument(
            "port",
            default_value="/dev/marco_stm32",
            description="STM32 seri port yolu",
        ),
    ]

    bridge = Node(
        package="marco_base",
        executable="pwm_bridge",
        name="marco_pwm_bridge",
        output="screen",
        parameters=[
            config,
            {
                "use_fake_hardware": LaunchConfiguration("sahte"),
                "serial_port": LaunchConfiguration("port"),
            },
        ],
    )

    return LaunchDescription(arguments + [bridge])
