# csrpi_edge_relay

树莓派主动连接后端 WebSocket 的 ROS 中继包，用于上传 odom、IMU、雷达和多功能状态，
并将后端控制命令转换为本地 ROS 话题。

| 文件 | 用途 |
| --- | --- |
| [`scripts/edge_relay.py`](scripts/edge_relay.py) | WebSocket 重连、遥测和控制转换 |
| [`launch/edge_relay.launch`](launch/edge_relay.launch) | ROS 参数与话题入口 |
| [`README_edge_relay.md`](README_edge_relay.md) | C-3.2.4 早期联调记录 |

## 主要接口

| 方向 | 默认接口 | 说明 |
| --- | --- | --- |
| 订阅 | `/odom_lsm`、`/imu/data`、`/scan` | 上传机器人状态和障碍摘要 |
| 发布 | `/cmd_vel` | 后端手动速度；当前整车入口会覆盖为 `/cmd_vel_nav` |
| 发布/订阅 | `/fans/enable`、风机 PWM/RPM、顶盖状态 | 多功能控制与状态同步 |

当前推荐由 `catkin_ws/run_robot_hardware_multifunction.sh` 统一启动，不要在导航链运行时
另起第二个 relay。新增部署应通过启动环境或本机配置注入设备令牌，不在新文档中记录凭据。
