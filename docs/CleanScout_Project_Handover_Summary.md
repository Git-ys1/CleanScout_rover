# CleanScout Project Handover Summary

## 项目定位

`CleanScout_rover` 当前是一套以 Raspberry Pi 为上位主控、下位机逐步从 Arduino UNO 过渡到 OpenRF1(STM32F103) 的移动机器人项目。

项目当前主线包括：

1. 树莓派 ROS1/Noetic 工作区接管
2. 底盘串口控制链收口
3. A3 雷达接入
4. MPU6050 IMU 接入
5. Bench bringup 收口
6. 地图保存与 AMCL / move_base 导航入口接入
7. OpenRF1 USB 串口 smoke test

## 当前长期工作区

当前树莓派长期主工作区为：

```text
Raspberrypi/catkin_ws
```

当前不再建议将旧 `goolge_ws`、旧 `~/catkin_ws` 当作默认主线工作区。

## 当前树莓派已打通的硬件与链路

### 一、A3 雷达

- 设备别名：`/dev/clblidar`
- 波特率：`256000`
- 已通过官方 `rplidar_ros`
- `/scan` 可稳定发布

### 二、MPU6050

- 总线：`I2C-1`
- 地址：`0x68`
- 已通过 `mpu6050_i2c_bridge`
- 已接通：
  - `/raw_imu`
  - `/imu/data_raw`
  - `/imu/data`

### 三、UNO 基线

- 树莓派侧已形成 `W,w1,w2,w3,w4` 串口桥基线
- 已有：
  - `wheel_bridge.py`
  - `cmdvel_to_wheels.py`
  - `enc_to_raw_vel.py`

### 四、双风机

- `GPIO17`：继电器总开关
- `GPIO18`：风机 A PWM
- `GPIO19`：风机 B PWM
- 双风机四段最小验证已通过

### 五、地图与导航入口

- 已保存地图：

```text
Raspberrypi/maps/desk_map_001.yaml
Raspberrypi/maps/desk_map_001.pgm
```

- 已补导航入口：

```text
clbrobot/launch/desk_map_navigation.launch
```

## 当前下位机现状

### UNO

UNO 曾长期作为底盘主控基线。

### OpenRF1

当前下位机已进入：

```text
STM32F103 + OpenRF1
```

树莓派端当前已完成 OpenRF1 USB 串口 smoke test，但尚未替换旧 ROS bridge 主线。

## OpenRF1 当前树莓派侧结论

当前树莓派端已经确认：

1. OpenRF1 对应设备为：

```text
/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
```

2. `python3-serial` 串口 smoke test 已打通
3. 已实际收到：
   - `ACK:E`
   - `ACK:M`
   - `ACK:STOP`
   - `ACK:W`
   - `VEL,...`
   - `PWM,...`
   - `ENC,...`

4. 当前旧 `bringup.launch` 仍然是 Arduino 时代的 `/dev/clbbase + rosserial_python` 基线，不适用于 OpenRF1

## 当前运行时问题与整改

### 已查明的旧问题

过去树莓派端长期被以下问题反复干扰：

1. 残留 `rosmaster/roscore`
2. 旧工作区自动 source
3. 自动连旧 master
4. 多入口、后台启动导致 run_id 冲突

### 已落地整改

新增并冻结：

1. `use_cleanscout_pi.sh`
2. `check_ros_master.sh`
3. `clean_ros_sessions.sh`
4. `start_slam_mapping.sh`
5. `start_desk_navigation.sh`

## 当前还未完全收口的问题

### 一、导航执行链稳定性

虽然导航入口、AMCL、move_base、地图、雷达、IMU、底盘桥均已接通到可实验阶段，但当前仍存在：

1. 导航启动时序与底盘桥 ready 时序不稳
2. 某些会话里底盘桥会出现 `ready timeout`
3. 导航层虽然能接受目标，但车辆不一定稳定执行

### 二、里程计/编码器尺度异常

当前已实测到：

1. 手动拨动轮子时，地图中的位移偏大
2. 点近距离导航目标时，车辆可能冲出地图

因此当前主问题已经收敛为：

```text
odom/encoder scale 不正确
```

## 当前分支与发布口径

树莓派 ROS 相关工作已经补充进入：

```text
main
```

OpenRF1 当前 smoke test 仍建议在单独自测分支推进，待下一轮再决定是否补充回 main。

## 给下一位接手者的一句话

不要再从头验证雷达、IMU、地图保存这些已完成项；当前最应该继续推进的是：

1. OpenRF1 ROS bridge 正式替换旧 `/dev/clbbase` 路线
2. 导航启动时序收口
3. 里程计/编码器尺度校准
4. 导航执行链真正落地到实车
