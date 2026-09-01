"""Konftel kamerayi OpenCV MJPG ile tek kez acip ROS'a yayinla."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    camera = Node(
        package='lane_tracking',
        executable='front_camera_publisher',
        name='front_camera_publisher',
        output='screen',
        respawn=True,
        respawn_delay=2.0,
        parameters=[{
            'video_device': LaunchConfiguration('camera'),
            'image_width': ParameterValue(
                LaunchConfiguration('width'), value_type=int),
            'image_height': ParameterValue(
                LaunchConfiguration('height'), value_type=int),
            'framerate': ParameterValue(
                LaunchConfiguration('framerate'), value_type=float),
            'fourcc': 'MJPG',
            'compressed_topic': '/camera/image_raw/compressed',
            'jpeg_quality': ParameterValue(
                LaunchConfiguration('jpeg_quality'), value_type=int),
        }],
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
        DeclareLaunchArgument('camera', default_value='/dev/video0'),
        DeclareLaunchArgument('width', default_value='640'),
        DeclareLaunchArgument('height', default_value='480'),
        DeclareLaunchArgument('framerate', default_value='25.0'),
        DeclareLaunchArgument('jpeg_quality', default_value='75'),
        DeclareLaunchArgument('web_stream', default_value='true'),
        DeclareLaunchArgument('web_video_port', default_value='8080'),
        camera,
        web_video,
    ])
