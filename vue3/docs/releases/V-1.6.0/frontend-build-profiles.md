# V-1.6.0 前端构建 profile 冻结

## 当前脚本矩阵

本轮把本地调试与生产发布入口拆开：

```text
dev:h5:local
build:h5:local
build:h5:production
dev:mp-weixin:local
build:mp-weixin:local
build:mp-weixin:production
build:app
build:app:production
```

## 默认口径

- `build:h5` 仍作为本地联调别名，等价于 `build:h5:local`
- `build:mp-weixin` 仍作为本地微信小程序调试别名，等价于 `build:mp-weixin:local`
- `scripts/release-mp-weixin.*` 只调用 `build:mp-weixin:production`

## API 地址

- H5 本地：`http://127.0.0.1:3000/api`
- 微信小程序本地：`http://10.117.77.190:3000/api`
- 生产：`https://api.hzhhds.top/api`

当前 `VITE_WS_BASE_URL` 全部留空，因为 backend 仍没有真实 `/ws` 服务。
