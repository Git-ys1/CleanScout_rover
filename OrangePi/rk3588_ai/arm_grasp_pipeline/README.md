# D435 + RKNN YOLO11 动态闭环抓取

本目录是在香橙派 RK3588 上运行的非 ROS 机械臂抓取管线。它保留现有 RKNN
YOLO11、Intel RealSense D435 深度对齐到 RGB、总线舵机 ASCII 协议与 `PRAD`
回读，并将真实路径从固定相机外参改为实时关节姿态驱动的动态坐标链。

当前实现已经具备软件级阶段门控，但**不把代码完成或舵机到位写成实机抓取成功**。
当前配置的动态手眼多姿态验证、closed TCP、运动学和冻结 PWM 映射已经进入真实动态
坐标链；`tool_tcp.open_calibrated=false` 只表示 open TCP 仍是暂存几何，最终规划明确
使用已标定的 closed TCP。Servo005 安全闭合 PWM/夹爪内宽尚未完成独立实测，因此
`gripper_close_calibrated=false` 时 CLOSE、VERIFY、LIFT 和 `full` 必须在连接设备前
拒绝；observe、center、pregrasp、approach 不得绕过六轴 PRAD。若相机支架、机械臂
安装或夹爪结构发生变化，必须重新标定并从 observe/center 开始验收。

## 硬件与坐标模型

- 平台：香橙派 RK3588，不引入 ROS/ROS2。
- 检测：RKNN YOLO11，默认目标类别为 `bottle`。
- RGB-D：D435 深度流先对齐到 RGB，再使用对齐后彩色相机内参反投影；不叠加商家
  例程的 RGB/深度像素硬编码偏移。
- 执行器：现有 `#xxxPxxxxTxxxx!` ASCII 命令和 `#xxxPRAD!` PWM 回读。写串口成功
  不等于到位，真实运动结果必须通过回读容差门禁。
- 相机固定在 Servo004 定子上，随 Servo000～003 运动，不随 Servo004 转子或
  Servo005 开合运动；Servo004 全程固定为 `1500`。
- 退出或失败时保持当前姿态，程序永不自动发送 `PDST`。

坐标变换统一采用 `T_parent_child`，即把 child 坐标表达转换到 parent：

```text
T_base_camera = T_base_wrist(PRAD 实时 PWM 000..003) × T_wrist_camera
T_base_tcp     = T_base_wrist(PRAD 实时 PWM 000..003) × T_wrist_tcp_open/closed
```

真实动态路径不读取
`fixed_view_calibration.base_to_camera_matrix_4x4`。旧固定视角数据仅保留作诊断和回滚
证据，不能重新接入真实抓取。

`wrist`、`camera_color_optical`、`tcp_open` 和 `tcp_closed` 是四个不同坐标系：

- `wrist`：Servo004 定子/轴心处的机械臂本体末端。
- `camera_color_optical`：D435 RGB 光学系，`+X` 图像向右、`+Y` 图像向下、`+Z`
  镜头向前。
- `tcp_open`：夹爪张开时的工具中心，仅作张开状态几何描述，目前仍为未标定的暂存值。
- `tcp_closed`：夹爪闭合时两指真实夹持区域中点，最终 IK、接近、闭爪和抬升均以它
  为工具点。

当前夹爪张开端的真实可达回读为 Servo005=`1112`：发送旧 `1000` 后，两次历史实测
和本次实测都稳定停在 `1111/1112`。因此生产配置使用 `1112` 作为张开目标；这不修改
Servo000～003 的冻结零位、方向或线性系数。

### 已确认物理值

| 物理量 | 当前值 | 配置含义 |
|---|---:|---|
| L3 总长度（Servo003 后段到闭合 TCP） | 190 mm | `kinematics.measured_l3_total_closed_m=0.190` |
| Servo003 到 wrist/Servo004 定子 | 55 mm | `kinematics.wrist_link_m=0.055` |
| wrist 到 closed TCP 的轴向距离 | 135 mm | `T_wrist_tcp_closed` 的 `+X=0.135 m` |
| RGB 原点到 closed TCP 的物理竖直差 | TCP 向下 13 mm | 相机原点在 closed TCP 中为 `Z=+13 mm`；不是 RealSense optical Z，也不是 wrist→TCP Z |
| 机械臂安装基座平面高出桌面 | 120 mm | base `+Z` 向上，因此桌面 `Z=-0.120 m` |
| D435 对齐深度可靠下限 | 0.17 m | 小于该值停止使用深度继续接近 |

