# C-1.2.0 OpenMV 颜色抓取 UART POC

本目录是 `C-1.2.0` 起的 J 线受控实验副本，当前已扩展到 `C-1.2.3` 的夹爪恢复阶段。

## 1. 目录说明

- `vendor_baseline_COLOR_AUTOcatch_ov2640.py`
  卖家原始基线副本，仅作为对照
- `main.py`
  当前受控实验入口，支持分层恢复模式
- `claw_selftest.py`
  夹爪独立自检入口
- `claw_runtime.py`
  夹爪共享原语与默认开合角定义
- `cj_link.py`
  `OpenMV UART1(A9/A10)` 串口协议辅助
- `pid.py`
  从卖家资料复制的依赖文件
- `deployment_checklist.md`
  OpenMV 板端部署清单
- `claw_calibration_notes.md`
  夹爪角度/PWM 标定记录
- `wiring.md`
  接线说明
- `test_record.md`
  实验记录

## 2. 当前恢复顺序

1. 先运行 `claw_selftest.py`
2. 再让 `main.py` 跑 `MODE_FORCE_LOCAL_GRAB`
3. 再跑 `MODE_VISION_LOCAL_GRAB`
4. 最后才恢复 `MODE_CJ_LINKED`

## 3. 当前边界

- `UNO` 本轮不动
- `F411` 本轮不主攻协议状态机
- 协议端点仍冻结为 `OpenMV UART1(A9/A10)`
- 不加载 `LCD / WiFi / 图传 / 卖家 APP` 相关功能
- 不把本轮扩成 `J-STM32` 统一对外接口工程
