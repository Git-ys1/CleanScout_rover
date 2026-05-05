# V-1.7.0 public-edge 云端部署说明

## profile

云端 edge-relay 部署使用：

```text
APP_PROFILE=public-edge
ROS_TRANSPORT=edge-relay
EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
```

模板位置：

```text
deploy/env/vline-backend.public-edge.env.example
```

`EDGE_DEVICE_BOOTSTRAP_TOKEN` 必须替换为 32 位以上随机 token。该 token 只用于 seed 初始化，入库后是 bcrypt hash。

## Nginx

`deploy/nginx/api.hzhhds.top.conf` 已包含两类反代：

- `/api/`：REST API
- `/edge/ros`：WebSocket edge-relay

WebSocket 反代必须显式透传：

```text
Upgrade
Connection
```

并设置较长的：

```text
proxy_read_timeout
proxy_send_timeout
```

正式入口：

```text
https://api.hzhhds.top/api
wss://api.hzhhds.top/edge/ros
```

## systemd

`backend` 入口已经切到：

```text
node src/server.js
```

不要再使用旧的：

```text
node src/app.js
```

## 部署边界

本轮只交付 backend 与 Nginx 配套，不实际登录 VPS 部署。

公网部署时，微信小程序配置的是微信后台 `request 合法域名`；`CORS_ALLOWED_ORIGINS` 只给 H5 / 浏览器 Origin 校验使用。

## 第三方 H5 托管域名

如果 H5 部署在 Netlify 等第三方平台，并且同时使用第三方默认域名和自定义域名访问，就必须把两个浏览器 Origin 都加入 backend CORS 白名单。

当前 Netlify H5 口径：

```text
自定义域名：https://h5.hzhhds.top
Netlify 默认域名：https://cleanscoutrover-management.netlify.app
```

VPS `/etc/vline-backend.env` 应使用：

```text
CORS_ALLOWED_ORIGINS=https://h5.hzhhds.top,https://admin.hzhhds.top,https://cleanscoutrover-management.netlify.app
```

更新后执行：

```bash
sudo systemctl restart vline-backend
```

说明：

- `https://h5.hzhhds.top` 是正式 H5 访问域名
- `https://cleanscoutrover-management.netlify.app` 是 Netlify 默认访问域名
- 如果不加入 Netlify 默认域名，从该域名打开页面时浏览器会因为 CORS 拒绝访问 `https://api.hzhhds.top/api`
- 微信小程序不看这个字段，仍然只看微信后台的 `request 合法域名`
