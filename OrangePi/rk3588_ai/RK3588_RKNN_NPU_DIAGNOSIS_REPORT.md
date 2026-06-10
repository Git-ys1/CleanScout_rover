# RK3588 RKNN NPU 诊断报告

诊断时间：2026-06-09
设备：Orange Pi 5 Max 8GB
结论：已修复，C API 和 RKNNLite Python NPU 推理均成功。

## 1. 最终结论

根因不是模型、Python wheel、RKNPU 驱动、NPU 硬件或系统镜像，而是
`/usr/lib/librknnrt.so` 文件损坏。

损坏库虽然能被 `strings` 识别为 2.3.2，但它只有 7,726,204 字节，
比同一官方仓库中的完整文件少 28 字节，并且中部内容已发生偏移。
`readelf` 报告节头超出文件末尾。直接执行
`ctypes.CDLL("/usr/lib/librknnrt.so")` 会收到 `SIGSEGV`。

使用仓库内完好的 2.3.2 Runtime 做 C API 对照测试时：

- `rknn_init ret=0`
- API 版本为 2.3.2
- 驱动版本为 0.9.6
- 官方 YOLO11 模型被识别为 1 个输入、9 个输出

这证明当前内核、驱动、硬件和模型是兼容的，不需要更换系统镜像。

## 2. 系统与 NPU

| 项目 | 结果 |
| --- | --- |
| 系统 | Orange Pi 1.0.0 Focal / Ubuntu 20.04.6 LTS |
| 内核 | `5.10.160-rockchip-rk3588` |
| 架构 | `aarch64` |
| 系统 Python | 3.8.10 |
| RKNPU 驱动 | `0.9.6 20240322` |
| 驱动初始化 | 成功，IOMMU 模式 |
| 用户权限 | `orangepi` 属于 `video` 和 `render` 组 |

`/dev/rknpu` 不存在，但这不是故障。本机 RKNPU 使用 DRM 设备：

- `/dev/dri/card1` -> `RKNPU`
- `/dev/dri/renderD129` -> `RKNPU`
- `/sys/devices/platform/rknpu_dev.13.auto` 存在

修复后的两次推理未在 `dmesg` 中产生新的 NPU、IOMMU、DMA 或段错误。

## 3. Runtime 与 Server

### librknnrt.so

修复前：

- 路径：`/usr/lib/librknnrt.so`
- 版本字符串：2.3.2
- 大小：7,726,204 字节
- SHA-256：`481ee2c00178ff4ea8c6f7ff62969c725e5cba12f56d08ec08ab5c58e8c7d19e`
- 状态：损坏，直接 `dlopen` 即段错误

官方完整文件：

- 来源：`~/rk3588_ai/rknn_model_zoo/3rdparty/rknpu2/Linux/aarch64/librknnrt.so`
- 大小：7,726,232 字节
- SHA-256：`d31fc19c85b85f6091b2bd0f6af9d962d5264a4e410bfb536402ec92bac738e8`
- 版本：`2.3.2 (429f97ae6b@2025-04-09T09:09:27)`

修复后 `/usr/lib/librknnrt.so` 与官方文件的大小和 SHA-256 完全一致。
损坏文件已备份为：

`/usr/lib/librknnrt.so.corrupt_bak_20260609_192332`

旧的 1.4.0 Runtime 备份仍为：

`/usr/lib/librknnrt.so.bak_20260609_163139`

### librknn_api.so

`/usr/lib/librknn_api.so` 存在，大小 3,569,000 字节，SHA-256 为：

`0ebc1b408f897863a91a1b9ed60f3838a801386c7b1ef7c54d55ead624cd8347`

它与旧 1.4.0 `librknnrt.so` 备份内容相同，是遗留文件。但 `LD_DEBUG`
证明 RKNNLite 2.3.2 本次只加载 `/usr/lib/librknnrt.so`，没有加载
`librknn_api.so`，因此它不是本次崩溃原因。

不要把 Model Zoo 的 `3rdparty/rknpu1/.../librknn_api.so` 安装到系统中；
那是 RKNPU1 库，不是 RK3588 RKNPU2 Runtime。

### rknn_server

- 路径：`/usr/bin/rknn_server`
- 版本：`2.3.2 (1842325 build@2025-03-30T09:54:34)`
- SHA-256：`eea12fe4270fad8aff015056319705b2eb871563ebd001eff8d8788bdd1c0cfa`
- 当前无进程、无 systemd service

