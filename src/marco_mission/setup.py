from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'marco_mission'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='MarCO Yazilim Ekibi',
    maintainer_email='marco@marmara.edu.tr',
    description='Gorev durum makinesi, PLC mock arayuzu, /robot_status (GUI)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mock_plc = marco_mission.mock_plc:main',
            'mission_manager = marco_mission.mission_manager:main',
            'qr_reader_adapter = marco_mission.qr_reader_adapter:main',
            'test_lift_server = marco_mission.test_lift_server:main',
            'phase10_test_interfaces = marco_mission.phase10_test_interfaces:main',
            'phase10_acceptance = marco_mission.phase10_acceptance:main',
        ],
    },
)
