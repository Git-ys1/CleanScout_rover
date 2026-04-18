# C-1.2.0 F411 Bridge Core

本目录存放 `C-1.2.0` 的 F411 通信桥接源码骨架。

当前冻结口径：

- `USART2 (PA2/PA3)` 对接 UNO
- `USART1 (PA9/PA10)` 对接 J 线 OpenMV UART1
- 状态机：`IDLE -> WAIT_UNO_STOP_ACK -> WAIT_J_RESULT -> WAIT_UNO_RESUME_ACK -> IDLE`
- 超时：UNO ACK `1000 ms`，J 本地抓取 `10000 ms`，F411 外层 watchdog `12000 ms`

当前实现边界：

- 已落仓：桥接状态机、ASCII 行协议解析、J 侧定界帧协议、环形缓冲区、主循环集成桩、最小启动文件与链接脚本
- 已补 Gate0 最小板级验证：`PB2` 心跳灯、`SysTick` 毫秒节拍
- 已产物：`artifacts/C-1.2.0/f411/cj_bridge_f411.elf`、`cj_bridge_f411.hex`
- 未完成：`USART1/USART2` 真实初始化、烧录验证、UART 回环

原因：

- 当前工作站未使用完整 CubeIDE 工程外壳，而是先通过 `tools/build_f411_bridge.ps1` 调用你提供的 STM32 工具链路径完成最小产物构建
- 这一步只证明协议骨架和启动/链接链路可编译，不等同于板级 Gate0 已通过

建议下一步：

1. 把当前源码接回真正的 CubeIDE 工程外壳
2. 绑定 `SysTick/HAL_GetTick`、`USART1/USART2 IRQ` 和 LED 心跳
3. 先验证 `PB2` 心跳，再继续做 UART 回环
