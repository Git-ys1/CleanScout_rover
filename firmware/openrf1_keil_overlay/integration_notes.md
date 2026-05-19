# OpenRF1 Keil Overlay 集成说明

## 1. 本目录角色

本目录不是完整工程，也不是可直接单独编译的 Keil 项目。

它的角色是：

- 作为公开仓库中的自研应用层 overlay
- 指导如何把这些文件放入本地 vendor 工作副本
- 明确需要在 vendor 例程 9 上做哪些最小挂接

## 2. 本地工作副本建议路径

- `_local/openrf1_keil_work/`

建议做法：

1. 将 `docs/STM32F103RCT6/03.源代码程序/9.控制霍尔编码器电机` 复制到 `_local/openrf1_keil_work/`
2. 把本目录 `User/` 下的自研文件复制到工作副本对应的 `User/`
3. 在 Keil 工程中手动把这些新文件加入 `User` 分组

## 3. 需要保留的 vendor 底层

保留：

- `app_motor.c/.h`
- `y_encoder/*`
- `y_motor/*`
- `y_timer/*`
- `y_usart/*`

当前不建议继续沿用：

- `app_uart.c/.h`
- `app_ps2.c/.h`
- `app_sensor.c/.h`
- 与舵机、PS2、超声、传感器相关的应用层入口

当前建议由 overlay 接管：

- `app_motor.c/.h`
- `app_csr_bridge.c/.h`
- `app_chassis.c/.h`
- `app_telemetry.c/.h`

## 4. 推荐挂接点

### main.c

初始化建议收口为：

1. `SysTick_Init();`
2. `app_motor_init();`
3. `app_chassis_init();`
4. `app_csr_bridge_init();`
5. `app_telemetry_init();`
6. 输出 `CSR_RF1_READY`

主循环建议只保留：

1. `app_csr_bridge_run();`

### y_timer.c

建议改为同一节拍内按顺序执行：

1. `app_chassis_tick_20ms();`
2. `app_motor_run();`
3. `app_telemetry_tick_20ms();`

## 5. 串口协议

输入：

```text
W,va,vb,vc,vd
```

输出：

```text
CSR_RF1_READY
ACK:W
ERR:<reason>
VEL,rt1,rt2,rt3,rt4,tg1,tg2,tg3,tg4
PWM,p1,p2,p3,p4
```

超时：

- `400ms`

实现建议：

- 接收侧优先使用行缓冲
- 浮点解析优先使用手动分段 + `strtof`
- 不建议把 `%f` 的 `sscanf` 当成默认正式实现，避免额外依赖 `scanf float` 链接配置

## 6. 当前边界

本轮不处理：

- 树莓派接入
- ROS `cmd_vel`
- `odom`
- 机械臂 / OpenMV
- 旧 `UNO` 协议兼容
