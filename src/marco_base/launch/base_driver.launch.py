"""Alt seviye surucuyu baslatir.

Yalnizca STM32 koprusunu ayaga kaldirir. Robot modeli, EKF ve navigasyon
marco_bringup icindeki bileske launch dosyalarinin isi.

Ornekler:
  ros2 launch marco_base base_driver.launch.py
  ros2 launch marco_base base_driver.launch.py sahte:=true
  ros2 launch marco_base base_driver.launch.py sahte:=true tf:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = os.path.join(
        get_package_share_directory("marco_base"), "config", "base_driver.yaml"
    )

    arguments = [
        DeclareLaunchArgument(
            "sahte",
            default_value="false",
            description="Gercek STM32 yerine yazilim taklidini kullan",
        ),
        DeclareLaunchArgument(
            "tf",
            default_value="false",
            description=(
                "odom -> base_footprint donusumunu bu dugum yayinlasin. "
                "Yalnizca EKF calismiyorken true yapin, aksi halde TF cakismasi olur."
            ),
        ),
        DeclareLaunchArgument(
            "port",
            default_value="/dev/marco_stm32",
            description="STM32 seri port yolu",
        ),
    ]

    driver = Node(
        package="marco_base",
        executable="base_driver",
        name="marco_base_driver",
        output="screen",
        parameters=[
            config,
            {
                "use_fake_hardware": LaunchConfiguration("sahte"),
                "publish_tf": LaunchConfiguration("tf"),
                "serial_port": LaunchConfiguration("port"),
            },
        ],
    )

    return LaunchDescription(arguments + [driver])
