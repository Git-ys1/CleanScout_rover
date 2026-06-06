# clbrobot_project

该目录是 CleanScout 整车编排层，目前包含一个 ROS 包。

| 路径 | 职责 |
| --- | --- |
| [`clbrobot/`](clbrobot/) | launch、参数、地图、URDF 和少量整车工具 |

整车入口优先通过 `catkin_ws` 顶层脚本调用，不建议直接拼装多个 launch，
否则容易重复发布 `/odom`、TF 或速度话题。
