"""Yalnizca gorselleştirme: robot modeli + RViz. Surucu veya sensor baslatmaz.

Iki kullanim sekli var.

1) UZAKTAKI BILGISAYARDA canli izleme
   Orange Pi uzerinde RViz calistirmak LiDAR'i acliga sokuyor (olculdu: %244
   CPU, /scan 9.96 Hz'den 6 Hz'e duser, 3.4 saniyelik boşluklar olusur). Bu
   yuzden RViz ayni agdaki baska bir makinede, ayni ROS_DOMAIN_ID ile
   calistirilmali. Robot tarafinda hicbir sey degismez.

       ros2 launch marco_bringup viewer.launch.py

2) KAYITTAN OYNATMA  (tek makinede, CPU cakismasi olmadan)
   Arac hareket ederken RViz hic acilmaz, sadece kayit alinir. Sonra kayit
   oynatilirken izlenir. Olcum dogrulugu bozulmaz.

       # robot tarafinda, arac hareket ederken:
       ros2 bag record -o /tmp/kayit /scan /odom /joint_states /tf /tf_static \\
           /robot_description /odometry/filtered

       # sonra:
       ros2 launch marco_bringup viewer.launch.py sim:=true
       ros2 bag play /tmp/kayit --clock

   sim:=true, dugumlere kayittaki zamani kullanmalarini soyler. --clock
   olmadan sim:=true kullanilirsa TF "gelecekten" gelmis gorunur ve RViz
   hicbir sey cizmez.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    description_share = get_package_share_directory("marco_description")
    bringup_share = get_package_share_directory("marco_bringup")

    xacro_file = os.path.join(description_share, "urdf", "marco.urdf.xacro")
    rviz_config = os.path.join(bringup_share, "config", "robot.rviz")

    sim = LaunchConfiguration("sim")

    arguments = [
        DeclareLaunchArgument(
            "sim",
            default_value="false",
            description="Kayittan oynatirken true; ros2 bag play --clock ile birlikte",
        ),
    ]

    # Modeli yayinlar. Kayittan oynatmada da gerekli: /robot_description
    # transient_local bir topik oldugu icin kayittan tekrar yayinlanmasi
    # guvenilir degil, RViz oynatma baslamadan once baglanmis olmali.
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": ParameterValue(
                    Command(["xacro ", xacro_file]), value_type=str
                ),
                "publish_frequency": 50.0,
                "use_sim_time": sim,
            }
        ],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": sim}],
    )

    return LaunchDescription(arguments + [robot_state_publisher, rviz])
