# CleanScout_rover

实验室清扫巡检系统主仓。

当前这个仓库不再只是“一个小车代码仓”，而是围绕车体 `C` 线展开的统一工程仓，包含：

- `OpenRF1` 下位机固件
- `Raspberry Pi 4B + ROS` 上位机工作区
- 机械臂 `J` 线受控实验副本
- 硬件/软件/验证/交接文档

## 1. 如果你只读一个文件

先读：

- [docs/C-3.4.2_仓库总述与导航.md](docs/C-3.4.2_仓库总述与导航.md)

这份文档是当前仓库的统一总述，专门用来回答：

- 这个仓库现在到底是什么
- 当前实物硬件是什么
- 当前软件主线是什么
- 新同学应该先看哪里

## 2. 当前实物系统一句话

当前主车实物已经收敛为：

- 上位机：`Raspberry Pi 4B`
- 下位机：`OpenRF1 (STM32F103RCT6)`
- 感知：`思岚 A3` 激光雷达、`MPU6050`
- 执行：四轮霍尔编码麦轮底盘、双风机、继电器、顶盖舵机
- 扩展：`OpenMV` 机械臂

也就是：

**树莓派负责 ROS 与系统协调，OpenRF1 负责底盘实时控制。**

## 3. 仓库主入口

### 3.1 总述与交接

- [仓库总述与导航](docs/C-3.4.2_仓库总述与导航.md)
- [项目退休交接总包](docs/clean_scout_rover_退休交接总包.md)
- [树莓派 4B / OpenClaw 交接书](docs/OpenClaw_树莓派4B_项目交接书.md)

### 3.2 操作与调试

- [操作指令速查](docs/000操作指令)
- [`tools/`](tools/)

### 3.3 OpenRF1 / STM32 下位机

- [OpenRF1 开发速查](docs/STM32F103RCT6/OpenRF1_开发速查.md)
- [OpenRF1 运行时基线](docs/SOFTWARE/C-3.0.4_openrf1_runtime_baseline.md)
- [OpenRF1 闭环与协议更新](docs/SOFTWARE/C-3.0.6_pid_close_loop_and_protocol_update.md)
- [OpenRF1 定时器复测收敛](docs/VERIFY/C-3.1.4B_openrf1_timer_final_convergence.md)
- [OpenRF1 后轮方向热修](docs/VERIFY/C-3.1.4C_openrf1_rear_wheel_direction_hotfix.md)
- [OpenRF1 闭环平滑调试](docs/VERIFY/C-3.1.4D_openrf1_closed_loop_smoothing.md)
- 当前本地固件工作副本：
  - [`_local/openrf1_keil_work_3/`](./_local/openrf1_keil_work_3/)

### 3.4 Raspberry Pi / ROS 上位机

- [`Raspberrypi/README.md`](Raspberrypi/README.md)
- [`Raspberrypi/releases/`](Raspberrypi/releases/)

### 3.5 机械臂 J 线

- [`jixiebi/`](jixiebi/)
- `J-jixiebi/` 仅保留为原始资料/历史脏目录，不是当前规范主线

## 4. 当前仓库结构怎么理解

### `docs/`

文档主入口。  
优先看这里，不要先从分支名和零散提交猜项目状态。

### `_local/`

本地工作副本、Keil 工程、vendor 对照副本。  
当前 RF1 底层最重要的施工目录在这里。

### `Raspberrypi/`

树莓派 ROS 工作区、脚本与发布目录。

### `jixiebi/`

机械臂受控实验副本。

### `tools/`

本地构建、串口测试、辅助脚本入口。

## 5. 阅读建议

### 想先搞清全貌

1. [仓库总述与导航](docs/C-3.4.2_仓库总述与导航.md)
2. [项目退休交接总包](docs/clean_scout_rover_退休交接总包.md)
3. [树莓派 4B / OpenClaw 交接书](docs/OpenClaw_树莓派4B_项目交接书.md)

### 想先看底盘

1. [OpenRF1 开发速查](docs/STM32F103RCT6/OpenRF1_开发速查.md)
2. [OpenRF1 运行时基线](docs/SOFTWARE/C-3.0.4_openrf1_runtime_baseline.md)
3. [OpenRF1 闭环与协议更新](docs/SOFTWARE/C-3.0.6_pid_close_loop_and_protocol_update.md)
4. [`_local/openrf1_keil_work_3/`](./_local/openrf1_keil_work_3/)

### 想先看树莓派

1. [`Raspberrypi/README.md`](Raspberrypi/README.md)
2. [`Raspberrypi/releases/`](Raspberrypi/releases/)
3. [树莓派 4B / OpenClaw 交接书](docs/OpenClaw_树莓派4B_项目交接书.md)

### 想先看机械臂

1. [`jixiebi/`](jixiebi/)
2. `C-1.2.5_vendor_actuator_baseline`
3. `C-1.2.6_vendor_vision_grasp_baseline`

## 6. 当前 README 的定位

这份 `README` 现在只承担两件事：

1. 告诉你这个仓库当前是什么
2. 把你跳转到正确的文档入口

具体阶段细节、冻结结论、验证记录，不再继续直接堆在首页，而统一收口到：

- [docs/C-3.4.2_仓库总述与导航.md](docs/C-3.4.2_仓库总述与导航.md)
