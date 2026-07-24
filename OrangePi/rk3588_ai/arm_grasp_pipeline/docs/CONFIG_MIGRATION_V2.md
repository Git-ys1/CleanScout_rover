# arm_grasp 配置迁移：schema v1 → v2

本文说明如何把旧 fixed-view 配置迁移到动态 wrist-camera closed-loop schema v2。
仓库中的 `config/arm_grasp_default.json` 已完成结构迁移。当前安装的手眼平移来自实测，
旋转经三安全姿态静态 bottle 验证，最大散布 14.15 mm，因此
`hand_eye.calibrated=true` 且 `hand_eye.dynamic_validation.accepted=true`。这只对当前
锁紧安装成立；迁移本身仍不等于标定，支架/TCP 变化后必须重新验证。Servo005 安全
闭合 PWM/内宽仍未完成独立实测，`gripper_close_calibrated=false` 时 CLOSE/LIFT 必须
在连接设备前拒绝。

## 核心变化

v1 的真实路径假设机械臂位于一个固定参考 PWM，并直接使用
`T_base_camera_reference`。v2 的正式坐标链是：

```text
T_base_wrist  = FK(PRAD 当前 Servo000..003 PWM)
T_base_camera = T_base_wrist × T_wrist_camera_color_optical
T_base_tcp    = T_base_wrist × T_wrist_tcp_open/closed
```

相机安装在 Servo004 定子，随 Servo000～003 运动，不随 Servo004/005 运动。
Servo004 保持 1500。`fixed_view_calibration.base_to_camera_matrix_4x4` 仍保留作诊断和
历史回滚证据，但 v2 动态真实路径不能读取它。

## 字段映射

| v1 概念/字段 | v2 字段 | 迁移规则 |
|---|---|---|
| 无 schema 或旧 schema | `schema_version=2` | 显式标记新结构 |
| 固定 `T_base_camera_reference` | `hand_eye.T_wrist_camera_color_optical` | 不能直接复制；需结合 wrist FK 求 seed，最终必须用实测相机原点+轴映射替换 |
| `fixed_view_calibration.*` | 原字段保留 | 仅诊断/回滚，不进入动态真实抓取 |
| 混合含义 `kinematics.l3_m` | `wrist_link_m` + `tool_tcp.T_wrist_tcp_*` | 机械臂本体与工具长度彻底分离 |
| Servo003 后段到闭合中心 | `measured_l3_total_closed_m=0.190` | 记录总物理校核量 190 mm |
| Servo003→Servo004 定子 | `wrist_link_m=0.055` | FK 本体截止到 wrist |
| Servo004 定子→closed TCP | `T_wrist_tcp_closed.x=+0.135` | closed TCP 在 wrist 前方 135 mm；不要写成反号 |
| 张开工具中心 | `T_wrist_tcp_open` | 暂存旧 116 mm，保持 `open_calibrated=false` 直到重测 |
| 单一工具点 | `tool_tcp.active_grasp_tcp=closed` | 最终 IK/抓取使用闭合夹持中心 |
| RGB/TCP 高差混入 optical Z | `hand_eye.measurement_record.closed_tcp_vertical_down_from_rgb_origin_m=0.013` | 单独保存物理竖直证据；必须结合轴映射，不能直接写成 wrist/TCP Z |
| 未建模桌面 | `environment.base_mounting_plane_to_table_m=0.120` | base `+Z` 向上，对应 `table_surface_z_base_m=-0.120` |
| 旧单点/简单 ROI 深度参数 | `depth_observation.*` | front-cluster ROI + valid/MAD/IQR/jump/range 门禁 |
| 未声明 D435 近距限制 | `depth_observation.min_depth_m=0.17`、`closed_loop.minimum_reliable_aligned_depth_m=0.17` | 小于 170 mm 停止反馈接近 |
| 一次性 APPROACH waypoint | `grasp_compensation.approach_step_m` + `closed_loop.*` | 每次只走 5～10 mm、PRAD 到位后取新 RGB-D/PWM 再规划 |
| `pre_grasp_standoff_m` | `grasp_compensation.pregrasp_standoff_m=0.060` | 仅中间重新观察位置，不是最终抓取点 |
| 隐含/硬编码偏移 | `grasp_compensation.*` | 按像素、深度、相机点、表面到中心、local approach XYZ、最终插入分层 |
| 旧 bottle radius | `object_geometry.bottle_radius_m` | 保留实物参考值；实际补偿由 `object_surface_to_grasp_center_m` 明确控制 |
| 最后一段盲走 | `final_insertion_m=0.010`、`max_final_insertion_m=0.015` | 仅 FINAL_ALIGN 后沿水平工具 +along，禁止左右/高低分量；深度异常不能启用更长 RGB-only 路径 |
| 命令已发送即完成 | `serial.readback_*` + `MotionResult.readback_reached` | 真实到位必须依赖正确 ID 的 PRAD 回读 |
| 无目标身份 | `target_tracker.*` | 目标丢失、歧义、切换即停止下一运动命令 |
| 动作完即抓取成功 | `closed_loop.verify_*` | CLOSE 只证明 Servo005 到位；小抬升视觉证据再判定抓取 |

