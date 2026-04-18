# V-1.4.0 backend 部署硬化

## 当前 backend stack

当前 `vue3/backend` 技术栈冻结为：

- `Express 5.2.1`
- `Prisma 6.19.3`
- `SQLite`
- `bcrypt`
- `jsonwebtoken`
- `ws`

## 当前阶段部署结论

本轮只冻结单机 VPS / Linux + systemd 部署路径，不做容器化，不引入额外编排层。

新增文件：

- `deploy/systemd/vline-backend.service`
- `scripts/deploy-backend.sh`
- `scripts/update-backend.sh`

## CORS 白名单规则

当前 backend 已从 localhost-only 改为环境变量白名单：

```text
CORS_ALLOWED_ORIGINS=https://vline.example.com,https://admin.example.com
```

规则：

- `Origin` 为空时继续放行，兼容 `curl`、反向代理健康检查和无源请求
- `Origin` 有值时，只允许命中 `CORS_ALLOWED_ORIGINS`
- 若该变量为空，则默认仅放行本地开发 `localhost / 127.0.0.1`
- 公网部署前必须改成真实 H5 域名，不得继续沿用本地默认值

## SQLite 约束

当前 `SQLite` 只适合单机 / 小流量阶段。

生产部署时，`DATABASE_URL` 必须指向 repo 工作树外部路径，例如：

```text
DATABASE_URL="file:/var/lib/vline-backend/dev.db"
```

不要把生产数据库文件继续绑在仓库工作树里。

## systemd 服务默认值

当前默认值冻结为：

- `User=vline`
- `WorkingDirectory=/opt/vline-backend/backend`
- `EnvironmentFile=/etc/vline-backend.env`
- `ExecStart=/usr/bin/env node src/app.js`
- `Restart=always`

如果部署时需要改目录或用户，使用 `scripts/deploy-backend.sh` 的环境变量覆盖；脚本会在安装 service 时渲染对应值。

## 部署顺序

首次部署：

1. 在服务器放置当前 `vue3/` 仓库内容
2. 创建环境文件 `/etc/vline-backend.env`
3. 设置 `DATABASE_URL` 指向 repo 工作树外部路径
4. 执行：

```bash
./scripts/deploy-backend.sh
```

该脚本会：

- 准备 `/opt/vline-backend` 与 `/var/lib/vline-backend`
- 同步 `backend/`
- 执行 `npm ci`
- 执行 `npx prisma generate`
- 执行 `npx prisma migrate deploy`
- 安装并启用 `vline-backend.service`

后续更新：

```bash
./scripts/update-backend.sh
```

该脚本会：

- 同步最新 `backend/`
- 执行 `npm ci`
- 执行 `npx prisma generate`
- 执行 `npx prisma migrate deploy`
- 重启 `vline-backend`

## 当前限制

本轮仍未做：

- 多实例部署
- PostgreSQL 迁移
- 容器化部署
- 反向代理与 TLS 终止细节

这些内容后续按正式上线轮单独立项。