`L3=190 mm` 的拆分是 `55+135 mm`；不得再把一个含义不明的 `l3_m` 同时当作
机械臂连杆和工具 TCP。`RGB→closed TCP 向下 13 mm` 是现实世界竖直方向测量，只有
结合明确的相机轴映射才能进入完整手眼矩阵，不能直接写成 optical Z 或
`T_wrist_tcp_closed.z=-0.013`。

## 闭环行为与停止条件

状态机按 `OBSERVE → PREGRASP → REACQUIRE → FINE_APPROACH → FINAL_ALIGN →
CLOSE → VERIFY_LIFT → LIFT` 工作：

1. 每次坐标计算优先读取六轴 `PRAD`，用 Servo000～003 的实际 PWM 计算
   `T_base_wrist` 和动态 `T_base_camera`。纯 observe 在确认只有 Servo005 缺失时可用
   Servo000～004 继续输出只读诊断并记录缺失 ID；任何真实运动仍要求六轴完整回读。
2. PREGRASP 默认距目标约 60 mm，只是重新观察位置。到达后会废弃旧目标坐标，强制
   重新检测、重新测深度、重新读 PWM、重新计算坐标。
3. APPROACH 每次仅移动 5～10 mm（默认 8 mm）；每一步都等待回读到位，然后只接受
   动作结束之后的新 RGB-D 帧和新 PWM 快照。
4. 目标丢失/切换/歧义、帧过期、深度小于 0.17 m 或质量异常、PWM 回读失败、
   Servo004 偏离 1500、工作空间/PWM 越界、IK 失败或误差不收敛，都会停止下一步。
5. D435 近于 0.17 m 不再提供可信反馈。只有 FINAL_ALIGN 已用多帧新观测满足三轴
   收敛后，才允许沿当前工具水平前向做配置的最终 10 mm 插入；该动作禁止竖直或横向
   分量，且 `max_final_insertion_m=15 mm` 是硬上限。
6. Servo005 的闭爪 `PRAD` 只能证明夹爪 PWM 到位，**不等于抓取成功**。`lift` 阶段
   会先做 15 mm 验证抬升，并用物体相对相机/TCP 与桌面坐标变化分类为
   `grasp_verified`、`grasp_failed` 或 `uncertain`；默认不把 `uncertain` 当成功。

## 环境与安装

沿用香橙派现有目录和虚拟环境：

```bash
cd ~/rk3588_ai/arm_grasp_pipeline
source ~/rk3588_ai/scripts/use_realsense_rsusb.sh
PY=~/rk3588_ai/rknn_lite_env/bin/python3
```

运行前确认：

- D435 可用，RGB 与深度均为 `640×480@30`，指定序列号与实际设备一致；
- RKNN 模型默认位于 `~/rk3588_ai/models/official_yolo11.rknn`，YOLO11 Python
  目录存在；
- `/dev/ttyUSB0` 是当前机械臂控制器，115200 baud；
- 桌面、车体和机械臂底座固定，急停/断电手段可立即触达；
- 配置的工作空间、每轴 PWM 限位、Servo004=1500 和 frozen PWM 零位/方向/线性
  系数未被修改。

先做只读环境检查：

```bash
$PY tools/realsense_env_check.py
$PY tools/d435_yolo_grasp.py --help
$PY tools/configure_hand_eye_tcp.py --check-only
$PY tools/grasp_offset_tuner.py --check-only
$PY tools/tune_grasp_compensation.py --check-only
```

## 严格现场快捷入口

初始摆放建议：bottle 抓取区域距 Servo000 旋转轴约 `0.35～0.38 m`（优先约
`0.36 m`），横向靠近正中；003=`620` 初始桌面视角下，可见表面的 D435 深度至少
约 `0.20 m`。高度可用垫块改变，视觉居中会处理画面高低；当前最终抓取点另有明确的
`grasp_height_offset_m=+0.040 m`。瓶身前方必须为无障碍水平路径。

