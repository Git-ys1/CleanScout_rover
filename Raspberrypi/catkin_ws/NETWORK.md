# CleanScout 网络基线

`C-4.1.6` 起，CleanScout 的默认工作网络从手机热点迁移到随身 Wi-Fi。
网络地址由 `cleanscout_network.sh` 统一维护，PC 与树莓派入口不再各自保存一套推导规则。

## 当前默认：随身 Wi-Fi

| 项目 | 固定值 | 用途 |
| --- | --- | --- |
| SSID | `My Super Net` | 默认现场局域网 |
| 网关 | `192.168.8.1` | 随身 Wi-Fi 管理与 DHCP 网关 |
| Raspberry Pi | `192.168.8.108` | ROS master、硬件桥与 edge relay |
| Orange Pi | `192.168.8.148` | RK3588 AI 与机械臂视觉 |
| Ubuntu PC | `192.168.8.222` | RViz、导航、建图与本地 backend |

默认加载方式：

```bash
source ./use_cleanscout_pc.sh
```

结果应包含：

```text
CLEANSCOUT_NETWORK_MODE=portable_wifi
ROS_MASTER_URI=http://192.168.8.108:11311
```

树莓派端仍从默认路由自动读取自己的实际地址，因此 `use_cleanscout_pi.sh` 不硬编码本机 IP。

## 旧模式：手机热点

手机热点会改变 `10.x.x.0/24` 子网，因此旧逻辑不能冻结完整地址，只保留尾号约定：

| 角色 | 旧规则 |
| --- | --- |
| Raspberry Pi / ROS master | 当前 PC 子网 + `.84` |
| Ubuntu PC / 本地 backend | 当前树莓派子网 + `.190` |

需要临时回到手机热点时显式启用：

```bash
export CLEANSCOUT_NETWORK_MODE=phone_hotspot
source ./use_cleanscout_pc.sh
```

该模式只用于旧现场网络兼容，不再是仓库默认值。

## 手动覆盖

| 变量 | 作用 | 示例 |
| --- | --- | --- |
| `CLEANSCOUT_NETWORK_MODE` | 选择 `portable_wifi` 或 `phone_hotspot` | `phone_hotspot` |
| `CLEANSCOUT_PI_HOST` | 覆盖 PC 使用的 ROS master 主机 | `clbrobot.local` |
| `CLEANSCOUT_PC_HOST` | 覆盖树莓派使用的本地 backend 主机 | `192.168.8.222` |
| `CLEANSCOUT_PORTABLE_PI_IP` | 覆盖随身 Wi-Fi 树莓派地址 | `192.168.8.108` |
| `CLEANSCOUT_PORTABLE_PC_IP` | 覆盖随身 Wi-Fi PC 地址 | `192.168.8.222` |
| `CLEANSCOUT_PHONE_PI_SUFFIX` | 覆盖旧热点树莓派尾号 | `84` |
| `CLEANSCOUT_PHONE_PC_SUFFIX` | 覆盖旧热点 PC/backend 尾号 | `190` |

`EDGE_FALLBACK_HOST`、`EDGE_RELAY_HOST` 和完整 `*_URL` 变量仍具有最高优先级，便于专项联调。

## Wi-Fi 自动连接顺序

树莓派 NetworkManager 当前保存：

| 连接 | 自动连接优先级 | 说明 |
| --- | --- | --- |
| 手机热点 `please enter text` | `0` | 两者同时存在时优先保留旧控制链 |
| 随身 Wi-Fi `My Super Net` | `-1` | 手机热点关闭后自动接入默认工作网络 |

这里的 NetworkManager 优先级只决定开机/断线时选哪个 AP；仓库中的
`CLEANSCOUT_NETWORK_MODE=portable_wifi` 决定 ROS 与 backend 默认使用哪套地址，两者不要混淆。

## 只读检查

```bash
./cleanscout_network.sh
ping -c 2 192.168.8.108
ssh clbrobot@192.168.8.108
```

手机热点规则可在不切换 Wi-Fi 的情况下检查：

```bash
CLEANSCOUT_NETWORK_MODE=phone_hotspot ./cleanscout_network.sh
```

仓库只记录 SSID、地址和优先级，不记录 Wi-Fi 密码。
