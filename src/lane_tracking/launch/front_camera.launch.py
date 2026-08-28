"""Konftel Cam10 ortak ROS goruntu kaynagi ve HTTP video sunucusu.

Kamerayi yalniz usb_cam acar. Serit takip, QR ve web_video_server ayni
/camera/image_raw topigine abone olur; hicbiri /dev/video* yolunu tekrar acmaz.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    lane_share = get_package_share_directory('lane_tracking')
    camera_config = os.path.join(
        lane_share, 'config', 'front_camera.yaml')

    camera = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        namespace='camera',
        name='front_camera',
        output='screen',
        # USB aygiti gecici olarak yeniden numaralanirsa usb_cam temizce
        # kapanir. Launch onu tekrar baslatarak serit takibinin elle mudahale
        # olmadan goruntuyu yeniden almasini saglar.
        respawn=True,
        respawn_delay=2.0,
        parameters=[
            camera_config,
            {
            'video_device': LaunchConfiguration('camera'),
            'image_width': ParameterValue(
                LaunchConfiguration('width'), value_type=int),
            'image_height': ParameterValue(
                LaunchConfiguration('height'), value_type=int),
            'framerate': ParameterValue(
                LaunchConfiguration('framerate'), value_type=float),
            'pixel_format': LaunchConfiguration('pixel_format'),
            'frame_id': LaunchConfiguration('frame_id'),
            },
        ],
    )
    web_video = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        condition=IfCondition(LaunchConfiguration('web_stream')),
        parameters=[{
            'port': ParameterValue(
                LaunchConfiguration('web_video_port'), value_type=int),
            'address': '0.0.0.0',
        }],
    )
    return LaunchDescription([
        DeclareLaunchArgument(
            'camera', default_value='/dev/marco_front_camera'),
        DeclareLaunchArgument('width', default_value='640'),
        DeclareLaunchArgument('height', default_value='480'),
        DeclareLaunchArgument('framerate', default_value='20.0'),
        DeclareLaunchArgument('pixel_format', default_value='mjpeg2rgb'),
        DeclareLaunchArgument('frame_id', default_value='camera_front_link'),
        DeclareLaunchArgument('web_stream', default_value='true'),
        DeclareLaunchArgument('web_video_port', default_value='8080'),
        camera,
        web_video,
    ])
