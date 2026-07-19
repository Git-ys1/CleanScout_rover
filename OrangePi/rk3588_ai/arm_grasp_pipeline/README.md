# Arm Grasp Pipeline

`arm_grasp_pipeline/` 是独立于 ROS 的 D435 + RKNN YOLO11 固定观察姿态抓取管线。
C-5.2.5 不通过目标位置对应 PWM，也不通过检测框面积估距；目标位置来自 aligned
depth、相机反投影、实测 `T_base_camera_reference` 和机械臂 IK。

## C-5.2.5 当前状态

- 13 个唯一对应点经刚体一致性审查后保留 11 点，剔除 2 个异常点。
- 固定视角矩阵已通过质量门禁：RMSE `5.85 mm`，最大误差 `9.71 mm`。
- Servo000 使用厂家线性比例 `8.148148 PWM/deg`；Servo001--003 使用 D435 桌面
  平面法得到的逐轴有效斜率 `7.090824/7.935827/6.478096 PWM/deg`，禁止再统一套值。
- 厂家标称原始范围为 `500..2700`，但当前 STM32 控制器实际命令范围冻结为
  `500..2490`。
- Servo005 采用实测边界：`1000` 张开、`2000` 闭合；Servo004 始终固定 `1500`。
- 固定观察参考姿态统一为 `[1500,1909,1900,620,1500,1500]`。
- 旧 `000=1380` 的 11 点实测矩阵暂时原样用于 `000=1500` 参考姿态；解析增加
  `+14.727 deg` 偏航的方案在真实 PRE_GRASP 中导致明显偏转，已否决，不能再启用。
- 正式抓取冻结 `pitch_deg=0`，即 L3/TCP 水平接近；闭爪后的 80 mm 抬升使用
  `lift_pitch_deg=-11`。按当前连杆、逐轴比例和 `500..2490` 控制器边界，水平方案
  要求瓶心距底座至少约 `0.340 m`。瓶子更近时必须移动目标，不能用下俯 L3 或
  手调单轴 PWM 绕过 IK。
- `--max_stage` 只预检到请求阶段，不能再让未来 LIFT 无解反向阻断合法的
  PRE_GRASP；完整运行仍会逐阶段检查 workspace、IK、PWM 和 Servo004。
- 真实运行会先低速回到参考姿态，并用 `PRAD` 回读六轴；任一轴偏差超过 `40 PWM`
  会在视觉识别和运动前拒绝继续。`PRAD` 是控制器 PWM 状态，不是物理编码器反馈。

本轮冻结证据位于：

- `config/base_camera_points.consolidated11.csv`
- `config/base_camera_report.consolidated11.json`
- `config/base_camera_consolidation_audit.json`
- `config/base_camera_report.c525_reference1500.json`

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
`reference_servo_pwms=[1500,1909,1900,620,1500,1500]` 有效。真实抓取不会调用
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
`[1500,1909,1900,620,1500,1500]`，再通过 `PRAD` 核验 Servo000--004。
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
- 本机连杆和 PWM-angle 语义已验收，`kinematics.calibrated=true`
- `joint_pwm_calibration.calibrated=true`，四轴零位/方向/比例字段完整
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
- `configured_pitch_deg` 与 `l3_horizontal_commanded`
- 当前瓶心半径、完整分阶段计划的最小可达半径、仍需向外移动的距离
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
- APPROACH 从 PRE_GRASP 到瓶心保持同一 `Z`，默认每 `0.010 m` 一个 IK 路点；
  当前末端姿态为 `0 deg`，L3/TCP 水平直线接近，不允许从上方斜扎瓶子。
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

## 真实分阶段测试

每次命令都会先回到固定观察姿态并回读六轴。第一次按
`open -> pre_grasp -> approach -> close -> lift` 逐个增加 `STAGE`，不要直接从
`open` 跳到 `lift`：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
STAGE=pre_grasp
~/rk3588_ai/rknn_lite_env/bin/python3 tools/d435_yolo_grasp.py \
  --target_class bottle \
  --execute_on_lock true \
  --dry_run false \
  --enable_arm \
  --joint_pwm_calibrated \
  --serial_port /dev/ttyUSB0 \
  --max_stage "$STAGE" \
  --max_frames 600 \
  --no_show
```

`--max_stage pre_grasp` 完成 PRE_GRASP 后保持，不会发送任何 APPROACH 路点；
`approach` 只到瓶心且保持爪子张开；`close` 才把 Servo005 送到 `2000`；`lift`
才在闭爪后抬升。
规划器按 `--max_stage` 截断未来阶段，因此 PRE_GRASP 不会再被尚未请求的 LIFT
可达性反向阻断。
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

固定视角相机矩阵、实测连杆和舵机映射均已标记为 `calibrated=true`，但真实输出
仍需要命令行显式 `--enable_arm --joint_pwm_calibrated`，并受参考姿态回读、workspace、
IK、逐轴 PWM 边界、Servo004 固定值和 `--max_stage` 共同约束。当前沿用的实测
矩阵尚无 `000=1500` 姿态下的独立留出点复测，因此必须逐阶段观察；真实对正结果
只证明当前固定视角下的偏航可用，不能把它扩展成动态手眼标定。
