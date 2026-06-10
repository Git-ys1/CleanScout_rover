# OrangePi

OrangePi 是 CleanScout_rover 的边缘 AI 开发板目录，当前硬件为 Orange Pi 5 Max 8GB / RK3588 / Ubuntu 20.04.6。它和 `Raspberrypi/` 同属上位边缘计算层，但当前职责不同：本目录先冻结 RK3588 NPU、RKNN、YOLO11 和 USB 摄像头实时检测基线，暂不接 ROS、暂不接机械臂动作控制。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| RKNN Runtime | 已修复 `/usr/lib/librknnrt.so` 损坏问题，Runtime 2.3.2 可用 |
| RKNPU Driver | `0.9.6 20240322`，C API 与 Python RKNNLite 均验证通过 |
| YOLO11 图片检测 | 官方 `official_yolo11.rknn` 可完成 NPU 推理、后处理和结果图保存 |
| YOLO11 摄像头检测 | USB 摄像头、OpenCV 窗口、NPU 推理、截图和视频保存均已跑通 |
| ROS / 机械臂融合 | 未开始，本轮只冻结 AI 感知基线 |

## 目录

| 路径 | 说明 |
| --- | --- |
| [rk3588_ai/](rk3588_ai/) | OrangePi RK3588 AI 基线、任务书、报告、脚本和 overlay |
| [rk3588_ai/model_zoo_overlay/](rk3588_ai/model_zoo_overlay/) | 对官方 RKNN Model Zoo v2.3.2 的轻量覆盖文件 |
| [rk3588_ai/UPSTREAMS.md](rk3588_ai/UPSTREAMS.md) | 被忽略的上游仓库、虚拟环境、模型和日志的恢复说明 |

## 不入库内容

以下内容属于板端/本地运行环境，不提交到主仓：

- `rknn_toolkit2_env/`
- `rknn_lite_env/`
- `rknn_model_zoo/` 上游完整仓库
- `models/`
- `debug_logs/`
- `.rknn` / `.onnx` / `.pt` 模型文件
- 验收视频

需要完整上游代码时，在板端或开发机重新 clone 官方 `airockchip/rknn_model_zoo`，再把 `model_zoo_overlay/` 覆盖进去。当前对应上游为：

```text
https://github.com/airockchip/rknn_model_zoo.git
tag v2.3.2
commit bad6c73
```

也可以直接使用：

```bash
cd OrangePi/rk3588_ai
bash scripts/apply_model_zoo_overlay.sh ~/rk3588_ai
```
