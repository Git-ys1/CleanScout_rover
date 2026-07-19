# CleanScout Raspberrypi 协作任务书

本目录保存由 Raspberrypi / ROS 维护侧提出、但需要其他子系统先完成的跨团队任务书。
任务书用于冻结接口和验收口径，不表示 Raspberrypi 维护者接管对应子系统源码。

## 当前任务

| 文件 | 执行方 | 状态 | Raspberrypi 后续动作 |
| --- | --- | --- | --- |
| [`下位机双串口双协议合并任务书.md`](下位机双串口双协议合并任务书.md) | STM32 / 下位机维护方 | 合并固件已烧录，Raspberrypi 运动链已验收 | 机械臂与双域剩余门槛由对应维护方继续验收 |
| [`combined_dual_uart_controller_verification.md`](../../docs/VERIFY/combined_dual_uart_controller_verification.md) | STM32 / 下位机维护方 | ROS 实测前的原始交付记录 | 保留当时结论，由后续 Raspberrypi 验收记录补齐运动链结果 |
| [`树莓派ROS新下位机验收记录.md`](树莓派ROS新下位机验收记录.md) | Raspberrypi / ROS 维护方 | 通过 | 可继续接入 PC 导航和分布式 ROS 联调 |

## 边界

1. Raspberrypi 侧负责提出当前 RF1 串口兼容要求和 ROS-ready 验收条件。
2. 下位机维护方负责固件架构、编译、烧录、双 UART 并发和板级验证。
3. OrangePi 侧负责机械臂上位机协议适配；需要变更时必须保留 legacy 回退。
4. 任务书不得包含设备密钥、网络凭据或现场密码。
