# OpenRF1 Motion Controller

CleanScout Rover 当前正式的 OpenRF1 底盘下位机工程。

本目录是一个可独立打开、编译和烧录的 Keil 工程，不再依赖
`_local/openrf1_keil_work_2` 提供工程壳，也不再跨目录编译
`_local/openrf1_keil_work_3/User`。

## 硬件目标

| 项目 | 当前配置 |
| --- | --- |
| MCU | STM32F103RCT6 |
| Keil Device | STM32F103RC |
| 器件密度宏 | `STM32F10X_HD` |
| Flash / SRAM | 256KB / 48KB |
| PWM | TIM8 CH1~CH4 |
| 编码器 | CN1/TIM5、CN2/TIM3、CN3/TIM2 Full Remap、CN4/TIM4 |
| 串口 | USART2，115200 8N1 |

## 目录

```text
openrf1_motion_controller/
├─ CMSIS/                 STM32F1 CMSIS 与高密度启动文件
├─ Drivers/
│  ├─ inc/                实际使用的 SPL 头文件
│  └─ src/                GPIO/RCC/TIM/USART/NVIC 驱动
├─ User/                  唯一有效的底盘应用源码
├─ scripts/
│  ├─ build.ps1           Keil 命令行编译
│  └─ flash.ps1           STLink 烧录与复位
└─ OpenRF1_Motion.uvprojx Keil 工程入口
```

`Build/`、`*.uvoptx` 和 `*.uvguix.*` 属于本机生成物，不进入 Git。

## 编译

在仓库根目录执行：

```powershell
.\firmware\openrf1_motion_controller\scripts\build.ps1
```

默认使用：

```text
D:\Work\Keil5\UV4\UV4.exe
```

如 Keil 安装在其他位置：

```powershell
.\firmware\openrf1_motion_controller\scripts\build.ps1 `
  -Uv4Path 'C:\Keil_v5\UV4\UV4.exe'
```

成功后生成：

```text
firmware/openrf1_motion_controller/Build/Objects/OpenRF1_Motion.hex
```

## 烧录

连接 STLink 后执行：

```powershell
.\firmware\openrf1_motion_controller\scripts\flash.ps1
```

脚本会先列举 STLink，再写入、校验并复位目标板。若 CubeProgrammer
安装位置不同，可传入 `-ProgrammerCliPath`。

## 串口协议

| 命令 | 含义 |
| --- | --- |
| `W,a,b,c,d` | 锁存 CN1~CN4 四轮目标速度，单位 m/s |
| `M,ch,pwm` | 单通道原始 PWM 诊断，`pwm ∈ [-1000,1000]` |
| `E,ch` | 查询累计编码器计数和最近窗口增量 |
| `D,ch` | 查询 A/B 相位、TIM 原始计数和软件累计值 |
| `STOP` | 立即停车并清空控制状态 |

固定回传包括：

```text
CSR_RF1_READY
ACK:W / ACK:M / ACK:E / ACK:D / ACK:STOP
VEL,...
PWM,...
NAVDBG,...
ENC,...
DBG,...
```

## 当前控制参数

参数统一定义在 [`User/csr_board_map.h`](User/csr_board_map.h)。

| 参数 | 当前值 | 含义 |
| --- | ---: | --- |
| `CSR_CONTROL_PERIOD_MS` | 20ms | 闭环频率 50Hz |
| `CSR_WHEEL_RESOLUTION` | 1768 | 输出轴每圈编码器计数 |
| `CSR_WHEEL_DIAMETER_M` | 0.06m | 当前轮径 |
| `CSR_WHEEL_ACC_LIMIT_MPS2` | 2.5 | 目标轮速斜坡上限 |
| `CSR_PI_KP_DEFAULT` | 200 | 增量 PI 比例项 |
| `CSR_PI_KI_DEFAULT` | 2500 | 增量 PI 积分项 |
| `CSR_INPUT_PWM_MAX` | 1000 | 控制层绝对输出上限 |
| `CSR_VEL_FILTER_ALPHA` | 0.35 | 编码器速度一阶低通系数 |
| `CSR_W_COMMAND_TIMEOUT_MS` | 250ms | 闭环命令丢失停车 |

## 维护规则

1. 只修改 `User/` 下这一套 `csr_*` 源码。
2. 不得再复制第二份 `csr_board_map.h` 到工程根目录。
3. 轮序固定为 `CN1/LR、CN2/LF、CN3/RR、CN4/RF`。
4. 修改轮径、编码器分辨率、PI 或方向表后，必须同步更新验证文档。
5. 新源码和注释统一使用 UTF-8。

