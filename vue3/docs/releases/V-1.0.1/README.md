---
version: V-1.0.1
based_on_branch: feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery
branch_source: GitHub branches page
published_to_root: vue3/
published_at_commit: c409573637e890bde16e851ca1cdb5ce4b780493
---

# V-1.0.1 立项补充冻结索引

## 本轮结论

`V-1.0.1` 不是业务开发轮，而是立项补充冻结轮。

本轮新增冻结的核心结论有三项：

1. V 线云端发布必须实时追踪主项目当前最新施工分支，不再盯住历史旧分支。
2. uni-app 官方文档正式提升为“V线官方底层开发手册”。
3. 后端从本轮开始正式纳入 V 线系统边界，但本轮不创建后端工程。

## 本轮元数据说明

- `based_on_branch`：记录本轮发布前在 GitHub 分支页确认的最新施工分支。
- `branch_source`：固定记录制度来源为 `GitHub branches page`。
- `published_to_root`：固定记录云端镜像发布目标为 `vue3/`。
- `published_at_commit`：记录本轮实际发布所基于的本地 checkpoint commit。

当前云端目标地址：

- 仓库主页：`https://github.com/Git-ys1/CleanScout_rover`
- 当前实例分支：`https://github.com/Git-ys1/CleanScout_rover/tree/feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery`

## 本轮补充冻结范围

- 云端追踪与发布纪律
- 官方底层开发手册制度
- 后端正式纳入系统边界
- 三层系统架构口径
- release 元数据记录规则

## 关联文档

- 正文补充文档：[V-1.0.1_project_supplement.md](./V-1.0.1_project_supplement.md)
- 历史冻结快照：[../V-1.0.0/README.md](../V-1.0.0/README.md)
- 仓库总说明：[../../../README.md](../../../README.md)

## 本轮验收对照

- 已新增 `docs/releases/V-1.0.1/README.md`
- 已新增 `docs/releases/V-1.0.1/V-1.0.1_project_supplement.md`
- 已明确“实时追踪当前主项目最新分支”
- 已将 uni-app 官方文档提升为“官方底层开发手册”
- 已明确“后端正式纳入项目边界”

## 当前状态

当前文档中的 `based_on_branch` 使用 `feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery` 作为当轮实例。制度上仍然要求每轮发布前重新确认 GitHub 分支页中的最新施工分支，实例分支不得被视为永久固定值。

Git 纪律补充：

- 开工前先建 checkpoint。
- 开工后立即按轮次做 Git 留痕。
- 本轮提交标题使用中文，关键词保留英文。
