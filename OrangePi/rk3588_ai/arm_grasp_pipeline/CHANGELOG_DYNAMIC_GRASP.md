# Dynamic Closed-Loop Grasp Changelog

## C-5.2.6 — dynamic closed-loop grasp refactor (2026-07-24)

本变更集按任务书第 18 节顺序，将默认真实抓取路径从固定参考外参和一次性开环计划
迁移为实时 PWM 驱动的动态闭环。以下是代码与交付文件的逐文件说明；测试结论和实机
结论必须以对应运行日志为准，本记录不声称机械臂已经完成实机抓取。

### 坐标、配置与运动学

- `config/arm_grasp_default.json`
  - 升级到 schema v2，新增 `frames`、`environment`、`hand_eye`、`tool_tcp`、
    `grasp_compensation`、`target_tracker`、`depth_observation` 和 `closed_loop`。
  - 记录 L3=190 mm、wrist link=55 mm、wrist→closed TCP=135 mm、RGB 原点到
    closed TCP 物理向下 13 mm、基座平面高出桌面 120 mm。
  - D435 对齐深度可靠下限设为 0.17 m；APPROACH 默认 8 mm、限制在 5～10 mm；
    最终只沿水平工具前向插入 10 mm，上限 15 mm。
  - 保留冻结的 Servo000～003 PWM 零位、方向、逐关节线性系数、命令/安全范围和
    Servo004=1500。Servo005 张开目标由旧命令 1000 迁移为本次及历史均实际可达、
    可严格回读的 1112；历史 close 候选值不再等同于已标定值。
  - 增加独立 `gripper_close_calibrated` 门禁；Servo005 安全闭合 PWM/内宽实测未完成
    时，CLOSE/VERIFY/LIFT 在连接设备前拒绝，候选 close PWM 不算标定证据。
  - 动态手眼已采用用户实测 RGB→closed-TCP 平移和已验证轴映射，并记录三姿态静态
    bottle 最大散布 `14.15 mm`；`hand_eye.dynamic_validation.accepted=true` 后才允许
    真实运动。旧 fixed-view 矩阵降级为诊断/回滚数据。
  - 增加严格 `visual_centering` 配置。`demo_grasp` 仅保留历史实验参数和离线诊断；
    其真实入口已禁用，正式路径不使用 cached target、RGB-only 或缺失 Servo005
    PRAD 的接近方案。
- `geometry.py`
  - 统一 `T_parent_child` 变换语义和刚体校验。
  - 明确 wrist、RGB optical camera、open TCP、closed TCP，并实现动态
    `T_base_camera`/`T_base_tcp` 组合。
  - 增加 base/table 环境几何、局部 approach frame 和具有固定物理顺序的补偿链，
    返回所有中间结果供日志与测试复现。
- `official_kinematics.py`
  - 将机械臂本体 FK 截止到 Servo004 定子 wrist；L3 不再混用作工具长度。
  - 增加冻结 PWM→角度→`T_base_wrist`、wrist/closed-TCP FK 和以 TCP 为输入的 IK。
  - 旧估算接口保留兼容但产生弃用警告，动态真实路径不使用它。

### 串口、观测与规划

- `serial_servo_adapter.py`
  - 保留现有 ASCII 命令和 `PRAD`，增加带单调时间戳的严格六轴 PWM 快照。
  - 校验回复 ID、超时、重试、到位容差和 PWM 范围；真实 `ok` 依赖 PRAD 到位，
    dry-run 使用显式模拟状态。
  - 关闭连接时不自动发送 `PDST`。
  - observe 优先读取完整六轴；若且仅若 Servo005 缺失，可用 000～004 输出只读动态
    wrist/camera 诊断并记录缺失 ID。所有真实运动仍严格要求 000～005 完整快照。
- `arm_motion.py`
  - 增加 actual wrist/TCP pose、严格读回运动结果、每轴 PWM/Servo004 门禁和工具点
    TCP 运动接口。
  - 区分 command written、readback reached、simulated 和失败原因；最后发送命令不再
    充当真实姿态。
- `realsense_source.py`
  - 为对齐后的 RGB-D 帧增加设备、采集和到达单调时间戳，并提供只读取动作结束后新帧
    的接口。
- `target_depth.py`
  - 改为检测框内部 ROI 的 front-cluster 深度观测，记录 valid ratio/count、MAD、IQR
    和范围门禁；拒绝 0/NaN/Inf、跳变与 0.17 m 内不可靠深度。
- `target_tracker.py`
  - 新增基于类别、IoU、中心距离、尺寸和深度连续性的目标身份关联。
  - 对丢失、歧义和目标切换给出显式停止结果，不允许复用历史框继续运动。
