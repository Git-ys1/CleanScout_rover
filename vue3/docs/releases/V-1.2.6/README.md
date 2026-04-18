---
version: V-1.2.6
based_on_branch: feature/c-3.0.8-openrf1-cn1-cn3-encoder-recovery
branch_source: GitHub branches page
published_to_root: vue3/
published_at_commit: 92c5baa06074175afe08b60846585035eb9e9f09
---

# V-1.2.6 小范围热修

## 问题

当前 `src/pages.json` 虽然已经配置了原生 `tabBar`，但实际在当前 `H5` 手机访问场景下，底部导航栏没有稳定显示出来，导致：

- 首页 / 对话 / 我的 三个一级入口在底部不可见
- 手机端主导航体验中断

## 热修策略

本轮不推翻 `pages.json` 里的原生 `tabBar` 配置，只追加一个 `H5` 兜底方案：

- 新增 `src/components/H5TabBarFallback.vue`
- 仅挂载到 `首页 / 对话 / 我的` 三个一级页面
- 组件会在 `H5` 端检测原生 `uni-tabbar` 是否真实可见
- 若原生 `tabBar` 未显示，则展示兜底底栏
- 若原生 `tabBar` 已正常可见，则不重复显示

## 本轮改动

- 新增 `src/components/H5TabBarFallback.vue`
- `src/pages/index/index.vue` 接入 `H5` 兜底底栏
- `src/pages/chat/index.vue` 接入 `H5` 兜底底栏
- `src/pages/profile/index.vue` 接入 `H5` 兜底底栏

## 验证

已完成：

- `cmd /c npm.cmd run build:h5`

通过标准：

- 当前 `H5` 构建通过
- 即便原生 `tabBar` 未正常渲染，手机端仍能看到底部导航
- 管理员页仍不进入一级底部导航

## 结论

`V-1.2.6` 是移动端导航可见性热修，不改后端、不改 OpenClaw 接入、不改管理员系统结构，只修复当前 `H5` 手机端看不到底部导航栏的问题。
