# CleanScout_rover

实验室清扫巡检系统仓库。  
当前仓名与工程代号仍为 `CleanScout_rover`，但当前统一对内口径已收拢为“实验室清扫巡检系统”。

## 1. 项目定位

当前项目不是单独做一个会吸尘的小车、一个独立机械臂或一个独立飞行器，而是在尝试构建面向实验室场景的综合运维系统。

当前主线目标包括：

- 近地面移动与基础清扫
- 日常巡检与异常发现
- 近场接近与局部处置
- 结果留痕与后续协同

当前统一角色口径：

- `C`：车体 / 小车本体，当前核心地面终端与主线原型
- `J`：机械臂，近场操作与局部处置候选子系统
- `FSD`：飞行器，高位感知与协同扩展候选子系统

管理总纲见：

- `docs/before_all.md`

## 2. 当前文档入口

### 2.1 系统定位

- `docs/SYSTEM/C-1.1.6_lab_system_positioning.md`

### 2.2 C 线硬件与软件冻结

- `docs/HARDWARE/C-1.1.1_hardware_freeze.md`
- `docs/HARDWARE/C-1.1.1_pin_budget.md`
- `docs/HARDWARE/C-1.1.1_power_and_relay_plan.md`
- `docs/SOFTWARE/C-1.1.3B_protocol_freeze.md`
- `docs/SOFTWARE/C-1.1.3B_event_vs_mode.md`
- `docs/SOFTWARE/C-1.1.3B_test_cases.md`
- `docs/PLAN/C-1.2.0.md`
- `docs/SOFTWARE/C-1.2.0_cj_comm_poc_protocol.md`
- `docs/HARDWARE/C-1.2.0_cj_comm_wiring.md`
- `docs/VERIFY/C-1.2.0_test_log.md`

### 2.3 J 线资料评估

- `docs/JLINE/C-1.1.6_J_line_material_inventory.md`
- `docs/JLINE/C-1.1.6_J_line_system_assessment.md`

### 2.4 J 线受控实验副本

- `jixiebi/experiments/C-1.2.0_color_grasp_uart_poc/README.md`
- `jixiebi/experiments/C-1.2.0_color_grasp_uart_poc/wiring.md`
- `jixiebi/experiments/C-1.2.0_color_grasp_uart_poc/test_record.md`

说明：

- `J-jixiebi/` 当前未纳入 Git 历史。
- `J-jixiebi/` 仍作为卖家原始资料证据链保留。
- `jixiebi/` 目录中的 `C-1.2.0` 内容是受控实验副本，可继续二开。

### 2.5 树莓派端发布入口

- `Raspberrypi/README.md`
- `Raspberrypi/releases/README.md`
- `docs/PLAN/C-2.0.5_raspberrypi_publish_path.md`

说明：

- `Raspberrypi/` 用于承接树莓派侧由 `opencode` 或本地端独立推进的结果发布。
- 树莓派端每轮结果先在 `Raspberrypi/releases/` 下按版本目录留痕。
- 树莓派端与当前 `UNO + AFMotor` 基线隔离推进，需回写主线时再单独立项。

## 3. 当前阶段判断

- `C` 线已经具备核心终端原型地位，当前仓库中的受控代码与构建流程仍以 C 线为主。
- `J` 线已进入“资料归纳 + 主线适配判断”阶段，当前更像半开放二开平台，不是纯黑盒，也不是已成熟可直接并线模块。
- `FSD` 线当前未在本仓纳入本地材料，因此只保留系统角色接口，不在本轮做事实评估。

## 4. C 线工程基线

当前 C 线仍沿用 `Tyler` 基线收编路线：

- 上游原始基线：`Tyler_1_Library/`
- 受控维护副本：`libraries/Tyler_1/`
- 风机控制模块：`libraries/CleanScoutFan/`
- 电机驱动依赖：`Adafruit-Motor-Shield-library-master/`
- 标准编译入口：`sketches/c002_uno_baseline/c002_uno_baseline.ino`

当前 C 线硬件冻结摘要：

- 风机方案当前仅为继电器开关版，不包含调速实现
- 蓝牙当前作为下行控制通道
- 主控与 IO 余量有限，后续扩展可能触发重评估
- `C-1.2.0` 已新增 `UNO <-> F411 <-> J(OpenMV)` 最小双向通信闭环的软件骨架

## 5. Windows 环境准备（arduino-cli 标准）

### 5.1 安装 arduino-cli

可选方案：

1. 官方安装文档：<https://docs.arduino.cc/arduino-cli/installation/>
2. 使用 VSCode Arduino Community Edition 插件内置 `arduino-cli`

安装后确认：

```powershell
arduino-cli version
```

### 5.2 安装 UNO core

```powershell
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib update-index
arduino-cli lib install Servo
```

或直接运行：

```powershell
.\tools\setup_arduino_cli.ps1
```

## 6. C 线标准编译入口

推荐：

```powershell
.\tools\compile_uno_cli.ps1
```

回退：

```powershell
.\tools\compile_uno.ps1
```

Arduino IDE 直接 Verify 兼容入口：

```powershell
.\tools\install_sketchbook_links.ps1
```

`C-1.2.0` 的 F411 桥接最小产物构建：

```powershell
.\tools\build_f411_bridge.ps1
```

说明：

- 仓库脚本仍然是主标准入口
- Arduino IDE 直接 Verify 是兼容入口
- `"Servo.h" 对应多个库` 只是库选择提示，不是 `CleanScoutFan.h` 缺失的根因
- `build_f411_bridge.ps1` 当前只验证 F411 桥接源码能产出 `.elf/.hex`，不等同于实板 Gate0 已完成

## 7. VSCode 使用方式

- 默认构建任务：`C-0.0.2: compile UNO (arduino-cli)`
- 回退任务：`compile UNO (arduino-builder)`
- `.ino` 已在工作区配置中关联为 C++ 语法高亮

## 8. 第三方来源与许可证

详见：

- `THIRD_PARTY_NOTICES.md`

当前 `Tyler` 与 `AFMotor` 的许可证信息在仓内均未发现明确 `LICENSE` 文件，状态标记为“待核验”。

## 9. Git 纪律（摘要）

- 开工先 checkpoint，再施工提交
- 一轮只解决一类问题，保持可追踪、可回退
- 共享分支回退优先 `revert`

详细规则见：

- `docs/before_all.md`