本次是板端本地 RKNNLite/C API 推理，不依赖运行中的 `rknn_server`。

## 4. Python 与崩溃证据

Python 环境：

- 虚拟环境：`~/rk3588_ai/rknn_lite_env`
- Python：3.8.10
- `rknn-toolkit-lite2`：2.3.2
- `RKNNLite` 导入成功

修复前的干净环境复现结果为退出码 139。`LD_DEBUG` 显示：

1. RKNNLite 通过 `_ctypes` 打开 `/usr/lib/librknnrt.so`。
2. 动态加载器刚生成该库的 link map 就段错误。
3. 尚未看到 Runtime 初始化日志，也没有进入 NPU 驱动调用。
4. `librknn_api.so` 未被加载。

独立对照：

- `ctypes.CDLL(官方完整 librknnrt.so)`：成功
- `ctypes.CDLL(修复前 /usr/lib/librknnrt.so)`：退出码 139

因此 Python Lite2 只是触发了损坏库，Python 封装本身没有问题。

## 5. C API 隔离测试

已编译并运行最小 C API 程序：

`~/rk3588_ai/debug_logs/capi_test/rknn_capi_smoke`

使用官方完整 Runtime 时结果：

```text
rknn_init ret=0
RKNN_QUERY_SDK_VERSION ret=0 api=2.3.2 driver=0.9.6
RKNN_QUERY_IN_OUT_NUM ret=0 inputs=1 outputs=9
rknn_destroy ret=0
```

系统 Runtime 修复后，通过 `/usr/lib/librknnrt.so` 再测也全部成功。

## 6. 最终 Python NPU 推理

原测试脚本还存在一个独立问题：模型要求 4 维输入，脚本传入了
`(640, 640, 3)`。脚本已改为 `(1, 640, 640, 3)`，显式指定 NHWC，
并且在 RKNNLite 返回 `None` 时正确报错。

修复后结果：

| 模型 | init_runtime | inference | 输出 | 单次耗时 |
| --- | --- | --- | --- | --- |
| `models/official_yolo11.rknn` | 0 | 成功 | 9 个 | 约 63.7 ms |
| `models/lxmyzzs/yolo11n.rknn` | 0 | 成功 | 9 个 | 约 62.9 ms |

输出形状与官方优化 YOLO11 的三尺度 9 输出结构一致。
静态模型的 `RKNN_QUERY_INPUT_DYNAMIC_RANGE` 警告可忽略。

## 7. 最终判断

- 模型问题：否
- Python Lite2 问题：否
- Runtime 问题：是，系统 Runtime 文件损坏，现已修复
- 驱动问题：否，0.9.6 已通过 C API 和完整推理验证
- 系统镜像问题：否
- 硬件问题：否

## 8. 建议操作

1. 保持当前系统，不重装、不换镜像；当前组合已实际推理成功。
2. 后续更新 Runtime 时只使用官方 aarch64 文件，复制后核验 SHA-256，
   并先执行 `ctypes.CDLL("/usr/lib/librknnrt.so")` 冒烟测试。
3. 暂时保留旧 `librknn_api.so`；若以后清理，先审计是否有旧程序依赖，
   不要用 RKNPU1 的同名库覆盖它。

## 9. 关键日志

- `50_reproduce_official_python.txt`
- `51_lddebug_official_python.txt`
- `52_lddebug_rknn_grep.txt`
- `55_runtime_binary_integrity.txt`
- `59_ctypes_dlopen_smoke.txt`
- `capi_test/00_build_and_run.txt`
- `80_runtime_repair.txt`
- `81_post_repair_loader_and_capi.txt`
- `84_final_official_python_inference.txt`
- `85_final_custom_python_inference.txt`
- `86_dmesg_after_successful_inference.txt`
- `88_final_system_inventory.txt`

以上文件均位于 `~/rk3588_ai/debug_logs/`。

## 10. 官方参考

- RKNN Toolkit2 v2.3.2 aarch64 Runtime：
  https://github.com/airockchip/rknn-toolkit2/tree/v2.3.2/rknpu2/runtime/Linux/librknn_api/aarch64
- RKNN Model Zoo v2.3.2：
  https://github.com/airockchip/rknn_model_zoo/tree/v2.3.2
- 官方 YOLO11 示例：
  https://github.com/airockchip/rknn_model_zoo/tree/v2.3.2/examples/yolo11