## 不得改变的冻结字段

迁移 v2 不授权重新标定以下值：

- `joint_pwm_calibration.zero_pwms=[1500,1500,1500,1500]`
- `joint_pwm_calibration.pwm_signs=[1,-1,1,1]`
- `pwm_per_deg_by_joint=[8.148148148148149, 7.0908242948362,
  7.93582743625423, 6.478095739111546]`
- 控制器命令范围 `500..2490`
- 每轴 `grasp.servo_pwm_limits`
- Servo004 固定 `1500`
- Servo005 实测最大张开目标 `1112`

这些字段只能在独立测量、证据和专门迁移说明下变更，不能为让 IK 或测试通过而扩大
限位或改方向。`grasp.gripper_close_pwm=2000` 当前只是历史候选值，不属于已冻结实测；
安全闭合 PWM 和最小内宽完成独立测量前，必须保持
`gripper_close_calibrated=false`。

## 当前测量与门禁状态

已进入 v2 的实测值：

- L3（Servo003 后段到 closed TCP）190 mm；
- wrist/Servo004 定子到 closed TCP 135 mm；
- closed TCP 是夹爪闭合时两指真实夹持区域中点；
- 以 RGB 原点为参照，closed TCP 在物理竖直方向低 13 mm；
- 机械臂安装基座平面高出桌面 120 mm；
- D435 对齐深度可靠下限 170 mm；
- Servo005 最大张开目标 1112，已由严格 PRAD 复验；
- 当前手眼矩阵经三个安全姿态的同一静态目标验证，最大散布 14.15 mm。

当前门禁为：

```text
hand_eye.calibrated=true
hand_eye.dynamic_validation.accepted=true
tool_tcp.open_calibrated=false
tool_tcp.closed_calibrated=true
gripper_close_calibrated=false
```

因此动态 observe/center/pregrasp/approach 可以在其余安全检查通过后使用 closed TCP；
open TCP 不能冒充正式工具点。CLOSE、VERIFY、LIFT 和 `full` 还必须等待 Servo005
安全闭合 PWM/内宽实测并由独立迁移把 `gripper_close_calibrated` 设为 true。直接手改
布尔值不构成标定证据。

## 安全迁移步骤

### 1. 备份并只读检查

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
PY=~/rk3588_ai/rknn_lite_env/bin/python3
mkdir -p ~/rk3588_ai/calibration

cp -a config/arm_grasp_default.json \
  ~/rk3588_ai/calibration/arm_grasp_default.before-v2-check.json
$PY tools/configure_hand_eye_tcp.py \
  --check-only \
  --report ~/rk3588_ai/calibration/hand-eye-tcp-before.md
$PY tools/tune_grasp_compensation.py --check-only
```

### 2. 安装变化后重新写入 hand-eye/TCP

当前安装不需要重复写入。只有相机支架、安装方向或 TCP 几何发生变化时，以下内容才由
新的现场测量填写；变量文字不是可执行测量值：

```bash
CAMERA_ORIGIN_IN_CLOSED_TCP_MM='实测X,实测Y,实测Z'
CAMERA_AXIS_MAP='实测相机+X,实测相机+Y,实测相机+Z在wrist轴中的映射'

$PY tools/configure_hand_eye_tcp.py \
  --camera-reference-tcp closed \
  --camera-origin-in-tcp-mm="$CAMERA_ORIGIN_IN_CLOSED_TCP_MM" \
  --camera-axis-map="$CAMERA_AXIS_MAP" \
  --wrist-tcp-closed-mm=135,0,0 \
  --closed-tcp-vertical-down-from-rgb-mm=13 \
  --mark-hand-eye-calibrated \
  --mark-closed-calibrated \
  --replace-existing \
  --write \
  --report ~/rk3588_ai/calibration/hand-eye-tcp-v2.md
