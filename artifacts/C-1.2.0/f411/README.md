# F411 Artifacts Placeholder

本目录保存 `C-1.2.0` 的 `F411` 产物：`.elf`、`.hex`、`.map`。

当前状态：

- 已通过 `tools/build_f411_bridge.ps1` 产出：
  - `cj_bridge_f411.elf`
  - `cj_bridge_f411.hex`
  - `cj_bridge_f411.map`
- 当前产物基于最小启动文件 + 链接脚本 + 协议骨架 + `PB2` 心跳灯验证
- `PB2` 语义：外接 LED 阴极接 `PB2` 时，`PB2` 下拉为亮、上拉为灭
- 尚未完成实板烧录确认和 UART 回环验证
