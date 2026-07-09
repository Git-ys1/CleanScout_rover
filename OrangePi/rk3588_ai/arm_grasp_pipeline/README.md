# Arm Grasp Pipeline

`arm_grasp_pipeline/` 是 C-5.1.1 新增的 RGB-D 抓取预研管线。它和现有 `arm_tracking_demo/` 分开，当前目标是把 D430/D435 深度、像素反投影、5DoF IK、RF1 总线舵机文本协议和后续 ROS 边界先整理清楚。

## 当前边界

| 模块 | 状态 |
| --- | --- |
| D430 | 只做 depth-only smoke，不做 YOLO RGB-D 抓取 |
| D435 | 预留 RGB + aligned depth smoke，设备到货后验证 |
| YOLO | 暂不接入本目录，继续沿用 `arm_tracking_demo/` 作为二维视觉追踪基线 |
| ROS | 当前不启动 ROS；`ros_compat.py` 只保留后续 topic/action/service 的数据边界 |
| RF1 | 只作为总线舵机文本命令执行层，不放 IK、视觉或抓取状态机 |

## 快速验证

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
~/rk3588_ai/rknn_lite_env/bin/python3 tools/ik_sweep_check.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/mock_grasp_cycle.py
```

D430 深度预检：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d430_depth_smoke.py --frames 80
```

D435 RGB-D 预检：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d435_smoke.py
```

## 关键原则

- 不用 2D 框面积估距，目标距离只能来自 RealSense depth。
- D430 无 RGB，不能完成 YOLO RGB-D 抓取闭环。
- D435 到货后先验证彩色流、深度流、对齐、内参和 ROI 深度稳定性，再接抓取状态机。
- 当前安全起始姿态沿用 C-5.0.9：`0=1500,1=1907,2=1900,3=900,4=1500,5=1500`。
- `003 pitch` 方向不要随意翻转：现有追踪基线是 `pitch_pwm_sign=-1`、`invert_pitch=false`。
