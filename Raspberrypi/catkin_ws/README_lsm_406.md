# 406 LSM Mapping Backup Line

This backup line keeps `gmapping` as the map builder and adds `laser_scan_matcher` as an odom fallback for mapping.

## Purpose

Use this backup line when wheel odom quality is not good enough for clean 406 mapping.

Runtime chain:

`/scan` -> `laser_scan_matcher` -> `/odom_lsm` + `odom_lsm -> base_link` tf -> `gmapping`

## Files

1. `src/clbrobot_project/clbrobot/launch/slam/laser_scan_matcher_406.launch`
2. `src/clbrobot_project/clbrobot/launch/slam/slam_406_lsm.launch`
3. `run_mapping_406_lsm.sh`

## Usage

```bash
cd /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
bash ./run_mapping_406_lsm.sh
```

## Key topics

1. Input scan: `/scan`
2. LSM odom fallback: `/odom_lsm`
3. Wheel odom topic remains: `/odom`
4. Map output: `/map`

## Important notes

1. This backup line does not replace the current RF1 bridge.
2. This backup line does not overwrite `/odom`.
3. `bringup_rf1_min.launch` is started with `publish_odom_tf:=false` here to avoid tf conflict with the `odom_lsm -> base_link` chain.
4. `gmapping` is bound to `odom_lsm`, not the wheel odom frame.

## Logs

1. `/tmp/c331_lsm.log`
2. `/tmp/c331_mapping_406_lsm.log`
3. `/tmp/c331_lsm_rf1.log`
4. `/tmp/c331_lsm_lidar.log`

## Validation checklist

1. `/scan` exists
2. `/odom_lsm` exists
3. `/map` exists
4. RViz fixed frame can use `map`
