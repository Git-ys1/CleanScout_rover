# RK3588 AI Baseline

本目录记录 Orange Pi 5 Max 8GB 上 RK3588 NPU / RKNN / YOLO11 / USB 摄像头实时检测的已验证基线，并从 C-5.0.1 开始保存机械臂二维视觉追踪 dry-run 原型。这里不是完整 Python 虚拟环境，也不是 RKNN Model Zoo 上游仓库镜像；仓库只保存能复现结论的轻量脚本、报告、任务书、overlay 和安全 demo。

## 硬件与系统

| 项目 | 当前值 |
| --- | --- |
| 开发板 | Orange Pi 5 Max 8GB |
| SoC | RK3588 |
| 系统 | Ubuntu 20.04.6 / Orange Pi Focal |
| 内核 | `5.10.160-rockchip-rk3588` |
| RKNPU Driver | `0.9.6 20240322` |
| RKNN Runtime | 2.3.2 |
| Python 推理接口 | `rknn-toolkit-lite2 == 2.3.2` |
| 摄像头 | USB 2.0 Camera，`/dev/video0` 为 Video Capture 节点 |

## 关键结论

1. NPU 最初崩溃根因是 `/usr/lib/librknnrt.so` 文件损坏，不是模型、驱动、硬件或系统镜像问题。
2. 官方完整 Runtime 2.3.2 替换后，C API smoke 和 RKNNLite Python 推理均通过。
3. 官方 YOLO11 Python demo 的 `dfl()` 晚加载 PyTorch 会触发 aarch64 static TLS / libgomp 问题。
4. 最终采用 NumPy DFL，和 torch 版输出对比 `max_abs_error: 0.0`，运行不需要 `LD_PRELOAD`。
5. 新增 `yolo11_camera.py` 后，USB 摄像头实时检测窗口可运行，`q` / ESC 退出、资源释放已验证。
6. 新增 `arm_tracking_demo/` 后，YOLO11 检测结果可进入 target selector 与 visual servo，默认只 dry-run，不接 ROS。

## 文件说明

| 文件 / 目录 | 说明 |
| --- | --- |
| `任务书.txt` | RKNN Runtime 段错误诊断任务书 |
| `任务书2` | YOLO11 图片检测可视化修复任务书 |
| `任务书3` | USB 摄像头实时检测任务书 |
| `RK3588_RKNN_NPU_DIAGNOSIS_REPORT.md` | Runtime / Driver / C API / Python 推理诊断报告 |
| `YOLO11_VISUAL_DEMO_FIX_REPORT.md` | YOLO11 NumPy DFL 修复报告 |
| `YOLO11_CAMERA_DEMO_REPORT.md` | USB 摄像头实时检测报告 |
| `指令合集.md` | 板端摄像头、YOLO、机械臂 dry-run、单关节和真实追踪测试命令 |
| `test_rknn_core0.py` | RKNNLite 最小 Python 推理脚本 |
| `rknn_capi_smoke.c` | 最小 C API smoke test |
| `compare_dfl_numpy_torch.py` | NumPy DFL 与 torch DFL 等价性测试 |
| `test_import_orders.py` | torch / cv2 / RKNNLite 导入顺序测试 |
| `model_zoo_overlay/` | 已验证的 `yolo11.py` 与 `yolo11_camera.py` 覆盖文件 |
| `UPSTREAMS.md` | 被忽略的上游仓库、虚拟环境、模型和日志恢复说明 |
| `scripts/apply_model_zoo_overlay.sh` | clone 官方 Model Zoo 并应用 CleanScout overlay |
| `arm_tracking_demo/` | C-5.0.1 机械臂二维视觉追踪 dry-run demo |
| `*.jpg` | 图片与摄像头验收结果 |

## 板端使用

板端预期目录：

```bash
~/rk3588_ai
```

进入 YOLO11 示例：

```bash
cd ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python
source ~/rk3588_ai/rknn_lite_env/bin/activate
```

运行图片检测：

```bash
python3 yolo11.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --img_save
```

运行 USB 摄像头实时检测：

