# 机械臂专用网关固件只读审计

日期：2026-06-10

## 1. 结论先行

当前仓库里已经存在两类机械臂相关资产：

1. `firmware/mechanical_arm_official_baseline/`：可烧录的官方冻结基线，能解析 `#000P1500T1000!` 这类文本命令，并把结果落到本地舵机输出或串口转发。
2. `firmware/mechanical_arm_controller/`：目前只有 `.gitkeep`，尚未形成可编译工程、协议层或安全网关层。

因此，`C-5.0.3` 的正确起点不是“改一下现有控制逻辑就完”，而是先明确新网关工程从哪份官方基线复制、哪些旧模块保留、哪些危险命令默认禁用。

## 2. 当前机械臂官方基线入口

官方基线的可见入口如下：

- 工程：`firmware/mechanical_arm_official_baseline/Project/RVMDK（uv5）/BH-STM32.uvprojx`
- 烧录产物：`firmware/mechanical_arm_official_baseline/Output/template.hex`
- 启动入口：`firmware/mechanical_arm_official_baseline/User/main.c`
- 串口分发：`firmware/mechanical_arm_official_baseline/User/app_uart.c`
- 协议/业务入口：`firmware/mechanical_arm_official_baseline/User/Components/y_global/y_global.c`
- 舵机输出层：`firmware/mechanical_arm_official_baseline/User/Components/y_servo/y_servo.c`
- 串口驱动：`firmware/mechanical_arm_official_baseline/User/Components/y_usart/y_usart.c`

`template.build_log.htm` 显示历史构建为 `0 Error(s), 0 Warning(s)`，说明这份官方基线至少曾经在历史环境中成功构建过。

## 3. 当前是否已有 `yh_pwm_text` 或类似文本命令封装

有。

OrangePi 侧当前 demo 的默认协议仍是 `yh_pwm_text`，并直接打包 `#000PxxxxTxxxx!`。

官方基线侧也明确在 `parse_action()` 中解析：

- `#000P1500T1000!`
- `#000PDST!`
- `#000PSCK...`
- 以及动作组形式 `{#000P1500T1000!#001P1500T1000!}`

这说明机械臂当前不是“没有文本协议”，而是“已有文本协议，但命名和执行层边界还容易误导”。

## 4. 当前是否已有 `parse_action()` / 类似命令解析函数

有。

`firmware/mechanical_arm_official_baseline/User/Components/y_global/y_global.c` 中存在：

- `parse_action(char *str)`
- `parse_cmd(char *cmd)`
- `set_servo(int index, int pwm, int time)`

其中 `parse_action()` 会把文本命令转成舵机动作，`parse_cmd()` 则负责诸如 `#255PDST!` 之类的上层控制命令。

## 5. 当前是否已有 UART3 / 总线舵机串口初始化

有，但不是专门为“网关安全层”命名的。

`firmware/mechanical_arm_official_baseline/User/Components/y_usart/y_usart.c` 中：

- `uart3_init()` 配置了 `GPIOB10/GPIOB11`
- `GPIO_Mode_AF_OD` 被用于 UART3
- `USART_HalfDuplexCmd(UART5, ENABLE)` 也存在

`firmware/mechanical_arm_official_baseline/User/app_uart.c` 里把 `uart1/2/3/5` 都初始化了，并统一标注为“连接总线设备串口”。

这说明当前官方基线有串口总线相关能力，但没有把 `HOST_UART / DEBUG_UART / SERVO_UART` 的职责显式分层写死。

## 6. 当前是否把 `#000P1500T1000!` 转发给总线舵机

是的，至少在官方基线和 vendor 例程里都能看到这一层。

证据：

- `parse_action()` 直接处理 `#...P...T...!`
- `set_servo()` 会构造 `#%03dP%04dT%04d!`
- `parse_cmd()` 里会发 `#255PDST!`
- vendor 例程同样把串口 3 标成总线设备口

但要注意：当前官方基线同时也有本地 PWM 舵机实现，所以“转发给总线舵机”并不是唯一执行路径。

## 7. 当前是否也会解析文本命令并控制本地 PWM

会。

`firmware/mechanical_arm_official_baseline/User/Components/y_servo/y_servo.c` 明确存在：

