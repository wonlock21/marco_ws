from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'marco_perception'

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
    description='Serit/QR arayuzu — mock yayinci (gercek uygulama goruntu ekibinde)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mock_lane_qr = marco_perception.mock_lane_qr:main',
        ],
    },
)
