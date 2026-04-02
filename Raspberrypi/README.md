# Raspberrypi

树莓派端结果发布入口。  
该目录用于承接树莓派侧由 `opencode` 或本地端单独推进的代码、文档和验证记录。

当前冻结口径：

- 树莓派端改动与主机端现有 `UNO + AFMotor` 基线隔离推进
- 每轮树莓派侧结果先在本目录发布，再决定是否回写到其他主线目录
- 本目录优先承接“上位机侧 / ROS2 侧 / 树莓派服务侧”成果，不混入 `J` 线机械臂实验副本

## 发布规则

- 每一轮单独建一个版本目录
- 目录名必须带版本号和主题
- 每轮至少提交一份 `README.md`
- 每轮必须写明：
  - 本轮目标
  - 改动文件
  - 运行环境
  - 启动方法
  - 验证结果
  - 已知问题

推荐目录结构：

```text
Raspberrypi/
  README.md
  releases/
    R-0.0.1_xxx/
      README.md
      src/
      scripts/
      configs/
      logs/
      assets/
```

## 当前约束

- 不直接覆盖 `sketches/`、`libraries/`、`jixiebi/` 下的现有受控基线
- 不把树莓派侧临时调试文件直接散放到仓库根目录
- 若树莓派侧只产出文档，也必须放在本目录对应版本子目录下

## 关联文档

- `docs/PLAN/C-2.0.5.md`
- `docs/PLAN/C-2.0.5_raspberrypi_publish_path.md`