快捷脚本只调用严格的 `d435_yolo_grasp.py` 动态状态机。它不读取磁盘中的旧目标锁，
不允许 RGB-only 代替失效深度，也不允许缺失 Servo005 PRAD。旧
`bottle_demo.py` / `tools/bottle_grasp_demo.py` 只保留作历史和软件诊断，真实模式已经
禁用，不能作为答辩入口。

纯视觉居中，不接近、不闭爪：

```bash
bash tools/run_bottle_stage.sh center
```

严格一键到 FINAL_ALIGN 前，流程为 center 后重新建立目标，再执行
PREGRASP→强制重观测→5～10 mm 闭环 APPROACH；不会闭爪或抬升：

```bash
bash tools/run_bottle_stage.sh oneclick
```

只有安全闭爪实测完成、配置门禁明确为 true，并且五阶段验收已逐项通过后，才允许：

```bash
bash tools/run_bottle_stage.sh full
```

`full` 从严格 center 开始重新观测，随后运行到 CLOSE、验证小抬升和 LIFT。任一步
目标丢失/切换、深度异常、帧过期、六轴 PRAD 不完整、Servo004 偏离 1500、IK/PWM
失败都会停止，不会复用旧坐标继续走，也不会自动发送 PDST。

## 手眼与 TCP 配置

查看当前矩阵、方向和标定状态并生成报告，不修改配置：

```bash
mkdir -p ~/rk3588_ai/calibration
$PY tools/configure_hand_eye_tcp.py \
  --check-only \
  --report ~/rk3588_ai/calibration/hand-eye-tcp-check.md
```

当前安装已经通过三安全姿态静态目标验证。仅在支架、安装方向或 TCP 几何变化后重新
写入；届时必须同时提供“RGB 光学原点在选定 TCP 物理轴中的 XYZ”和完整相机轴映射。
以下变量必须替换为新的现场测量，不得照抄示意值：

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
  --report ~/rk3588_ai/calibration/hand-eye-tcp-final.md
```

工具会校验刚体矩阵、检测与既有矩阵的冲突，并在写入前备份 JSON。只有确认轴映射、
报告方向和至少三个安全姿态下静态目标的基座坐标一致性（目标平均散布不超过
10～15 mm）后，才可保留 `hand_eye.calibrated=true`。配置迁移详见
[`docs/CONFIG_MIGRATION_V2.md`](docs/CONFIG_MIGRATION_V2.md)。

## Dry-run

`--dry_run true` 不打开串口、不发送任何机械臂命令，但仍使用真实 D435 与 RKNN
走状态机；PWM/到位回读由模拟状态提供。保存 RGB、深度、overlay、ROI 统计和 JSONL：

```bash
RUN=~/rk3588_ai/debug_logs/dryrun-pregrasp-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode pregrasp \
  --target_class bottle \
  --dry_run true \
  --max_frames 600 \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

如需演练更多软件阶段，可将 `--mode` 改为 `approach`，或使用
`--mode grasp --max_stage close|lift`。由于真实机械臂和相机不会随模拟命令运动，
全流程收敛应以自动化 fake-source 测试为准，不能把 dry-run 结果记作实机到位或抓取。

## 分阶段实机命令

下面命令是**人工逐条执行的验收入口**，程序不会自动串联启动下一条。运动命令只有在
手眼与 closed TCP 标定门禁通过后才能运行。每次运行使用新的日志目录；操作者必须在
每个阶段检查现场、日志和急停条件，再决定是否进入下一阶段。CLOSE/LIFT 还必须通过
独立的 `gripper_close_calibrated` 门禁；当前未测完成时保留命令用于验收流程说明，
实际运行应在连接设备前安全拒绝。

### 0. center：620 桌面视角起步，只视觉居中