- `pwmServo_init()`
- `pwmServo_angle_set()`
- `pwmServo_stop_motion()`
- `pwmServo_bias_set()`
- TIM7 中断模拟 PWM

这意味着当前官方基线的“文本协议层”与“本地舵机执行层”是耦合在同一份代码中的，不是纯粹的串口透传网关。

## 8. 当前哪些模块必须保留

如果要新建机械臂网关固件，以下模块属于必须保留或重写的最小集合：

- 系统时钟
- `delay / systick`
- `USART`
- `GPIO`
- 总线舵机协议解析
- 安全限位
- 调试日志
- 启动入口
- 错误处理

如果继续沿用官方基线思路，`y_global.c`、`y_usart.c`、`y_servo.c` 里的协议/执行/串口路由逻辑都需要拆分，而不是原样拷走。

## 9. 当前哪些模块属于旧实验、底盘或无关功能

从 `firmware/mechanical_arm_official_baseline/` 看，以下内容不属于“机械臂专用网关”第一阶段的核心：

- `app_ps2.c` / `app_ps2.h`
- `app_sensor.c` / `app_sensor.h`
- `tracking/`
- `ultrasonic/`
- `flash/` 里的大部分动作组/存储能力，如果第一版网关不需要动作组存储

如果目标是机械臂安全网关，这些模块应先从编译目标里剔除，而不是和网关协议层混在一起。

## 10. 当前工程是否能直接编译

官方基线能编译。

证据：

- `firmware/mechanical_arm_official_baseline/Output/template.build_log.htm`
- 日志显示 `0 Error(s), 0 Warning(s)`

但 `firmware/mechanical_arm_controller/` 目前不能直接编译，因为目录里仅有 `.gitkeep`，没有工程文件、`main.c`、`uvprojx` 或源码。

## 11. 当前工程烧录后是否有启动日志

官方基线有历史产物 `template.hex`，但当前审计阶段没有重新烧录验证。

所以这里的结论只能写成：

- 历史上有可烧录产物
- 当前这次只读审计没有重新点火验证

这不构成“当前板上就是这份镜像”的证明。

## 12. 当前串口命令入口是哪一个

当前官方基线的串口命令入口是：

- `app_uart_run()`
- `parse_cmd()`
- `parse_action()`

接收来源由 `y_usart.c` 的 `uart_data_parse()` 和各串口中断驱动。

## 13. 当前总线舵机输出口是哪一个

从代码看，`uart3` 与 `uart5` 都带有总线/半双工相关迹象，但没有在代码里以“唯一 servo UART”形式明确命名。

当前只能安全地写：

- UART3：在 vendor 例程里被明确标成“连接总线设备串口”
- UART5：在官方基线里启用了半双工，且也参与串口路由

实际物理接法仍需上板核验，不能仅凭源码硬判。

## 14. 当前是否有急停、停止当前位置、释放扭力、恢复扭力等命令

有。

可见命令包括：

- `#...PDST!`：停止当前位置/停止
- `#...PULK!`：释放扭力
- `#...PULR!`：恢复扭力

上层 `parse_cmd()` 也会把 `$DST!` 这类命令转成 `#255PDST!` 广播停止。

## 15. 当前是否有危险命令防护

没有形成新网关意义上的完整防护。

官方基线里已经能看到的危险命令有：

- `PID`
- `PBD`
- `PCLE`
- `PSMI`
- `PSMX`
- `PSCK`
- `PCSD`
- `PCSM`
- `PMOD`

但这份官方基线没有把这些命令默认禁用、白名单化、分维护模式授权，也没有专门做 `RAW_SAFE` / `SERVO_MOVE` 这类上位机安全协议层。

## 16. 当前最合理的下一步

如果要把 `C-5.0.3` 真正做成“机械臂专用安全网关”，下一步应该是：

1. 从 `firmware/mechanical_arm_official_baseline/` 复制官方可编译工程，而不是从空目录起手。
2. 拆分出独立的 host 协议层、servo 协议层和安全过滤层。
3. 默认禁止危险配置命令。
4. 先实现 `PING / STATUS / STOP / RAW_SAFE` 最小闭环，再接 Orange Pi。
5. 上板前先确认物理接法是本地 PWM 还是 UART 总线链。

