# CleanScout_rover

实验室清扫巡检车项目（CleanScout_rover）立项仓库。

当前主线为 C 系列（车体）。C-0.0.2 的目标是把 Tyler 基线收编为可长期维护的受控库，并建立 VSCode + arduino-cli 的标准编译流程。

当前硬件冻结版本为 `C-1.1.1`。

## 1. 项目定位

- 项目代号：`CleanScout_rover`
- 子系统：
- `C`：车体 / 小车本体（当前主线）
- `J`：机械臂（当前仅文档与版本位）
- 管理总纲：`docs/before_all.md`

## 2. C-0.0.2 继承关系（重点）

- 上游原始基线：`Tyler_1_Library/`（保留不改，作为证据链）
- 受控维护副本：`libraries/Tyler_1/`（后续二次开发基线）
- 电机驱动依赖：`Adafruit-Motor-Shield-library-master/`
- 标准编译入口：`sketches/c002_uno_baseline/c002_uno_baseline.ino`

本轮不做功能开发，不改 `Tyler_1` 外部 API，不改动作语义与默认控制流程。

## 2.1 C-1.1.1 Hardware Entry

当前硬件冻结文档入口：

- `docs/HARDWARE/C-1.1.1_hardware_freeze.md`
- `docs/HARDWARE/C-1.1.1_pin_budget.md`
- `docs/HARDWARE/C-1.1.1_power_and_relay_plan.md`

当前硬件冻结摘要：

- 当前风机方案仅为继电器开关版，不包含调速实现。
- 当前蓝牙为单向接法，仅作为下行控制通道。
- 当前硬件扩展余量有限，未来多传感器方案可能触发主控或 IO 重评估。

## 2.2 C-1.1.3B Software Entry

当前蓝牙协议冻结文档入口：

- `docs/SOFTWARE/C-1.1.3B_protocol_freeze.md`
- `docs/SOFTWARE/C-1.1.3B_event_vs_mode.md`
- `docs/SOFTWARE/C-1.1.3B_test_cases.md`

当前 `C-1.1.3B` 协议摘要：

- `A`：进入自动模式
- `M`：进入手动模式
- `T`：进入体感模式
- `G`：一次性风机翻转事件
- 自动模式下 `G` 无效但立即消费，不改变当前模式
- `Tyler_1_Library/` 中旧协议仅作为上游历史证据，不作为现行协议依据

## 3. 目录结构

```text
CleanScout_rover/
├─ docs/
│  ├─ before_all.md
│  └─ PLAN/
├─ Tyler_1_Library/                         # 原始基线（保留不改）
├─ libraries/
│  └─ Tyler_1/                              # 受控副本
├─ Adafruit-Motor-Shield-library-master/    # AFMotor 依赖
├─ sketches/
│  └─ c002_uno_baseline/
│     └─ c002_uno_baseline.ino              # 标准编译入口
├─ tools/
│  ├─ compile_uno_cli.ps1                   # 标准（arduino-cli）
│  ├─ setup_arduino_cli.ps1                 # 安装/初始化 core
│  └─ compile_uno.ps1                       # 回退（arduino-builder）
└─ .vscode/
   ├─ tasks.json
   └─ settings.json
```

## 4. Windows 环境准备（arduino-cli 标准）

### 4.1 安装 arduino-cli

可选方案：

1. 官方安装文档：<https://docs.arduino.cc/arduino-cli/installation/>
2. 使用 VSCode Arduino Community Edition 插件内置 `arduino-cli`（本仓脚本会自动尝试探测）

安装后请确认：

```powershell
arduino-cli version
```

### 4.2 安装 UNO core

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

## 5. 标准编译入口

标准命令（推荐）：

```powershell
.\tools\compile_uno_cli.ps1
```

该脚本会：

- 检查 `arduino-cli` 可用性
- 检查 `arduino:avr` core 是否安装
- 检查 `Servo` 库是否安装
- 以 `arduino:avr:uno` 编译 `sketches/c002_uno_baseline/`
- 显式指定库路径（`libraries/` + `Adafruit-Motor-Shield-library-master`）

回退命令（过渡方案）：

```powershell
.\tools\compile_uno.ps1
```

## 5.1 Arduino IDE 直接 Verify 兼容

如果你希望在 Arduino IDE 或插件里直接点 Verify，而不是只走仓库脚本，请先运行：

```powershell
.\tools\install_sketchbook_links.ps1
```

该脚本会把仓库内需要的库补到 Arduino sketchbook，避免出现：

- `CleanScoutFan.h: No such file or directory`

说明：

- 仓库脚本仍然是官方主标准入口。
- Arduino IDE 直接 Verify 是兼容入口。
- 若 sketchbook 中已存在兼容库，脚本会保留现有库，不会直接覆盖。
- `"Servo.h" 对应多个库` 只是库选择提示，不是 `CleanScoutFan.h` 缺失的根因。

## 6. VSCode 使用方式

- 默认构建任务：`C-0.0.2: compile UNO (arduino-cli)`
- 回退任务：`compile UNO (arduino-builder)`
- `.ino` 已在工作区配置中关联为 C++ 语法高亮。

## 7. 第三方来源与许可证

详见：

- `THIRD_PARTY_NOTICES.md`

当前 Tyler 与 AFMotor 的许可证信息在仓内均未发现明确 LICENSE 文件，状态标记为“待核验”。

## 8. Git 纪律（摘要）

- 开工先 checkpoint，再施工提交。
- 一轮只做一类问题，保持可追踪、可回退。
- 共享分支回退优先 `revert`，避免改写公共历史。

详细规则见：`docs/before_all.md`。
