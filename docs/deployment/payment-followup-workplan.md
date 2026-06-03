# 支付收尾执行计划

> 创建日期：2026-05-26
> 用途：开新对话框后，可直接让编码 agent 按本计划执行。

## 当前状态

- 小程序备案：已完成。
- 域名与 HTTPS：已完成，当前唯一小程序 API Base 为 `https://gaokao.aicoming.cn`。
- 服务器分工：47 运行 `gaokao-proxy`、报告生成和静态报告；159 运行 Dify、PostgreSQL、分数 API。
- 数据导入：当前需要放进去的数据已完成导入。
- PDF 下载：公开综合 PDF 和会员态深度 PDF 已处理并验证过。
- 微信支付开发：已打通，1 元测试支付已真机成功。
- 当前待处理：邀请码生成/核销、支付异常与回调兜底、正式 19.9 元复测、支付后报告/PDF 全链路补测。

## 任务 1：邀请码生成与核销工具

### 背景

当前代码已支持 `POST /api/membership/redeem-code`，并会从 `MEMBERSHIP_VIP_CODES` 读取少量固定邀请码。这个方式适合临时测试，不适合批量发放、停用、追踪兑换。

### 要做什么

- 增加一个服务器侧脚本，例如 `gaokao-proxy/scripts/manage-vip-codes.js`。
- 支持命令：
  - `generate --count 20 --prefix FG --max-uses 1 --expires-days 30`
  - `list`
  - `disable --code FG-XXXXXX`
  - `show --code FG-XXXXXX`
- 写入/读取 SQLite 表 `vip_invite_codes` 和 `vip_code_redemptions`。
- 保留 env 方式作为兼容，但生产发码优先用数据库脚本。

### 生成规则建议

- 格式：`FG-YYYYMM-XXXXXX`。
- 字符集：大写字母和数字，排除 `0/O/1/I`。
- 默认 `max_uses=1`，内部测试码可以 `max_uses=5`。
- 默认有效期 30 天；永不过期必须显式传参数。

### 验收标准

- 有效码兑换后会员变为 `active`，`source=vip_code`。
- 同一用户重复兑换同一码失败。
- 过期码失败。
- 用尽次数失败。
- 被 disable 的码失败。
- `list/show` 能看到 `used_count` 和兑换记录。
- 新增或更新测试覆盖以上场景。

## 任务 2：支付异常与回调兜底

### 背景

真实支付主链路已成功，但异常路径还没有系统验证。当前数据库里已经出现过未完成的 `paying` 测试订单，说明需要订单过期或补偿机制。

### 要做什么

- 用户取消支付：前端提示“支付已取消”，不显示“支付暂时不可用”这种误导文案。
- 支付失败：前端提示可重试，订单不解锁。
- 回调延迟：前端轮询订单；超时后提示稍后刷新，用户重新进入页面可继续查询状态。
- 重复回调：保持幂等，不重复激活或重复写异常。
- 回调验签失败：返回失败响应，记录日志，不解锁。
- 金额不一致：回调金额必须等于本地订单 `amount_cents`，否则拒绝解锁并记录告警。
- 订单不存在：回调拒绝并记录。
- 订单过期：长期 `created/paying` 订单应变为 `expired`，或至少查询时明确展示为超时未支付。
- 已开通会员再次点击支付：后端返回 `alreadyUnlocked`，前端不拉起支付。

### 验收标准

- 后端单元测试覆盖：重复回调、验签失败、金额不一致、订单不存在、订单过期。
- 小程序手工测试覆盖：取消支付、已开通再次点击、支付中断后刷新。
- 日志能用 `orderId`、`outTradeNo`、`transactionId` 串起一次支付全过程。

## 任务 3：支付后会员全链路补测

### 要做什么

- 使用一个新测试账号，从未开通状态开始。
- 完成资料和两项测评（性格类型定位 + 霍兰德职业兴趣）。
- 发起支付。
- 支付成功后检查：
  - 会员状态为 `active/payment`。
  - 综合报告能生成。
  - 报告 HTML 可打开。
  - 综合 PDF 可下载。
  - 深度 PDF 可下载。
  - 深度 PDF 下载剩余次数正确减少。

### 验收标准

- `GET /api/membership/status` 返回 `active`。
- `POST /api/report/generate` 成功返回 `https://gaokao.aicoming.cn/reports/*.html`。
- `GET /reports/*.pdf` 返回 `application/pdf`。
- `GET /api/reports/deep/pdf` 返回 `application/pdf`，响应头剩余次数减少。

## 任务 4：恢复正式价格并复测

### 要做什么

- 把 47 服务器 `/opt/gaokao-proxy/.env` 改回：

```bash
MEMBERSHIP_PRICE_CENTS=1990
LIMITED_FREE_UNLOCK_ENABLED=false
```

- 把小程序 `.env` 改回：

```bash
VITE_MEMBERSHIP_PRICE_LABEL=¥19.9
VITE_PAYMENT_ENABLED=true
```

- 重新构建并上传体验版。
- 使用新测试账号完成 19.9 元真实支付。

### 验收标准

- 微信收银台显示 19.9 元。
- 线上最近一笔订单 `amount_cents=1990`，`status=paid`。
- 对应会员 `status=active`，`source=payment`。
- 小程序不再出现 `¥1 测试价`。

## 任务 5：文档和提交

### 要做什么

- 更新：
  - `docs/deployment/production-launch-todo.md`
  - `docs/deployment/wechat-pay-launch-flow.md`
  - `docs/deployment/current-live-chain.md`
  - `docs/周报-2026-05-18_05-26.md`
- 运行相关测试。
- 提交一个清晰 commit，例如：

```bash
git commit -m "fix(payment): harden payment callbacks and vip code operations"
```

### 验收标准

- 文档中明确区分“1 元测试已过”和“19.9 元正式复测是否已过”。
- 不提交 `.env`、证书、私钥、真实密钥。
- `git status` 中没有误加入的敏感文件。

## 任务 6：MVP 上线前内容排期与验收表

### 要做什么

- 建立一份上线前内容排期，建议放在 `docs/deployment/mvp-content-launch-plan.md`。
- 覆盖小程序内需要对外展示的内容：会员权益文案、报告页说明、支付页文案、邀请码发放说明、PDF 下载说明、客服/售后话术。
- 每项内容都要有负责人、完成日期、验收标准和发布位置。
- 增加最终上线验收表，覆盖支付、邀请码、邀请 5 人、报告生成、PDF 下载、深度 PDF 配额、异常提示、隐私与备案信息。

### 验收标准

- 每个上线入口都有对应文案和截图验收项。
- 任何“测试价”“测试入口”“限免调试”都不得出现在对外版本。
- 全部验收项通过后，才能提交审核或正式发布。
