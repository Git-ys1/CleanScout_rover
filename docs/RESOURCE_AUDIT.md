# 合并下位机资源审计

## 唯一底层设施

合并工程只有一套 `main()`、SysTick、CMSIS/SPL、启动文件、中断向量和 Keil target。
`scripts/static_audit.ps1` 对 `main`、SysTick、USART2、USART3、UART5 IRQHandler 的唯一定义
进行自动检查。

## 外设资源

| 资源 | 引脚/映射 | 用途 |
| --- | --- | --- |
| TIM5 | PA0/PA1 | CN1 编码器 |
| TIM3 | PA6/PA7 | CN2 编码器 |
| TIM2 全重映射 | PA15/PB3 | CN3 编码器 |
| TIM4 | PB6/PB7 | CN4 编码器 |
| TIM8 CH1..4 | PC6/PC7/PC8/PC9 | 四路电机 PWM |
| GPIO | PA8/PA11/PA12/PC10 | CN1..CN4 方向 |
| USART2 | PA2/PA3 | Raspberry Pi 底盘链路 |
| USART3 | PB10/PB11 | Orange Pi 机械臂链路 |
| UART5 半双工 | PC12 | 总线舵机链路 |
| SWD | PA13/PA14 | 下载调试；JTAG 关闭以释放 PA15/PB3 |

## 中断优先级

NVIC 使用 Priority Group 2：USART2 抢占优先级 0，USART3 为 1，UART5 为 2。三路串口
IRQ 仅处理字节 ring；字符串解析、总线动作和遥测均在主循环执行。

## 缓冲区

| 模块 | RX | TX | 帧缓存 |
| --- | ---: | ---: | ---: |
| USART2 motion | 256 B | 1024 B | 64 B 行 |
| USART3 arm host | 512 B | 512 B | 128 B 帧 |
| UART5 servo bus | 256 B | 512 B | 64 B 回包 |

每个端口拥有独立 head/tail、overflow 计数和解析状态，不存在旧工程的
`uart_receive_buf`、`buf_index`、`uart_mode` 共享状态。

## 已排除冲突

机械臂旧工程 TIM7 本地 PWM 使用 PA9、PA8、PC5、PC4、PC2、PB11。PA8 已用于 CN1
方向，PA9 与 USART1 调试资源冲突，PB11 是 USART3 RX；同时启用本地 PWM 与总线舵机会
让同一命令重复执行。因此正式合并工程明确只使用 `servo_bus`，不编译 TIM7 后端。

## 最终资源占用

最终 Keil map 的发布数值记录在
[`VERIFY/combined_dual_uart_controller_verification.md`](VERIFY/combined_dual_uart_controller_verification.md)。
