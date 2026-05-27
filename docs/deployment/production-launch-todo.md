# 生产上线待办：HTTPS 域名、小程序备案与微信支付

更新日期：2026-05-28

## 当前结论

- 当前小程序 API 地址已切换为 `https://gaokao.aicoming.cn`。
- 47 服务器上的 `gaokao-proxy` 已具备报告 PDF、深度报告 PDF、会员与支付接口代码。
- 2026-05-24 已为 `gaokao.aicoming.cn` 配置 DNS、Nginx、HTTPS 证书和微信小程序服务器域名。
- 2026-05-25 已复测：公开综合报告 PDF 返回 `application/pdf`；会员 token 下学校/专业深度 PDF 返回 `application/pdf`；分数线 API live 脚本 7/7 通过；综合报告 HTML/PDF 生成链路通过。
- 2026-05-26 已完成小程序备案、微信支付开发打通、数据导入、PDF 下载处理；1 元真实微信支付已验证成功。
- 代码与文档当前正式价格统一为 19.9 元：后端 `MEMBERSHIP_PRICE_CENTS=1990`，小程序展示 `¥19.9`。47 服务器上一次核查仍是 1 元测试配置，必须上线前修正并复测。
- 支付接口联调仍有若干异常和边界场景待测试，见“支付收尾待办”。

## 一、域名与 HTTPS 待办

### 1. 主域名与 HTTPS 状态

- [x] 不再使用未备案的 `aicoming.com.cn`。
- [x] 使用已备案主域名 `aicoming.cn` 的子域名 `gaokao.aicoming.cn`。
- [x] 域名、HTTPS 和微信服务器域名配置已完成；无需再跟进旧域名备案路径。

说明：

- 微信小程序请求和下载必须走 HTTPS 合法域名。
- 当前上线链路以 `https://gaokao.aicoming.cn` 为准；不要再把小程序 API Base 指向 IP 或历史域名。

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
curl -I http://gaokao.aicoming.cn/api/health
```

期望：

```text
HTTP/1.1 301 Moved Permanently
Location: https://gaokao.aicoming.cn/api/health
```

HTTPS 健康检查：

```bash
curl -I https://gaokao.aicoming.cn/api/health
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

- [x] 已用 Certbot webroot 方式申请 `gaokao.aicoming.cn` 证书。
- [x] Nginx 已配置 HTTP 自动跳转 HTTPS。

验证：

```bash
curl -I https://gaokao.aicoming.cn/api/health
curl -I https://gaokao.aicoming.cn/reports/u_1779266091610_u1ynfoti-1779266155844.pdf
```

期望 PDF 响应：

```text
HTTP/1.1 200 OK
Content-Type: application/pdf
```

### 4. 更新服务器环境变量

47 服务器 `/opt/gaokao-proxy/.env`：

```bash
REPORT_BASE_URL=https://gaokao.aicoming.cn
WECHAT_PAY_NOTIFY_URL=https://gaokao.aicoming.cn/api/payment/wechat/notify
```

改完后重启：

```bash
pm2 restart gaokao-proxy --update-env
```

### 5. 更新小程序 API 地址

`gaokao-miniprogram/.env`：

```bash
VITE_API_BASE=https://gaokao.aicoming.cn
VITE_PDF_DOWNLOAD_ENABLED=true
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
https://gaokao.aicoming.cn

downloadFile 合法域名：
https://gaokao.aicoming.cn
```

如果后续使用 `web-view` 打开报告 HTML，再进入：

```text
小程序后台 -> 开发管理 -> 开发设置 -> 业务域名
```

添加：

```text
https://gaokao.aicoming.cn
```

业务域名通常需要下载微信给出的校验文件，并放到服务器站点根目录。等后台生成文件后，再上传到 47 服务器验证。

## 三、小程序备案状态

进入微信公众平台：

```text
小程序后台 -> 设置 -> 小程序备案
```

当前状态：

- [x] 小程序备案已完成。

注意：

- 小程序备案和域名 ICP 备案不是同一件事。
- 小程序备案影响正式发布审核。
- 域名 ICP 备案影响后端域名能否在中国大陆服务器上正常访问和被微信配置。

## 四、微信支付打通待办

### 1. 账号与主体

