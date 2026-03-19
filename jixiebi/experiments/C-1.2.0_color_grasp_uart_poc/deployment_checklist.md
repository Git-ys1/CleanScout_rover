# OpenMV 部署清单（C-1.2.3）

## 1. 目标

本清单用于冻结 `C-1.2.3` 的 OpenMV 板端部署包，避免再次出现缺文件导致的：

- `ImportError`
- 启动即异常退出
- 运行中自动重启

## 2. 板端应存在的文件

本轮最小部署包固定为：

- `main.py`
- `claw_selftest.py`
- `claw_runtime.py`
- `cj_link.py`
- `pid.py`

## 3. 启动入口规则

### 3.1 夹爪自检

把 `claw_selftest.py` 保存为板端 `main.py`。

用途：

- 只验证夹爪 `OPEN / CLOSE / OPEN`
- 不依赖识别
- 不依赖通信

### 3.2 分层抓取恢复

把实验目录中的 `main.py` 保存为板端 `main.py`。

用途：

- `MODE_FORCE_LOCAL_GRAB`
- `MODE_VISION_LOCAL_GRAB`
- `MODE_CJ_LINKED`

## 4. 当前口径

- 当前固件字符串：`MicroPython 38050c2-dirty OpenMV 38050c2-dirty 2025-02-11; MENGFEI_OPENMV4-STM32H7xx`
- 当前板型口径：`MENGFEI_OPENMV4-STM32H7xx`
- 当前固件判断：卖家定制固件口径

## 5. 上板前检查项

1. 板端文件名大小写与仓库内完全一致
2. 板上旧 `main.py` 已被本轮目标入口覆盖
3. `claw_runtime.py`、`cj_link.py`、`pid.py` 都已同步进板端文件系统
4. 上电后连续运行 3 分钟，无 `ImportError`、无异常退出、无重启循环
