# C-1.2.0 OpenMV 接线说明

## 1. 本轮对外口冻结

- `OpenMV UART1 TX = A9`
- `OpenMV UART1 RX = A10`
- 波特率：`9600 8N1`

## 2. 对 F411 接线

- `OpenMV A9 (TX) -> F411 PA10 (USART1_RX)`
- `OpenMV A10 (RX) <- F411 PA9 (USART1_TX)`
- `OpenMV GND <-> F411 GND`

## 3. 本轮不接入的模块

- `WiFi` 图传
- `LCD`
- 卖家蓝牙 / APP 协议
- 额外状态辅助线

## 4. 注意事项

- 本轮只共地，不共 `VCC`
- 若后续改由 `J-STM32` 对外，再重新冻结接线图
- 若串口下载模式占用 `A9/A10`，调试前需先断开外链