- [x] 确认小程序 AppID：`wx52fc7943bf6e76aa`。
- [x] 小程序备案已完成。
- [x] 微信支付开发链路已打通。
- [x] 小程序能真实拉起微信支付并完成 1 元测试支付。
- [ ] 正式上线前恢复 `MEMBERSHIP_PRICE_CENTS=1990` 并完成 19.9 元复测。

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
WECHAT_PAY_NOTIFY_URL=https://gaokao.aicoming.cn/api/payment/wechat/notify
COMMERCE_SESSION_SECRET=32位以上随机字符串
COMMERCE_DB_PATH=/opt/gaokao-proxy/data/gaokao-commerce.sqlite
MEMBERSHIP_PRICE_CENTS=1990
MEMBERSHIP_INVITE_REQUIRED=5
MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT=10
MEMBERSHIP_VIP_CODES=FENGGE2026
DEEP_REPORT_VIEW_TOKEN_TTL_MS=600000
```

证书和密钥文件不要提交到 Git。
`MEMBERSHIP_VIP_CODES` 支持用英文逗号配置多个会员邀请码；生产环境应使用不易猜测的短码，并在发放渠道外单独记录。

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

- [x] 小程序微信登录成功，后端能拿到 `openid`。
- [x] `POST /api/payment/create` 能创建 1 元测试会员订单；正式上线前需恢复 `MEMBERSHIP_PRICE_CENTS=1990` 后复测 19.9 元订单。
- [x] 小程序能拉起 `wx.requestPayment`。
- [x] 支付成功后微信回调 `POST /api/payment/wechat/notify` 能到达 47 服务器。
- [x] 后端能验签、解密、更新订单状态。
- [x] 会员状态变为 `active`。
- [x] PDF 下载已处理；公开综合 PDF 和会员态深度 PDF 均已验证可下载。
- [ ] 综合报告生成通过支付会员校验的真机链路待补测。
- [ ] 邀请 5 位新用户完成基础资料后，会员状态变为 `active`。
- [ ] 输入有效 `MEMBERSHIP_VIP_CODES` 会员邀请码后，会员状态变为 `active`。
- [ ] 会员打开学校/专业深度报告在线阅读页成功，页面内搜索可用，且不消耗 PDF 下载次数。
- [ ] 学校/专业深度 PDF 下载成功后，`X-Deep-Report-Downloads-Remaining` 正确减少。

2026-05-26 实测记录：体验版使用 `MEMBERSHIP_PRICE_CENTS=100` 和 `VITE_MEMBERSHIP_PRICE_LABEL=¥1 测试价`，真机微信支付成功；线上订单表最近一笔支付订单为 `paid`，`amount_cents=100`，对应会员 `source=payment`。测试期间已关闭 `LIMITED_FREE_UNLOCK_ENABLED=false`，避免体验版限免入口绕过支付。

### 5. 异常场景

- [ ] 用户取消支付：不解锁，提示支付已取消。
- [ ] 支付成功但回调延迟：前端显示确认中，后端可查单补偿。
- [ ] 回调验签失败：记录日志，不解锁。
- [ ] 重复回调：保持幂等，不重复写订单。
- [ ] 会员已开通：再次点击支付直接提示已解锁。
- [ ] 无效或重复兑换会员邀请码：不解锁，并提示邀请码无效或已兑换。
- [ ] 深度 PDF 下载次数耗尽：返回 `DOWNLOAD_QUOTA_EXHAUSTED`，小程序提示下载次数已用完。

## 五、学校/专业深度解读内容优化待办

- [x] 数据导入已完成，当前需要放进去的数据已入库。
- [ ] 清洗已入库 Markdown 原始数据，删除不适合给家长和学生直接展示的内部标签，例如“权重数值”“考察维度”“直接回答”等。
- [x] 学校/专业深度 PDF 已增加面向志愿决策的二次排版与摘要规则。
- [ ] 抽样检查学校与专业各 5 份 PDF，确认标题层级、重点结论、风险提示和行动建议可读。

## 六、上线验收清单

- [x] `https://gaokao.aicoming.cn/api/health` 返回 `200`。
- [x] `https://gaokao.aicoming.cn/reports/*.pdf` 返回 `application/pdf`。
- [x] 小程序后台已配置 request 合法域名。
- [x] 小程序后台已配置 downloadFile 合法域名。
- [x] 小程序体验版使用 `https://gaokao.aicoming.cn`。
- [x] 综合报告 PDF 下载成功：`/reports/u_1779266091610_u1ynfoti-1779266155844.pdf` 返回 `200 application/pdf`。
- [x] 学校/专业深度 PDF 下载成功：会员 token 请求 `/api/reports/deep/pdf?type=major&id=080901` 返回 `200 application/pdf`。
- [x] 159 分数线 API 从 47 通过 `http://159.75.110.157/score-api` 可访问，健康检查记录数 `894681`，`tests/test_scores_api.py` live 7/7 通过。
- [x] 离线后端完整链路通过：dev 登录、限免解锁、综合报告生成、新生成 HTML、新生成 PDF、会员态深度 PDF 均已验证。
- [ ] 深度报告在线 HTML 阅读页真机打开成功，目录/搜索/打印布局正常。
- [x] 微信支付 1 元测试下单成功；正式 19.9 元下单待恢复价格后复测。
- [x] 支付回调后会员自动解锁。
- [ ] 邀请 5 人免费解锁链路通过。
- [ ] 会员邀请码解锁链路通过。
- [ ] 深度报告下载次数限制链路通过。
- [x] 小程序备案已完成。

