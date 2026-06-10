# Upstreams And Ignored Artifacts

本目录采用轻量发布：提交 CleanScout 自己验证过的任务书、报告、脚本、overlay 和验收图片；不把上游完整仓库、虚拟环境、模型和运行日志直接提交到主仓。

## Official Upstream

| 组件 | 来源 | 当前本地版本 |
| --- | --- | --- |
| RKNN Model Zoo | `https://github.com/airockchip/rknn_model_zoo.git` | tag `v2.3.2`, commit `bad6c73` |

重建官方仓库：

```bash
cd ~/rk3588_ai
git clone https://github.com/airockchip/rknn_model_zoo.git rknn_model_zoo
cd rknn_model_zoo
git checkout bad6c73
```

或使用本目录脚本：

```bash
cd ~/CleanScout_rover/OrangePi/rk3588_ai
bash scripts/apply_model_zoo_overlay.sh ~/rk3588_ai
```

## What Is Ignored

| 路径 / 类型 | 原因 | 恢复方式 |
| --- | --- | --- |
| `rknn_model_zoo/` | 官方上游 Git 仓库，体积大且应保留上游历史 | 从 `airockchip/rknn_model_zoo` clone 到 `v2.3.2`，再应用 `model_zoo_overlay/` |
| `rknn_toolkit2_env/` / `rknn_lite_env/` | 本机或板端虚拟环境，不可跨机器直接复用 | 在目标机器按 RKNN 官方说明新建 venv 并安装对应 wheel |
| `models/` | `.rknn` / `.onnx` / `.pt` 模型通常较大且可重新转换或单独分发 | 放到 `~/rk3588_ai/models/`，当前命令默认使用 `official_yolo11.rknn` |
| `debug_logs/` | 板端运行日志和视频，容易快速膨胀 | 报告已提炼关键结论；需要原始日志时从板端导出 |
| `*.mp4` / `*.avi` | 验收视频体积大 | 重新运行 `yolo11_camera.py --no_show --save_path ...` 生成 |

## CleanScout Overlay

仓库提交的 overlay 文件：

```text
model_zoo_overlay/examples/yolo11/python/yolo11.py
model_zoo_overlay/examples/yolo11/python/yolo11_camera.py
```

它们覆盖到官方 Model Zoo 后提供：

1. NumPy DFL，规避 torch / libgomp static TLS 问题。
2. USB 摄像头实时 YOLO11 RKNN 检测脚本。
3. `--no_show`、`--save_path`、`--snapshot_path`、`--max_frames` 等验收参数。

## Why Not Vendor Everything

完整发布 `rknn_model_zoo/` 会把一个独立上游 Git 仓库嵌进 CleanScout 主仓，并且容易混入本地改动、模型和构建产物。当前方式更利于长期维护：上游来自官方 Git，CleanScout 只保存自己的差异和已验证结论。
