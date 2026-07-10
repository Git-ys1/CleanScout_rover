# Arm Grasp Pipeline

`arm_grasp_pipeline/` 是 C-5.1.1 新增的 RGB-D 抓取预研管线。它和现有 `arm_tracking_demo/` 分开，当前目标是把 D430/D435 深度、像素反投影、5DoF IK、RF1 总线舵机文本协议和后续 ROS 边界先整理清楚。

## 当前边界

| 模块 | 状态 |
| --- | --- |
| D430 | 深度模组已完成 depth-only smoke |
| D435 | 重组设备已完成 RGB + aligned depth 真机 smoke |
| YOLO | 暂不接入本目录，继续沿用 `arm_tracking_demo/` 作为二维视觉追踪基线 |
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

`pyrealsense2` 与 `librealsense2` 必须来自同一个 2.56.5 RSUSB 构建，不能再混用旧的 pip 2.55.1 绑定和系统 2.56.5 运行库。上游源码不入库，需要重建时从 Intel 官方 `librealsense` 仓库检出 `v2.56.5`。

## 关键原则

- 不用 2D 框面积估距，目标距离只能来自 RealSense depth。
- 深度层默认不设置人为最近/最远距离，只拒绝 `0`、负值、`NaN` 和 `Inf`；硬件近距能力约 `0.17 m` 仅作设备记录。
- 机械臂可达范围由后续坐标变换、IK 和安全层判断，不能在深度采集层提前截断。
- D430 无 RGB，不能完成 YOLO RGB-D 抓取闭环。
- 重组 D435 已验证彩色流、深度流、对齐、内参、ROI 深度和像素反投影；长 USB 3.0 线到货后再做末端安装与手眼标定。
- 当前安全起始姿态沿用 C-5.0.9：`0=1500,1=1907,2=1900,3=900,4=1500,5=1500`。
- `003 pitch` 方向不要随意翻转：现有追踪基线是 `pitch_pwm_sign=-1`、`invert_pitch=false`。