## 七、支付收尾待办

这部分是后续新对话框优先执行的任务。标准是：每个任务必须有代码/配置变更、自动化测试或可重复的线上/本地验证步骤，不能只靠手工印象。

### 0. 异常处理排期（2026-05-27）

- [x] 2026-05-27 第一批：补后端支付回调安全网，覆盖重复回调、验签失败、金额不一致、订单不存在、订单过期，并让日志能按 `outTradeNo` / `transactionId` / 错误码串联。
- [x] 2026-05-27 第一批：补小程序支付取消、支付失败、回调延迟确认中的用户提示，避免取消支付时误报“支付暂时不可用”。
- [x] 2026-05-27 第二批：做会员邀请码生成/查询/停用脚本，并补数据库邀请码核销测试。
- [ ] 2026-05-28：部署到 47 服务器后，复测异常回调日志、订单轮询、深度 PDF 配额和邀请码链路。
- [ ] 2026-05-29：恢复 19.9 元正式价格，真机完成 19.9 元支付、会员解锁、综合报告、公开 PDF、深度 PDF 下载全链路验收。

### 1. 会员邀请码生成与核销

- [x] 设计邀请码规则：格式 `FG-YYYYMM-XXXXXX`，使用大写字母和数字，避免易混淆字符 `0/O/1/I`。
- [x] 增加本地/服务器脚本生成邀请码，可指定数量、最大使用次数、过期时间。
- [x] 生成结果写入 `vip_invite_codes` 表；`--dry-run` 可只输出预览码，生产推荐写库。
- [x] 增加查询脚本：列出 code、status、max_uses、used_count、expires_at、最近兑换用户。
- [x] 增加停用/启用脚本：可以将泄露或废弃的邀请码置为 inactive，也可重新启用。
- [x] 增加测试：覆盖 CLI 生成、查询、停用、启用和 dry-run 行为；后端核销测试继续由会员接口测试覆盖。
- [ ] 真机验收：体验版输入测试邀请码后会员变为 `active`，source 为 `vip_code`。

验收标准：

- 后端不需要重启即可发放/停用新邀请码，或明确记录当前仍需重启的限制。
- 邀请码不在 Git 中明文长期保存。
- 发放记录和兑换记录可追踪。

### 2. 支付异常与回调兜底

- [x] 用户取消支付：前端提示“支付已取消”，订单不解锁会员。
- [x] 支付失败：前端展示可重试提示，订单保持未支付或失败状态。
- [x] 支付中断/回调延迟：前端轮询订单；超过轮询次数后提示稍后刷新。
- [x] 重复回调：回调接口保持幂等，同一 `out_trade_no` 不重复增加权益。
- [x] 回调验签失败：返回失败响应，记录安全日志，不解锁会员。
- [x] 金额不一致：回调金额必须等于本地订单金额，否则拒绝解锁并记录告警。
- [x] 订单不存在：回调拒绝并记录，不解锁会员。
- [x] 订单过期：对长期 `created/paying` 未支付订单增加过期状态或查询补偿策略。
- [x] 已开通会员再次点击支付：后端返回 `alreadyUnlocked`，前端不再拉起支付。

验收标准：

- 后端单元测试覆盖回调验签失败、重复回调、金额不一致、订单不存在、订单过期。
- 小程序端手工测试覆盖取消支付、支付失败提示、已开通再点击（待真机复测）。
- 线上日志能通过 orderId / outTradeNo / transactionId 串起一次支付全过程（待 47 部署后复测 PM2 日志）。

### 3. 正式价格恢复与全链路验收

- [ ] 将 47 服务器 `MEMBERSHIP_PRICE_CENTS` 恢复为 `1990`。
- [ ] 将小程序展示从 `¥1 测试价` 恢复为 `¥19.9`，重新构建并上传体验版。
- [ ] 用新测试账号验证 19.9 元下单、支付、回调、会员解锁。
- [ ] 支付后继续验证综合报告生成、公开 PDF、深度 PDF 下载和下载次数扣减。
- [ ] 更新 `docs/deployment/current-live-chain.md`、本文件和周报，标记 19.9 元正式链路已验收。

验收标准：

- 线上最近一笔正式订单 `amount_cents=1990` 且 `status=paid`。
- 会员表对应用户 `status=active`、`source=payment`。
- 小程序端不再出现测试价或限免入口。
