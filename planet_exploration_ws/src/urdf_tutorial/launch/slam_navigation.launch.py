from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # SLAM Toolbox Node
        Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                {
                    'use_sim_time': False,
                    'slam_toolbox_param_file': '/home/hyuna/test3_ws/slam.yaml'
                }
            ],
            remappings=[
                ('scan', 'dolly2/scan')  
            ]
        ),

        # RViz2 Node for Visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', '/opt/ros/humble/share/slam_toolbox/config/default.rviz']
        )
    ])

