# J-0.3.0 Magnetic Pick Baseline

## Scope
- Forked from `C-1.2.6_vendor_vision_grasp_baseline`
- `F411` 联调暂停
- 太阳能板问题不纳入本轮
- 本轮只做：
  - 黑色电容单目标识别
  - 金色螺帽单目标识别
  - 磁吸接近
  - 接触后抬起保持

## Runtime Files
- `main.py`: 磁吸接近状态机入口
- `vision.py`: 黑色电容 / 金色螺帽识别与 blob 二级过滤
- `actuator.py`: 继承 `C-1.2.5` 的执行边界，改成磁吸动作语义
- `pid.py`: 沿用仓内已验证版本

## Snapshot
- `vendor_baseline_snapshot/` 保存 `C-1.2.6` 的可回退基线
- 运行时代码不直接 import snapshot

## Frozen Motion Boundaries
- `PAN_CENTER_DEG = 0`
- `PAN_MIN_DEG = -90`
- `PAN_MAX_DEG = 90`
- `TILT_CENTER_DEG = 85`
- `TILT_MIN_DEG = 0`
- `TILT_MAX_DEG = 90`
- `CLAW_OPEN_ANGLE = -60`
- `CLAW_CLOSE_ANGLE = 40`

## State Machine
- `SCAN`
- `TRACK`
- `APPROACH_READY`
- `CONTACT`
- `LIFT`
- `HOLD`
- `RESET`

## Runtime Defaults
- `TARGET_MODE = TARGET_MODE_BLACK_CAP`
- `ENABLE_SECOND_TARGET = False`
- 默认搜索位：`pan=0, tilt=85, claw=closed`

## Hardware Notes
- 黑色电容和金色螺帽都必须先做手工磁铁试吸
- 本轮代码可以先跑通主链，但“磁吸成功”结论只以实物试吸和 `HOLD` 观察为准
