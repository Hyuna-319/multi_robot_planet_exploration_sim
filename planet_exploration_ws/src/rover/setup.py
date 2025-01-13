from setuptools import setup
import os
from glob import glob

package_name = 'rover'

setup(
    name=package_name,
    version='0.0.0',  
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.py')),
        (os.path.join('share', package_name), glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mondkurry',
    maintainer_email='aryan.mondkar@gmail.com',
    description='A ROS2 package for controlling the Rover robot',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'obstacle_avoider = rover.obstacle_avoidance:main',
        ],
    },
)

