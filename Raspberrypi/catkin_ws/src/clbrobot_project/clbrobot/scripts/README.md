# clbrobot Scripts

此目录目前只保存 RF1 协议层的独立烟测工具，不是日常整车启动入口。

| 路径 | 用途 |
| --- | --- |
| [`rf1_bridge/README.md`](rf1_bridge/README.md) | RF1 工具使用说明 |
| [`rf1_bridge/PROTOCOL.md`](rf1_bridge/PROTOCOL.md) | RF1 串口协议记录 |
| [`rf1_bridge/openrf1_min_bridge_smoketest.py`](rf1_bridge/openrf1_min_bridge_smoketest.py) | 最小桥接烟测 |
| [`rf1_bridge/openrf1_smoketest.py`](rf1_bridge/openrf1_smoketest.py) | 完整协议烟测 |

涉及实车电机输出时，先架空车轮或留出安全区域。正式 ROS 底盘链位于
`csrpi_base_bridge`，不要在此复制第二套驱动实现。
