# 微信小程序支付上线流程

更新日期：2026-05-17

## 目标

在 3 天内把“深度填报会员”小程序支付链路推进到可交付上线状态：

- 用户可在小程序内用微信支付 29 元解锁会员。
- 用户邀请 3 位新用户完成基础资料后可免费解锁。
- 大学深度研究、综合志愿报告、PDF 下载、家长分享必须由后端会员状态控制。
- 支付成功后，微信支付回调能可靠解锁会员。

## 当前代码已具备的能力

- 后端已有会员、邀请、支付订单表和接口。
- 后端已有微信登录、JSAPI 下单、支付回调解密、报告生成付费校验。
- 小程序已有会员 API、会员 store、“我的”会员中心、报告页付费锁定态。
- 需要补齐真实微信小程序和微信支付商户配置，再部署到公网服务。

## 当前业务决策和账号状态

截至 2026-05-17：

- 小程序基本信息已填写，正在进行小程序备案。
- 微信支付商户号尚未注册。
- 小程序 AppID 和微信支付商户号尚未绑定。
- 商品名确认：`深圳元说咨询`。
- 价格确认：`29 元一次性全部解锁`，不再做 `9.9 元只解锁大学`。
- 有效期确认：永久有效。
- 域名方案确认：使用微信云托管提供的 HTTPS 域名，不再优先走阿里云域名备案路径。

## 概念澄清

### 小程序认证、备案、微信支付商户号不是同一件事

1. 小程序认证
   - 这是微信公众平台对小程序主体资质的认证。
   - 微信支付文档中，商户号绑定 AppID 时支持“小程序”类型 AppID；商户平台会要求 AppID 账号具备对应资质，主体不一致时还要补充 AppID 主体信息并发起授权确认。

2. 小程序备案
   - 这是小程序上线发布侧的备案要求。
   - 你现在正在做的是这一项。

3. 微信支付商户号
   - 这是收款账户和支付结算主体。
   - 需要单独注册或开通，拿到商户号后再绑定小程序 AppID。

4. 后端 HTTPS 域名
   - 这是小程序请求后端接口和微信支付回调通知使用的公网地址。
   - 如果继续使用当前 `gaokao-proxy` 后端，需要一个 HTTPS 域名指向后端服务。
   - 如果完全改用微信云开发/云托管，则可以使用微信云提供的 HTTPS 域名，但后端部署形态要相应调整。

## 需要准备的微信支付参数

| 参数 | 用途 | 从哪里获取 | 放到哪里 |
| --- | --- | --- | --- |
| `WECHAT_APPID` | 小程序 AppID，用于微信登录和 JSAPI 支付 | 微信公众平台 -> 小程序后台 -> 开发管理 -> 开发设置 | 后端 `.env` |
| `WECHAT_SECRET` | 小程序 AppSecret，用于后端 `jscode2session` 换取 `openid` | 微信公众平台 -> 小程序后台 -> 开发管理 -> 开发设置 | 后端 `.env` |
| `WECHAT_MCH_ID` | 微信支付商户号 | 微信支付商户平台 -> 账户中心 -> 商户信息 | 后端 `.env` |
| `WECHAT_PAY_SERIAL_NO` | 商户 API 证书序列号，用于请求签名 | 微信支付商户平台 -> 账户中心 -> API 安全 -> API 证书 | 后端 `.env` |
| `WECHAT_PAY_PRIVATE_KEY_PATH` | 商户 API 私钥文件路径，用于后端签名下单和前端支付参数签名 | API 证书生成后本地保存的 `apiclient_key.pem` | 服务器文件路径 |
| `WECHAT_PAY_API_V3_KEY` | API v3 密钥，用于解密微信支付回调 `resource` | 微信支付商户平台 -> 账户中心 -> API 安全 -> APIv3 密钥 | 后端 `.env` |
| `WECHAT_PAY_PUBLIC_KEY_ID` | 微信支付公钥 ID，用于响应/回调验签 | 微信支付商户平台 -> 账户中心 -> API 安全 -> 微信支付公钥 | 后端 `.env` |
| `WECHAT_PAY_PUBLIC_KEY_PATH` | 微信支付公钥文件路径，用于支付回调验签 | 微信支付商户平台下载或复制公钥后保存到服务器 | 服务器文件路径 |
| `WECHAT_PAY_NOTIFY_URL` | 支付成功回调地址 | 自己配置，必须是 HTTPS 公网地址 | 后端 `.env` |
| `COMMERCE_SESSION_SECRET` | 小程序会员登录态签名密钥 | 自己生成 32 位以上随机字符串 | 后端 `.env` |
| `COMMERCE_DB_PATH` | 会员/支付 SQLite 数据库路径 | 自己配置 | 后端 `.env` |

## 微信支付参数获取步骤

### 1. 确认小程序主体与商户主体