```bash
python3 yolo11_camera.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --width 640 \
  --height 480 \
  --fps 30 \
  --fourcc MJPG
```

普通 SSH 终端启动到 NoMachine 桌面：

```bash
DISPLAY=:0 \
XAUTHORITY=$HOME/.Xauthority \
XDG_RUNTIME_DIR=/run/user/1000 \
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
python3 yolo11_camera.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0
```

无窗口保存验收视频和截图：

```bash
python3 yolo11_camera.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --width 640 \
  --height 480 \
  --fps 30 \
  --fourcc MJPG \
  --no_show \
  --max_frames 90 \
  --save_path ~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_test.mp4 \
  --snapshot_path ~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_result.jpg
```

运行机械臂视觉追踪 dry-run：

```bash
cd ~/rk3588_ai/arm_tracking_demo
~/rk3588_ai/rknn_lite_env/bin/python3 yolo_arm_track.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --track_class any \
  --dry_run true \
  --enable_arm \
  --print_cmd \
  --no_show \
  --max_frames 5
```

真实机械臂动作前必须先执行：

```bash
~/rk3588_ai/rknn_lite_env/bin/python3 tools/scan_serial.py
~/rk3588_ai/rknn_lite_env/bin/python3 tools/bus_servo_probe.py --serial_port /dev/ttyUSB0 --read position --ids 0-5
~/rk3588_ai/rknn_lite_env/bin/python3 tools/test_arm_driver_dryrun.py --print_cmd
```

退出方式：

- 窗口获得焦点后按 `q`
- 或按 ESC
- 终端 `Ctrl+C` 会进入 Python 清理流程

## 应用 overlay

本仓不提交完整 `rknn_model_zoo/`，只提交 overlay。完整上游来自：

```text
https://github.com/airockchip/rknn_model_zoo.git
tag v2.3.2
commit bad6c73
```

自动 clone 并应用 overlay：

```bash
cd OrangePi/rk3588_ai
bash scripts/apply_model_zoo_overlay.sh ~/rk3588_ai
```

手动覆盖方式：

```bash
cp -av model_zoo_overlay/examples/yolo11/python/yolo11.py \
  ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11.py

cp -av model_zoo_overlay/examples/yolo11/python/yolo11_camera.py \
  ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11_camera.py
```

覆盖前请确认当前官方仓库版本为 RKNN Model Zoo v2.3.2 或兼容版本。

## 排障要点

| 现象 | 优先检查 |
| --- | --- |
| `RKNNLite.init_runtime()` 段错误 | 先核验 `/usr/lib/librknnrt.so` 文件大小、SHA-256、`readelf` 和 `ctypes.CDLL` |
| `Invalid RKNN model version` | Runtime 版本可能过旧，需要匹配 RKNN 2.3.2 |
| `torch.libs/libgomp... static TLS` | 不在主流程依赖 torch，使用 NumPy DFL |
| 摄像头节点打不开 | 先查 `v4l2-ctl --list-devices`；若节点存在但打不开，查 `fuser -v /dev/video0 /dev/video1` 是否被旧进程占用 |
| `mp4v` 写视频失败 | 使用 MJPEG fallback |
| SSH 没窗口 | 使用 `--no_show` 或设置 NoMachine 的 `DISPLAY=:0` |
| 机械臂真实模式报 `No module named serial` | 执行 `~/rk3588_ai/rknn_lite_env/bin/python3 -m pip install pyserial` 后再测单关节 |
| 机械臂“发了命令但不动/读不到角度” | 先用 `tools/bus_servo_probe.py --command '#000PRAD!'` 和 `--command '#000P1600T1000!'` 分别测读回与动作；读回指令属于官方总线舵机协议，若 OrangePi `rx_len=0`，优先查端口、线序、DTR/RTS 和是否接到正确总线链路 |

## 后续边界

当前阶段已证明 RK3588 上 YOLO11 感知链路可用，并建立了不接 ROS 的机械臂二维视觉追踪 dry-run demo。真实机械臂动作控制需要下一轮完成串口接线、`pyserial`、单关节方向和 PWM 安全范围验证；抓取、ROS 话题发布、完整 IK、鱼眼标定仍后续另开任务。
