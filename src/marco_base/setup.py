from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'marco_base'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'docs'), glob('docs/*.md')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='MarCO Yazilim Ekibi',
    maintainer_email='marco@marmara.edu.tr',
    description='Orange Pi ile STM32 arasindaki UART koprusu ve diferansiyel odometri.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'base_driver = marco_base.base_driver:main',
            'odometry_turn_calibration = '
            'marco_base.odometry_turn_calibration:main',
        ],
    },
)
