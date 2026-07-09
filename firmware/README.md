# Firmware

仓库内可直接开发、编译的 MCU 固件入口。

| 路径 | 状态 | 说明 |
| --- | --- | --- |
| [`openrf1_motion_controller/`](openrf1_motion_controller/) | 当前主线 | OpenRF1 / STM32F103RCT6 底盘运动控制器，含自包含 Keil 工程 |
| [`mechanical_arm_official_baseline/`](mechanical_arm_official_baseline/) | 冻结基线 | 机械臂 STM32F103RC 官方例程基线，当前唯一官方参考，不直接承担日常迭代 |
| [`mechanical_arm_controller/`](mechanical_arm_controller/) | 机械臂自研工程 | 从官方基线复制出的可编译/可烧录工程；C-5.1.2 起固定 USART3 作为香橙派机械臂入口 |
| [`cj_bridge_f411_cubeide/`](cj_bridge_f411_cubeide/) | 独立历史子项目 | STM32F411 CJ bridge，不属于 RF1 底盘工程 |
| [`archive/openrf1_keil_overlay/`](archive/openrf1_keil_overlay/) | 历史归档 | 早期 OpenRF1 overlay，禁止作为当前编译入口 |

RF1 后续开发只修改 `openrf1_motion_controller/`。`_local/` 下的旧工作区、
跨目录 Keil 工程和实验副本只保留在开发机，不再作为发布入口。

机械臂后续工作遵守两条纪律：

1. `mechanical_arm_official_baseline/` 只用来保留官方冻结基线、核对原始行为和必要时重新烧录，不直接承接连续实验改动。
2. `mechanical_arm_controller/` 作为后续独立开发入口，先跑通基础舵机/动作组控制，再评估与底盘系统融合。
