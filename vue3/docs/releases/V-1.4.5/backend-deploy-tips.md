# V-1.4.5 backend 部署 tips

## 当前问题

当前部署卡点不是 backend 代码报错，而是对 `CORS_ALLOWED_ORIGINS` 的理解发生了混淆：

- 误以为它应该填“小程序地址”
- 误以为它应该填“backend 自己的网站地址”

这两个理解都不对。

## 正确结论

`CORS_ALLOWED_ORIGINS` 管的是：

- 浏览器页面所在的前端网页 Origin

它不管：

- 微信小程序的项目目录
- 微信小程序后台里的 `request 合法域名`
- backend API 自己的域名本身

也就是说，只有“浏览器里的 H5 页面 / admin web 页面”直接请求 backend API 时，`CORS_ALLOWED_ORIGINS` 才需要填写这些网页的 Origin。

## 当前项目的推荐默认值

如果当前线上只有：

- 微信小程序

且暂时没有：

- 浏览器 H5 页面
- 公网 admin web 页面

那么当前推荐部署口径是：

```text
CORS_ALLOWED_ORIGINS=
```

也就是先留空。

原因：

- 当前 backend 代码对“无 Origin”的请求仍然放行
- 微信小程序访问 backend 的核心约束不是浏览器 CORS，而是微信公众平台里的 `request 合法域名`
- 因此，小程序上线时，真正要配的是微信后台的 HTTPS 域名，而不是先在 backend 里乱填 CORS 白名单

## 小程序上线时真正要配置的东西

当前如果走微信小程序线上请求 backend，必须确认的是：

1. backend 已有公网可访问的 `HTTPS` 域名  
   例如：`https://api.example.com`
2. 微信小程序后台已把这个域名加入：
   - `request 合法域名`
3. backend 反向代理和 TLS 证书已正常

这一条和 `CORS_ALLOWED_ORIGINS` 是两套不同的约束。

## 什么时候才需要填写 CORS_ALLOWED_ORIGINS

只有当后续出现下面任一情况时，才需要明确写：

- 上线 `H5` 页面
- 上线浏览器版管理后台
- 上线浏览器调试页，并且这些网页直接请求 backend API

示例：

如果未来上线：

- `https://admin.example.com`
- `https://h5.example.com`

那么 backend 才应该配置：

```text
CORS_ALLOWED_ORIGINS=https://admin.example.com,https://h5.example.com
```

注意：

- 这里填的是“网页所在域名”
- 不是 backend API 的域名
- 也不是微信小程序自身

## 当前建议给部署人员的直接口径

如果你现在只是把 backend 提供给已上线的小程序使用，那么：

```text
CORS_ALLOWED_ORIGINS=
```

先留空即可。

与此同时，要把真正的 backend HTTPS 域名配置到微信小程序后台的 `request 合法域名` 里。

## 项目负责人需要拍板的事项

这部分必须由项目负责人明确方向，避免部署侧继续猜：

1. 近期是否会上浏览器 `H5` 页面
2. 近期是否会上浏览器版 `admin web`
3. 如果会上，这些页面的正式 Origin 是什么
4. backend 是否长期只服务于小程序，还是要同时服务 H5 / admin web

## 当前建议

当前建议给项目负责人的默认方案是：

- 第一阶段：backend 先服务微信小程序
- `CORS_ALLOWED_ORIGINS` 暂时留空
- 由项目负责人后续确认是否追加 `H5 / admin web` 入口
- 一旦确认浏览器前端域名，再补精确白名单，不提前猜测

## 一句话总结

当前如果只有小程序，没有浏览器 H5，就不要把 `CORS_ALLOWED_ORIGINS` 误填成 backend 域名；先留空，真正要去配的是微信小程序后台的 `request 合法域名`。
