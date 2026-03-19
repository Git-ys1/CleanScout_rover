# OpenMV 部署清单（C-1.2.4）

## 1. 目标

本清单用于冻结 `C-1.2.4` 的 OpenMV 板端部署包，避免再次出现缺文件导致的：

- `ImportError`
- 启动即异常退出
- 运行中自动重启

## 2. 标准实验入口的板端文件

当你要运行当前受控实验 `main.py` 时，板端最小部署包固定为：

- `main.py`
- `claw_selftest.py`
- `claw_runtime.py`
- `cj_link.py`
- `pid.py`

## 3. Vendor 直通 smoke test 入口

### 3.1 vendor_claw_smoketest.py

部署规则：

- 板端 `main.py` 必须直接来自 `vendor_claw_smoketest.py`
- 这是独立 smoke test，不与实验 `main.py` 共享入口
- 该脚本不依赖：
  - `claw_runtime.py`
  - `cj_link.py`
  - `pid.py`

用途：

- 直接复刻卖家 `Timer(2) + CH3 + B10` 夹爪链路
- 只看 `60 -> 150 -> 60` 是否能让夹爪物理运动

### 3.2 vendor_pwm_sweep.py

部署规则：

- 板端 `main.py` 必须直接来自 `vendor_pwm_sweep.py`
- 这是独立 smoke test，不与实验 `main.py` 共享入口
- 该脚本不依赖：
  - `claw_runtime.py`
  - `cj_link.py`
  - `pid.py`

用途：

- 直接扫描 `2.5 / 5.0 / 7.5 / 10.0 / 12.5`
- 排除“60 / 150 只是当前实物无效角度”的干扰
## 4. 启动入口规则

### 4.1 夹爪自检

把 `claw_selftest.py` 保存为板端 `main.py`。

用途：

- 只验证夹爪 `OPEN / CLOSE / OPEN`
- 不依赖识别
- 不依赖通信

### 4.2 分层抓取恢复

把实验目录中的 `main.py` 保存为板端 `main.py`。

用途：

- `MODE_FORCE_LOCAL_GRAB`
- `MODE_VISION_LOCAL_GRAB`
- `MODE_CJ_LINKED`

## 5. 当前口径

- 当前固件字符串：`MicroPython 38050c2-dirty OpenMV 38050c2-dirty 2025-02-11; MENGFEI_OPENMV4-STM32H7xx`
- 当前板型口径：`MENGFEI_OPENMV4-STM32H7xx`
- 当前固件判断：卖家定制固件口径

## 6. 上板前检查项

1. 板端文件名大小写与仓库内完全一致
2. 板上旧 `main.py` 已被本轮目标入口覆盖
3. 若运行受控实验入口，`claw_runtime.py`、`cj_link.py`、`pid.py` 都已同步进板端文件系统
4. 若运行 vendor smoke test，必须确认板端 `main.py` 已来自对应 vendor 脚本，而不是实验 `main.py`
5. 上电后连续运行 3 分钟，无 `ImportError`、无异常退出、无重启循环

## 7. 结论分支

- 若 `vendor_claw_smoketest.py` 能动，下一轮回到 `claw_runtime.py` / `main.py` 调用层排查
- 若 `vendor_claw_smoketest.py` 和 `vendor_pwm_sweep.py` 都不动，本轮结论升级为板级/固件/接线/供电问题
