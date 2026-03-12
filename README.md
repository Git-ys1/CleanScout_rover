# CleanScout_rover

实验室清扫巡检车项目（CleanScout_rover）立项仓库。

当前阶段目标是先完成 C 线（车体）基线纳管：将既有 `Tyler_1_Library` 原样接入版本管理，形成可追踪、可回退、可继续拆解任务的 C-0.0.x 基础版本。

## 1. 项目定位

- 项目代号：`CleanScout_rover`
- 子系统：
- `C`：车体 / 小车本体（当前主线）
- `J`：机械臂（当前仅保留文档与版本位）
- 管理总纲：`docs/before_all.md`

> 本仓库当前优先做“建立基线”，不在首轮导入时改动底层逻辑和控制策略。

## 2. 目录结构

```text
CleanScout_rover/
├─ docs/
│  └─ before_all.md               # 项目立项前总纲（角色、版本、Git纪律）
└─ Tyler_1_Library/               # 既有 Arduino 小车库（C 线基线）
   ├─ Tyler_1.h
   ├─ Tyler_1.cpp
   ├─ keywords.txt
   ├─ README.md
   └─ examples/
      ├─ Tyler_1/Tyler_1.ino      # 主控制示例
      ├─ Check_1~7_*.ino          # 舵机/测距/蓝牙/电机/转向标定示例
```

## 3. C 线代码逻辑理解（Tyler_1_Library）

### 3.1 主入口

- 主控制示例：`Tyler_1_Library/examples/Tyler_1/Tyler_1.ino`
- `setup()`：
- 初始化蓝牙软串口（`SoftwareSerial`）
- 初始化头部舵机并设为 90 度
- `loop()`：
- 持续读取蓝牙控制字符
- 根据模式分发到手动/体感或自动避障逻辑

### 3.2 电机驱动方式

- 封装类：`Tyler_1`（定义在 `Tyler_1.h/.cpp`）
- 依赖 `AFMotor`，使用 4 路 `AF_DCMotor(1..4)` 控制底盘
- 构造函数支持传入每个电机方向映射参数（`dir1~dir4`），用于适配装配方向差异
- 提供基础动作接口：
- `forward / backward / turnL / turnR`
- `forwardL / forwardR / backwardL / backwardR`
- `stop`

### 3.3 传感器输入

- 超声波测距：`HC-SR04`（`Trig=A0`，`Echo=A1` 为示例默认）
- 通过 `getDistance()` 触发测距并返回厘米值
- 舵机负责“转头扫描”左右距离，支持自动避障决策

### 3.4 控制逻辑

- 运行模式：
- `MAN` 手动
- `GEST` 体感（复用手动控制字符）
- `AUTO` 自动避障
- 控制字符（蓝牙）：
- 运动：`8/2/4/6/5/7/9/1/3`
- 模式切换：`A/M/G`
- 自动避障流程（`autoMode + autoTurn`）：
- 正前方距离大于阈值（默认 `OK_DIST=35cm`）则前进
- 否则停车，舵机扫描左右距离后选择更大一侧并按设定延时转向

### 3.5 依赖库

- `AFMotor`（Adafruit Motor Shield 相关库）
- `Servo`（Arduino 内置）
- `SoftwareSerial`（Arduino 内置）

## 4. 当前阶段编译检查结论（C-0.0.1B）

已在本机完成 UNO 编译验证（使用你提供的 Arduino 安装路径）：

- Arduino 工具链路径：`F:\AcademicHub\Arduino`
- 编译目标：`arduino:avr:uno`
- 示例入口：`Tyler_1_Library/examples/Tyler_1/Tyler_1.ino`
- 编译结果：通过
- 占用：`Flash 6584 bytes (20%)`，`RAM 212 bytes (10%)`

说明：

- 当前环境虽未安装 `arduino-cli`，但可使用 `arduino-builder.exe` 完成命令行编译。
- AFMotor 库会出现若干上游 warning（如未使用参数），不影响当前示例编译通过。

可复现命令（PowerShell）：

```powershell
& "F:\AcademicHub\Arduino\arduino-builder.exe" `
  -compile `
  -hardware "F:\AcademicHub\Arduino\hardware" `
  -tools "F:\AcademicHub\Arduino\tools-builder" `
  -tools "F:\AcademicHub\Arduino\hardware\tools\avr" `
  -built-in-libraries "F:\AcademicHub\Arduino\libraries" `
  -libraries "F:\Project\CleanScout_rover" `
  -fqbn arduino:avr:uno `
  -build-path "F:\Project\CleanScout_rover\.build\tyler1_uno" `
  -warnings all `
  "F:\Project\CleanScout_rover\Tyler_1_Library\examples\Tyler_1\Tyler_1.ino"
```

仓库内也提供了脚本：`tools/compile_uno.ps1`。

## 5. VSCode 推荐环境

为保证后续 C 线稳定开发，建议在 VSCode 使用以下任一方案：

1. Arduino CLI 方案（推荐）
- 安装 `arduino-cli`
- 安装扩展：`Arduino`（Microsoft）或 `Arduino Community Edition`
- 安装 UNO 板卡 core：`arduino:avr`
- 在 CLI 或任务里调用 `arduino-cli compile`

2. Arduino IDE 1.x 工具链方案（当前可用）
- 保持 `F:\AcademicHub\Arduino` 可用
- 使用 `arduino-builder.exe` 命令行编译（本仓已验证）

3. PlatformIO 方案（可选）
- 安装 `PlatformIO IDE` 扩展
- 新建/迁移为 PlatformIO 工程后管理依赖与构建

## 6. 分支与版本约定（执行摘要）

- C/J 版本独立维护（示例：`C-0.0.1`、`J-0.0.1`）。
- 开工先 checkpoint，再进入施工提交。
- 功能开发走 `feature/...`，热修走 `hotfix/...`，实验走 `exp/...`。
- 共享分支回退优先 `revert`，避免改写公共历史。

详细规则见：`docs/before_all.md`。