```bash
RUN=~/rk3588_ai/debug_logs/center-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode center \
  --target_class bottle \
  --dry_run false \
  --enable_arm \
  --serial_port /dev/ttyUSB0 \
  --center_duration_s 12 \
  --prepare_center_pose true \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

该阶段先到 `[1500,1909,1968,620,1500,1112]`，再以 000/003 对齐画面中心；004 和
张开夹爪始终保持，不会 PREGRASP 或闭爪。继续当前姿态微调时可把
`--prepare_center_pose` 改为 `false`。

### 1. observe：只读动态坐标，不动臂

这是始终可优先执行的只读实机入口。它打开 D435、RKNN 和串口，只发 `PRAD` 读取
当前 PWM，不发任何舵机位置命令。若仅 Servo005 瞬时不响应，
输出会以 `missing_pwm_ids=[5]` 明确标记并继续只读坐标；运动入口不会使用该降级：

```bash
RUN=~/rk3588_ai/debug_logs/observe-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode observe \
  --target_class bottle \
  --dry_run false \
  --serial_port /dev/ttyUSB0 \
  --max_frames 30 \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

至少在三个已确认安全的人工姿态分别执行，比较同一静态 bottle 的
`target_base`/`T_base_camera`。在散布满足 10～15 mm 之前不要进入 PREGRASP。

### 2. pregrasp：约 60 mm 中间观察位

```bash
RUN=~/rk3588_ai/debug_logs/pregrasp-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode pregrasp \
  --target_class bottle \
  --dry_run false \
  --enable_arm \
  --serial_port /dev/ttyUSB0 \
  --max_frames 600 \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

该阶段打开夹爪、到 PREGRASP、强制获取动作后的新 RGB-D/PWM/坐标并保持；不会发送
APPROACH 或 CLOSE。

### 3. approach：5～10 mm 闭环到 FINAL_ALIGN

```bash
RUN=~/rk3588_ai/debug_logs/approach-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode approach \
  --closed_loop true \
  --target_class bottle \
  --dry_run false \
  --enable_arm \
  --serial_port /dev/ttyUSB0 \
  --max_frames 600 \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

该阶段每步后重新观测并停在 FINAL_ALIGN，夹爪保持张开，不发送 CLOSE。确认 closed
TCP 相对 bottle 的 along/lateral/vertical 误差后，再通过调参工具修正配置。

### 4. close：闭爪但不宣称成功

```bash
RUN=~/rk3588_ai/debug_logs/close-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode grasp \
  --max_stage close \
  --closed_loop true \
  --target_class bottle \
  --dry_run false \
  --enable_arm \
  --serial_port /dev/ttyUSB0 \
  --max_frames 600 \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

它重新完成观察、PREGRASP、闭环接近与 FINAL_ALIGN 后才闭爪。`SUMMARY.ok=true` 在
这里仅表示 close 阶段及 PWM 回读完成，`grasp_verification=not_verified`，不能记录为
抓取成功。安全闭爪 PWM/内宽未标定时，本命令必须 fail closed，不得发送闭爪动作。

### 5. lift：小抬升验证后才完整抬升

```bash
RUN=~/rk3588_ai/debug_logs/lift-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/d435_yolo_grasp.py \
  --mode grasp \
  --max_stage lift \
  --closed_loop true \
  --target_class bottle \
  --dry_run false \
  --enable_arm \
  --serial_port /dev/ttyUSB0 \
  --max_frames 600 \
  --save_dir "$RUN" \
  --metrics_path "$RUN/grasp_events.jsonl" \
  --no_show 2>&1 | tee "$RUN/console.log"
```

该阶段闭爪后先抬升 15 mm 获取验证证据；只有 `grasp_verified` 才默认继续完成余下抬升。
`grasp_failed` 或 `uncertain` 会停止且不会伪报成功。任何退出路径都打印
`ARM_HOLD_LAST_POSE automatic_PDST=false`。安全闭爪门禁未通过时，本命令必须在
设备连接前拒绝。

## 补偿调参工具

正式的 `grasp_offset_tuner.py` 是**纯观察调参器**：它没有机械臂运动入口，也拒绝
`--enable_arm`。先用上面的 pregrasp 或 approach 阶段把机械臂停在安全观察位/
FINAL_ALIGN，再单独启动调参器；`--stage` 只记录当前人工确认的阶段标签，不会发送
定位动作。

PREGRASP 位置启动：

```bash
RUN=~/rk3588_ai/debug_logs/tuner-pregrasp-$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUN"
$PY tools/grasp_offset_tuner.py \
  --stage pregrasp \
  --dry_run false \
  --serial_port /dev/ttyUSB0 \
  --target_class bottle \
  --save_dir "$RUN" \
  --metrics_path "$RUN/events.jsonl"
