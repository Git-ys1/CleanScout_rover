# Arm Grasp Pipeline

`arm_grasp_pipeline/` 是独立于 ROS 的 D435 + RKNN YOLO11 固定观察姿态抓取管线。
C-5.2.4 不通过目标位置对应 PWM，也不通过检测框面积估距；目标位置来自 aligned
depth、相机反投影、实测 `T_base_camera_reference` 和机械臂 IK。

## C-5.2.4 当前状态

- 13 个唯一对应点经刚体一致性审查后保留 11 点，剔除 2 个异常点。
- 固定视角矩阵已通过质量门禁：RMSE `5.85 mm`，最大误差 `9.71 mm`。
- 当前瓶子位置完成 `OPEN -> PRE_GRASP -> APPROACH -> CLOSE -> LIFT` 全流程 dry-run。
- 为满足水平接近路径的 IK 可达性，当前抓取俯仰角为 `35 deg`。
- 尚未执行真实抓取；`kinematics.calibrated=false` 和
  `serial.joint_pwm_calibrated=false` 继续阻止真实输出。

本轮冻结证据位于：

- `config/base_camera_points.consolidated11.csv`
- `config/base_camera_report.consolidated11.json`
- `config/base_camera_consolidation_audit.json`

## 坐标系

| 坐标系 | 轴定义 |
| --- | --- |
| `camera_color_optical` | RealSense 彩色光学坐标，`+X` 图像向右、`+Y` 图像向下、`+Z` 镜头向前 |
| `arm_base` | 机械臂底座坐标，`+X` 向前、`+Y` 向左、`+Z` 向上，单位为米 |

固定观察矩阵方向只有一种：

```text
p_base = R_base_camera * p_camera + t_base_camera
p_base_h = T_base_camera_reference * p_camera_h
```

`T_base_camera_reference` 只在配置中的
`reference_servo_pwms=[1380,1909,1900,620,1500,1500]` 有效。真实抓取不会调用
`estimate_tool_matrix_from_pwm`，也不会使用旧 `manual_seed`。

## 标定

### 1. 一行数据代表什么

每一行是**同一个实体标记点**在两个坐标系下的位置：

- `camera_x/y/z`：D435 aligned depth 自动测得，工具负责填写。
- `base_x/y/z`：从 Servo000 竖直轴与底座安装平面的交点量到该标记点，人工实测后在终端输入。

底座坐标必须按 `X=向前、Y=向左、Z=向上` 测量。终端输入单位是毫米，CSV
自动换算成米。例如标记点位于底座原点前方 230 mm、右侧 60 mm、高 85 mm，输入：

```text
230,-60,85
```

右侧对应负 `Y`，因此是 `-60`。不能把瓶子检测框中心、桌面上另一个点或估算的
舵机 FK 坐标填进来；相机点击处和卷尺测量处必须是同一物理点。

### 2. 标记物与采点布局

使用一个平整、边长约 15--30 mm、中心清楚的标记面；点击标记面中心，同时测量该
中心。推荐准备直尺/卷尺、直角尺和若干已知高度的垫块。

- 数量：最低 3 个非共线点，正式标定建议 8--15 个点。
- 分布：覆盖左/中/右、近/中/远，至少使用 3 个不同高度。
- 禁止：全部点排成直线；正式标定也不要只取同一桌面高度。
- 精度：目标门禁是平均/RMSE 10 mm、最大 15 mm，人工测量最好控制在 5 mm 内。
- 全程固定机械臂底座、相机支架和标定物基准，不要碰动相机。

### 3. 在香橙派采集

推荐在香橙派远程桌面的终端运行，这样可以直接看到 OpenCV 窗口。下面的命令会先
通过 `/dev/ttyUSB0` 用 5 秒低速动作把机械臂送到
`[1380,1909,1900,620,1500,1500]`，再通过 `PRAD` 核验 Servo000--004。
核验成功后串口立即关闭，采点期间不会再发送机械臂命令：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
~/rk3588_ai/rknn_lite_env/bin/python3 tools/collect_base_camera_points.py \
  --prepare_reference_pose \
  --serial_port /dev/ttyUSB0 \
  --output ~/rk3588_ai/calibration/base_camera_points.csv
```

每个点按以下顺序操作：

1. 把标记面放在一个已测量的底座 XYZ 位置，不移动机械臂和相机。
2. 在相机窗口左键点击标记面中心。
3. 回到终端，输入同一中心的 `X,Y,Z` 毫米值并回车。
4. 看到 `POINT_SAVED` 后再移动标记物，采下一个点。
5. 按 `u` 撤销最后一点；按 `q` 或 `ESC` 完成采集。

工具生成：

- `~/rk3588_ai/calibration/base_camera_points.csv`：用于 SVD 标定的六列数据。
- `~/rk3588_ai/calibration/base_camera_points.session.json`：六轴回读、D435 内参、
  点击像素、深度与每个点的双坐标证据。

再次运行采集工具时，如果 `--output` 仍指向同一个 CSV，工具会读取旧行并在末尾
追加新点，**不会清空旧 CSV**。如果要完全独立地重做一轮，应改用新文件名：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/collect_base_camera_points.py \
  --prepare_reference_pose \
  --serial_port /dev/ttyUSB0 \
  --output ~/rk3588_ai/calibration/base_camera_points_round2.csv
```

