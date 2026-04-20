# CleanScout Project Handover Summary

## 文档定位

这不是宣传稿，也不是阶段总结 PPT。

这份文档的目标只有一个：

```text
让下一位树莓派端代码工程师和项目负责人，用最短时间理解这个项目现在到底是什么状态、哪里能用、哪里不能用、哪些坑已经踩过、哪些错误不要再重复。
```

本文档会明确写出：

1. 项目当前真实主线
2. 当前工作区与旧工作区的关系
3. 已打通链路与真实运行口径
4. 当前最脆弱、最容易误判的部分
5. 这段时间实际犯过的错误
6. 下一位接手时最该优先做什么

## 0. 工作纪律

下一位接手者必须先遵守下面这些纪律，否则会重复踩坑：

### 纪律 1：先看代码和工作区，再动手

不要凭记忆认为：

1. 某个 launch 还是正式入口
2. 某个 topic 还是当前主口径
3. 某个包一定来自当前工作区

这个项目里“看起来像”的东西很多，真正运行的来源经常不是直觉上的那个。

### 纪律 2：不要把旧入口当正式入口

旧文件很多都还在仓里，但“还在”不等于“还该用”。

尤其不要随手继续用：

1. `bench_full_stack.launch`
2. `slam/lidar_slam_pi.launch`
3. `desk_map_navigation.launch`
4. 旧 UNO 桥相关 wrapper

### 纪律 3：不要一上来再写新脚本

先确认：

1. 当前正式入口是哪几个
2. 当前实际运行时来源是哪几个
3. 当前阻塞点到底是脚本、环境、还是底层依赖

这个项目最怕“还没理清入口，就继续新增入口”。

### 纪律 4：不要在没确认来源前乱删旧工作区内容

旧 `~/catkin_ws` 现在虽然不是主线工作区，但它仍然可能提供：

1. 雷达运行时
2. 历史地图/launch 线索
3. 旧包来源核查依据

没彻底切正前，不要贸然删旧工作区内容。

### 纪律 5：不要口头说“通了”，要说明是哪个链路通了

必须明确区分：

1. RF1 串口 smoke test 通了
2. Web/edge-relay 联调通了
3. 建图链通了
4. 导航链通了
5. 雷达真实运行时已经切到当前工作区了

这五件事不是一回事。

## 0.1 项目目标

项目当前真实目标不是泛泛的“机器人能跑起来”，而是分层推进：

### 当前硬目标

1. 用 OpenRF1 正式替换旧 UNO 底盘主链
2. 收口树莓派 ROS 工作区到 `Raspberrypi/catkin_ws`
3. 保持雷达、IMU、odom、建图、导航链可追踪
4. 建立 406 地图的正式建图/导航入口
5. 在不破坏主栈的前提下支持新后端联调 transport

### 当前阶段目标

按优先级看，当前阶段的重点是：

1. 正式入口收口
2. 雷达运行时来源收口
3. RF1 建图/导航链稳定性收口

而不是再扩展新功能。

## 0.2 项目组成

这个项目不是单一 ROS 包，而是多层组成的：

### 组成 1：树莓派 ROS 工作区

主工作区：

```text
/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
```

这是当前应该维护的主线。

### 组成 2：旧树莓派 ROS 工作区

旧工作区：

```text
/home/clbrobot/catkin_ws
```

它当前不是主线，但仍可能影响运行结果。

### 组成 3：系统 ROS 包

系统路径：

```text
/opt/ros/noetic
```

当前像 `gmapping`、`map_server`、`amcl`、`move_base` 等包都来自这里。

### 组成 4：树莓派 ROS 包层

当前主工作区里的关键包包括：

1. `clbrobot`
2. `csrpi_base_bridge`
3. `mpu6050_i2c_bridge`
4. `csrpi_edge_relay`
5. `rplidar_ros`（源码已迁入当前工作区）

### 组成 5：下位机与历史基线

当前同时存在两代底盘基线：

1. 旧 UNO 基线
2. 新 OpenRF1 基线

这是项目复杂度的重要来源。

### 组成 6：文档与任务书

项目大量状态不是全写在代码里，而是散落在：

1. `docs/PLAN/*.txt`
2. `docs/交流使用.txt`
3. `Raspberrypi/releases/*`
4. 本交接文档

所以下一位不能只看代码不看文档。

## 0.3 Git 纪律

下一位接手者必须遵守下面的 Git 纪律，否则很容易把现场状态搞乱：

### 纪律 1：主分支就是 `main`

当前树莓派相关成果已经持续回收到：

```text
main
```

