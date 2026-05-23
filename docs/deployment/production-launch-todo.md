# 生产上线待办：HTTPS 域名、小程序备案与微信支付

更新日期：2026-05-23

## 当前结论

- 当前小程序 API 地址仍是 `http://47.113.125.147`。
- 47 服务器上的 `gaokao-proxy` 已具备报告 PDF、深度报告 PDF、会员与支付接口代码。
- PDF 下载失败的核心阻塞不是后端没有 PDF 功能，而是小程序真机下载需要 HTTPS 合法域名，不能长期使用 HTTP IP。
- 建议新增专用后端域名：`gaokao.aicoming.com.cn`，指向 `47.113.125.147`。

## 一、域名与 HTTPS 待办

### 1. 确认主域名 ICP 备案状态

- [ ] 确认 `aicoming.com.cn` 是否已完成 ICP 备案。
- [ ] 如果未备案，在服务器接入商处完成备案或接入备案。
- [ ] 如果已备案，继续使用子域名 `gaokao.aicoming.com.cn`。

说明：

- 微信小程序请求和下载必须走 HTTPS 合法域名。
- 子域名通常复用主域名备案，但仍要确认域名服务商和服务器接入商是否放行。

### 2. 配置 DNS 解析

在域名 DNS 控制台添加：

```text
记录类型：A
主机记录：gaokao
记录值：47.113.125.147
TTL：默认
```

验证：

```bash
curl -I http://gaokao.aicoming.com.cn/api/health
```

期望：

```text
HTTP/1.1 200 OK
Server: nginx
```

### 3. 在 47 服务器申请 HTTPS 证书

登录服务器：

```bash
ssh -i /Users/MarkHuang/Downloads/mark123-.pem root@47.113.125.147
```

申请证书：

```bash
certbot --nginx -d gaokao.aicoming.com.cn
```

选择自动将 HTTP 跳转到 HTTPS。

验证：

```bash
curl -I https://gaokao.aicoming.com.cn/api/health
curl -I https://gaokao.aicoming.com.cn/reports/u_1779266091610_u1ynfoti-1779266155844.pdf
```

期望 PDF 响应：

```text
HTTP/1.1 200 OK
Content-Type: application/pdf
```

### 4. 更新服务器环境变量

47 服务器 `/opt/gaokao-proxy/.env`：

```bash
REPORT_BASE_URL=https://gaokao.aicoming.com.cn
WECHAT_PAY_NOTIFY_URL=https://gaokao.aicoming.com.cn/api/payment/wechat/notify
```

改完后重启：

```bash
pm2 restart gaokao-proxy --update-env
```

### 5. 更新小程序 API 地址

`gaokao-miniprogram/.env`：

```bash
VITE_API_BASE=https://gaokao.aicoming.com.cn
```

构建：

```bash
cd gaokao-miniprogram
npm run build:mp-weixin
```

## 二、微信小程序后台配置待办

进入微信公众平台：

```text
小程序后台 -> 开发管理 -> 开发设置 -> 服务器域名
```

添加：

```text
request 合法域名：
https://gaokao.aicoming.com.cn

downloadFile 合法域名：
https://gaokao.aicoming.com.cn
```

如果后续使用 `web-view` 打开报告 HTML，再进入：

```text
小程序后台 -> 开发管理 -> 开发设置 -> 业务域名
```

添加：

```text
https://gaokao.aicoming.com.cn
```

业务域名通常需要下载微信给出的校验文件，并放到服务器站点根目录。等后台生成文件后，再上传到 47 服务器验证。

## 三、小程序备案待办

进入微信公众平台：

```text
小程序后台 -> 设置 -> 小程序备案
```

待办：

- [ ] 确认主体类型：个人或企业。
- [ ] 填写主体证件信息。
- [ ] 填写负责人身份信息和手机号。
- [ ] 填写小程序名称、简介、服务类目。
- [ ] 等待备案审核通过。

注意：

- 小程序备案和域名 ICP 备案不是同一件事。
- 小程序备案影响正式发布审核。
- 域名 ICP 备案影响后端域名能否在中国大陆服务器上正常访问和被微信配置。

## 四、微信支付打通待办

### 1. 账号与主体

- [ ] 确认小程序 AppID：`wx52fc7943bf6e76aa`。
- [ ] 确认小程序是否已认证。
- [ ] 开通或确认微信支付商户号。
- [ ] 绑定小程序 AppID 与微信支付商户号。
- [ ] 确认商户产品权限已开通 JSAPI 支付。

### 2. 获取支付参数

需要放入 47 服务器 `/opt/gaokao-proxy/.env`：

```bash
WECHAT_APPID=小程序AppID
WECHAT_SECRET=小程序AppSecret
WECHAT_MCH_ID=商户号
WECHAT_PAY_SERIAL_NO=商户API证书序列号
WECHAT_PAY_PRIVATE_KEY_PATH=/opt/gaokao-proxy/certs/apiclient_key.pem
WECHAT_PAY_PUBLIC_KEY_ID=微信支付公钥ID
WECHAT_PAY_PUBLIC_KEY_PATH=/opt/gaokao-proxy/certs/wechatpay_public_key.pem
WECHAT_PAY_API_V3_KEY=32字节APIv3密钥
WECHAT_PAY_NOTIFY_URL=https://gaokao.aicoming.com.cn/api/payment/wechat/notify
COMMERCE_SESSION_SECRET=32位以上随机字符串
COMMERCE_DB_PATH=/opt/gaokao-proxy/data/gaokao-commerce.sqlite
MEMBERSHIP_PRICE_CENTS=2900
MEMBERSHIP_INVITE_REQUIRED=3
```

证书和密钥文件不要提交到 Git。

### 3. 服务器证书目录

建议：

```bash
mkdir -p /opt/gaokao-proxy/certs
chmod 700 /opt/gaokao-proxy/certs
```

上传：

```text
/opt/gaokao-proxy/certs/apiclient_key.pem
/opt/gaokao-proxy/certs/wechatpay_public_key.pem
```

### 4. 支付接口联调

- [ ] 小程序微信登录成功，后端能拿到 `openid`。
- [ ] `POST /api/payment/create` 能创建 29 元会员订单。
- [ ] 小程序能拉起 `wx.requestPayment`。
- [ ] 支付成功后微信回调 `POST /api/payment/wechat/notify` 能到达 47 服务器。
- [ ] 后端能验签、解密、更新订单状态。
- [ ] 会员状态变为 `active`。
- [ ] PDF 下载和综合报告生成通过会员校验。

### 5. 异常场景

- [ ] 用户取消支付：不解锁，提示支付已取消。
- [ ] 支付成功但回调延迟：前端显示确认中，后端可查单补偿。
- [ ] 回调验签失败：记录日志，不解锁。
- [ ] 重复回调：保持幂等，不重复写订单。
- [ ] 会员已开通：再次点击支付直接提示已解锁。

## 五、上线验收清单

- [ ] `https://gaokao.aicoming.com.cn/api/health` 返回 `200`。
- [ ] `https://gaokao.aicoming.com.cn/reports/*.pdf` 返回 `application/pdf`。
- [ ] 小程序后台已配置 request 合法域名。
- [ ] 小程序后台已配置 downloadFile 合法域名。
- [ ] 小程序体验版使用 `https://gaokao.aicoming.com.cn`。
- [ ] 综合报告 PDF 下载成功。
- [ ] 学校/专业深度 PDF 下载成功。
- [ ] 微信支付 29 元下单成功。
- [ ] 支付回调后会员自动解锁。
- [ ] 小程序备案通过或明确处于审核流程中。
