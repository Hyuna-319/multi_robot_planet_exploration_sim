#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # TurtleBot3 기본 모델 설정
    TURTLEBOT3_MODEL = 'waffle'
    turtlebot3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    turtlebot3_sdf = os.path.join(turtlebot3_gazebo_dir, 'models', f'turtlebot3_{TURTLEBOT3_MODEL}', 'model.sdf')
    turtlebot3_urdf = os.path.join(turtlebot3_gazebo_dir, 'urdf', f'turtlebot3_{TURTLEBOT3_MODEL}.urdf')

    # 3번 로봇은 다른 모델을 사용
    TURTLEBOT3_ALIEN_MODEL = 'alien'
    turtlebot3_alien_sdf = os.path.join(turtlebot3_gazebo_dir, 'models', f'turtlebot3_{TURTLEBOT3_ALIEN_MODEL}', 'model.sdf')
    turtlebot3_alien_urdf = os.path.join(turtlebot3_gazebo_dir, 'urdf', f'turtlebot3_{TURTLEBOT3_ALIEN_MODEL}.urdf')

    # Gazebo world 
    gazebo_world = os.path.join(get_package_share_directory('urdf_tutorial'), 'world', 'moon.world')

    # Gazebo 
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': gazebo_world}.items()
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gzclient.launch.py')
        )
    )

    # Spawn TurtleBot3 
    spawn_turtlebot3_cmds = []
    state_publisher_cmds = []
    drive_turtlebot3_cmds = []  
    for i in range(1, 4):
        turtlebot3_namespace = f'turtlebot3_{i}'
        
        if i == 3:
            # 3번 로봇은 다른 모델 사용
            spawn_entity_file = turtlebot3_alien_sdf
            urdf_file = turtlebot3_alien_urdf
            position_x, position_y = 9.950472, 5.406988
            yaw = 0.0  
        else:
            # 기본 로봇 설정 (1번, 2번 로봇)
            spawn_entity_file = turtlebot3_sdf
            urdf_file = turtlebot3_urdf
            if i == 1:
                position_x, position_y = 9.5, -7
                yaw = 3.14159  
            elif i == 2:
                position_x, position_y = 10, -6.5
                yaw = 1.5708  

        # Spawn entity
        spawn_turtlebot3_cmds.append(TimerAction(
            period=5.0 * i,  
            actions=[
                Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    namespace=turtlebot3_namespace,
                    arguments=[
                        '-entity', turtlebot3_namespace,
                        '-file', spawn_entity_file,
                        '-x', str(position_x), '-y', str(position_y), '-z', '0.01',
                        '-Y', str(yaw),  # Yaw 값 추가
                        '-robot_namespace', turtlebot3_namespace
                    ],
                    output='screen',
                )
            ]
        ))

        # Robot state publisher 
        with open(urdf_file, 'r') as urdf_file_handle:
            urdf_content = urdf_file_handle.read()

        state_publisher_cmds.append(Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace=turtlebot3_namespace,
            output='screen',
            parameters=[{
                'robot_description': urdf_content,
                'use_sim_time': use_sim_time,
                'frame_prefix': f'{turtlebot3_namespace}/'
            }]
        ))
        
        robot_interaction_node = Node(
            package='urdf_tutorial',  
            executable='robot_interaction_node',
            name='robot_interaction_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        )
        # 자율주행 드라이브 추가 (로봇 1, 2에만 적용)
        if i in [1, 2]:
            drive_turtlebot3_cmds.append(Node(
                package='turtlebot3_gazebo',
                executable='turtlebot3_drive',
                namespace=turtlebot3_namespace,
                output='screen',
                parameters=[{'use_sim_time': use_sim_time}],
            ))

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time'
        ),
        gzserver_cmd,
        gzclient_cmd,
        *spawn_turtlebot3_cmds,
        *state_publisher_cmds,
        *drive_turtlebot3_cmds,  
        robot_interaction_node,  
    ])