不要再以为“真正主线只在某个本地未推分支”。

### 纪律 2：提交前先分清“本轮相关”和“无关文件”

当前仓里长期会有：

1. 新增但未跟踪的 `docs/PLAN/*.txt`
2. 其他链路的文档
3. 前端/V 线相关改动

提交树莓派改动时，必须只带本轮相关内容。

### 纪律 3：如果远端 `main` 更新了，优先同步，不要硬顶

当前多人协作痕迹明显，远端 `main` 经常先走一步。

原则是：

1. 先 `fetch`
2. 再按要求 `merge` 或 `rebase`
3. 再推送

不要想当然地把自己的本地状态硬推成唯一真相。

### 纪律 4：不要删除你没有彻底核清来源的旧文件

特别是：

1. 旧 launch
2. 旧地图
3. 旧工作区引用线索

在交接期，这些文件常常是唯一能解释“历史上到底怎么跑过”的证据。

### 纪律 5：每轮提交都要写明“干了什么”和“没解决什么”

这个项目最怕只写“完成某功能”，不写：

1. 运行时是否仍借旧工作区
2. 当前是否只是阶段性打通
3. 哪些旧入口仍保留但废弃

如果不写清楚，下一位就会把阶段性进展误判成完全收口。

## 一、项目本质

`CleanScout_rover` 当前是一套以 Raspberry Pi 为上位主控、底盘下位机从 Arduino UNO 逐步切换到 OpenRF1(STM32F103) 的移动机器人项目。

项目并不是“从零开始”，也不是“只有一套干净的新工程”。

它的真实状态是：

1. 新链路已经在逐步建立
2. 旧链路还没有完全退出
3. 新旧工作区、新旧 launch、新旧底盘语义长期交织
4. 能跑起来不等于已经彻底收口

这个项目最大的难点，不是“会不会写 ROS 节点”，而是：

```text
在旧链路还留着的前提下，把真实运行链、调试链、建图链、导航链、新后端联调链分别理顺，不让它们互相误伤。
```

## 二、当前长期主工作区

当前长期主工作区是：

```text
/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws
```

这是后续应该继续维护的主线工作区。

### 但必须强调

虽然主线工作区已经切到这里，运行时仍然和旧环境有交叉：

1. `/home/clbrobot/catkin_ws/`
2. 系统 `/opt/ros/noetic`

这些交叉不是理论上的，而是**已经实际影响运行结果**。

## 三、当前最重要的项目特点

这项目最容易坑死接手者的，不是代码复杂，而是结构复杂。

### 特点 1：旧新工作区交织

当前真实情况不是“新工作区完全独立运行”。

而是：

1. 当前工作区：`Raspberrypi/catkin_ws`
2. 旧工作区：`/home/clbrobot/catkin_ws`
3. 系统包：`/opt/ros/noetic`

三者会同时影响运行结果。

### 特点 2：旧新底盘口径交织

当前至少存在两套底盘语义：

1. 旧 UNO 口径
   - `wheel_bridge.py`
   - `cmdvel_to_wheels.py`
   - `enc_to_raw_vel.py`
   - `W,w1,w2,w3,w4`
   - ticks/ticks/s 语义

2. 新 RF1 口径
   - `rf1_serial_bridge.py`
   - `cmdvel_to_rf1.py`
   - `rf1_vel_to_odom.py`
   - `W,a,b,c,d`
   - 单位 `m/s`

只要把两套东西混到一个入口里，基本就会出事。

### 特点 3：旧新 launch 长期共存

当前工作区里同时存在：

1. 旧总栈 / 旧 wrapper
2. Web 联调栈
3. RF1 最小基线栈
4. 新建图/导航分阶段入口

这些文件很多都还在仓里，**不代表都该继续用**。

### 特点 4：有些包来自当前工作区，有些包来自系统，有些运行时仍借旧工作区

当前已经查清：

1. `gmapping` 来自系统 `/opt/ros/noetic`
2. `map_server / amcl / move_base` 来自系统 `/opt/ros/noetic`
3. `rplidar_ros` 源码已迁入当前工作区
4. 但 `rplidarNode` 运行时长期仍可能借旧 `~/catkin_ws/devel/lib/rplidar_ros/rplidarNode`

这不是小问题，是当前建图/导航稳定性的核心脆弱点之一。

### 特点 5：有 Web/后端联调链，但那不是建图导航链

当前还存在：

1. rosbridge 本地链
2. edge-relay 新后端链

这两条链对 V 线联调重要，但对建图/导航不是必需。

如果把它们混进建图链，树莓派这类弱板子很容易变得不稳定。

