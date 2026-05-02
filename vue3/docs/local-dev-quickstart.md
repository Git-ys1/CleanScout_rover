# 本地联调快捷启动

## 一条命令启动 backend + H5

在仓库根目录执行：

```powershell
cmd /c npm.cmd run local:edge
```

这条命令会：

1. 生成本地 `public-edge` 临时 env 文件
2. 新开窗口启动 backend
3. 新开窗口启动 H5 前端
4. 在终端打印当前局域网 `edge` 地址

## 启动后访问

```text
H5: http://localhost:5173
backend: http://127.0.0.1:3000
```

树莓派侧 `edge_url` 使用脚本输出的这一行：

```text
ws://<当前本机局域网IP>:3000/edge/ros
```

当前固定设备参数：

```text
edge_device_id=csrpi-001
edge_device_token=ac27b6d55f9446daae792bccbb51df4438da3c88d7f9d74986276da8898e66d2
```

## 关闭本地前后端

```powershell
Get-NetTCPConnection -LocalPort 3000,5173 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess |
  Sort-Object -Unique |
  ForEach-Object { Stop-Process -Id $_ -Force }
```
