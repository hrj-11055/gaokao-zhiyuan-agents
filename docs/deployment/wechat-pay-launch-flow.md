# 微信小程序支付上线流程

更新日期：2026-05-28

## 目标

在 3 天内把“深度填报会员”小程序支付链路推进到可交付上线状态：

- 用户可在小程序内用微信支付 19.9 元解锁会员。
- 用户邀请 5 位新用户完成基础资料后可免费解锁。
- 用户输入后台配置的会员邀请码后可直接解锁会员。
- 大学/专业深度研究在线阅读、综合志愿报告、PDF 下载、家长分享必须由后端会员状态控制。
- 深度报告在线阅读不限次数；PDF 下载继续按深度报告下载额度控制。
- 支付成功后，微信支付回调能可靠解锁会员。

## 当前代码已具备的能力

- 后端已有会员、邀请、支付订单表和接口。
- 后端已有微信登录、JSAPI 下单、支付回调解密、报告生成付费校验。
- 小程序已有会员 API、会员 store、“我的”会员中心、报告页付费锁定态。
- 真实微信小程序、微信支付商户配置和公网 HTTPS 服务已经完成首轮联调；下一步重点是异常场景、邀请码和正式价格复测。

## 当前业务决策和账号状态

截至 2026-05-26：

- 小程序备案已完成。
- 微信支付开发链路已打通，1 元测试支付已真机验证成功。
- 后端订单状态能变为 `paid`，会员状态能自动变为 `active/payment`。
- 商品名确认：`深圳元说咨询`。
- 价格确认：`19.9 元一次性全部解锁`，不再做 `9.9 元只解锁大学`。
- 有效期确认：永久有效。
- 域名方案确认：使用已备案域名 `https://gaokao.aicoming.cn` 指向 47 服务器的 `gaokao-proxy`。
- 剩余重点：将邀请码管理脚本部署到 47 并真机核销、支付异常与回调兜底复测、正式 19.9 元复测。

## 概念澄清

### 小程序认证、备案、微信支付商户号不是同一件事

1. 小程序认证
   - 这是微信公众平台对小程序主体资质的认证。
   - 微信支付文档中，商户号绑定 AppID 时支持“小程序”类型 AppID；商户平台会要求 AppID 账号具备对应资质，主体不一致时还要补充 AppID 主体信息并发起授权确认。

2. 小程序备案
   - 这是小程序上线发布侧的备案要求。
   - 当前已完成。

3. 微信支付商户号
   - 这是收款账户和支付结算主体。
   - 需要单独注册或开通，拿到商户号后再绑定小程序 AppID。

4. 后端 HTTPS 域名
   - 这是小程序请求后端接口和微信支付回调通知使用的公网地址。
   - 当前统一使用 `https://gaokao.aicoming.cn` 指向 47 服务器的 `gaokao-proxy`。

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

填入 `WECHAT_PAY_NOTIFY_URL`。当前项目已使用 `https://gaokao.aicoming.cn/api/payment/wechat/notify` 作为支付回调地址；如果未来迁移服务，仍必须保持公网 HTTPS 回调可访问。

## HTTPS 域名方案判断

### 当前方案：继续使用 47 服务器 + `gaokao.aicoming.cn` HTTPS 域名

这是当前线上路径。`gaokao-proxy` 仍部署在 `47.113.125.147`，由 Nginx 暴露 `https://gaokao.aicoming.cn`，小程序 `VITE_API_BASE` 使用该域名，支付回调地址使用 `https://gaokao.aicoming.cn/api/payment/wechat/notify`。

已完成：

- DNS A 记录指向 `47.113.125.147`。
- HTTPS 证书和 HTTP 到 HTTPS 跳转已配置。
- 小程序 request/downloadFile 合法域名已配置。
- 公共 health、综合报告 HTML/PDF、会员态深度 PDF、分数 API 反代均已离线验收。
- 1 元测试支付已真机验收成功。

仍需完成：

- 支付异常场景和回调边界测试。
- 邀请码管理脚本已完成；还需要部署到 47 并跑真机核销流程。
- 恢复 19.9 元正式价格后复测。

### 当前建议

继续走 `https://gaokao.aicoming.cn`。这条链路已经覆盖小程序合法域名、报告 PDF 下载、会员态深度 PDF、分数 API 反代和 1 元真机支付验收；剩余工作集中在部署邀请码管理脚本并真机核销、支付异常回调兜底和恢复 19.9 元正式价格后的复测。

## 我们当前项目的后端配置模板

服务器 `/opt/gaokao-proxy/.env` 需要补齐：

