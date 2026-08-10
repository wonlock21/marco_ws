import os
from glob import glob

from setuptools import setup

package_name = 'lane_tracking'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='MarCO goruntu isleme ekibi',
    maintainer_email='marco@teknofest.local',
    description='Kameradan serit takibi ve PD kontrol.',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imgprocess = lane_tracking.imgprocess_node:main',
            'turnaround = lane_tracking.turnaround_node:main',
            'turn_then_rear_lane = '
            'lane_tracking.turn_then_rear_lane_node:main',
        ],
    },
)
