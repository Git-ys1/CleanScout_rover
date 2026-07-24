# 仍需实测的物理量

本文件只列尚未测得或仍为暂存值的项目。已经冻结的 PWM 零位、方向、逐关节线性系数、
限位、Servo004=1500、closed TCP 及当前手眼验证结果不在此重复。

## CLOSE/LIFT 前必须完成

| 待测量 | 必须采用的定义 | 写入位置/门禁 |
|---|---|---|
| Servo005 最大安全闭合 PWM | 正常电池电压、标准瓶在位、不得强顶连杆；记录命令与严格 PRAD 回读 | 独立测量记录审核后更新 `grasp.gripper_close_pwm` |
| 最大张开时夹爪内宽 | Servo005 位于已测张开 PWM 时，两实际接触面间净距 | 夹爪标定报告/物体宽度门禁 |
| 安全闭合时最小内宽 | 上述安全闭合 PWM 下，两实际接触面间净距 | 夹爪标定报告/物体宽度门禁 |
| 标准 bottle 夹持处直径 | 实际计划接触高度处瓶身直径，不量瓶盖 | `object_geometry.bottle_radius_m` 与 `object_surface_to_grasp_center_m` 的实测依据 |
| 计划夹持高度 | 两指实际接触中心相对桌面的高度 | `target_pixel_y_ratio`、高度补偿和调参报告 |
| 标准 bottle 质量 | 明确空瓶/装液状态 | LIFT 验收报告 |

上述 Servo005 安全闭合 PWM 和内宽证据未完成前，必须保持
`gripper_close_calibrated=false`。CLOSE、VERIFY、LIFT 与
`bash tools/run_bottle_stage.sh full` 必须在连接设备前拒绝；不得把候选 PWM、
串口写入成功或 Servo005 回读到位当成抓取许可。

## 仍需补强的通用精度测量

| 待测量 | 用途 |
|---|---|
| open TCP 相对 Servo004 定子/wrist 的三轴 XYZ | 取 Servo005 位于实测张开 PWM 时计划抓取区域中心；写入 `T_wrist_tcp_open` 后才能设置 `open_calibrated=true` |
| RGB optical 相对 Servo004 定子的直接 yaw/pitch/roll | 为当前三姿态静态目标验证补充独立 6-DoF 手眼证据 |
| 至少 5 个未参与求解的手眼验证姿态 | 独立统计 TCP 三维误差和图像重投影误差 |
| Servo005 PWM—夹爪内宽曲线 | 后续实现面向物体宽度的闭爪验证，而不是长期依赖单一 PWM |