```bash
COMMERCE_DB_PATH=/opt/gaokao-proxy/data/gaokao-commerce.sqlite
COMMERCE_SESSION_SECRET=请生成一个长随机字符串
MEMBERSHIP_PRICE_CENTS=1990
MEMBERSHIP_INVITE_REQUIRED=5
MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT=10
MEMBERSHIP_VIP_CODES=FENGGE2026

WECHAT_APPID=小程序AppID
WECHAT_SECRET=小程序AppSecret
WECHAT_MCH_ID=商户号
WECHAT_PAY_SERIAL_NO=商户API证书序列号
WECHAT_PAY_PRIVATE_KEY_PATH=/opt/gaokao-proxy/certs/apiclient_key.pem
WECHAT_PAY_PUBLIC_KEY_ID=微信支付公钥ID
WECHAT_PAY_PUBLIC_KEY_PATH=/opt/gaokao-proxy/certs/wechatpay_public_key.pem
WECHAT_PAY_API_V3_KEY=APIv3密钥
WECHAT_PAY_NOTIFY_URL=https://gaokao.aicoming.cn/api/payment/wechat/notify
```

## 3 天上线排期

### Day 1：账号、证书、域名和配置

- [x] 确认小程序 AppID、AppSecret、认证状态。
- [x] 确认或开通微信支付商户号。
- [x] 完成小程序 AppID 与商户号绑定。
- [x] 生成商户 API 证书和 API v3 密钥。
- [x] 准备 HTTPS 域名和回调地址。
- [x] 把证书、私钥、公钥安全上传到服务器。
- [x] 在测试环境 `.env` 配置全部参数。

交付标准：

- [x] 后端能成功调用微信 `jscode2session` 换取 `openid`。
- [x] 后端能成功调用 JSAPI 下单接口拿到 `prepay_id`。

### Day 2：联调支付和会员解锁

- [x] 小程序真机发起会员支付。
- [x] 验证 `uni.requestPayment` 能拉起微信支付。
- [x] 支付成功后验证微信回调到达后端。
- [x] 验证订单状态变为 `paid`。
- [x] 验证会员状态变为 `active`。
- [ ] 验证报告生成接口未登录/未付费返回 401/402。
- [ ] 验证付费后可生成综合报告。
- [ ] 验证付费后可打开深度报告在线阅读页，且不减少 PDF 下载额度。

交付标准：

- [x] 支付成功后 5-10 秒内会员自动解锁。
- [x] 后端订单、会员状态和小程序页面状态一致。

2026-05-26 记录：本轮为 1 元测试支付，后端 `MEMBERSHIP_PRICE_CENTS=100`；正式发布前需要恢复 `1990` 并再跑一次 19.9 元订单。

### Day 3：上线验收和兜底

- [ ] 配置正式环境参数。
- [ ] 小程序体验版全链路验收。
- [ ] 检查错误提示、支付取消、支付失败、重复支付、重复回调。
- [ ] 检查邀请 5 人解锁流程。
- [ ] 检查会员邀请码解锁流程。
- [ ] 检查学校/专业深度 PDF 下载次数耗尽提示。
- [ ] 检查报告生成、PDF 下载、家长分享。
- [ ] 准备上线回滚方案和问题排查清单。

交付标准：

- 体验版通过完整支付、邀请、报告生成验收。
- 后端日志能定位登录、下单、回调、解锁、报告生成问题。
- 可以提交小程序审核或发布。

## 待确认问题

1. 正式 19.9 元复测安排在哪个测试账号上执行？
2. 邀请码需要面向哪些渠道发放：内部测试、种子用户、合作老师、售后补偿？
3. 邀请码是否需要一次性码、多人码、过期时间和备注字段？
4. 支付异常日志是否需要接入外部告警，还是先用 PM2/Nginx 日志排查？

## 已确认问题

1. 商品名：`深圳元说咨询`。
2. 价格：`19.9 元一次性全部解锁`。
3. 有效期：永久有效。
4. 暂不做 `9.9 元只解锁大学`。
5. 域名方案：使用 `https://gaokao.aicoming.cn` 指向 47 服务器。
6. 小程序备案：已完成。
7. 微信支付开发：1 元测试支付已打通。

## 参考文档

- 微信支付 API v3 JSAPI 下单：`https://pay.weixin.qq.com/wiki/doc/apiv3/open/pay/chapter2_8_3.shtml`
- 微信支付 API v3 服务商 JSAPI 下单参数说明：`https://pay.weixin.qq.com/wiki/doc/apiv3_partner/open/pay/chapter2_4.shtml`
- 微信支付商户号绑定 AppID：`https://pay.wechatpay.cn/doc/v3/merchant/4013287010`
