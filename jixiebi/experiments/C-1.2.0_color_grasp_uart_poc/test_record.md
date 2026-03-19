# C-1.2.0 OpenMV 实验记录

## 1. 当前状态

- 受控实验副本：已建立
- `main.py`：已增加 `WAIT_PICK_WINDOW` 状态门
- `cj_link.py`：已实现最小帧协议
- 实板测试：未执行

## 2. 计划验证项

1. `COLOR_FOUND` 连续 3 帧稳定上报
2. 未收到 `PICK_WINDOW` 前不进入抓取动作
3. 收到 `PICK_WINDOW` 后回 `ARM_BUSY`
4. 抓取成功回 `PICK_DONE`
5. 超过 `10 s` 未完成回 `PICK_TIMEOUT`
6. `WAIT_PICK_WINDOW` 阶段收到 `ABORT` 能回到扫描态

## 3. 本轮已知限制

- 协议端点仍是 `OpenMV` 直出，不是最终的 `J-STM32` 统一收口
- 抓取动作本体仍保留 vendor 例程的阻塞式序列
- 尚未完成真实串口往返和抓取现象记录