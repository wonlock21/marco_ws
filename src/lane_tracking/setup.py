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
            'trackerfinal = lane_tracking.trackerfinal:main',
            'controller = lane_tracking.controller:main',
        ],
    },
)
