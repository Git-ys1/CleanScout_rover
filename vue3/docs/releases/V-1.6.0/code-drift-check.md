# V-1.6.0 main 代码 / 文档漂移收口

## 检查结论

本轮先收口 `V-1.5.0` 之后可能出现的公开漂移：

- `src/api/config.js` 已读取 `import.meta.env.VITE_API_BASE_URL`
- `src/api/config.js` 已读取 `import.meta.env.VITE_WS_BASE_URL`
- 前端不再硬编码 `http://127.0.0.1:3000/api`
- 当前 backend 仍没有真实 `/ws` 服务，因此 `VITE_WS_BASE_URL` 继续留空

## 生产 API 口径

从 `V-1.6.0` 起，生产 API 域名冻结为：

```text
https://api.hzhhds.top/api
```

当前新增生产环境文件：

- `.env.production`
- `.env.mp-weixin.production`
- `.env.app.production`

## 当前不变项

- 本地 H5 仍走 `.env.h5.local`
- 本地微信小程序仍走 `.env.mp-weixin.local`
- ROS 固定控制仍由前端调用 backend HTTP API，不允许前端直连 `rosbridge`
