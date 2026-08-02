from setuptools import find_packages
from setuptools import setup

setup(
    name='marco_msgs',
    version='0.1.0',
    packages=find_packages(
        include=('marco_msgs', 'marco_msgs.*')),
)
