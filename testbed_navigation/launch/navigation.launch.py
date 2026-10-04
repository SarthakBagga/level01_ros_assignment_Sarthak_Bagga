"""Start navigation servers; simulation, map loading and AMCL run separately."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile


def generate_launch_description():
    params = ParameterFile(
        os.path.join(
            get_package_share_directory('testbed_navigation'),
            'config', 'nav2_params.yaml',
        ),
        # Resolve the installed stock BT paths in the YAML.
        allow_substs=True,
    )

    # No velocity smoother: controller and moving recoveries use /cmd_vel
    # directly, matching the robot's Gazebo diff-drive subscription.
    return LaunchDescription([
        Node(
            package='nav2_planner', executable='planner_server',
            name='planner_server', parameters=[params], output='screen',
        ),
        Node(
            package='nav2_controller', executable='controller_server',
            name='controller_server', parameters=[params], output='screen',
        ),
        Node(
            package='nav2_behaviors', executable='behavior_server',
            name='behavior_server', parameters=[params], output='screen',
        ),
        Node(
            package='nav2_bt_navigator', executable='bt_navigator',
            name='bt_navigator', parameters=[params], output='screen',
        ),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_navigation', parameters=[params],
            output='screen',
        ),
    ])
