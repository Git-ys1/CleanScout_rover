# 双串口双协议契约

## 物理链路

| 链路 | 配置 | 帧边界 | 执行域 |
| --- | --- | --- | --- |
| USART2 PA2/PA3 | 115200 8N1 | `\n` | 底盘 |
| USART3 PB10/PB11 | 115200 8N1 | `!` 或成组帧 `}` | 机械臂主机 |
| UART5 PC12 | 115200 8N1 半双工 | `!` | MCU 到总线舵机 |

USART2 不解析机械臂帧；USART3 不解析底盘行协议；UART5 不是主机入口。

## USART2 底盘协议

### 命令

```text
W,a,b,c,d\n
M,ch,pwm\n
E,ch\n
D,ch\n
STOP\n
INFO\n
ESTOP\n
CLEAR_ESTOP\n
```

- `W` 单位为 m/s，顺序固定为 CN1/LR、CN2/LF、CN3/RR、CN4/RF。
- `M` 通道为 1..4，PWM 为 -1000..1000。
- `STOP` 只停止底盘；`ESTOP` 同时停止底盘和机械臂并锁存。
- `CLEAR_ESTOP` 仅在底盘已停止且机械臂执行器空闲时成功。

### 响应与遥测

```text
CSR_RF1_READY
ACK:<command>
ERR:<reason>
INFO,COMBINED,1.0.0,MOTION_V1,ARM_V2
VEL,...
PWM,...
NAVDBG,...
ENC,...
DBG,...
```

控制周期为 20 ms，正常遥测周期为 100 ms。`W` 停发超过 250 ms 自动停车，`M` 停发
超过 2000 ms 自动停车。

## USART3 机械臂 Legacy 协议

```text
#000P1500T0200!
{#000P1500T0200!#001P1600T0200!}
#000PDST!
#000PRAD!
```

- 舵机 ID 仅允许 000..005，广播 ID 255 禁用。
- PWM 仅允许 0500..2490，时间为 0000..9999 ms。
- 成组移动先完整校验，再一次性转发；重复 ID、残帧、嵌套、超长和越界帧均拒绝。
- `$KMS` 等 `$` 历史命令返回 `@ERR:UNSUPPORTED!`，不静默执行。
- Legacy 成功移动和停止不增加主动 ACK，保持现有 OrangePi 驱动兼容。
- `PRAD` 成功时透传匹配 ID 的总线回包，例如 `#000P1500!`。

## USART3 ARM_V2

```text
@HELLO:ARM_V2!  -> @READY:ARM_V2!
@INFO!          -> @INFO:COMBINED:1.0.0:ARM_V2!
@PING!          -> @ACK:OK!
@DIAG!          -> @DIAG:...! 和 @BUSRAW:<hex>!
@ESTOP!         -> @ACK:OK!
@CLEAR:ESTOP!   -> @ACK:OK! 或 @ERR:BUSY!
```

进入 ARM_V2 后采用 stop-and-wait：成功返回 `@ACK:OK!`，失败返回
`@ERR:BAD_FRAME|LIMIT|BUSY|TIMEOUT|UNSUPPORTED|WATCHDOG!`。400 ms 没有命令或心跳会对
000..005 逐轴发送 `PDST`，只停止机械臂域，不改变底盘控制状态。

## UART5 回包同步

实机曾观测到查询回包为 `##000P1500!`。UART5 接收状态机在遇到新的 `#` 时以最新帧头
重新同步，然后仍按严格格式和期望 ID 校验；这只处理半双工回显前缀，不放宽有效载荷。

## 急停语义

| 来源 | 急停 | 清除 |
| --- | --- | --- |
| USART2 | `ESTOP\n` | `CLEAR_ESTOP\n` |
| USART3 | `@ESTOP!` | `@CLEAR:ESTOP!` |

急停为全局锁存。普通底盘 `STOP` 和单轴 `PDST` 不等同于全局急停。
