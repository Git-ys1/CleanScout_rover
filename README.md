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

## 4. 当前阶段编译检查结论（C-0.0.1）

- 本地未检测到 `arduino-cli`，无法在当前环境直接执行 CLI 编译校验。
- 结论：源码已纳管并完成结构核对，但“自动化编译通过”待补工具链后执行。

建议后续补充步骤：

1. 安装 `arduino-cli` 与目标板卡 core（如 `arduino:avr`）。
2. 安装/确认 `AFMotor` 依赖。
3. 对 `examples/Tyler_1/Tyler_1.ino` 执行一次标准编译检查并留痕到文档或提交记录。

## 5. 分支与版本约定（执行摘要）

- C/J 版本独立维护（示例：`C-0.0.1`、`J-0.0.1`）。
- 开工先 checkpoint，再进入施工提交。
- 功能开发走 `feature/...`，热修走 `hotfix/...`，实验走 `exp/...`。
- 共享分支回退优先 `revert`，避免改写公共历史。

详细规则见：`docs/before_all.md`。
