# cleanscout_navigation

CleanScout 的定点路线记录与顺序执行包。它复用现有 AMCL 和 `move_base`，
不替代底层规划器或速度安全链。

| 文件 | 用途 |
| --- | --- |
| [`scripts/record_current_pose.py`](scripts/record_current_pose.py) | 将当前 `/amcl_pose` 写入路线 YAML |
| [`scripts/route_executor.py`](scripts/route_executor.py) | 按路线点向 `move_base` action 发送目标 |
| [`config/routes.yaml`](config/routes.yaml) | 路线与停留时间配置 |
| [`launch/route_tools.launch`](launch/route_tools.launch) | 启动路线执行节点 |

## ROS 接口

| 类型 | 名称 | 说明 |
| --- | --- | --- |
| 订阅 | `/amcl_pose` | 当前定位结果，可通过参数覆盖 |
| Action 客户端 | `move_base` | 逐点导航 |
| 服务 | `start_route` | 启动默认路线 |
| 服务 | `cancel_route` | 取消当前路线 |
| 服务 | `get_route_status` | 查询执行状态 |

使用前必须先启动并确认完整导航链已定位成功。路线文件中的坐标属于 `map`
坐标系；更换地图后应重新记录或验证所有点位。
