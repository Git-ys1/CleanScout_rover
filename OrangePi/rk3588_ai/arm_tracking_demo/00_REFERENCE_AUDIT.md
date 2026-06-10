# C-5.0.1 OrangePi 机械臂视觉追踪只读审计

生成位置：`~/rk3588_ai/debug_logs/arm_visual_tracking/00_REFERENCE_AUDIT.md`

本报告用于 C-5.0.1 第一阶段，只读审计当前可见资料，不把未接线验证的内容写成事实。

## 0. 当前板端状态

- OrangePi：`orangepi5max`，Linux `5.10.160-rockchip-rk3588`。
- 视觉目录：`~/rk3588_ai/rknn_model_zoo/examples/yolo11/python`。
- 模型：`~/rk3588_ai/models/official_yolo11.rknn`。
- Python 环境：`~/rk3588_ai/rknn_lite_env`。
- 相机：当前能看到 `USB 2.0 Camera: HD USB Camera`，设备为 `/dev/video0` 与 `/dev/video1`。
- 串口：当前未看到 `/dev/ttyUSB*` 或 `/dev/ttyACM*`，只看到 `/dev/ttyS7`。
- Python 串口库：当前 RKNN venv 缺 `pyserial`，真实串口输出不能直接运行。
- 结论：本轮只能安全完成 dry-run 与协议封装；真实机械臂动作必须等下位机连线、串口端口和方向确认。

## 1. 当前 STM32 / OPENRF1 工作区机械臂入口

当前仓库中机械臂官方冻结基线为：

- `firmware/mechanical_arm_official_baseline/User/app_uart.c`
- `firmware/mechanical_arm_official_baseline/User/Components/y_usart/y_usart.c`
- `firmware/mechanical_arm_official_baseline/User/Components/y_global/y_global.c`
- `firmware/mechanical_arm_official_baseline/User/Components/y_servo/y_servo.c`
- `firmware/mechanical_arm_official_baseline/User/Components/y_kinematics/y_kinematics.c`

关键入口：

- `app_uart_init()` 初始化 UART1/UART2/UART3/UART5，波特率均为 `115200`。
- `app_uart_run()` 根据 `uart_mode` 调用 `parse_cmd()`、`parse_action()`、`save_action()`。
- `parse_action()` 解析 `#000P1500T1000!` 类文本舵机命令。
- `parse_cmd()` 解析 `$DST!`、`$DGS:x!`、`$DGT:x-y,z!`、`$KMS:x,y,z,time!` 等命令。
- `pwmServo_angle_set(index, aim, time)` 执行 PWM 舵机目标。

## 2. 是否存在 Python 控制接口

当前机械臂 STM32 官方基线没有发现可直接复用的 Python SDK。参考 ROS2 项目有 Python 类 `ArmControl`，但它通过 ROS2 topic 发布 `JointState`，不是裸串口 SDK。

本轮新增 `arm_driver.py` 作为薄封装，默认只 dry-run。

## 3. 是否存在串口协议说明

当前官方机械臂基线的协议来自源码解析，不是独立 PDF 协议文档：

- 单舵机/多舵机文本命令：`#000P1500T1000!`
- 单舵机停止：`#000PDST!`
- 全部停止：`$DST!`
- 动作组执行：`$DGS:x!`
- 动作组区间执行：`$DGT:x-y,z!`
- 运动学命令：`$KMS:x,y,z,time!`

参考 ROS2 项目另有 `car_base.cpp` 二进制帧协议，但它属于 ROS2 底盘基线，不等同于当前机械臂官方冻结基线。

## 4. 默认串口端口

参考 ROS2 `car_base.cpp` 与 `base_serial.launch.py` 默认 `/dev/ttyAMA0`。

当前 OrangePi 实测只看到 `/dev/ttyS7`，未看到 USB 串口。C-5.0.1 demo 配置默认使用 `/dev/ttyS7`，但真实端口必须用 `tools/scan_serial.py` 在接线后确认。

## 5. 波特率

- 官方机械臂 STM32 基线：UART1/UART2/UART3/UART5 均初始化为 `115200`。
- ROS2 参考 `car_base.cpp`：`serial_baud_rate = 115200`。

## 6. 是否是总线舵机

当前机械臂官方基线以 PWM 舵机为主：

- `pwmServo_angle_set(index, aim, time)`
- PWM 范围 `500..2500`
- TIM7 软件 PWM，周期 20ms

仓库也有 `docs/001-总线舵机资料`，但当前冻结基线没有证明本轮机械臂已使用总线舵机 Python SDK。

## 7. 是否支持单舵机位置控制

支持。文本格式为：

```text
#000P1500T1000!
```

源码路径：`parse_action()` -> `pwmServo_angle_set(index, pwm, time)`。

## 8. 是否支持一次性下发 6 个关节位置

文本协议支持串联多个舵机命令：

```text
#000P1500T0200!#001P1500T0200!#002P1500T0200!#003P1500T0200!
```

ROS2 参考协议支持一次性发送 6 个关节，但当前默认不采用它。

## 9. 是否支持动作组

支持。源码中 `save_action()`、`do_group_once()`、`app_action_run()` 处理动作组。

相关命令：

- 保存动作组：`<G0000#000P1500T1000!>`
- 执行动作组：`$DGS:x!`
- 执行动作组范围：`$DGT:x-y,z!`

## 10. 角度单位

当前官方机械臂文本协议使用 PWM 脉宽值，不是弧度：

- `P1500` 表示目标 PWM 脉宽约 1500us。
- 有效范围约 `500..2500`。
- 执行时间 `T1000` 单位为 ms。

