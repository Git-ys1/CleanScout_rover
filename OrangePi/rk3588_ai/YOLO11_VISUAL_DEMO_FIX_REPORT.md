# YOLO11 RKNN Python 可视化修复报告

诊断时间：2026-06-09
设备：Orange Pi 5 Max 8GB / RK3588
结果：官方 YOLO11 RKNN 模型已完成 NPU 推理、后处理和结果图片保存。

## 1. 根因

官方 `yolo11.py` 在 `dfl()` 内部晚加载 PyTorch。此时进程已经加载
OpenCV、NumPy 和 RKNNLite。OpenCV 依赖系统
`/lib/aarch64-linux-gnu/libgomp.so.1`，PyTorch 2.4.1 则依赖其 wheel
内的 `libgomp-804f19d4.so.1.0.0`。两者 SONAME 不同，都会占用
aarch64 glibc 的 static TLS 空间。

测试结果：

- `import torch`：成功。
- `cv2 -> torch`：PyTorch 自带 libgomp static TLS 分配失败。
- `torch -> cv2`：系统 libgomp static TLS 分配失败。
- `rknnlite -> cv2 -> torch`：失败。
- 仅 `LD_PRELOAD`、保留晚加载 torch：仍失败。
- `torch-first + LD_PRELOAD`：成功。

因此问题确实由两套 libgomp 和动态库加载顺序共同触发，不是 RKNN
Runtime、模型或 NPU 驱动故障。

## 2. 方案验证

### Torch-first + LD_PRELOAD

以下组合端到端成功：

```bash
LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1 \
python3 yolo11.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --img_save
```

它能完成检测，但要求每次启动都带环境变量，且脚本仍依赖仅用于 DFL
后处理的完整 PyTorch。

### NumPy DFL

最终采用 NumPy 实现稳定 softmax 和 DFL 加权求和。随机输入对比结果：

```text
max_abs_error: 0.0
mean_abs_error: 0.0
```

NumPy 版本与 torch-first + LD_PRELOAD 版本生成的最终 JPEG SHA-256
也完全相同：

```text
e2a22ffdfb2b91c11f87dfd52cefc5aafdb444117116c17ab33da083bf4af7fd
```

最终方案不需要 `LD_PRELOAD`，也没有向 `.bashrc` 写入环境变量。

## 3. 最终运行结果

运行命令：

```bash
cd ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python
source ~/rk3588_ai/rknn_lite_env/bin/activate

python3 yolo11.py \
  --model_path ~/rk3588_ai/models/official_yolo11.rknn \
  --target rk3588 \
  --img_save
```

结果：

```text
init_runtime ret = 0
person @ (109 236 223 536) 0.898
person @ (212 240 285 509) 0.843
person @ (477 230 559 521) 0.831
person @ (79 359 116 515) 0.448
bus  @ (91 135 552 435) 0.944
Detection result save to ./result/bus.jpg
exit_status=0
```

验收状态：

1. `official_yolo11.rknn` 成功推理：是。
2. 完成 `post_process`：是。
3. 输出 person / bus 类别：是。
4. 保存带检测框结果图：是。
5. 最终方案：NumPy DFL。
6. 最终运行是否需要 `LD_PRELOAD`：否。
7. RKNN Runtime / NPU 是否正常：是，Runtime 2.3.2，Driver 0.9.6。

结果图片：

```text
~/rk3588_ai/debug_logs/yolo11_visual_fix/yolo11_result.jpg
```

图片为 640x640 JPEG，已人工确认检测框、标签和置信度正常。

## 4. 文件改动

本任务修改：

```text
~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11.py
```

改动仅限 `dfl()`：删除局部 torch 导入和 torch tensor/softmax，替换为
数值等价的 NumPy 实现。

本任务没有修改：

```text
~/rk3588_ai/rknn_model_zoo/py_utils/rknn_executor.py
```

该文件在任务开始前已经是 RKNNLite 板端适配版本；任务前后 SHA-256
均为：

```text
9a2c3fa1a27d91cec4c5cbcb9386394b06177999b4d6f2095395cbdddb596cf5
```

## 5. 备份与恢复

任务开始前备份：

```text
~/rk3588_ai/debug_logs/yolo11_visual_fix/yolo11.py.before_fix.20260609_204322
~/rk3588_ai/debug_logs/yolo11_visual_fix/rknn_executor.py.before_fix.20260609_204322
```

恢复命令：

```bash
cp -av \
  ~/rk3588_ai/debug_logs/yolo11_visual_fix/yolo11.py.before_fix.20260609_204322 \
  ~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11.py

cp -av \
  ~/rk3588_ai/debug_logs/yolo11_visual_fix/rknn_executor.py.before_fix.20260609_204322 \
  ~/rk3588_ai/rknn_model_zoo/py_utils/rknn_executor.py
```

## 6. 摄像头接入

后续应继续基于：

```text
~/rk3588_ai/rknn_model_zoo/examples/yolo11/python/yolo11.py
```

保留其中的 `setup_model()`、letterbox、RGB 转换、`model.run()`、
`post_process()` 和 `draw()`。将当前图片文件循环替换为
`cv2.VideoCapture` 的逐帧读取循环即可。板端 executor 已负责为
三维 HWC 输入补 batch 维。

SSH 会话没有 `DISPLAY`，所以摄像头阶段优先保存视频/图片或发布到 ROS
图像话题；只有在图形桌面会话中才使用 `cv2.imshow()`。

## 7. 关键日志

日志目录：

```text
~/rk3588_ai/debug_logs/yolo11_visual_fix
```

关键文件：

- `05_import_order_results.txt`
- `07_baseline_img_show.txt`
- `09_preload_system_import_order.txt`
- `13_run_torch_first_preload.txt`
- `20_compare_dfl_numpy_torch.txt`
- `23_final_plain_run_numpy_dfl.txt`
- `24_final_result_sha256.txt`
- `25_final_image_validation.txt`
- `27_final_audit.txt`

## 8. 官方参考

- https://github.com/airockchip/rknn_model_zoo/blob/v2.3.2/examples/yolo11/python/yolo11.py
- https://github.com/airockchip/rknn_model_zoo/blob/v2.3.2/examples/yolo11/README.md
- https://github.com/airockchip/rknn-toolkit2/tree/v2.3.2
