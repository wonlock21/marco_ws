"""Install the marco_plc ROS 2 Python package."""

import os
from glob import glob

from setuptools import find_packages, setup


package_name = 'marco_plc'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='MarCO Yazilim Ekibi',
    maintainer_email='marco@marmara.edu.tr',
    description='Protocol-independent production PLC adapter with SRU UDP',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'plc_bridge_node = marco_plc.plc_bridge_node:main',
        ],
    },
)
