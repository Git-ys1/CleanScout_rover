# Firmware

仓库内可直接开发、编译的 MCU 固件入口。

| 路径 | 状态 | 说明 |
| --- | --- | --- |
| [`openrf1_motion_controller/`](openrf1_motion_controller/) | 当前主线 | OpenRF1 / STM32F103RCT6 底盘运动控制器，含自包含 Keil 工程 |
| [`cj_bridge_f411_cubeide/`](cj_bridge_f411_cubeide/) | 独立历史子项目 | STM32F411 CJ bridge，不属于 RF1 底盘工程 |
| [`archive/openrf1_keil_overlay/`](archive/openrf1_keil_overlay/) | 历史归档 | 早期 OpenRF1 overlay，禁止作为当前编译入口 |

RF1 后续开发只修改 `openrf1_motion_controller/`。`_local/` 下的旧工作区、
跨目录 Keil 工程和实验副本只保留在开发机，不再作为发布入口。
