# Raspberry Pi Releases

本目录按阶段保存 Raspberrypi / ROS Noetic 线的发布结论、验证证据和已知问题。

## 当前基线

| 版本 | 日期 | 主题 | 记录 |
| --- | --- | --- | --- |
| `C-4.1.8` | 2026-07-20 | 后向盲区安全、新车体二维几何与无 IMU `K_M` | [`C-4.1.8_rear_blind_sector_and_new_geometry.md`](C-4.1.8/C-4.1.8_rear_blind_sector_and_new_geometry.md) |
| `C-4.1.7` | 2026-07-19 | 从成熟运行链移除 MPU6050 | [`C-4.1.7_remove_mpu6050_from_active_stack.md`](C-4.1.7/C-4.1.7_remove_mpu6050_from_active_stack.md) |
| `C-4.1.6` | 2026-07-19 | 随身 Wi-Fi 固定拓扑与手机热点回退 | [`C-4.1.6_portable_wifi_network_baseline.md`](C-4.1.6/C-4.1.6_portable_wifi_network_baseline.md) |
| `C-4.1.5` | 2026-06-06 | Raspberrypi 仓库分层 README 与入口治理 | [`C-4.1.5_raspberrypi_repository_governance.md`](C-4.1.5/C-4.1.5_raspberrypi_repository_governance.md) |
| `C-4.1.4` | 2026-06-06 | TEB/AMCL/costmap 实车调优与参数注释治理 | [`C-4.1.4_navigation_tuning_and_parameter_cleanup.md`](C-4.1.4/C-4.1.4_navigation_tuning_and_parameter_cleanup.md) |
| `C-4.1.3` | 2026-06-06 | TEB 导航正式基线 | [`C-4.1.3_teb_navigation_baseline.md`](C-4.1.3/C-4.1.3_teb_navigation_baseline.md) |
| `C-4.1.2` | 2026-06-06 | RF1 转向几何与补充合并发布 | [`C-4.1.2_supplemental_merge_release.md`](C-4.1.2/C-4.1.2_supplemental_merge_release.md) |

## 历史发布

| 版本 | 主题 | 记录 |
| --- | --- | --- |
| `C-3.3.0` | 建图/导航分阶段启动状态 | [`C-3.3.0_staged_mapping_nav_startup_status.md`](C-3.3.0/C-3.3.0_staged_mapping_nav_startup_status.md) |
| `C-3.2.4` | edge relay 主发布 | [`C-3.2.4_edge_relay_main_release.md`](C-3.2.4/C-3.2.4_edge_relay_main_release.md) |
| `C-3.2.2` | RF1 速度契约对齐 | [`C-3.2.2_rf1_v_contract_alignment.md`](C-3.2.2/C-3.2.2_rf1_v_contract_alignment.md) |
| `C-3.2.1` | RF1 Web 栈验证 | [`C-3.2.1_rf1_web_stack_validation.md`](C-3.2.1/C-3.2.1_rf1_web_stack_validation.md) |
| `C-3.2.0` | RF1 最小桥验证 | [`C-3.2.0_rf1_min_bridge_validation.md`](C-3.2.0/C-3.2.0_rf1_min_bridge_validation.md) |
| `C-3.1.7` | OpenRF1 USB 烟测 | [`C-3.1.7_openrf1_usb_smoketest.md`](C-3.1.7/C-3.1.7_openrf1_usb_smoketest.md) |
| `C-2.3.5` | 运行时真实状态 | [`C-2.3.5_runtime_truth.md`](C-2.3.5/C-2.3.5_runtime_truth.md) |
| `C-2.3.3` | SLAM 前检查清单 | [`C-2.3.3_pre_slam_checklist.md`](C-2.3.3/C-2.3.3_pre_slam_checklist.md) |

更早的串口、A3 雷达、MPU6050、台架和风机验证记录继续保留在对应版本目录中。

## 发布规则

| 项目 | 最低要求 |
| --- | --- |
| 目录 | 使用正式版本号，如 `C-4.1.5/` |
| 记录 | 说明前序基线、范围、验证、已知问题和同步状态 |
| 代码 | 不把 `build/`、`devel/`、rosbag、日志作为发布内容 |
| 实车 | 明确是否执行运动测试、是否同步树莓派 |
| 索引 | 新版本必须更新本页和 `Raspberrypi/README.md` |
