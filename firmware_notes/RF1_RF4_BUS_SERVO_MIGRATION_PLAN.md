# RF1 参考 RF4 迁移总线舵机执行层计划

## 迁移原则

RF4 学习包可以迁移的是“总线舵机外设/协议执行层”，不是 IK、视觉或 ROS。

OrangePi 是大脑：YOLO、D430/D435、坐标变换、IK、抓取状态机。
RF1 是执行器控制器：串口收帧、解析、限位、ACK/ERR、watchdog、舵机输出。

## RF4 可参考文件

```text
CODE/src/arm_control.c    # parse_action / 文本命令解析思路
Core/Src/usart.c          # UART 接收中断/帧边界
Core/Src/freertos.c       # 执行任务/周期调度
Core/Src/y_servo.c        # 舵机输出、方向、限幅入口
```

## RF1 建议模块

```text
arm_bus_protocol.c/.h     # 只做 #...! 和 {...} 解析
arm_servo_executor.c/.h   # 目标 PWM、限位、速度斜坡、同步执行
arm_host_link.c/.h        # OrangePi UART、ACK/ERR、watchdog
```

## 推荐协议

上位机命令：

```text
#000P1500T1000!
{#000P1500T1000!#001P1600T1000!#002P1450T1000!}
#000PDST!
@PING!
```

下位机响应：

```text
@ACK:OK!
@ACK:<seq>,OK!
@ERR:BAD_FRAME!
@ERR:LIMIT!
@ERR:WATCHDOG!
@ERR:IK_ON_HOST!
```

## 必做安全项

1. 独立 RX buffer，不与其它 UART/总线回包复用。
2. `{}` 多舵机帧必须完整收到后再执行，不能收到一半就动。
3. 每个舵机有 min/max PWM 和 max time 限制。
4. 速度斜坡或目标变化率限制，避免跳变。
5. watchdog 超时进入 hold 或逐轴 stop。
6. `#255PDST!` 未验证前禁用或修复越界。
7. 003 号反向只保留一端。

## 禁止项

- RF1 不做 IK。
- RF1 不解析坐标命令作为最终能力；如收到 `$KINEMATICS...` 只能返回 `@ERR:IK_ON_HOST!`。
- RF1 不处理相机、OpenCV、YOLO。
