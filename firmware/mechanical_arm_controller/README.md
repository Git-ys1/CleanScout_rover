# Mechanical Arm Controller

这是 CleanScout 机械臂 STM32 自研控制工程，从 `firmware/mechanical_arm_official_baseline/` 复制官方可烧录基线后开始迭代。

## 当前定位

- 目标芯片：`STM32F103RC`
- 工程文件：`Project/RVMDK（uv5）/BH-STM32.uvprojx`
- 烧录产物：`Output/template.hex`
- 当前协议：继续兼容官方机械臂文本舵机协议，例如 `#000P1500T0200!`、`#000PDST!`、`{#000P1500T0200!#001P1500T0200!}`
- 当前串口冻结：C-5.1.2 起香橙派机械臂控制入口固定为 USART3 / PB10_TX3 / PB11_RX3 / 115200 8N1

## C-5.1.2 串口资源边界

| 串口 | OpenRF1 引脚/接口 | 当前职责 |
|---|---|---|
| USART2 | PA2_TX2 / PA3_RX2，用户串口 H5 | 保留给未来树莓派底盘 50Hz 控制链路 |
| USART3 | PB10_TX3 / PB11_RX3，蓝牙串口 H6 | 香橙派机械臂视觉追踪与后续抓取控制入口 |
| UART5 | 总线接口 | RF1 到总线舵机等下游设备，不作为香橙派入口 |

本工程不得修改 `firmware/openrf1_motion_controller/`，也不承担底盘协议合并。

## 与官方基线的关系

`firmware/mechanical_arm_official_baseline/` 只作为冻结对照和回退参考，不直接承接实验改动。

本目录才是机械臂后续自研入口。当前保留官方源码结构：

- `Libraries/`：STM32F10x CMSIS/FWlib
- `User/`：机械臂应用源码
- `Project/`：Keil 工程主体
- `Output/template.hex`：当前可烧录产物

## 构建与烧录

在 Windows 开发机上：

```powershell
$uv4 = 'D:\Work\Keil5\UV4\UV4.exe'
$project = (Resolve-Path 'firmware\mechanical_arm_controller\Project\RVMDK（uv5）\BH-STM32.uvprojx').Path
$log = (Resolve-Path 'firmware\mechanical_arm_controller\Output').Path + '\build.log'
& $uv4 -b $project -j0 -o $log
```

烧录当前机械臂产物：

```powershell
$cli = 'F:\CodeForge\STM32CubeIDE_2.1.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.400.202601091506\tools\bin\STM32_Programmer_CLI.exe'
$hex = (Resolve-Path 'firmware\mechanical_arm_controller\Output\template.hex').Path
& $cli -c port=SWD mode=UR reset=HWrst -w $hex -v -rst
```

## 验证记录

- C-5.1.2 验证文档：`docs/C-5.1.2_USART3_ARM_PORT_MIGRATION.md`
