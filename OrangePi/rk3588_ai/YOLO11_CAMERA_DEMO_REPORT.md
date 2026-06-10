# YOLO11 RKNN USB 摄像头实时检测报告

诊断与实现时间：2026-06-09
设备：Orange Pi 5 Max 8GB / RK3588
结果：USB 摄像头、RKNN NPU 推理、YOLO11 后处理、实时窗口、截图和
视频保存链路均已跑通。

## 1. 摄像头与 V4L2

设备：

```text
USB 2.0 Camera: HD USB Camera
USB ID: 05a3:9230
Driver: uvcvideo
```

节点：

- `/dev/video0`：真正的 Video Capture 流节点。
- `/dev/video1`：UVC Metadata Capture 节点，不能读取普通图像。

脚本已验证节点自动回退：以 `--camera 1` 启动时，`/dev/video1`
失败后自动打开 `/dev/video0`。

`/dev/video0` 支持：

- MJPG：1280x720@60、1920x1080@30、640x480@120.101 等。
- YUYV：640x480@30、1280x720@9、1920x1080@6 等。

实际 OpenCV 参数：

```text
device=/dev/video0
backend=V4L2
width=640
height=480
fps=120.101
fourcc=MJPG
```

请求参数为 640x480、30 FPS、MJPG。摄像头在该 MJPG 分辨率下选择了
其离散模式 120.101 FPS；实际处理速率由单线程 YOLO Pipeline 决定。

## 2. 新增脚本

新增文件：

```text
~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11_camera.py
```

任务前该文件不存在，所以没有可备份的旧版本。本任务没有修改已经通过
验收的 `yolo11.py` 或 `py_utils/rknn_executor.py`。

脚本复用现有 YOLO11 实现中的：

- `setup_model`
- `post_process`
- `COCO_test_helper`
- `letter_box`
- `IMG_SIZE`
- `CLASSES`

主要功能：

- V4L2 摄像头节点自动回退。
- FOURCC、宽、高、FPS 设置及实际值回读。
- Letterbox、BGR 到 RGB、显式 `(1, 640, 640, 3)` 输入。
- RKNNLite NPU 推理和 NumPy DFL 后处理。
- 检测框、类别、置信度和 FPS 叠加。
- `q` 或 ESC 退出。
- `--skip` 跳帧推理。
- `--print_boxes` 可选框日志，默认不刷屏。
- `--no_show` 无窗口运行。
- `--save_path` 保存视频。
- `--snapshot_path` 保存验收帧。
- `--max_frames` 用于自动化限帧测试。
- 所有退出路径释放摄像头、视频写入器、RKNN 模型和 OpenCV 窗口。

脚本还会清理 `COCO_test_helper` 的逐帧 letterbox 历史，避免实时运行时
列表持续增长。

## 3. 无窗口和视频验收

测试使用错误入口 `/dev/video1`，确认自动回退到 `/dev/video0`：

```bash
cd ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python
source ~/rk3588_ai/rknn_lite_env/bin/activate

python3 yolo11_camera.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 1 \
  --width 640 \
  --height 480 \
  --fps 30 \
  --fourcc MJPG \
  --no_show \
  --max_frames 90 \
  --save_path ~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_test.mp4 \
  --snapshot_path ~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_result.jpg
```

结果：

```text
Frames=90
Inferences=90
Pipeline FPS=12.31
NPU inference=40.74 ms
exit_status=0
```

输出视频：

```text
~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_test.mp4
```

视频属性：

```text
codec=mjpeg
resolution=640x480
fps=15
frames=90
duration=6 seconds
```

板端 OpenCV 的 `mp4v` 会错误选择不可用的
`mpeg4_v4l2m2m` 编码器。脚本根据实际探针结果优先使用 MJPEG；
生成的 MP4 已通过 `ffprobe` 和逐帧解码验证。

## 4. NoMachine GUI 验收

NoMachine 使用本机 X11 会话：

```text
DISPLAY=:0
XAUTHORITY=/home/orangepi/.Xauthority
```

