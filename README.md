# CleanScout_rover

实验室清扫巡检系统主仓。当前仓库围绕车体 `C` 线展开，统一收纳底盘下位机、树莓派 ROS 上位机、机械臂实验副本、硬件资料和验证文档。

## 快速入口

| 入口 | 地址 / 文件 | 用途 |
| --- | --- | --- |
| 仓库总述 | [docs/C-3.4.2_仓库总述与导航.md](docs/C-3.4.2_仓库总述与导航.md) | 了解仓库定位、当前硬件、软件主线和阅读路径 |
| 快速上手 | [docs/快速上手.md](docs/快速上手.md) | 常用启动、编译、烧录、串口调试、Vue/H5/后端运维命令 |
| H5 正式入口 | [https://h5.hzhhds.top](https://h5.hzhhds.top) | 小程序 / H5 管理前端正式域名 |
| H5 Netlify 入口 | [https://cleanscoutrover-management.netlify.app](https://cleanscoutrover-management.netlify.app) | H5 托管平台备用/源站入口 |
| RF1 串口工具 | [tools/openrf1_serial_probe.ps1](tools/openrf1_serial_probe.ps1) | Windows 下位机串口调试入口 |
| RF1 固件工作区 | [_local/openrf1_keil_work_3/User/](./_local/openrf1_keil_work_3/User/) | 当前 OpenRF1 自写运行层源码 |

## 当前实物系统

| 层级 | 当前实物 / 模块 | 当前职责 |
| --- | --- | --- |
| 上位机 | Raspberry Pi 4B | ROS 工作区、传感器接入、系统协调、上层功能编排 |
| 下位机 | OpenRF1 / STM32F103RCT6 | 四轮底盘实时控制、编码器采样、闭环控制、串口协议 |
| 感知 | 思岚 A3、MPU6050 | 激光扫描、IMU 数据 |
| 执行 | 四轮霍尔编码麦轮、双风机、继电器、顶盖舵机 | 运动、清扫、开关控制 |
| 扩展 | OpenMV 机械臂 | 机械臂视觉与抓取实验线 |


## 仓库目录

| 路径 | 状态 | 说明 |
| --- | --- | --- |
| [docs/](docs/) | 主线文档 | 总述、计划、软件说明、验证记录、硬件速查 |
| [_local/openrf1_keil_work_3/](./_local/openrf1_keil_work_3/) | 当前 RF1 本地固件工作区 | OpenRF1 自写运行层，配合 Keil 工程编译烧录 |
| [Raspberrypi/](Raspberrypi/) | 树莓派 / ROS 工作区 | ROS 包、launch、脚本与发布目录 |
| [jixiebi/](jixiebi/) | 机械臂受控实验副本 | OpenMV / 机械臂实验线当前可读入口 |
| `vue3/`（外部工作区：`F:\Project\CSc——uniapp\vue3`） | 前后端 / 小程序 / H5 系统 | uni-app / H5 管理端、Node 后端、Edge 联调与云端发布体系 |
| [tools/](tools/) | 本地工具 | 串口探测、UNO/RF1 辅助脚本等 |

## 主线文档

| 方向 | 推荐入口 | 说明 |
| --- | --- | --- |
| 全局总览 | [C-3.4.2_仓库总述与导航](docs/C-3.4.2_仓库总述与导航.md) | 新同学先读这一份 |
| 快速操作 | [快速上手](docs/快速上手.md) | 启动 pigpiod、catkin_make、RF1 串口、H5/后端命令 |
| RF1 速查 | [OpenRF1_开发速查](docs/STM32F103RCT6/OpenRF1_开发速查.md) | OpenRF1 板级资源与接线事实 |
| RF1 协议 | [C-3.0.6_pid_close_loop_and_protocol_update](docs/SOFTWARE/C-3.0.6_pid_close_loop_and_protocol_update.md) | `W/M/E/D/STOP`、闭环周期、看门狗与遥测 |
| RF1 收敛 | [C-3.1.4B_openrf1_timer_final_convergence](docs/VERIFY/C-3.1.4B_openrf1_timer_final_convergence.md) | 原生定时器与编码器问题收敛证据 |
| RF1 方向热修 | [C-3.1.4C_openrf1_rear_wheel_direction_hotfix](docs/VERIFY/C-3.1.4C_openrf1_rear_wheel_direction_hotfix.md) | CN1/CN3 方向与后轮热修记录 |
| RF1 平滑调试 | [C-3.1.4D_openrf1_closed_loop_smoothing](docs/VERIFY/C-3.1.4D_openrf1_closed_loop_smoothing.md) | 闭环平顺性调参记录 |
| 树莓派 | [Raspberrypi/README.md](Raspberrypi/README.md) | ROS 上位机入口 |
| 机械臂 | [jixiebi/](jixiebi/) | 机械臂实验入口 |


