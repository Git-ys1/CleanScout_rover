# Mechanical Arm Official Baseline

这份目录是当前 `CleanScout_rover` 下位机线里的机械臂 STM32 官方冻结基线。

## 当前定位

- 来源：用户提供并已上板核验的机械臂官方例程
- 目标芯片：`STM32F103RC`
- 工程文件：`Project/RVMDK（uv5）/BH-STM32.uvprojx`
- 可直接烧录产物：`Output/template.hex`
- 当前范围：舵机、动作组、PS2、串口、W25Q64 参数/动作存储、基础运动学

## 使用纪律

1. 这里是官方基线，不作为连续实验开发目录。
2. 需要核对厂家原始行为、回退到官方状态、或重新烧录官方 `hex` 时，优先使用本目录。
3. 后续机械臂自研修改统一在 `../mechanical_arm_controller/` 开始，先与 RF1 底盘电机控制隔离。

## 当前已保留的关键内容

- `Libraries/`：官方 STM32F10x CMSIS/FWlib
- `User/`：官方应用源码
- `Project/`：Keil 工程主体
- `Output/template.hex`：当前可直接烧录的官方构建产物
- `Output/template.build_log.htm`：历史构建记录

## 当前刻意未纳入的本地噪声

- `*.uvguix*`
- `BH-STM32.uvoptx`
- `JLinkLog.txt`
- `JLinkSettings.ini`
- 大量 `Output/*.o/*.d/*.crf`
- `Listing/`

这些文件代表个人 IDE 状态或可再生成的本地产物，不应定义仓库里的官方基线。