窗口 `YOLO11 RKNN Camera` 已在 X11 中映射并持续读取 `/dev/video0`。
测试通过 XTest 发送真实 `q` 键，程序日志为：

```text
Stopped: q pressed.
Frames=50
Inferences=50
Pipeline FPS=17.03
NPU inference=33.69 ms
Camera released
RKNN model released
OpenCV windows destroyed
process_exit_status=0
```

这证明：

1. 窗口能够显示。
2. 窗口持续刷新摄像头原始画面和 YOLO 叠加层。
3. `cv2.waitKey(1)` 能接收 `q`。
4. 按键退出后摄像头与 NPU 正常释放。
5. 退出后 X11 窗口消失，`/dev/video0` 无进程占用。

代码同样处理 ESC 键值 27。

## 5. 性能

单线程初版实测：

- GUI、不写视频：Pipeline 约 15 到 18 FPS，最终约 17 FPS。
- 同时写 MJPEG 视频：Pipeline 约 12 FPS。
- 单次 RKNN inference：约 28 到 47 ms，随系统状态波动。
- 摄像头原始 MJPG 模式：640x480@120.101 FPS。

Pipeline FPS 包含采集、letterbox、颜色转换、NPU、后处理、画框和显示，
因此它是用户实际看到的刷新率。性能达到本任务预期，不使用多线程。

## 6. 结果媒体

无窗口验收截图：

```text
~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_headless_result.jpg
```

最终 GUI 验收截图：

```text
~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_result.jpg
```

验收视频：

```text
~/rk3588_ai/debug_logs/yolo11_camera/yolo11_camera_test.mp4
```

当前摄像头朝向机柜/墙面，画面倾斜且缺少清晰 COCO 目标，因此偶发边缘
误检。截图已确认 FPS、检测计数、框线和实时图像叠加正常。将摄像头摆正
并让 person、car、bottle 等目标进入画面后，脚本会直接显示对应类别和
置信度。

## 7. 正常运行方法

在 NoMachine 桌面终端运行：

```bash
cd ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python
source ~/rk3588_ai/rknn_lite_env/bin/activate

python3 yolo11_camera.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --camera 0 \
  --width 640 \
  --height 480 \
  --fps 30 \
  --fourcc MJPG
```

从普通 SSH 终端启动到 NoMachine 桌面：

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

退出方式：

- 窗口获得焦点后按 `q`。
- 或按 ESC。
- 终端 `Ctrl+C` 也会进入 Python 清理流程。

## 8. 文件与恢复

新增：

```text
examples/yolo11/python/yolo11_camera.py
```

未修改：

```text
examples/yolo11/python/yolo11.py
py_utils/rknn_executor.py
```

如需移除本次功能，只需删除新脚本：

```bash
rm ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11_camera.py
```

现有图片检测脚本不受影响。

## 9. 下一步

1. 调整鱼眼摄像头方向，使用清晰 person/bottle/chair 目标复核检测效果。
2. 如需更低延迟，再做采集线程和推理线程解耦，只保留最新帧。
3. 鱼眼边缘目标若明显变形，可标定内参并在推理前执行去畸变。

本阶段未接 ROS、未做机械臂、未修改 `.bashrc`，也未改动
`~/Fast-Drone-250`。

## 10. 关键日志

目录：

```text
~/rk3588_ai/debug_logs/yolo11_camera
```

关键文件：

- `01_v4l2_devices.txt`
- `02_video0_formats.txt`
- `03_camera_users.txt`
- `04_display.txt`
- `10_headless_camera_run_after_writer_fix.txt`
- `11_headless_artifact_audit.txt`
- `18_gui_camera_run_q_exit.txt`
- `19_gui_window_and_q_exit.txt`
- `20_gui_xtest_final_audit.txt`
- `21_final_code_and_resource_audit.txt`

## 11. 官方参考

- https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html
- https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
- https://docs.opencv.org/4.x/d7/dfc/group__highgui.html
- https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html
- https://github.com/airockchip/rknn_model_zoo/tree/v2.3.2/examples/yolo11