## 四、当前硬件与设备事实

### 1. OpenRF1

当前树莓派侧已确认 OpenRF1 设备优先路径为：

```text
/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
```

回退设备应视为：

```text
/dev/ttyUSB1
```

不是 `ttyUSB0`。

### 2. RPLIDAR A3

当前雷达设备别名口径为：

```text
/dev/clblidar
```

波特率：

```text
256000
```

### 3. MPU6050

当前 IMU 口径：

1. 总线：`I2C-1`
2. 地址：`0x68`
3. 当前输出目标是标准 `/imu/data`

### 4. 地图文件

历史旧图：

```text
Raspberrypi/maps/desk_map_001.yaml
Raspberrypi/maps/desk_map_001.pgm
```

当前新目标图：

```text
$(find clbrobot)/maps/406.yaml
$(find clbrobot)/maps/406.pgm
```

## 五、当前已经完成并确认的链路

### 1. OpenRF1 串口 smoke test 已打通

已实际收到过：

1. `ACK:E`
2. `ACK:M`
3. `ACK:STOP`
4. `ACK:W`
5. `VEL,...`
6. `PWM,...`
7. `ENC,...`

### 2. RF1 ROS 最小基线已建立

当前已建立的新底盘桥包括：

1. `cmdvel_to_rf1.py`
2. `rf1_serial_bridge.py`
3. `rf1_vel_to_odom.py`

### 3. 新后端 edge-relay 已阶段性打通

已经明确拿到过：

```text
hello_ack accepted=True
```

并且现场已确认过：

```text
通过新后端链路可以控制小车
```

### 4. 旧地图不是假历史，确实是 SLAM 建出来的

旧链路已经核清：

1. `start_slam_mapping.sh`
2. `slam/lidar_slam_pi.launch`
3. `slam/lidar_slam.launch`
4. `param/navigation/slam_gmapping.xml`

并且旧 `slam_gmapping.xml` 里明确是：

```xml
<node pkg="gmapping" type="slam_gmapping" ...>
```

所以：

```text
旧图确实是通过 gmapping SLAM 链建出来的。
```

## 六、当前已知但还没真正收口的问题

### 问题 1：雷达运行时仍依赖旧工作区编译产物

这是当前最重要的问题之一。

当前已经查实：

1. `rplidar_ros` 源码已迁入当前工作区
2. 但运行时长期仍可能走：

```text
/home/clbrobot/catkin_ws/devel/lib/rplidar_ros/rplidarNode
```

这意味着：

1. 雷达还没完全转正到当前工作区
2. 这会直接影响建图/导航启动稳定性
3. 如果后续继续挡住 406 建图/导航，就必须考虑在当前工作区正式重新编译并切正

### 问题 2：启动链长期混乱

当前项目里长期同时存在：

1. 旧总栈 `bench_full_stack.launch`
2. 旧建图 wrapper `lidar_slam_pi.launch`
3. 旧导航 wrapper `desk_map_navigation.launch`
4. Web 联调栈 `bringup_rf1_web.launch`
5. 新建图/导航分阶段脚本

只要口径没写清，很容易误用。

### 问题 3：旧 UNO 链残留还在

以下旧脚本还在仓里：

1. `wheel_bridge.py`
2. `cmdvel_to_wheels.py`
3. `enc_to_raw_vel.py`

它们并不代表当前就该用，但如果 launch 里再引用到它们，就会把项目拉回旧语义。

### 问题 4：导航执行链仍未真正证明完全稳定

虽然已有：

1. `/scan`
2. `/odom`
3. `/imu/data`
4. `/amcl_pose`
5. `/move_base/status`

这些链路的阶段性工作，但仍不能等价于：

```text
406 导航链已经完全稳定可长期值守。
```

### 问题 5：里程计尺度仍需后续校准

这一点在旧交接里已经提过，当前依然没完全证明已经收口。

## 七、这段时间我实际犯过的错误

这一段必须写，不然下一位还会再踩一遍。

### 错误 1：一开始把 `rplidar_ros` 不在当前工作区误判成“雷达没了”

真实情况是：

1. 雷达包原先确实主要在旧 `~/catkin_ws`
2. 这次新会话没有自动带上旧环境
3. 我前期没有第一时间把“旧环境来源”钉死

这个错误导致前期对雷达链判断不够稳。

### 错误 2：一度用 `/scan` stub 顶合同

在当前机器找不到 `rplidar_ros` 的瞬间，我曾临时放过一个 `/scan` stub 来维持 V 线 topic 合同。

