# RF1 机械臂串口执行层必须改动

参考上传的 RF4 源码：`CODE/src/arm_control.c`、`Core/Src/usart.c`、`Core/Src/freertos.c`、`Core/Src/y_servo.c`。

## 分工边界

- OrangePi：YOLO、D435、深度 ROI、手眼变换、IK、抓取状态机、串口文本命令生成。
- RF1：串口收帧、限幅、执行、ACK/ERR、急停、watchdog。
- RF1 不实现 `$KINEMATICS:x,y,z,time!`，最多保留命令码但返回 `ERR:IK_ON_HOST`。

## RF1 必做

1. OrangePi 控制口使用独立 RX buffer 和状态机，不能与总线舵机回包/其它 UART 共用一个 `uart_receive_buf` 和 `buf_index`。
2. 支持 `{#000P1500T1000!#001P...T...!}` 一帧多舵机原子执行。
3. 对每帧返回 `@ACK:<seq>,OK!` 或 `@ERR:<seq>,<reason>!`；没有 seq 时也返回 `@ACK:OK!`。
4. 保留逐轴停止 `#000PDST!`，修复或禁用 `#255PDST!` 的 index=255 越界路径。
5. 003 号舵机反向只能存在一处：RF1 `aim=3000-aim` 或 OrangePi `pitch_pwm_sign=-1` 二选一，实测后固定。
6. 每路舵机做软限位、时间上限、速度斜坡，拒绝突变命令。
7. 添加 300~500 ms 上位机心跳 watchdog，超时 hold 或 stop。
8. 默认不要把 OrangePi 收到的 `#...!` 同时无脑回灌到总线 UART 和本地 PWM；应由编译开关/配置选择 mirror、bus-only 或 local-PWM-only。

## RF1 不做

- 不做视觉。
- 不接 D435。
- 不做逆运动学。
- 不根据图像面积估距。
