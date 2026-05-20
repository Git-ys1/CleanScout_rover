# OpenRF1 Keil Overlay

这个目录只存放 `OpenRF1` 的自研应用层 overlay，不存放 vendor 原工程整包。

当前目的：

- 公开仓库保留迁移所需的最小自研代码与接口
- 避免把 vendor 原工程直接纳入公开 Git 历史

当前包含：

- `User/app_motor.*`
- `User/app_csr_bridge.*`
- `User/app_chassis.*`
- `User/app_telemetry.*`
- `integration_notes.md`

本地可编译工作副本统一放在：

- `_local/openrf1_keil_work/`

集成方式见：

- [integration_notes.md](f:/Project/CleanScout_rover/firmware/openrf1_keil_overlay/integration_notes.md)
