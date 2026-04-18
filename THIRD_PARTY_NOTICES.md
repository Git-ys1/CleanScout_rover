# THIRD_PARTY_NOTICES

本文件记录 CleanScout_rover 在 C-0.0.2 阶段纳入的第三方代码来源与许可证核验状态。

## 1) Tyler_1_Library

- 名称：Tyler_1（太乐1号）Arduino 库
- 当前仓库路径：
- 原始基线保留：`Tyler_1_Library/`
- 受控副本：`libraries/Tyler_1/`
- 来源线索：
- 太极创客 Tyler-1 项目页：<http://www.taichi-maker.com/homepage/arduino-tutorial-index/arduino-hardware/#taile1>
- 库内 README 中引用的资源页（同站点教程与资料）
- 使用方式：
- 在本仓先“原样保留 + 完整拷贝受控纳管”；
- C-0.0.2 不修改外部 API 与控制逻辑语义。
- 许可证状态：`待核验`
- 备注：当前导入包内未发现明确 LICENSE 文件；后续需由项目负责人补充核验结论。

## 2) Adafruit Motor Shield Library (AFMotor)

- 名称：Adafruit-Motor-Shield-library (AFMotor)
- 当前仓库路径：`Adafruit-Motor-Shield-library-master/`
- 来源：
- 仓库地址：<https://github.com/adafruit/Adafruit-Motor-Shield-library>
- 文档页：<https://learn.adafruit.com/adafruit-motor-shield>
- 使用方式：
- 本仓 C-0.0.x 阶段按现状引入，用作 UNO + AFMotor 扩展板构建依赖；
- 暂不改动其驱动逻辑。
- 许可证状态：`待核验`
- 备注：当前导入目录中未发现 LICENSE 文件（仅见版权注释）；后续需补许可证核验记录。
