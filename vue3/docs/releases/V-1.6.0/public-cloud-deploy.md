# V-1.6.0 public-cloud 部署交付包

## 部署结论

本轮只做仓库交付，不实际登录服务器部署。

推荐公网部署路径：

- ECS / VPS：优先非中国内地节点；若使用中国内地服务器，按服务商要求处理 ICP 备案
- OS：`Ubuntu 22.04`
- Node：优先 `24 LTS`，保守可用 `22 LTS`
- 反向代理：`Nginx`
- TLS：`Certbot / Let's Encrypt`
- backend：`systemd` 托管，监听 `127.0.0.1:3000`

## 域名冻结

API 域名：

```text
https://api.hzhhds.top
```

前端生产 API：

```text
https://api.hzhhds.top/api
```

未来预留：

- H5：`https://h5.hzhhds.top`
- 管理后台：`https://admin.hzhhds.top`

## Nginx 配置

示例文件：

```text
deploy/nginx/api.hzhhds.top.conf
```

核心规则：

- `80` 端口只用于 ACME challenge 和跳转 HTTPS
- `443` 端口反代到 `http://127.0.0.1:3000`
- 不让 Node backend 直接暴露公网端口

安装示例：

```bash
sudo install -m 644 deploy/nginx/api.hzhhds.top.conf /etc/nginx/sites-available/api.hzhhds.top.conf
sudo ln -s /etc/nginx/sites-available/api.hzhhds.top.conf /etc/nginx/sites-enabled/api.hzhhds.top.conf
sudo nginx -t
sudo systemctl reload nginx
```

## Certbot

证书申请示例：

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
sudo certbot --nginx -d api.hzhhds.top
```

## backend env

公网环境文件仍落在：

```text
/etc/vline-backend.env
```

内容应按以下模板生成：

```text
deploy/env/vline-backend.public.env.example
```

关键值：

```text
APP_PROFILE=public-cloud
CORS_ALLOWED_ORIGINS=https://h5.hzhhds.top,https://admin.hzhhds.top
ROS_TRANSPORT=mock
ROSBRIDGE_URL=ws://127.0.0.1:9090
```

公网版这轮不直连局域网树莓派。

## 微信小程序后台

微信小程序正式发布时配置的是：

```text
request 合法域名：https://api.hzhhds.top
```

注意：

- 不填 IP
- 不填 localhost
- 配置后台域名时不写端口
- 这不是 `CORS_ALLOWED_ORIGINS`

`CORS_ALLOWED_ORIGINS` 只影响浏览器 H5 / admin web 的 Origin 校验。
