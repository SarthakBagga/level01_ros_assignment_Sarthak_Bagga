# Testbed navigation

Manual ROS 2 Humble navigation for the supplied Testbed robot and playground.
Map loading, localization and navigation have separate launch files and lifecycle
managers. All resources resolve from installed package shares; CMake installs
`launch/`, `config/` and `rviz/`. No custom nodes or behavior tree are needed.

## Architecture and data flow

| Component | Responsibility and choice |
| --- | --- |
| Gazebo / diff-drive plugin | Simulates the supplied world; publishes clock, scan and odometry; consumes velocity commands. |
| Map server | Publishes the supplied `testbed_world.yaml` / PGM as `/map`. |
| AMCL | Uses map, scan and odometry to estimate the robot pose. DifferentialMotionModel matches the two-wheel drive. |
| Planner server / NavFn | Dijkstra search on the global costmap. Suitable for this small static 2D playground; no orientation-constrained global planner is needed. |
| Controller server / Regulated Pure Pursuit | Tracks the path, slows for curvature and obstacle costs, and checks projected collisions. Fits the differential drive at conservative speed. |
| Behavior server | Provides exactly Spin, BackUp and Wait required by the stock recovery tree. |
| BT navigator | Coordinates planning, following and recovery through the installed Humble `navigate_to_pose_w_replanning_and_recovery.xml`. |

The global costmap combines static map, scan obstacles and inflation. The local
costmap uses scan obstacles and inflation in a rolling `odom` grid. NavFn creates
`/plan`; RPP follows it using the local costmap and `/odom`, publishing directly
to `/cmd_vel`. Moving recoveries also publish there. The Gazebo diff-drive plugin
executes these commands and feeds odometry back into localization/control.

TF: `map -> odom -> base_footprint -> base_link -> lidar_link_1`.
AMCL owns `map -> odom`, Gazebo diff-drive owns `odom -> base_footprint`, and
robot_state_publisher supplies the robot's link transforms.

| Interface | Publisher → consumers |
| --- | --- |
| `/clock` | Gazebo → simulation-time nodes |
| `/map` | Map server → AMCL, global costmap, RViz |
| `/scan` | Gazebo LiDAR → AMCL, both costmaps, RViz |
| `/odom` | Gazebo diff-drive → controller, BT navigator |
| `/tf`, `/tf_static` | AMCL, diff-drive, robot_state_publisher → transform users |
| `/amcl_pose`, `/particle_cloud` | AMCL → localization inspection / RViz |
| `/plan` | Planner → path inspection / RViz |
| `/global_costmap/*`, `/local_costmap/*` | Planner/controller costmaps → navigation and RViz |
| `/cmd_vel` | Controller / behavior server → Gazebo diff-drive |
| `/navigate_to_pose`, `/compute_path_to_pose`, `/follow_path` | Navigator, planner and controller action servers |

Lifecycle managers autostart map_server, AMCL, and the four navigation servers
in separate groups. Navigation activation order is planner, controller, behavior,
BT navigator. An active AMCL still needs an initial pose before usable map TF.

## Design choices

All relevant nodes use simulation time. AMCL uses `map`, `odom`,
`base_footprint`, `/scan` and laser limits 0.10–10 m. Its baseline is Humble's
likelihood-field model with 500–2000 particles and 0.25 m / 0.2 rad update thresholds.

The footprint comes from transformed collision meshes, including wheels and
casters: x=[-0.22570,0.12430], y=[-0.24076,0.16524] m. Both costmaps use
`[[-0.23,-0.25],[0.13,-0.25],[0.13,0.17],[-0.23,0.17]]` plus 0.01 m padding.
The origin is off-center; a borrowed circular radius would misrepresent it.
See the [visual geometry check](rviz/testbed_footprint.png).

RPP cruises at 0.10 m/s, aligns at 0.30 rad/s and uses a fixed 0.40 m lookahead.
The local grid is 4×4 m; both grids use the map's 0.05 m resolution. Inflation is
0.50 m with factor 3.0, matching RPP's cost interpretation. Scan obstacles mark
through 9.5 m and clear through 10 m. Progress checking allows 20 s for 0.10 m
movement; goal tolerances are 0.15 m / 0.15 rad. These are conservative baseline
choices, not aggressively tuned values.

The stock BT replans at 1 Hz and loads only its 11 required plugin libraries.
Humble activates both built-in navigator interfaces, so both default-tree
parameters reference the selected stock tree to avoid loading unrelated plugins.
Only NavigateToPose is supported/tested; do not use NavigateThroughPoses.

## Environment and clean build

