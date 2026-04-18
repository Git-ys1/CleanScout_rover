# V-1.4.0 微信小程序构建脚本冻结

## 当前结论

当前 `vue3/package.json` 已存在 `build:mp-weixin` 脚本，后续不再发明新的微信小程序打包命令。本轮只补可重复执行的本地包装脚本：

- `scripts/release-mp-weixin.ps1`
- `scripts/release-mp-weixin.sh`

两个脚本都固定调用：

```powershell
npm run build:mp-weixin
```

## 本地命令

Windows PowerShell：

```powershell
.\scripts\release-mp-weixin.ps1
```

Linux / macOS / Git Bash：

```bash
./scripts/release-mp-weixin.sh
```

## 产物目录

构建完成后，uni-app CLI 默认产物目录固定为：

```text
dist/build/mp-weixin
```

脚本执行成功后会在终端显式打印这个目录。

## 微信开发者工具导入流程

1. 执行微信小程序构建脚本。
2. 打开微信开发者工具。
3. 选择“导入项目”。
4. 将项目目录指向 `dist/build/mp-weixin`。
5. 填入当前小程序 `AppID` 或使用测试号继续本地调试。

## App Plus 占位说明

本轮同时冻结：

- `scripts/release-app-plus.ps1`

它是明确的占位脚本，不会伪装成已经可构建。当前规则是：

- 后续再补 `build:app-plus`
- CLI 只负责生成 App 资源 / `wgt`
- 真正的 `APK/IPA` 云打包仍走 Windows 侧 `HBuilderX`