- `grasp_planner.py`
  - 增加 closed TCP 驱动的 PREGRASP、单步 APPROACH、最终水平插入和分阶段 LIFT
    规划；保留工作空间、IK、逐轴 PWM、最大关节步长和 Servo004 检查。
- `grasp_state_machine.py`
  - 默认状态机改为 observe/pregrasp/approach/close/verify/lift 动态闭环。
  - PREGRASP 后强制重新检测、测深、读 PWM 和变换；APPROACH 每次只执行一个
    5～10 mm 步骤，再以动作结束时间作为下一帧屏障。
  - FINAL_ALIGN 多帧收敛后才允许最终水平 10 mm 插入；闭爪 PRAD 与抓取成功分离，
    先小抬升验证，再决定是否继续完整 LIFT。
  - 增加 JSONL 状态/观测/计划/命令/回读/验证/失败日志。
- `legacy_fixed_view_runtime.py`
  - 将旧 fixed-view 执行封装在显式弃用边界内；默认动态路径不导入固定外参，回滚仍
    受完整六轴 PRAD、参考姿态和不自动 PDST 约束。

### 入口与调参工具

- `tools/d435_yolo_grasp.py`
  - 改为非 ROS 动态入口，模式为 `observe`、`center`、`pregrasp`、`approach`、
    `grasp` 和显式隔离的 `legacy_fixed_view`；动态闭环为默认，fixed-view 不再进入
    真实路径。
  - 保留 RKNN YOLO11 与 D435 RGB 对齐，增加 tracker、深度质量、PRAD 新鲜度、
    `--save_dir`、`--metrics_path`、变换/补偿打印和 fail-before-connect 标定门禁。
  - `observe` 不发运动；真实运动同时要求 `--dry_run false --enable_arm` 和校准通过；
    所有退出路径保持最后姿态且不自动 PDST。
- `visual_centering.py`
  - 新增 000/003 有界图像中心伺服；每步保持六轴、004=`1500`、005=`1112`，动作后
    重新检测并以完整 PRAD 到位为准。
- `bottle_demo.py`
  - 保留历史答辩原型和软件测试构件，但真实模式退役：不得再通过 cached target、
    RGB-only 近距继续或缺失 Servo005 PRAD 执行动作。
- `tools/bottle_grasp_demo.py`
  - 保留历史 CLI/诊断入口；真实模式明确禁用，不再作为 README 或现场指令入口。
- `tools/run_bottle_stage.sh`
  - 统一现场快捷入口到严格 `d435_yolo_grasp.py`：`center` 仅视觉居中，
    `oneclick` 为 center 后重新观测并严格闭环到 approach、绝不闭爪，`full` 为
    center 后严格运行到验证 LIFT。
  - 删除目标锁文件接续、RGB-only 近距 fallback 和 missing-005 豁免；所有运动均要求
    Servo000～005 完整 PRAD。
- `tools/run_bottle_approach_demo.sh`
  - 保留兼容包装，但转向严格动态阶段入口，不得重新启用旧 bottle demo 真实路径。
- `tools/configure_hand_eye_tcp.py`
  - 新增配置检查/迁移工具，接收明确的 camera reference TCP、相机原点、相机轴映射、
    open/closed TCP 和物理竖直记录。
  - 校验方向、正交性、尺度与既有配置冲突；写入前备份并可输出人类可读报告。
- `tools/fit_hand_eye_from_observation_logs.py`
  - 从多姿态只读观测日志拟合/核验 wrist-camera 旋转，为直接手眼标定提供独立工具。
- `tools/grasp_offset_tuner.py`
  - 新增正式实时纯观察调参器：先由独立分阶段命令停在 PREGRASP/FINAL_ALIGN，工具
    自身拒绝 `--enable_arm` 且没有运动/CLOSE/LIFT API。
  - 同屏显示 RGB、对齐深度、目标、closed TCP、三轴误差和补偿；每次修改使用全新
    RGB-D 与完整六轴 PRAD，支持 1/2 mm、撤销、恢复、空格暂停、双击保存和报告。
- `tools/tune_grasp_compensation.py`
  - 保留完全不访问硬件的离线配置预览/脚本化调参工具。
  - 把前后、左右、高低、深度、相机点、物体半径/表面到中心、像素选点、最终插入
    分为有单位和物理意义的字段；保存需要双重确认并自动备份、写报告。
- `tools/test_fixed_view_grasp.py`
  - 更新旧兼容测试使用的 v2 几何字段和 L3/TCP 语义，使旧诊断路径与新 schema
    能被同时检查而不进入默认真实路径。