```

`--replace-existing` 只表示操作员已检查 seed 冲突，不会替代物理测量。工具会在原配置
旁创建时间戳备份。

### 3. 软件测试

```bash
$PY -m unittest discover -s tests -t .. -p 'test_*.py' -v
$PY -m unittest discover -s tools -t .. -p 'test_*.py' -v
$PY tools/mock_dynamic_grasp_cycle.py
```

任何预期成功测试的非零退出都必须先处理，不能降低安全阈值绕过。

### 4. observe 多姿态验证

只读运行 `README.md` 的 observe 命令，在至少三个已确认安全姿态观测同一固定 bottle：

- 每次记录实际六轴 PWM；
- 输出动态 `T_base_camera` 与 `target_base`；
- 检查每帧是在 PWM 快照之后取得的新 aligned RGB-D；
- 同一静态目标的基座 XYZ 平均散布目标为 10～15 mm 内。

超过门限时修正 FK/hand-eye，不能用 grasp compensation 掩盖刚体链错误。

### 5. 分阶段实机验收

严格按 README 的 `pregrasp → approach → close → lift` 逐项执行和留存独立日志：

- PREGRASP 后必须看到 `REACQUIRE_AFTER_PREGRASP` 和新时间戳；
- APPROACH 每步 5～10 mm，且每步都有新图像、新 PWM、新动态坐标；
- FINAL_ALIGN 后只允许水平前伸 10 mm，配置硬上限 15 mm；
- CLOSE 的 PRAD 到位不能记作抓取成功；
- LIFT 先进行 15 mm 验证抬升，只有 `grasp_verified` 才默认继续。

Servo005 安全闭合门禁未通过时，只验收到 approach；close/lift 命令必须在设备连接前
拒绝，不得用候选 PWM 或放宽 PRAD 代替实测。

程序在失败和退出时都保持最后姿态并明确打印 `automatic_PDST=false`。操作者负责现场急停
和后续安全回撤，不能期待程序自动释放重力保持。

## 补偿字段的迁移原则

补偿的固定顺序是：

1. `target_pixel_offset_px` / `target_pixel_y_ratio` 选择 RGB 像素；
2. `depth_bias_m` 修正 aligned optical depth；
3. `camera_point_bias_m` 修正相机三维点；
4. 动态 `T_base_camera` 得到物体可见表面基座坐标；
5. `object_surface_to_grasp_center_m` 得到物体抓取中心；
6. `grasp_bias_approach_frame_m` 与 `grasp_height_offset_m` 修正 along/lateral/vertical；
7. `final_insertion_m` 只在 FINAL_ALIGN 后作为独立受限水平动作。

不要把多种误差重新塞进一个“magic XYZ offset”。通过
`tools/grasp_offset_tuner.py` 做实时纯观察调参：先由独立分阶段命令停在 PREGRASP 或
FINAL_ALIGN，再启动工具；不传 `--enable_arm`，每次调整必须读取新 RGB-D 和完整六轴
PRAD，空格暂停。仅需离线预览/脚本化写 JSON 时使用
`tools/tune_grasp_compensation.py`；写入必须双重确认，且修改后重新观测。

## 旧真实入口退役

`tools/run_bottle_stage.sh` 的 center/oneclick/full 和各分阶段命令只允许调用严格动态
状态机：不读取 cached target lock，不允许 RGB-only 近距继续，不允许 Servo005 PRAD
缺失。旧 `bottle_demo.py` / `tools/bottle_grasp_demo.py` 只保留作历史和软件诊断，其
真实模式已禁用。深度异常必须停止；唯一允许的盲插仍是 FINAL_ALIGN 已稳定后的配置
小量，且不超过 15 mm。

## 回滚

旧 fixed-view 配置、采点和报告仍在仓库中用于审计。当前 CLI 只有在显式选择
`--mode legacy_fixed_view` 时才进入隔离的弃用回滚模块；它要求旧标定和参考姿态冻结，
真实模式还要求 `--enable_arm`，并在观察前与每个动作阶段核对完整六轴 PRAD。该模块
不进入 v2 动态状态机，也不自动发送 PDST。不要只把旧 `T_base_camera_reference` 拷回
v2，不要把 v1/v2 字段混合后继续真实运动。