Verified: Ubuntu 22.04, ROS 2 Humble, Gazebo Classic 11.10.2, Nav2 1.1.20 and RViz.
The manifest declares the selected server/plugin packages, launch dependencies,
ament_index_python, testbed_bringup and the RViz particle display plugin.
The [Docker environment](../docker/README.md) provides these dependencies.

From the repository root on the host, open a build shell that bypasses the
helper's automatic workspace sourcing:

```bash
./docker/humble.sh start
docker exec -it eric_assignment_humble bash --noprofile --norc
```

Inside that shell:

```bash
source /opt/ros/humble/setup.bash
cd /workspace
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
rm -rf build/* install/* log/*
colcon build
source /workspace/install/setup.bash
ros2 pkg prefix testbed_navigation
```

## Documented staged startup

Open four container shells with `./docker/humble.sh shell`. In **each** shell:

```bash
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
export CYCLONEDDS_URI='<CycloneDDS><Domain id="any"><Discovery><MaxAutoParticipantIndex>100</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
```

Run these commands in separate terminals, in this order:

```bash
# Terminal 1
ros2 launch testbed_bringup testbed_full_bringup.launch.py \
  rvizconfig:="$(ros2 pkg prefix --share testbed_navigation)/rviz/navigation.rviz"
# Terminal 2: wait for map_server active
ros2 launch testbed_navigation map_loader.launch.py
# Terminal 3: initialize and verify localization before Terminal 4
ros2 launch testbed_navigation localization.launch.py
# Terminal 4
ros2 launch testbed_navigation navigation.launch.py
```

In RViz, keep Fixed Frame `map`. Use **2D Pose Estimate**, click the estimated
robot position and drag along its heading. The tested start was near (0.08,5.0),
facing east; refine it by checking red scans against map walls and green particles.
Exact equality with Gazebo's (0,5,0) spawn is unproven, so automatic initialization
is disabled. Check `map -> odom` and scan alignment before sending a goal.
RViz offers Playground overview and Robot detail views with eight relevant displays.

Stop all four launches with Ctrl+C for a restart, then repeat initialization.
`./docker/humble.sh stop` followed by `start` clears container processes;
`recreate` refreshes display mounts when the desktop authentication file changes.

## Verify and send a goal

Use another sourced container shell with the same DDS setting:

```bash
for node in map_server amcl planner_server controller_server behavior_server bt_navigator; do
  ros2 lifecycle get /$node
done
ros2 topic list
ros2 node list
ros2 topic echo /clock --once
ros2 topic echo /odom --once
ros2 topic echo /scan --once --qos-reliability best_effort
ros2 topic echo /map --once --qos-durability transient_local --qos-reliability reliable
ros2 topic info /cmd_vel --verbose
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_tools view_frames
ros2 action list -t
```

All six servers should report `active [3]`. Verify advancing clock, complete TF,
scan/map alignment and costmap displays. From the initialized start, this tested
westbound goal is reachable (quaternion represents yaw π):

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: map}, pose: {position: {x: -4.0, y: 4.5, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 1.0, w: 0.0}}}}' --feedback
```

Expect acceptance, a blue global path, populated costmaps, nonzero `/cmd_vel`,
robot movement and `SUCCEEDED`. If it fails, inspect lifecycle → TF → localization
→ costmaps → planner → controller → BT, before changing parameters.

## Results, challenges and limits

Three different routes, including a divider detour, and one clean-restart repeat
succeeded with recorded plans and positive sampled footprint clearance. No Nav2
parameter was changed during those tests. See [test results](../NAVIGATION_TEST_RESULTS.md).

Verified starter fixes include packaging/map paths, simulation time, LiDAR range
(1.5 m gave zero usable returns; 10 m gave 222/300), the unavailable legacy control
plugin, and paused-spawn sequencing (10/10 startup checks). Details and verification
are confined to [BUGS_AND_FIXES.txt](../BUGS_AND_FIXES.txt).
Combined startup exhausted Cyclone DDS participant discovery; the setting above
resolved it. Stock BT substitution and Humble's two-interface activation needed
explicit handling. Occasional BT tick-rate warnings occurred under CPU load.

**Unresolved:** later video capture showed poorer AMCL scan alignment: only
42–60% of finite endpoints were within 0.15 m of mapped walls, despite action
success. Its post-result pose was 0.188 m from the goal. This has not been fixed
or tuned; do not treat that capture as proof of sustained localization accuracy.
Earlier localization evidence measured 97.5% alignment. Recovery execution,
dynamic obstacles and hardware operation were not tested. Clearance evidence
uses estimated TF/map/scan, not a ground-truth contact sensor.

[Evidence](../evidence/README.md): short real-time video, localization screenshot,
navigation/result screenshot, action log and measured capture limits.
[Submission audit](../SUBMISSION_AUDIT.md) records remaining submission checks.
