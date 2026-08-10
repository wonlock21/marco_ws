from setuptools import find_packages, setup

package_name = 'lidar_filter'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
    	(
        	'share/ament_index/resource_index/packages',
        	['resource/lidar_filter']
    	),
    	(
        	'share/lidar_filter',
        	['package.xml']
    	),
    	(
        	'share/lidar_filter/launch',
        	['launch/lidar_with_filter.launch.py']
    	),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='orangepi',
    maintainer_email='emrefistikci1@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	'self_scan_filter = lidar_filter.self_scan_filter:main',
	],
    },
)

