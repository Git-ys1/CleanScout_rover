# Arm Grasp Pipeline

`arm_grasp_pipeline/` 是独立于 ROS 的 D435 感知与抓取管线。它和现有
`arm_tracking_demo/` 分开，直接在 Orange Pi 上连接 D435、RKNN YOLO11、
像素反投影、手眼变换、官方 F103 000--003 IK 与总线舵机文本协议。

## 当前边界

| 模块 | 状态 |
| --- | --- |
| D430 | 深度模组已完成 depth-only smoke |
| D435 | 原厂完整设备已完成 RGB、深度、双红外和 aligned depth 真机验证 |
| YOLO | 已接入 RKNN YOLO11，默认目标类为 `bottle` |
| 抓取 | 已完成感知锁定、官方 `$KMS` 预检和命令规划；2026-07-13 实机预抓失败，尚未完成一次真实抓取 |
| ROS | 当前不启动 ROS；`ros_compat.py` 只保留后续 topic/action/service 的数据边界 |
| RF1 | 只作为总线舵机文本命令执行层，不放 IK、视觉或抓取状态机 |

## 快速验证

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
~/rk3588_ai/rknn_lite_env/bin/python3 tools/ik_sweep_check.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/mock_grasp_cycle.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/mock_grasp_cycle.py --print_ros
```

D430/D435 统一使用板端隔离的 librealsense 2.56.5 RSUSB 环境：

```bash
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
```

D430 深度预检：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/realsense_env_check.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d430_depth_smoke.py --frames 80
```

D435 RGB-D 预检：

```bash
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
~/rk3588_ai/rknn_lite_env/bin/python3 tools/realsense_env_check.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d435_smoke.py \
  --frames 60 \
  --save_dir ~/rk3588_ai/debug_logs/c-5.1.1-d435-transplant
```

纯 Python D435 + YOLO 感知 dry-run：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d435_yolo_grasp.py \
  --target_class bottle \
  --max_frames 300 \
  --no_show \
  --save_dir ~/rk3588_ai/debug_logs/c-5.2.0-d435-grasp-dryrun \
  --metrics_path ~/rk3588_ai/debug_logs/c-5.2.0-d435-grasp-dryrun/metrics.jsonl
```

未完成外参标定时，该命令只验收目标框、对齐深度与相机坐标，并输出
`GRASP_PLAN_BLOCKED`；不会再用占位矩阵生成看似有效的基座抓取路径。

如果只想验证锁定后生成的舵机命令序列，在仍保持 dry-run 时增加：

```bash
--execute_on_lock true
```

`pyrealsense2` 与 `librealsense2` 必须来自同一个 2.56.5 RSUSB 构建，不能再混用旧的 pip 2.55.1 绑定和系统 2.56.5 运行库。上游源码不入库，需要重建时从 Intel 官方 `librealsense` 仓库检出 `v2.56.5`。

## 关键原则

- 不用 2D 框面积估距，目标距离只能来自 RealSense depth。
- 深度层默认不设置人为最近/最远距离，只拒绝 `0`、负值、`NaN` 和 `Inf`；硬件近距能力约 `0.17 m` 仅作设备记录。
- 机械臂可达范围由后续坐标变换、IK 和安全层判断，不能在深度采集层提前截断。
- D430 无 RGB，不能完成 YOLO RGB-D 抓取闭环。
- 原厂 D435 已验证彩色流、深度流、双红外、对齐、内外参、ROI 深度和像素反投影。
- 目标必须同时满足框中心稳定、接近画面中心、ROI 深度多帧稳定，才能进入抓取计划。
- `hand_eye.calibrated`、`tool_reference.calibrated` 与 `serial.joint_pwm_calibrated`
  默认均为 `false`。三项未完成时，真实串口抓取入口强制拒绝运行。
- C-5.1.3 失败恢复与重新识别姿态固定为：`0=1380,1=1909,2=1900,3=620,4=1500,5=1500`。
- `003 pitch` 方向不要随意翻转：现有追踪基线是 `pitch_pwm_sign=-1`、`invert_pitch=false`。
- 2026-07-13 的预抓实测把 D435 光心推进到了 bottle，证明当前参考手眼矩阵不能代表真实夹爪 TCP；重新设计相机支架并完成标定前，禁止开启真实自动抓取。
- `005P0600` 已触发夹爪向全开方向运动，位置读回停在约 `1112`；`005P2400` 全闭端尚未在有电状态下验收，不能把配置值当成已标定结果。
- 官方 `$KMS` 只控制 000--003；004 与 005 必须独立控制。Python 端不再为官方 IK 补造两路 PWM。
- D435 固定在 004 的不转外壳，而 TCP 位于 004 输出侧；第一版抓取前强制
  `004=1500`，禁止在常量外参模式下转动 004。
- 真实抓取启动后先回到完整参考姿态
  `[1380,1909,1900,620,1500,1500]`，再开始识别；动态正运动学完成标定前，
  禁止把 `--auto_center` 与 `--execute_on_lock` 同时开启。
- D435 使用 depth-to-color 对齐，手眼矩阵固定为 `T_tool_camera_color_optical`；测量项见
  `docs/VERIFY/C-5.2.0_arm_camera_tcp_measurement_sheet.md`。