先确认小程序是否已经完成认证，并且主体是否能开通微信支付。理想情况是小程序主体和商户主体一致；如果不一致，需要在微信支付商户平台完成 AppID 绑定授权。

需要确认：

- 小程序 AppID 是哪个。
- 小程序是否已认证。
- 是否已经有微信支付商户号。
- 商户号和小程序 AppID 是否已绑定。

### 2. 获取小程序 AppID 和 AppSecret

进入微信公众平台的小程序后台：

- 复制 AppID，填入 `WECHAT_APPID`。
- 生成或查看 AppSecret，填入 `WECHAT_SECRET`。

注意：AppSecret 只给后端使用，不能放进小程序前端代码。

### 3. 开通或确认微信支付商户号

进入微信支付商户平台：

- 找到商户号，填入 `WECHAT_MCH_ID`。
- 确认产品权限里已开通 JSAPI 支付。
- 确认小程序 AppID 已关联到该商户号。

### 4. 生成商户 API 证书和私钥

在微信支付商户平台的 API 安全区域生成 API 证书。生成后会得到商户证书和商户私钥，后端主要需要：

- 商户证书序列号：填入 `WECHAT_PAY_SERIAL_NO`。
- 商户私钥文件 `apiclient_key.pem`：上传到服务器安全目录，并把路径填入 `WECHAT_PAY_PRIVATE_KEY_PATH`。

私钥文件不要提交到 Git，不要发给第三方。

### 5. 设置 API v3 密钥

在微信支付商户平台设置 API v3 密钥，填入 `WECHAT_PAY_API_V3_KEY`。

这个密钥用于解密支付成功回调里的加密资源。密钥必须是 32 字节字符串。

### 6. 准备微信支付公钥

在微信支付商户平台获取微信支付公钥或平台证书信息：

- 公钥 ID 填入 `WECHAT_PAY_PUBLIC_KEY_ID`。
- 公钥内容保存成服务器文件，路径填入 `WECHAT_PAY_PUBLIC_KEY_PATH`。

配置后，后端会对微信支付回调做签名校验。

### 7. 配置 HTTPS 回调地址

回调地址必须是公网可访问的 HTTPS 地址，例如：

```text
https://api.example.com/api/payment/wechat/notify
```

填入 `WECHAT_PAY_NOTIFY_URL`。如果当前只有 IP HTTP 服务，需要先准备域名和 HTTPS 证书，否则微信支付正式回调无法稳定上线。

## HTTPS 域名方案判断

### 方案 A：使用微信云托管 HTTPS 域名（当前选定）

适合当前 3 天上线目标。当前项目已经有 `gaokao-proxy` Express 后端，报告生成、会员、支付订单都在这个服务里。改为微信云托管后，后端仍然保留 Express 形态，但部署到云托管容器，由云托管提供公网 HTTPS 访问地址。

需要做：

- 开通微信云开发/云托管环境。
- 创建云托管服务，例如 `gaokao-proxy`。
- 将当前 `gaokao-proxy` 后端以 Node/Express 服务部署到云托管。
- 配置云托管环境变量，包括 Dify/DeepSeek、报告路径、会员支付、微信支付参数。
- 获取云托管提供的 HTTPS 访问地址。
- 支付回调地址设置为：`https://云托管域名/api/payment/wechat/notify`。
- 小程序调用方式二选一：
  - 短期最小改动：继续使用 `uni.request`，把 `VITE_API_BASE` 改成云托管 HTTPS 地址。
  - 云托管原生方式：改造 API 层为 `wx.cloud.callContainer`，通过 `X-WX-SERVICE` 调用云托管服务。

风险：

- 云托管容器文件系统和本地服务器不同，SQLite 数据库和报告 HTML/PDF 输出要确认是否可持久化。
- 当前报告生成依赖本地数据目录，部署前要确认数据文件是否随容器一起打包，或者迁到云存储/数据库。
- 微信支付回调必须使用公网 HTTPS URL，不能只依赖小程序端 `callContainer`。

### 方案 B：继续使用现有服务器，配置阿里云域名

这是备选方案。需要一个已备案域名、HTTPS 证书、DNS、Nginx。`aicoming.com.cn` 当前第三方查询结果显示未备案，所以暂不作为 3 天上线主方案。

需要做：

- 找到已备案域名，或完成新域名 ICP 备案。
- 配置子域名、HTTPS 证书、Nginx 反代。
- 小程序后台配置 request 合法域名。
- 后端 `.env` 设置：
  - `REPORT_BASE_URL=https://api.example.com`
  - `WECHAT_PAY_NOTIFY_URL=https://api.example.com/api/payment/wechat/notify`
  - 小程序 `VITE_API_BASE=https://api.example.com`

风险：

- 新域名备案通常不适合 3 天排期。
- 需要额外维护服务器 HTTPS、证书续期和 Nginx。

### 当前建议

