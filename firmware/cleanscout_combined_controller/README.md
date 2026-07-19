# CleanScout Combined Controller

STM32F103RCT6 底盘与机械臂正式合并固件。工程以
`firmware/openrf1_motion_controller/` 为母体，只移植机械臂的总线舵机协议与执行层；两份
独立固件仍作为回滚基线保留。

## 端口职责

| 端口 | 引脚 | 对端 | 职责 |
| --- | --- | --- | --- |
| USART2 | PA2/PA3 | Raspberry Pi | 四轮底盘命令与遥测 |
| USART3 | PB10/PB11 | Orange Pi | 机械臂 Legacy / ARM_V2 协议 |
| UART5 | PC12 | 6 路总线舵机 | MCU 内部半双工执行总线 |

三个端口各自拥有独立 RX/TX ring 和解析状态。串口中断仅收发字节，解析和动作提交均在主
循环中完成。旧机械臂 TIM7 本地 PWM 后端未进入本工程，避免 PA8、PA9、PB11 资源冲突和
同一动作被两个后端重复执行。

## 构建

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\firmware\cleanscout_combined_controller\scripts\build.ps1 -StrictWarnings
```

发布产物：

- `Build/Objects/CleanScout_Combined.hex`
- `Build/Objects/CleanScout_Combined.axf`
- `Build/Listings/CleanScout_Combined.map`
- `Build/build.log`

## 自动检查

```powershell
python -m unittest discover -s .\firmware\cleanscout_combined_controller\tests -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\firmware\cleanscout_combined_controller\scripts\static_audit.ps1
```

## 烧录

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\firmware\cleanscout_combined_controller\scripts\flash.ps1
```

脚本会写入、校验、复位，并显式从 `0x08000000` 启动，规避部分 ST-Link 组合在 `-rst` 后
仍暂停内核的问题。

## 安全边界

- 上电四轮目标为零，自动前进开关为关闭状态。
- `W` 看门狗 250 ms，`M` 看门狗 2000 ms。
- ARM_V2 会话看门狗 400 ms；Legacy 模式没有主动心跳要求。
- 全局 ESTOP 锁存并同时停止底盘和六轴舵机。
- 本轮已完成机械臂六轴只读链路，以及 Raspberry Pi 通过 USART2 的短时架空轮速回归；
  30 分钟双路并发和全部急停/断联门槛尚未验收，因此 `ROS_READY=NO`。

协议详见 [`docs/DUAL_UART_PROTOCOL.md`](../../docs/DUAL_UART_PROTOCOL.md)，资源审计详见
[`docs/RESOURCE_AUDIT.md`](../../docs/RESOURCE_AUDIT.md)。
