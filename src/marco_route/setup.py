import os
from glob import glob

from setuptools import find_packages, setup


package_name = "marco_route"

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
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="MarCO Yazilim Ekibi",
    maintainer_email="marco@marmara.edu.tr",
    description="Atomic semantic field graph editor and validator.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "route_editor = marco_route.route_editor_node:main",
            "route_guard = marco_route.route_guard_node:main",
        ],
    },
)
