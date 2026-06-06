# csrpi_openmv_bridge

OpenMV USB 串口与 ROS 话题之间的桥接包，支持自动重连、在线状态、事件和命令收发。

| 文件 | 用途 |
| --- | --- |
| [`scripts/openmv_usb_bridge.py`](scripts/openmv_usb_bridge.py) | 串口协议与 ROS 话题转换 |
| [`launch/openmv_usb_bridge.launch`](launch/openmv_usb_bridge.launch) | 串口、超时和重连参数 |

## ROS 接口

| 方向 | 话题 |
| --- | --- |
| 发布 | `/openmv/status_raw`、`/openmv/status`、`/openmv/event` |
| 发布 | `/openmv/ack`、`/openmv/error`、`/openmv/online` |
| 订阅 | `/openmv/cmd_mode`、`/openmv/cmd_observe_tilt` |
| 订阅 | `/openmv/cmd_ping`、`/openmv/cmd_status` |

默认串口为 `/dev/ttyACM0`、波特率为 `115200`。设备名不稳定时应新增 udev
规则并从 launch 覆盖 `port`，不要依赖 OpenMV 恰好枚举为第一个 ACM 设备。