参考 ROS2 `ArmControl.set_steer()` 使用弧度，经 `car_base.cpp` 放大 `*1000` 后打包。

## 11. 舵机 ID 与关节对应

当前官方基线能确认舵机编号 `0..5` 对应 PWM 输出引脚：

- Servo0: PB9
- Servo1: PB8
- Servo2: PB5
- Servo3: PB4
- Servo4: PD2
- Servo5: PC11

参考 ROS2 跟踪使用 `[joint0, joint1, joint2, joint3, joint4, joint5]`，其中视觉追踪主要改 `joint0` 与 `joint3`。

物理 yaw/pitch 与当前机械臂实物的最终对应仍需接线后单关节验证。

## 12. 每个关节安全范围

当前官方 PWM 层硬限制：

- `aim < 500` 或 `aim > 2500` 直接返回。

C-5.0.1 demo 默认采用更保守的上位限制：

- `pwm_min = 900`
- `pwm_max = 2100`
- `yaw = -0.5..0.5`
- `pitch = 0.9..1.5`

这些不是最终机械安全范围，必须通过单关节测试收敛。

## 13. 是否能读取当前舵机位置

官方机械臂 PWM 基线只维护 `pwmServo_angle[index].current` 这种 MCU 内部目标/当前值，并未证明上位机可通过串口读回每个舵机真实角度。

ROS2 参考 `car_base.cpp` 能从 36 字节下位机回包解析关节数据，但该回包是否存在于当前机械臂官方基线未确认。

## 14. 是否能急停或停止动作

支持停止命令：

- 全部停止：`$DST!`
- 单舵机停止：`$DST:x!` 或 `#000PDST!`

审计中发现官方固件 `pwmServo_stop_motion(255)` 分支疑似使用 `pwmServo_angle[index]`，`index=255` 存在越界风险。因此 C-5.0.1 demo 默认不发送 `$DST!`，而是分别发送本 demo 控制轴的单舵机停止命令：

```text
#000PDST!
#003PDST!
```

## 15. 参考 ROS2 项目视觉追踪文件/类/函数

重点参考文件：

- `src/car_app/car_app/app_object_tracking.py`
- `src/car_app/car_app/app_color_track.py`
- `src/car_vision/car_vision/object_tracking_arm.py`
- `src/car_vision/car_vision/arm_ik_sdk.py`
- `src/car_vision/car_vision/Kinematics.py`
- `src/car_base/src/car_base.cpp`
- `src/car_yolo/car_yolo/yolo_detect.py`
- `src/depend/interfaces/msg/ObjectInfo.msg`

核心类/函数：

- `ObjectTracker.__call__()`
- `ArmControl.set_steer()`
- `ArmControl.move_arm()`
- `car_base::arm_states_Callback()`
- `car_base::ik_states_Callback()`

## 16. 参考 ROS2 项目 PID 参数

`object_tracking_arm.py` / `app_object_tracking.py`:

- `pid_yaw = PID(0.003, 0.0, 0.0)`
- `pid_dist = PID(0.003, 0.0, 0.0)`

`face_tracking.py` 另有：

- `pid_yaw = PID(0.25, 0.05, 0.02)`
- `pid_pitch = PID(0.25, 0.05, 0.02)`

C-5.0.1 采用更保守的像素到关节增量：

- `kp_yaw = 0.0008`
- `kp_pitch = 0.0008`
- `ki = 0`
- `kd = 0`

## 17. 参考 ROS2 yaw / pitch 限位

参考 ROS2：

- yaw: `[-1.000, 1.000]`
- pitch: `[0.800, 1.600]`
- 初始 yaw: `0`
- 初始 pitch: `1.200`

C-5.0.1 第一版更保守：

- yaw: `[-0.5, 0.5]`
- pitch: `[0.9, 1.5]`

## 18. 追踪用完整 IK 还是少数关节直接控制

参考 `object_tracking_arm.py` 的追踪不是完整 IK，而是直接控制少数关节：

```python
set_steer([p_y[1], -0.930, 1.6, p_y[0], 0, 0.801], 0)
```

完整 IK 在 `ArmControl.move_arm()` 中调用 `Kinematics.get_inverseKinematics()`，不用于第一版二维目标追踪。

## 19. 可借鉴与不可直接迁移

可借鉴：

- 目标中心误差计算。
- yaw/pitch P 控制与限位。
- 丢失目标时不继续乱动。
- 只控制 yaw/pitch 两个自由度的思路。
- 6 关节固定姿态中只修改 joint0/joint3 的思路。

不可直接迁移：

- ROS2 topic 架构。
- `rclpy` 节点生命周期。
- `cv_bridge` 图像链路。
- `car_base.cpp` 二进制帧作为当前默认协议。
- 完整 IK/抓取/深度/鱼眼标定。

## 20. 第一版建议使用哪两个关节

建议第一版使用：

- yaw: `joint0` / Servo0
- pitch: `joint3` / Servo3

理由：

- 参考 ROS2 追踪明确只动态改 joint0 与 joint3。
- 其他关节保持固定姿态，降低首轮风险。
- 当前官方 PWM 协议可用单舵机命令逐个验证方向和范围。

## 当前结论

C-5.0.1 第一版应默认走官方机械臂文本协议的 dry-run 路线：

```text
YOLO box -> target_selector -> visual_servo -> ArmDriver(yh_pwm_text dry-run)
```

真实串口输出前必须完成：

- 下位机物理连接。
- `tools/scan_serial.py` 确认端口。
- 安装或确认 `pyserial`。
- 单关节 yaw 小范围测试。
- 单关节 pitch 小范围测试。
- 确认 `Pxxxx` 与物理方向的对应关系。
