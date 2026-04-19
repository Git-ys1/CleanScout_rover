---
version: V-1.4.5
based_on_branch: main
branch_source: GitHub branches page + origin/main latest branch policy
published_to_root: vue3/
published_at_commit: pending-cloud-publish
---

# V-1.4.5 backend 部署 tips 热修

## 本轮结论

本轮不改代码，只补一份部署口径热修文档，解决当前“微信小程序已上线，但 backend `CORS_ALLOWED_ORIGINS` 不知道怎么填”的认知歧义。

新增文档：

- `docs/releases/V-1.4.5/backend-deploy-tips.md`

## 本轮目的

- 把 `CORS_ALLOWED_ORIGINS` 的真实含义写清
- 把“微信小程序上线”和“浏览器 H5 跨域”两条链拆开
- 给项目负责人留出必须拍板的决策项，避免部署人员继续猜

## 通过标准

- 已明确写出：小程序上线时，`CORS_ALLOWED_ORIGINS` 不等于 backend 域名，也不等于小程序地址
- 已明确写出：如果当前只有小程序，没有浏览器 H5，推荐默认值是什么
- 已明确写出：后续如果上线 H5 / admin web，应该怎么补白名单
- 已明确写出：项目负责人需要拍板的后续方向
