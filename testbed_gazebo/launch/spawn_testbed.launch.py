#!/usr/bin/python3
# -*- coding: utf-8 -*-
import random

from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, ExecuteProcess, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    position = [0.0, 5.0, 0.0]
    orientation = [0.0, 0.0, 0.0]
    robot_base_name = "testbed"


    entity_name = robot_base_name
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=['-entity',
                   entity_name,
                   '-x', str(position[0]), '-y', str(position[1]
                                                     ), '-z', str(position[2]),
                   '-R', str(orientation[0]), '-P', str(orientation[1]
                                                        ), '-Y', str(orientation[2]),
                   '-topic', '/robot_description'
                   ]
    )

 

    def after_spawn(event, context):
        if event.returncode != 0:
            return [EmitEvent(event=Shutdown(reason='Robot spawn failed'))]
        # Wait for the service response instead of issuing a fire-and-forget request.
        return [ExecuteProcess(
            cmd=['ros2', 'service', 'call', '/unpause_physics',
                 'std_srvs/srv/Empty', '{}'],
            output='screen',
            condition=IfCondition(LaunchConfiguration('unpause')),
        )]

    # Register before spawning so even a fast exit is handled.
    return LaunchDescription(
        [
            DeclareLaunchArgument('unpause', default_value='false',
                                  description='Unpause Gazebo after successful robot spawn'),
            RegisterEventHandler(OnProcessExit(target_action=spawn_robot,
                                               on_exit=after_spawn)),
            spawn_robot,
        ]
    )
