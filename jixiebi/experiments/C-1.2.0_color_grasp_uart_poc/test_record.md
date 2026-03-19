# C-1.2.0 OpenMV 实验记录

## 1. 当前状态

- 受控实验副本：已建立
- `main.py`：已增加夹爪原语抽象、分层恢复模式和结果回传保留
- `claw_selftest.py`：已新增，用于独立验证夹爪 `OPEN / CLOSE / OPEN`
- `claw_runtime.py`：已新增，作为夹爪共享原语与默认参数源
- `cj_link.py`：已保留，继续承担结果回传协议
- 实板测试：未执行

## 2. 当前冻结参数

- `CLAW_OPEN_ANGLE = 60`
- `CLAW_CLOSE_ANGLE = 150`
- `CLAW_TEST_DELAY_MS = 1000`
- `RED_THRESHOLD = [(38, 76, 22, 59, 0, 28)]`
- `YELLOW_THRESHOLD = [(53, 99, -13, 46, 29, 57)]`
- `BLUE_THRESHOLD = [(33, 80, -31, 18, -56, -21)]`
- `PIXELS_THRESHOLD = 500`
- `STABLE_FRAMES_REQUIRED = 3`
- `VERTICAL_BIAS = -30`
- `WAIT_PICK_WINDOW_TIMEOUT_MS = 2000`
- `LOCAL_PICK_FALLBACK_DELAY_MS = 1400`
- `COLOR_FOUND_RETRY_INTERVAL_MS = 400`
- `MAX_COLOR_FOUND_RETRIES = 4`
- `DEFAULT_PICK_WINDOW_MS = 10000`
- `POST_PICK_COOLDOWN_MS = 1800`

## 3. 当前运行模式

- `MODE_CLAW_SELFTEST`
- `MODE_FORCE_LOCAL_GRAB`
- `MODE_VISION_LOCAL_GRAB`
- `MODE_CJ_LINKED`

当前默认恢复入口建议：

1. 先部署 `claw_selftest.py`
2. 再部署 `main.py` 并优先用 `MODE_FORCE_LOCAL_GRAB`

## 4. 当前可观察节点

终端至少应能看到：

- `CLAW_TEST -> OPEN/CLOSE/OPEN`
- `GRAB -> CLOSE_CLAW`
- `GRAB -> LIFT`
- `GRAB -> MOVE_TO_DROP`
- `GRAB -> OPEN_CLAW`
- `GRAB -> RESET_POSE`

## 5. 计划验证项

1. 板端文件完整，不再出现 `ImportError`
2. `claw_selftest.py` 肉眼确认 `OPEN -> CLOSE -> OPEN`
3. 跑离散角度扫描，确认当前实物有效开/合值
4. `MODE_FORCE_LOCAL_GRAB` 下完成一次最小抓取/放置/回位
5. `MODE_VISION_LOCAL_GRAB` 下完成识别后本地抓取
6. 最后再把结果挂回 `MODE_CJ_LINKED`

## 6. 当前已知限制

- 当前 `60 / 150` 只是冻结值，还不是实测确认值
- `B10 + Timer2 Channel3` 本轮先继续沿用；若自检完全无动作，应优先怀疑通道/供电/复用问题
- 本轮不再优先调 `WAIT_PICK_WINDOW / PICK_WINDOW`，而是优先验证夹爪原语是否已恢复