为了 3 天内交付上线，优先走方案 A：微信云托管 HTTPS 域名。

实施策略：

- Day 1 先部署一个最小云托管版 `gaokao-proxy`，确认 `/api/health`、`/api/auth/wechat-login`、`/api/payment/create` 可访问。
- 如果 SQLite 或报告输出在云托管持久化上出现风险，短期改为云数据库/云存储，或者临时保留现有服务器作为报告生成服务，由云托管做支付与会员网关。
- 支付回调统一使用云托管 HTTPS 地址。

## 我们当前项目的后端配置模板

服务器 `/opt/gaokao-proxy/.env` 需要补齐：

```bash
COMMERCE_DB_PATH=/opt/gaokao-proxy/data/gaokao-commerce.sqlite
COMMERCE_SESSION_SECRET=请生成一个长随机字符串
MEMBERSHIP_PRICE_CENTS=2900
MEMBERSHIP_INVITE_REQUIRED=3

WECHAT_APPID=小程序AppID
WECHAT_SECRET=小程序AppSecret
WECHAT_MCH_ID=商户号
WECHAT_PAY_SERIAL_NO=商户API证书序列号
WECHAT_PAY_PRIVATE_KEY_PATH=/opt/gaokao-proxy/certs/apiclient_key.pem
WECHAT_PAY_PUBLIC_KEY_ID=微信支付公钥ID
WECHAT_PAY_PUBLIC_KEY_PATH=/opt/gaokao-proxy/certs/wechatpay_public_key.pem
WECHAT_PAY_API_V3_KEY=APIv3密钥
WECHAT_PAY_NOTIFY_URL=https://云托管域名/api/payment/wechat/notify
```

## 3 天上线排期

### Day 1：账号、证书、域名和配置

- 确认小程序 AppID、AppSecret、认证状态。
- 确认或开通微信支付商户号。
- 完成小程序 AppID 与商户号绑定。
- 生成商户 API 证书和 API v3 密钥。
- 准备 HTTPS 域名和回调地址。
- 把证书、私钥、公钥安全上传到服务器。
- 在测试环境 `.env` 配置全部参数。

交付标准：

- 后端能成功调用微信 `jscode2session` 换取 `openid`。
- 后端能成功调用 JSAPI 下单接口拿到 `prepay_id`。

### Day 2：联调支付和会员解锁

- 小程序真机发起会员支付。
- 验证 `uni.requestPayment` 能拉起微信支付。
- 支付成功后验证微信回调到达后端。
- 验证订单状态变为 `paid`。
- 验证会员状态变为 `active`。
- 验证报告生成接口未登录/未付费返回 401/402。
- 验证付费后可生成综合报告。

交付标准：

- 支付成功后 5-10 秒内会员自动解锁。
- 后端订单、会员状态和小程序页面状态一致。

### Day 3：上线验收和兜底

- 配置正式环境参数。
- 小程序体验版全链路验收。
- 检查错误提示、支付取消、支付失败、重复支付、重复回调。
- 检查邀请 3 人解锁流程。
- 检查报告生成、PDF 下载、家长分享。
- 准备上线回滚方案和问题排查清单。

交付标准：

- 体验版通过完整支付、邀请、报告生成验收。
- 后端日志能定位登录、下单、回调、解锁、报告生成问题。
- 可以提交小程序审核或发布。

## 待确认问题

1. 小程序是否已经通过微信认证，还是目前只有小程序备案在进行中？
2. 微信支付商户号准备以哪个主体注册：公司、个体工商户，还是其他主体？
3. 小程序主体和未来商户号主体是否一致？
4. `ai.com.cn` 是否已经完成 ICP 备案？是否确定这个域名拼写就是 `ai.com.cn`？
5. 微信云托管环境 ID 是什么？
6. 云托管服务名是否确定为 `gaokao-proxy`？
7. 是否先走最小改动 `uni.request + 云托管 HTTPS 域名`，还是直接改成 `wx.cloud.callContainer`？
8. 是否需要开发测试期启用 `WECHAT_LOGIN_MOCK=1`，等商户号和证书齐全后再切真实微信登录？

## 已确认问题

1. 商品名：`深圳元说咨询`。
2. 价格：`29 元一次性全部解锁`。
3. 有效期：永久有效。
4. 暂不做 `9.9 元只解锁大学`。
5. 域名方案：使用微信云托管提供的 HTTPS 域名。

## 参考文档

- 微信支付 API v3 JSAPI 下单：`https://pay.weixin.qq.com/wiki/doc/apiv3/open/pay/chapter2_8_3.shtml`
- 微信支付 API v3 服务商 JSAPI 下单参数说明：`https://pay.weixin.qq.com/wiki/doc/apiv3_partner/open/pay/chapter2_4.shtml`
- 微信支付商户号绑定 AppID：`https://pay.wechatpay.cn/doc/v3/merchant/4013287010`