同名 `.session.json` 和标定报告 JSON 会被后一次运行更新，因此重要轮次应使用
`round1/round2` 文件名，或先复制到 `~/rk3588_ai/calibration/backups/`。异常点不要
直接从唯一原件中删除，应保留原 CSV，另建过滤后的候选 CSV 再复算。

如果机械臂已经处于参考姿态，只读回核验、不发送动作：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/collect_base_camera_points.py \
  --verify_reference_pose \
  --serial_port /dev/ttyUSB0 \
  --pose_check_only
```

CSV 表头固定为：

```csv
camera_x,camera_y,camera_z,base_x,base_y,base_z
```

工具会自动创建 CSV；`config/base_camera_points.template.csv` 只是格式参考，不需要
手工填写相机坐标。

### 4. 求解矩阵

运行 SVD/Kabsch 刚体配准并写入配置：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
~/rk3588_ai/rknn_lite_env/bin/python3 tools/calibrate_base_camera_3d.py \
  ~/rk3588_ai/calibration/base_camera_points.csv \
  --output_json ~/rk3588_ai/calibration/base_camera_report.json \
  --write_config
```

工具输出 `T_base_camera_reference`、逐点误差、平均误差、最大误差、RMSE 和
`det(R)`。反射矩阵直接拒绝。只有以下条件全部成立才允许真实抓取：

- `fixed_view_calibration.calibrated=true`
- `rmse_m <= 0.010`
- `max_error_m <= 0.015`
- 参考姿态 `Servo004=1500`
- 本机连杆/TCP 与 PWM-angle 零位已验收，`kinematics.calibrated=true`
- `serial.joint_pwm_calibrated=true` 且运行时显式传入 `--joint_pwm_calibrated`

## 只验证坐标

该工具没有串口参数，不导入串口适配器，也不会发送舵机命令：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
~/rk3588_ai/rknn_lite_env/bin/python3 tools/validate_fixed_view_target.py \
  --target_class bottle \
  --max_results 5 \
  --output_jsonl ~/rk3588_ai/debug_logs/fixed-view-targets.jsonl
```

每条 `FIXED_VIEW_TARGET` 包含：

- `pixel_xy`、`depth_m`、`point_camera_m`
- `point_base_surface_m`、`bottle_center_base_m`
- `pre_grasp_base_m`、`approach_base_m`
- 各点 workspace 标志、PRE/APPROACH IK 标志
- `serial_opened=false`、`servo_command_sent=false`

## 目标与路径

对 YOLO `bottle` 框内部 ROI 过滤 `0/NaN/Inf`，以 15--85 百分位剔除离群值后
取中位深度。前表面点通过固定矩阵变换到 `arm_base`，再按配置的瓶子半径修正：

```text
approach_axis = normalize([surface_base_x, surface_base_y, 0])
bottle_center = front_surface + approach_axis * bottle_radius_m
```

阶段固定为 `OPEN -> PRE_GRASP -> APPROACH -> CLOSE -> LIFT`：

- PRE_GRASP 在瓶心前方 `0.070 m`，允许配置范围仅为 `0.060..0.080 m`。
- APPROACH 从 PRE_GRASP 到瓶心保持同一 `Z`，默认每 `0.010 m` 一个 IK 路点。
- 每个路点执行前检查 workspace、IK、六路 PWM 边界并打印
  `GRASP_STAGE_PREFLIGHT`。
- Servo004 在全程固定为 `1500`。

## Dry-run

完成矩阵标定后，只生成计划和总线命令，不打开真实串口：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d435_yolo_grasp.py \
  --target_class bottle \
  --execute_on_lock true \
  --dry_run true \
  --max_stage lift \
  --max_frames 600 \
  --no_show
```

## 真实 PRE_GRASP 单阶段

先确认标定报告和五个不同位置的无串口坐标验证结果，再执行：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d435_yolo_grasp.py \
  --target_class bottle \
  --execute_on_lock true \
  --dry_run false \
  --enable_arm \
  --joint_pwm_calibrated \
  --serial_port /dev/ttyUSB0 \
  --max_stage pre_grasp \
  --max_frames 600 \
  --no_show
```

`--max_stage pre_grasp` 完成 PRE_GRASP 后保持，不会发送任何 APPROACH 路点。
真实抓取与 `--auto_center` 同时启用会在打开串口前被拒绝。

## 回归测试

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_fixed_view_grasp.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_grasp_safety.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_geometry_frames.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_official_kinematics.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/mock_grasp_cycle.py
```

固定视角相机矩阵已标记为 `calibrated=true`；本机运动学和舵机映射仍为
`calibrated=false` / `joint_pwm_calibrated=false`，所以仓库代码不会把 dry-run 结果
误当成真实机械臂标定完成。

`kinematics.l0_m..l3_m` 当前采用 C-5.2.0 测量表中的本机暂定值，不使用商家例程
连杆长度；由于 `L3` 的 TCP 定义和 PWM-angle 零位仍需实测确认，默认
`kinematics.calibrated=false`，真实抓取门禁不会放行。
