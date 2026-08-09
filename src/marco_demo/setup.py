import os
from glob import glob

from setuptools import find_packages, setup


package_name = "marco_demo"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="MarCO Yazilim Ekibi",
    maintainer_email="marco@marmara.edu.tr",
    description="Flutter kontrollu A/B hareket ve serit takip demosu.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "demo_scenario_manager = marco_demo.demo_scenario_manager:main",
        ],
    },
)
