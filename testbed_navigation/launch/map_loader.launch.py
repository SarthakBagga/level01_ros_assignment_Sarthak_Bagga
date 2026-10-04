"""Load the supplied map using independently managed Nav2 components."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    navigation_share = get_package_share_directory('testbed_navigation')
    bringup_share = get_package_share_directory('testbed_bringup')
    params_file = os.path.join(navigation_share, 'config', 'map_server_params.yaml')
    map_file = os.path.join(bringup_share, 'maps', 'testbed_world.yaml')

    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[params_file, {'yaml_filename': map_file}],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_map',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': ['map_server'],
            }],
        ),
    ])
