# C-1.2.0 OpenMV 实验记录

## 1. 当前状态

- 受控实验副本：已建立
- `main.py`：已增加 `WAIT_PICK_WINDOW` 状态门、状态叠加、重发、超时回退和本地抓取回退
- `cj_link.py`：已实现最小帧协议
- 实板测试：未执行

## 2. 当前冻结参数

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

## 3. 当前可观察状态

OpenMV IDE 画面与终端应能看到以下状态：

- `SCAN`
- `COLOR_FOUND`（事件提示）
- `WAIT_PICK_WINDOW`
- `LOCAL_PICK_FALLBACK`
- `PICKING`
- `DONE`
- `TIMEOUT`
- `FAIL`

## 4. 计划验证项

1. `COLOR_FOUND` 连续 3 帧稳定上报
2. 未收到 `PICK_WINDOW` 前不立即抓取
3. `WAIT_PICK_WINDOW` 期间每 `400 ms` 重发一次 `COLOR_FOUND`
4. 超过 `1400 ms` 且目标仍在视野里时，进入 `LOCAL_PICK_FALLBACK`
5. 本地回退抓取后继续回发 `PICK_DONE / PICK_TIMEOUT / ARM_FAIL`
6. 超过 `2000 ms` 仍未放行且目标丢失时回到 `SCAN`
7. `WAIT_PICK_WINDOW` 阶段收到 `ABORT` 能回到扫描态
8. 结果后进入最小冷却窗口，避免马上重触发

## 5. 本轮已知限制

- 协议端点仍是 `OpenMV` 直出，不是最终的 `J-STM32` 统一收口
- 抓取动作本体仍保留 vendor 例程的阻塞式序列
- 尚未完成真实串口往返和抓取现象记录
- 当前识别稳健性仍受现场光照、镜像/翻转和阈值影响
- 本地抓取回退是当前 bring-up 过渡策略，不是最终系统行为