- `tools/mock_dynamic_grasp_cycle.py`
  - 提供可执行的无硬件模拟闭环样例；预期成功场景失败时以非零退出，不伪装通过。

### 自动测试

- `tests/dynamic_fakes.py`
  - 提供无硬件的 fresh-frame、PRAD、目标与状态机场景构件。
- `tests/test_dynamic_frames.py`
  - 验证动态 hand-eye 组合以及真实路径不依赖固定参考矩阵。
- `tests/test_wrist_fk.py`
  - 验证冻结 PWM/角度与 wrist FK 往返。
- `tests/test_hand_eye_chain.py`
  - 验证静态物体在不同模拟关节姿态下的动态坐标一致性。
- `tests/test_tcp_open_closed.py`
  - 验证 open/closed TCP 明确分离，closed TCP 进入最终工具链。
- `tests/test_servo004_camera_invariance.py`
  - 验证 Servo004/005 改变不改变相机外参。
- `tests/test_serial_readback.py`
  - 验证 ASCII/PRAD ID、超时、重试、偏差、dry-run 与真实到位语义。
- `tests/test_target_tracker.py`
  - 验证稳定关联、丢失、歧义和目标切换停止。
- `tests/test_depth_observation.py`
  - 验证 front-cluster ROI、无效值/离群值与深度质量门禁。
- `tests/test_compensation_order.py`
  - 验证补偿执行顺序、中间值和最终插入隔离。
- `tests/test_compensation_tuner.py`
  - 验证调参单位、上下限、预览、备份和双重保存确认。
- `tests/test_grasp_offset_tuner.py`
  - 验证实时调参器默认 dry-run/纯观察、仅接受 PREGRASP/FINAL_ALIGN 标签、毫米键盘
    调整、越界事务回滚以及 `--check-only` 不访问硬件。
- `tests/test_closed_loop_state_machine.py`
  - 验证 PREGRASP 重观测、每步 approach 新 PWM/新图像、阶段截断和失败停止。
- `tests/test_no_stale_frame_after_motion.py`
  - 验证动作后的观测时间戳必须晚于运动完成时间。
- `tests/test_bottle_demo.py`
  - 旧原型仅保留软件级回归覆盖；不构成真实 RGB-only/cached 路径重新启用许可。
- `tests/test_legacy_mode.py`
  - 验证 fixed-view 只能显式选择、默认路径不导入旧外参，并检查回滚释放/串口边界。
- `tools/test_visual_centering.py`
  - 验证 000/003 居中方向、死区、PWM 单步和边界饱和停止。

### 文档

- `README.md`
  - 用动态坐标链替换旧 fixed-view 使用说明，增加安装/配置、0.17 m 深度边界、
    dry-run、实时纯观察调参、日志、测试、严格快捷入口、视觉居中以及
    observe/pregrasp/approach/close/lift 五阶段命令。
- `../指令合集.md`
  - 删除旧 bottle-demo、cached target、RGB-only 和 missing-005 真实命令；增加严格
    center/oneclick/full、五阶段动态实机命令及闭爪标定门禁。
- `docs/CONFIG_MIGRATION_V2.md`
  - 记录 v1→v2 字段映射、当前已验证 hand-eye、Servo005=1112、闭爪待测门禁、严格
    入口退役边界和安全迁移流程。
- `KNOWN_PHYSICAL_VALUES_TO_MEASURE.md`
  - 只列仍需实测的 open TCP、Servo005 闭合/内宽、标准 bottle 与精度验证项；明确
    `gripper_close_calibrated=false` 时 close/lift/full fail closed。
- `docs/example_logs/dry_run_lift.jsonl`
  - 提供带 `simulated=true` 运动记录的 dry-run 动态闭环 JSONL；不作为实机成功证据。
- `docs/current_live_target_lock.json`
  - 仅保留历史诊断证据；严格真实入口绝不读取该缓存作为接近依据。
- `CHANGELOG.md`
  - 作为稳定入口链接到本文件。
- `CHANGELOG_DYNAMIC_GRASP.md`
  - 本逐文件动态抓取重构记录。

### 安全与兼容说明

- 保留非 ROS、RK3588、RKNN YOLO11、D435 RGB 对齐、ASCII/PRAD、dry-run、工作空间
  与 PWM 限位、Servo004=1500、阶段门控和不自动 PDST。
- 默认动态路径不使用固定外参；只有显式 `legacy_fixed_view` 才进入隔离弃用回滚模块，
  且仍受 `--enable_arm`、冻结标定、参考姿态与逐阶段六轴 PRAD 门禁约束，不自动 PDST。
- 尚未完成的实机阶段不得写成“已通过”。
