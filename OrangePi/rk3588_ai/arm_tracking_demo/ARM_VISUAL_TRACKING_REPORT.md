# C-5.0.1 ARM_VISUAL_TRACKING_REPORT

## Summary

本轮完成 OrangePi RK3588 YOLO11 机械臂二维视觉追踪第一版开发骨架。当前实现不接 ROS、不改原 `yolo11_camera.py`、不做 IK/抓取/深度/鱼眼标定，默认 dry-run。

## 新增文件

- `arm_driver.py`
- `target_selector.py`
- `visual_servo.py`
- `yolo_arm_track.py`
- `config/arm_track_config.yaml`
- `tools/scan_serial.py`
- `tools/test_arm_driver_dryrun.py`
- `tools/test_one_joint_yaw.py`
- `tools/test_one_joint_pitch.py`
- `README_ARM_TRACKING.md`
- `00_REFERENCE_AUDIT.md`
- `ARM_VISUAL_TRACKING_REPORT.md`

## 当前 STM32 / OPENRF1 工作区审计结果

当前可确认的机械臂下位机基线为 `firmware/mechanical_arm_official_baseline`。它是 STM32F103RC 官方机械臂例程，使用 PWM 舵机文本协议，核心命令为：

```text
#000P1500T0200!
#000PDST!
#003PDST!
```

官方基线波特率为 `115200`。当前 OrangePi 只看到 `/dev/ttyS7`，未看到 USB/ACM 串口。

## 参考 ROS2 项目借鉴内容

借鉴：

- `object_tracking_arm.py` / `app_object_tracking.py` 中目标中心误差计算。
- `PID(0.003, 0.0, 0.0)` 的 P 控制思路。
- yaw/pitch 限位。
- `set_steer([yaw, fixed, fixed, pitch, fixed, fixed])` 只动两个关节的策略。
- `car_base.cpp` 中 6 关节打包协议作为可选参考后端。

没有采用：

- ROS2 topic。
- `rclpy`。
- `cv_bridge`。
- 完整 IK。
- 抓取流程。

## 当前机械臂控制协议

默认协议为 `yh_pwm_text`：

```text
#000P1500T0200!#003P1500T0200!
#000PDST!
#003PDST!
```

可选保留 `reference_binary_ik_0x90` 与 `reference_binary_arm_0x80`，但默认禁用，因为它们来自 ROS2 参考项目，不是当前官方机械臂基线的默认协议。

## 关节映射

第一版建议：

- yaw: `joint0` / Servo0
- pitch: `joint3` / Servo3

当前仍需下一轮真实接线确认物理方向与 PWM 映射。

## 安全范围与 PID

默认安全范围：

- yaw: `-0.5..0.5`
- pitch: `0.9..1.5`
- PWM: `900..2100`

默认控制参数：

- `dead_zone_px = 30`
- `control_rate_hz = 10`
- `max_yaw_delta = 0.015`
- `max_pitch_delta = 0.015`
- `kp_yaw = 0.0008`
- `kp_pitch = 0.0008`
- `ki = 0`
- `kd = 0`

## Dry-Run 测试结果

已在 OrangePi `~/rk3588_ai/arm_tracking_demo` 执行：

```bash
cd ~/rk3588_ai/arm_tracking_demo
~/rk3588_ai/rknn_lite_env/bin/python3 tools/scan_serial.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_arm_driver_dryrun.py --print_cmd
```

实际结论：

- `py_compile` 通过。
- `scan_serial.py` 当前只看到 `/dev/ttyS7`。
- `pyserial list_ports` 不可用，原因是当前 venv 缺 `serial` 模块。
- `test_arm_driver_dryrun.py` 输出了 yaw/pitch 两轴文本命令。

实际输出核心命令：

```text
#000P1500T0200!#003P1500T0200!
#000PDST!
#003PDST!
```

YOLO dry-run 入口已执行：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 yolo_arm_track.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --track_class any \
  --dry_run true \
  --enable_arm \
  --print_cmd \
  --no_show \
  --max_frames 5 \
  --log_interval 1
```

实际结论：

- `/dev/video0` 打开成功。
- RKNN 模型加载与 runtime 初始化成功。
- 5 帧推理完成，资源释放成功。
- 因目标未连续稳定出现，未触发 yaw/pitch 运动命令，这是预期安全行为。

## 单关节测试结果

当前未做真实单关节测试，原因：

- 当前电脑未连接下位机。
- OrangePi 当前未看到 USB/ACM 下位机串口。
- RKNN venv 当前缺 `pyserial`。

下一轮必须先执行 yaw 单关节，再执行 pitch 单关节。

## 联动追踪测试结果

当前仅完成代码层 dry-run 入口，未进行真实机械臂联动闭环。

## 运行命令

视觉 dry-run：

```bash
cd ~/rk3588_ai/arm_tracking_demo
~/rk3588_ai/rknn_lite_env/bin/python3 yolo_arm_track.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --track_class person \
  --dry_run true \
  --print_cmd
```

真实 yaw 小范围测试：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_one_joint_yaw.py \
  --serial_port /dev/ttyS7 \
  --enable_arm \
  --dry_run false \
  --yaw 0.03
```

## 退出方式

- `q` 或 ESC：退出并释放资源。
- Ctrl+C：进入 finally，尝试 `driver.stop()`、释放摄像头、释放 RKNN 模型。
- `space`：暂停/继续机械臂输出，视觉继续运行。
- `r`：重置 yaw/pitch 到初始值。

## 如何恢复或禁用

禁用方式：

- 不传 `--enable_arm`。
- 保持 `--dry_run true`。
- 删除或忽略 `~/rk3588_ai/arm_tracking_demo` 不影响原 `yolo11_camera.py`。

## 下一步建议

- 确认 OrangePi 到 STM32 下位机实际串口。
- 在 `~/rk3588_ai/rknn_lite_env` 安装 `pyserial`。
- 用 `tools/test_one_joint_yaw.py` 确认 Servo0 方向。
- 用 `tools/test_one_joint_pitch.py` 确认 Servo3 方向。
- 调整 `yaw_pwm_sign`、`pitch_pwm_sign`、`pwm_min/max`。
- 之后再考虑多线程采集/推理/显示、ROS 封装、抓取、鱼眼标定和 IK。