虽然这样能保联调合同，但它不等于真实雷达恢复。

这个选择在建图/导航语境下是危险的，因为会掩盖真实问题。

### 错误 3：把 edge-relay 初版做成独立第二套 ROS

这后来已经被证明方向不对。

正确方向应当是：

```text
edge-relay 必须并入现有 ROS 主栈，而不是自己另起第二套 master。
```

### 错误 4：一度把 websocket recv timeout 误判成断线

这导致 edge-relay 在 `hello_ack` 后仍然自杀式重连。

这个问题后来已修正，但它说明：

1. 后端联调时不要只盯 token
2. 客户端连接生命周期管理更容易出错

### 错误 5：启动脚本设计出现“套娃互相清场”

这是最近最明显、也最蠢的错误之一。

错误模式是：

1. 顶层脚本调下层脚本
2. 下层脚本里自己又 clean
3. 把上层刚拉起的东西又清掉

这属于启动链设计错误，不是参数小问题。

### 错误 6：前序把 `slam_gmapping` 当包名直接查找

这是一次定位方式错误。

正确关系应当是：

1. 包名：`gmapping`
2. 节点类型：`slam_gmapping`

这件事已经纠正，但必须写入交接，避免下一位再浪费时间。

### 错误 7：前序脚本写得过于复杂、入口重复、口径冲突

真实发生过：

1. 同类功能入口过多
2. 正式入口和调试入口没有严格区分
3. 文档写得不够稳
4. 有的脚本里没统一使用 `bash` 调，导致执行权限问题被用户踩到

这不是“用户不会用”，而是脚本口径没有收干净。

## 八、当前真正该视为正式口径的东西

### 当前正式应维护的环境脚本

1. `use_cleanscout_pi.sh`

### 当前正式应维护的建图/导航清场脚本

1. `clean_mapping_nav_sessions.sh`

### 当前正式应维护的建图/导航入口

1. `run_slam_mapping.sh`
2. `save_map.sh`
3. `start_desk_navigation.sh`

### 当前正式应维护的小 launch

1. `bringup_rf1_min.launch`
2. `core/imu_only.launch`
3. `lidar/rplidar.launch`
4. `slam/mapping_406_rf1.launch`
5. `nav/navigation_406_rf1.launch`

## 九、当前仍在仓里，但应视为旧实现 / 废弃入口

以下内容不一定马上删，但不应再作为正式建图/导航入口使用：

1. `bench_full_stack.launch`
2. `slam/lidar_slam_pi.launch`
3. `desk_map_navigation.launch`
4. `bringup_rf1_web.launch`
5. `run_rf1_web_stack.sh`
6. `start_slam_mapping.sh`
7. 旧 UNO 桥相关 wrapper

这些保留历史意义可以，但不能再让用户误以为它们等价于现行正式入口。

## 十、给下一位接手者最重要的建议

### 1. 不要再把“能起 topic”当成“已经彻底收口”

这项目很多问题都不是“完全起不来”，而是：

1. 能起
2. 但口径混
3. 运行时来源不纯
4. 偶发不稳

### 2. 先做来源收口，再谈稳定值守

最该优先核清的不是“再写新节点”，而是：

1. 雷达到底从哪个工作区的哪个二进制在跑
2. 建图/导航正式入口到底只剩哪几个
3. 旧 UNO 链到底还有没有被引用进正式入口

### 3. 如果雷达旧 runtime 持续挡路，就该下决心处理底层

如果继续观察到：

1. `/scan` 偶发没有
2. `rplidarNode` 起不稳
3. 仍依赖旧 `~/catkin_ws/devel/lib/rplidar_ros/rplidarNode`

那就不要再犹豫，应该推进：

1. 在当前工作区正式编译 `rplidar_ros`
2. 明确切断对旧运行时的依赖
3. 用当前工作区路径完成雷达链转正

### 4. 建图导航阶段不要把 Web / V 线联调链混进来

建图导航要尽量轻：

1. 不带 rosbridge
2. 不带 edge-relay
3. 不带 Web stack

V 线联调和建图导航都重要，但不是同一阶段的同一条链。

## 十一、一句话总结

```text
这个项目当前已经从“完全靠旧 UNO 和旧工作区跑”推进到“RF1 新基线、新后端联调链、406 建图导航入口逐步建立”的阶段，但最大特点仍然是旧新工作区、旧新 launch、旧新底盘口径长期交织。真正需要优先收口的不是再堆新功能，而是把正式入口、运行时来源和雷达底层依赖彻底理清，不再让旧工作区编译产物偷偷决定系统行为。
```
