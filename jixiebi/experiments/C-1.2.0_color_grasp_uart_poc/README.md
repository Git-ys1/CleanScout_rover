# C-1.2.0 OpenMV 颜色抓取 UART POC

本目录是 `C-1.2.0` 的 J 线受控实验副本。

本轮目标不是继续堆卖家演示，而是把“颜色目标发现 -> 等待上层放行 -> 执行抓取 -> 回传结果”压成一个最小系统接口。

## 1. 目录说明

- `vendor_baseline_COLOR_AUTOcatch_ov2640.py`
  卖家原始基线副本，仅作为对照
- `main.py`
  本轮修改版入口
- `cj_link.py`
  `OpenMV UART1(A9/A10)` 串口协议辅助
- `pid.py`
  从卖家资料复制的依赖文件
- `wiring.md`
  本轮接线说明
- `test_record.md`
  本轮实验记录

## 2. 当前冻结行为

- 同一颜色目标连续 3 帧稳定成立后，才上报一次 `COLOR_FOUND`
- 上报后不立即抓取，而是进入 `WAIT_PICK_WINDOW`
- 只有收到 `PICK_WINDOW` 才执行抓取动作序列
- 抓取成功回 `PICK_DONE`
- 超过 `10 s` 未完成回 `PICK_TIMEOUT`
- 发生异常回 `ARM_FAIL`

## 3. 当前边界

- 协议端点本轮直接冻结为 `OpenMV UART1(A9/A10)`
- 不加载 `LCD / WiFi / 图传 / 卖家 APP` 相关功能
- 不把本轮扩成 `J-STM32` 统一对外接口工程
- `ABORT` 只保证在 `WAIT_PICK_WINDOW` 阶段生效

## 4. 来源说明

- 基线来源：
  `J-jixiebi/introduction and examples/03 梦飞openmv外接模块驱动代码例程/04 梦飞openmv三自由度机械臂/红黄蓝三色自动分拣/COLOR_AUTOcatch_ov2640.py`
- `pid.py` 来源：
  `J-jixiebi/introduction and examples/01 双轴云台搭配机械爪三自由简易机械臂例程/02 黄红蓝三色自动分拣/pid.py`

## 5. 下一步

1. 真实接入 `F411 USART1`
2. 验证 `COLOR_FOUND -> PICK_WINDOW -> PICK_DONE/PICK_TIMEOUT`
3. 再把 OpenMV 对外协议收敛到独立 `J-STM32`