```

APPROACH 已停在 FINAL_ALIGN 后启动：

```bash
$PY tools/grasp_offset_tuner.py \
  --stage final_align \
  --dry_run false \
  --serial_port /dev/ttyUSB0 \
  --target_class bottle
```

调参器实时显示 RGB、对齐深度、目标框、closed TCP、目标点、三轴误差和补偿值；
每次调整后强制获取新的 RGB-D 与完整 Servo000～005 PRAD。`1/2` 切换毫米步长，
`w/s` 前后、`a/d` 左右、`r/f` 高低、`e/c` 深度、`t/g` 表面到中心、`[/]` 像素
高度，`u` 撤销、`0` 恢复启动值、空格立即暂停采集、双击 `p` 备份并保存。整个工具
没有 CLOSE/LIFT/运动 API。

仅需离线预览或脚本化修改 JSON 时，使用配置工具：

```bash
$PY tools/tune_grasp_compensation.py --check-only
$PY tools/tune_grasp_compensation.py \
  --set along_mm=1 \
  --write \
  --confirm-save SAVE
```

两种工具都会拒绝超过 15 mm 的最终插入。保存后必须重新运行 observe/pregrasp/
approach 获取新数据，不得沿用旧框、旧深度或旧 PWM。

## 日志与失败判定

`--metrics_path` 写入每个状态、观测和运动步骤的 JSONL；`--save_dir` 保存
`*_rgb.jpg`、`*_depth.png`、`*_overlay.jpg` 和 `*_depth_roi_stats.png`。控制台末尾
打印 `SUMMARY`，建议始终通过 `tee` 保存。

JSONL 包含目标 track、帧时间/年龄、完整深度质量、六轴 PWM、关节角、
`T_base_wrist`、`T_wrist_camera`、动态 `T_base_camera`、active closed TCP、补偿中间
值、三轴误差、IK/PWM 命令、PRAD 回读/偏差及停止原因。失败时先定位
`FAILED.stop_reason`，不得仅看串口写入或 `SUMMARY.ok`。

仓库样例位于 `docs/example_logs/`。样例中的 `simulated=true` 只证明软件闭环和日志
字段，不是实机抓取证据。

## 硬件无关测试

在开发机或香橙派项目目录运行：

```bash
$PY -m unittest discover -s tests -t .. -p 'test_*.py' -v
$PY -m unittest discover -s tools -t .. -p 'test_*.py' -v
$PY tools/mock_dynamic_grasp_cycle.py
```

测试覆盖动态坐标链、wrist FK/PWM 往返、open/closed TCP、Servo004/005 相机不变性、
严格 PRAD、目标关联、深度质量、补偿顺序、PREGRASP/APPROACH 阶段门控、每次运动后
拒绝旧帧、final 水平插入和闭爪/抬升验证。具体结果以本次执行输出为准，本 README
不声称实机已经通过。

## 旧 fixed-view 回滚边界

旧 `fixed_view.py`、标定点和报告仍保留用于对比/审计。只有操作者显式选择
`--mode legacy_fixed_view` 时，入口才会进入隔离的弃用回滚模块并显示强警告；默认动态
路径从不导入固定外参。该回滚仍要求 `--enable_arm`、旧标定冻结、参考姿态完整六轴
PRAD，以及每阶段完整六轴 PRAD 到位；不会自动发送 PDST。它只用于紧急回滚，不能把
旧 `T_base_camera_reference` 或一次检测后的开环 waypoint 混回动态真实路径。

仍需实测的值见
[`KNOWN_PHYSICAL_VALUES_TO_MEASURE.md`](KNOWN_PHYSICAL_VALUES_TO_MEASURE.md)；逐文件
变更见 [`CHANGELOG_DYNAMIC_GRASP.md`](CHANGELOG_DYNAMIC_GRASP.md)。
