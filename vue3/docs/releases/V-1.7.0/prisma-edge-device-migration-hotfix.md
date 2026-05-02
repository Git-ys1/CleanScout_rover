# V-1.7.11 Prisma EdgeDevice migration 热修

## 问题结论

云端 seed 报错：

```text
The table main.EdgeDevice does not exist in the current database.
```

判断正确：这不是 `/etc/vline-backend.env` 写错，也不是 token 问题。

根因是：

- `schema.prisma` 已新增 `EdgeDevice`
- `seed.js` 已开始读写 `prisma.edgeDevice`
- 但仓库 migration 目录此前没有创建 `EdgeDevice` 表的 migration
- 因此 `npx prisma migrate deploy` 会显示没有待执行 migration，随后 `npx prisma db seed` 在 `EdgeDevice` 表不存在时失败

## 正式修复

V-1.7.11 已新增 migration：

```text
backend/prisma/migrations/20260419073000_add_edge_device/migration.sql
```

该 migration 创建：

- `EdgeDevice`
- `EdgeDevice_deviceId_key`

## 云端修复步骤

在云端拉取包含 V-1.7.11 的最新 `main` 后，执行：

```bash
cd /opt/vline-backend/backend

set -a
source /etc/vline-backend.env
set +a

npx prisma generate
npx prisma migrate deploy
npx prisma db seed
sudo systemctl restart vline-backend
sudo systemctl status vline-backend --no-pager
```

预期结果：

- `migrate deploy` 会应用 `20260419073000_add_edge_device`
- `db seed` 会创建或确认 `csrpi-001`
- `EdgeDevice.tokenHash` 存 bcrypt hash，不存明文 token

## 临时应急方案

如果云端暂时无法拉取最新代码，但必须马上抢通，可以临时执行：

```bash
cd /opt/vline-backend/backend
set -a
source /etc/vline-backend.env
set +a
npx prisma db push
npx prisma db seed
```

但这只能作为应急方案，不作为 V 线正式发布纪律。

正式部署仍然必须回到：

```bash
npx prisma migrate deploy
```

## 备注

`package.json#prisma is deprecated` 只是 Prisma 7 前的配置迁移提醒，不是本次失败原因。
