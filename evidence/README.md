# Assignment evidence

- [Video: navigation and CLI result](localization_navigation.mp4) — 50 s,
  real RViz and terminal pixels; robot turns and follows the blue path.
- [Localization screenshot](01_localization.png) — map, robot, red scan alignment
  and green AMCL particles. This earlier check had 97.5% of finite scan endpoints
  within 0.15 m of map walls.
- [Navigation/result screenshot](02_navigation_result.png) — arrival view and
  actual accepted goal / `SUCCEEDED` output.
- [Unmodified action output](navigation_action.log) and
  [capture measurements](capture_metrics.json).

The filmed goal was map (-4,3.6), yaw -π/2, action ID
`f054aeb8efc44c83bffd975632af04d6`. It produced 29 plans, 291 nonzero commands,
1.032 m odometry travel and a final zero Twist. Maximum commands were 0.10 m/s
and 0.30 rad/s. The video preserves capture timing; no robot motion was synthesized.

The localization screenshot is an earlier stage, not the filmed goal's alignment.
During the later goal, alignment had degraded to 42.4% before / 59.6% after within
0.15 m, with mean wall distances 0.190 / 0.167 m. Post-result position error was
0.188 m; action success alone does not establish accurate localization or arrival.
No fix for this degradation was performed. Earlier multi-route checks and their
limits are in [navigation test results](../NAVIGATION_TEST_RESULTS.md).

[Earlier route evidence](routes/recorded_runs.zip) bundles the three route logs,
clean-restart repeat, raw path/motion samples and readiness checks. The individual
JSON summaries are in [routes/](routes/).
