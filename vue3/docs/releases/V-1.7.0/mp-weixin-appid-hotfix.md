# V-1.7.12 微信小程序 AppID 构建热修

## 问题结论

本地 `build:mp-weixin:production` 可以成功完成，但生成的：

```text
dist/build/mp-weixin/project.config.json
```

此前仍然是：

```json
{
  "appid": "touristappid"
}
```

原因是 `src/manifest.json` 中 `mp-weixin.appid` 为空。uni-app CLI 在 appid 为空时会生成游客 appid，这会导致微信开发者工具在导入、预览、上传或使用正式小程序能力时出现不稳定的工具侧错误。

本次微信工具报：

```text
系统错误，错误码：1
appid: wxce1a2e91132f4c41
```

该错误本身过于泛化，但当前工程侧已确认存在 appid 不一致风险，因此本轮优先修复 AppID 构建产物。

## 修复内容

已将 `src/manifest.json` 的 `mp-weixin.appid` 固定为：

```text
wxce1a2e91132f4c41
```

并在构建脚本中加入产物校验：

- `scripts/release-mp-weixin.ps1`
- `scripts/release-mp-weixin.sh`

如果生成的 `project.config.json.appid` 不是 `wxce1a2e91132f4c41`，脚本会直接失败，避免继续导入错误产物。

## 验证结果

已执行：

```powershell
cmd /c npm.cmd run build:mp-weixin:production
powershell -ExecutionPolicy Bypass -File .\scripts\release-mp-weixin.ps1
```

产物已确认：

```text
dist/build/mp-weixin/project.config.json
appid=wxce1a2e91132f4c41
```

API 地址仍为：

```text
https://api.hzhhds.top/api
```

## 重新导入方式

微信开发者工具中应导入：

```text
dist/build/mp-weixin
```

不要导入仓库根目录，也不要导入 `src/`。

## 后续若仍报错

如果 AppID 修复后微信开发者工具仍报 `系统错误，错误码：1`，下一步需要检查：

- 微信开发者工具是否登录了该小程序管理员 / 开发者账号
- 小程序后台 `request 合法域名` 是否包含 `https://api.hzhhds.top`
- 是否导入了最新 `dist/build/mp-weixin`
- 是否需要清理微信开发者工具项目缓存后重新导入
