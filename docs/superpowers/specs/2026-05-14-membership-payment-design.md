# “我的”页会员、邀请与微信支付设计

> 历史文档：本文保留 2026-05-14 的设计决策背景，只供追溯，不作为当前上线执行依据。当前上线配置以 `docs/deployment/current-live-chain.md`、`docs/deployment/production-launch-todo.md`、`docs/deployment/mvp-next-todo-2026-05-28.md` 和 `gaokao-proxy/.env.example` 为准。
> 当前实现提示：正式会员价已改为 `¥19.9` / `MEMBERSHIP_PRICE_CENTS=1990`；邀请门槛为 5 人；已新增会员邀请码和深度 PDF 下载额度。

## 已确认决策

- 页面方向：`我的` 页面采用“会员权益中心型”。
- 价格：`¥19.9` 一次性解锁。
- 权益归属：绑定当前微信用户，长期有效。
- 免费解锁：邀请 `5` 位新用户填写基本信息后自动解锁。
- 有效邀请：被邀请用户首次完成基本信息保存即计数，单个被邀请微信用户只能贡献一次。
- 付费权益：大学深度研究、综合志愿报告生成、PDF 下载、家长分享链接。
- 报告限制：`/api/report/generate` 生成前必须校验权益，未解锁不得生成付费报告。

## 产品结构

### 我的页

`gaokao-miniprogram/src/pages/profile/profile.vue` 从“测评记录页”升级为会员中心，页面顺序如下：

1. 用户头部：头像、产品名、当前会员状态。
2. 会员卡：展示“深度填报会员”、`¥19.9 一次性解锁`、核心权益和主按钮。
3. 邀请卡：展示 `有效邀请数/5`、进度条、分享按钮、邀请规则说明。
4. 付费权益列表：大学深度研究、综合报告生成、PDF 下载、家长分享。
5. 综合志愿报告入口：保留当前测评完成度；未解锁时显示“待解锁”，已解锁时显示“可生成”。
6. 测评记录：保留五环问卷、MBTI、霍兰德记录。
7. 设置与订单：订单记录、恢复权益、清除本地数据。

### 报告页

`gaokao-miniprogram/src/pages/report/report.vue` 保留当前生成流程，但在生成前增加权益状态分支：

- 测评未完成：提示先完成 3 项测评。
- 测评完成但未解锁：展示付费拦截页，不请求报告生成。
- 已解锁：正常请求 `/api/report/generate`。
- 支付完成但回调未到：提示“正在确认支付结果”，轮询订单状态或引导稍后刷新。

## 宣传文案

主标题：

> 解锁深度填报会员

副标题：

> 基于测评、对话记录和院校资料，生成可给家长一起看的志愿决策报告。

权益短文案：

- 大学深度研究：看清院校定位、优势专业、就业方向和填报风险。
- 综合志愿报告：整合测评、分数、兴趣和目标，输出完整填报建议。
- PDF 下载：保存成文件，方便打印或转发给家长。
- 家长分享链接：报告链接可直接发给家长共同讨论。

按钮文案：

- 主按钮：`¥19.9 立即解锁`
- 邀请按钮：`邀请 5 人免费解锁`
- 报告拦截按钮：`解锁并生成报告`
- 支付确认中：`正在确认支付结果`
- 已解锁：`已解锁，生成报告`

邀请说明：

> 邀请新用户填写基本信息后，计为 1 个有效邀请。累计 5 个有效邀请，即可免费解锁 ¥19.9 深度填报会员。

风险提示：

> 报告结果仅供志愿填报参考，请以各省考试院和高校官方信息为准。

## 技术架构

```
小程序
├── wx.login 获取 code
├── /api/auth/wechat-login 换取 openid 侧用户身份
├── /api/membership/status 获取权益与邀请进度
├── /api/payment/create 创建 ¥19.9 微信支付订单
├── wx.requestPayment 拉起支付
├── /api/payment/order/:id 查询订单确认结果
└── /api/report/generate 已解锁后生成报告

gaokao-proxy
├── SQLite 持久化用户、会员、邀请、订单
├── 微信 code2Session 换 openid
├── 微信支付 JSAPI 下单
├── 微信支付回调验签与解密
├── 邀请有效计数与自动解锁
└── 报告生成前权益校验

微信平台
├── jscode2session
├── JSAPI 下单获取 prepay_id
└── 支付结果通知 notify_url
```

后端必须作为可信源。小程序本地只缓存展示状态，不决定是否解锁。

## 数据持久化

当前 `gaokao-proxy` 只有 Redis 可选，不能承担订单和会员的长期事实来源。MVP 新增 SQLite 数据库，默认路径：

```text
/opt/gaokao-proxy/data/gaokao-commerce.sqlite
```

### users

```text
id                 TEXT PRIMARY KEY
openid             TEXT UNIQUE NOT NULL
unionid            TEXT
nickname           TEXT
avatar_url         TEXT
invited_by_user_id TEXT
profile_completed_at INTEGER
created_at         INTEGER NOT NULL
updated_at         INTEGER NOT NULL
```

### memberships

```text
user_id     TEXT PRIMARY KEY
status      TEXT NOT NULL  -- inactive | active
source      TEXT NOT NULL  -- payment | invite | admin
unlocked_at INTEGER
expires_at  INTEGER        -- MVP 为空，表示长期有效
```

### invites

```text
id                  TEXT PRIMARY KEY
inviter_user_id      TEXT NOT NULL
invitee_user_id      TEXT NOT NULL UNIQUE
status              TEXT NOT NULL  -- pending | effective
effective_at         INTEGER
created_at           INTEGER NOT NULL
```

`invitee_user_id` 唯一，防止同一个被邀请用户给多人重复贡献。若用户第一次进入时已有 inviter，后续保存基本信息时把 invite 标记为 `effective`。

### payment_orders

```text
id                  TEXT PRIMARY KEY
user_id              TEXT NOT NULL
out_trade_no         TEXT UNIQUE NOT NULL
transaction_id       TEXT
amount_cents         INTEGER NOT NULL  -- 1990
status               TEXT NOT NULL     -- created | paying | paid | closed | failed
prepay_id            TEXT
paid_at              INTEGER
created_at           INTEGER NOT NULL
updated_at           INTEGER NOT NULL
raw_notify           TEXT
```

## 后端接口

### `POST /api/auth/wechat-login`

请求：

```json
{
  "code": "wx.login 返回的 code",
  "inviterId": "可选，分享路径带入"
}
```

响应：

```json
{
  "userId": "u_1778740000000_abcd1234",
  "sessionToken": "后端签发的轻量 token",
  "membership": { "status": "inactive" },
  "invite": { "effectiveCount": 0, "requiredCount": 3 }
}
```

说明：后端用 `WECHAT_APPID` 和 `WECHAT_SECRET` 调 `jscode2session` 换取 `openid`。后续请求使用 `sessionToken` 识别用户，不再信任前端传来的本地 `userId`。

### `GET /api/membership/status`

返回当前会员状态、邀请进度和最近订单状态。

```json
{
  "status": "active",
  "source": "invite",
  "unlockedAt": 1778740000000,
  "invite": {
    "effectiveCount": 3,
    "requiredCount": 3
  },
  "features": {
    "universityResearch": true,
    "comprehensiveReport": true,
    "pdfDownload": true,
    "familyShare": true
  }
}
```

### `POST /api/profile/complete`

当前小程序保存基本信息后调用。若该用户是被邀请进入且尚未计数，则把邀请关系标记为 `effective`。如果邀请人有效邀请数达到 3，自动写入 `memberships` 解锁。

### `POST /api/payment/create`

创建 `¥19.9` 微信支付 JSAPI 订单。

后端职责：

1. 若用户已解锁，直接返回当前会员状态，不重复下单。
2. 创建本地订单，金额固定 `1990` 分。
3. 调微信支付 API v3 JSAPI 下单拿 `prepay_id`。
4. 生成前端 `wx.requestPayment` 所需参数：`timeStamp`、`nonceStr`、`package`、`signType=RSA`、`paySign`。

响应：

```json
{
  "orderId": "ord_1778740000000_abcd1234",
  "payment": {
    "timeStamp": "1778740000",
    "nonceStr": "random",
    "package": "prepay_id=wx...",
    "signType": "RSA",
    "paySign": "..."
  }
}
```

### `POST /api/payment/wechat/notify`

微信支付回调地址。后端验签并解密通知体后：

1. 根据 `out_trade_no` 找订单。
2. 金额必须等于 `1990` 分。
3. 微信交易状态为成功时把订单改为 `paid`。
4. 写入 `memberships`，`source=payment`。
5. 返回微信支付要求的成功响应。

支付成功不能只以前端 `requestPayment` 成功回调为准。

### `GET /api/payment/order/:orderId`

小程序支付后轮询订单状态。若回调延迟，可以后端主动查询微信支付订单状态并补偿更新。

### `POST /api/report/generate`

保留当前请求结构，但新增权益校验：

- 未登录：`401`
- 未解锁：`402`，返回解锁文案和邀请进度
- 已解锁：执行现有报告生成逻辑

```json
{
  "error": "请先解锁深度填报会员",
  "code": "MEMBERSHIP_REQUIRED",
  "priceCents": 1990,
  "invite": { "effectiveCount": 1, "requiredCount": 3 }
}
```

## 微信支付配置

新增 `.env` 变量：

```text
WECHAT_APPID=
WECHAT_SECRET=
WECHAT_MCH_ID=
WECHAT_PAY_SERIAL_NO=
WECHAT_PAY_PRIVATE_KEY_PATH=
WECHAT_PAY_PUBLIC_KEY_ID=
WECHAT_PAY_PUBLIC_KEY_PATH=
WECHAT_PAY_API_V3_KEY=
WECHAT_PAY_NOTIFY_URL=
COMMERCE_DB_PATH=/opt/gaokao-proxy/data/gaokao-commerce.sqlite
MEMBERSHIP_PRICE_CENTS=1990
MEMBERSHIP_INVITE_REQUIRED=5
```

正式支付要求 `notify_url` 使用公网 HTTPS 域名，并填入 `WECHAT_PAY_NOTIFY_URL`。当前 `47.113.125.147` 的 HTTP 地址可以用于报告访问，但微信支付回调上线前需要准备合规域名和 HTTPS。

## 前端状态管理

新增 `stores/membership.js`：

- `status`
- `source`
- `effectiveInviteCount`
- `requiredInviteCount`
- `features`
- `lastOrderStatus`
- `loadStatus()`
- `createPayment()`
- `pollOrder(orderId)`
- `markProfileCompleted()`

用户身份从本地 UUID 升级为微信身份：

- 保留本地 `user_id` 作为兼容字段和历史数据关联。
- 新增后端 `userId/sessionToken`，后续付费和报告生成接口使用后端身份。
- 清除本地数据不影响已购买权益；重新 `wx.login` 后可从后端恢复。

## 邀请路径

分享路径示例：

```text
/pages/index/index?inviterId=u_1778740000000_abcd1234
```

处理流程：

1. 被邀请人打开小程序，前端保存 `inviterId`。
2. `wx.login` 后调用 `/api/auth/wechat-login`，后端创建 pending invite。
3. 被邀请人保存基本信息时调用 `/api/profile/complete`。
4. 后端确认该 invitee 首次有效，计入 inviter。
5. inviter 有效邀请数达到 3 后自动激活会员。

边界：

- 自己邀请自己不计数。
- 已注册用户再次通过邀请链接进入不计数。
- 同一个 invitee 只能给一个 inviter 计数。
- 被邀请人清除本地数据不撤销已经生效的邀请计数。

## 错误处理

- 支付取消：不解锁，保留订单为 `created` 或 `closed`，前端提示“支付已取消”。
- 支付成功但回调延迟：前端显示确认中，轮询订单状态，后端必要时查单补偿。
- 金额不一致：订单标记异常，不解锁，写日志。
- 微信登录失败：前端可继续使用免费测评和咨询，但报告付费功能提示“请先登录微信身份”。
- 数据库不可写：支付和邀请接口返回 503，报告已解锁用户仍应可读取已有权益。
- 报告生成失败：不影响会员状态，用户可重试，继续保留现有 10 分钟冷却策略或按会员身份调整。

## 验收标准

- “我的”页展示会员卡、¥19.9、权益列表、邀请进度和测评记录。
- 未解锁用户完成 3 项测评后进入报告页，会看到付费拦截，不会调用报告生成。
- 已解锁用户可以生成报告，并可下载 PDF、复制链接。
- 支付下单返回 `wx.requestPayment` 参数，支付回调成功后会员状态变为 active。
- 邀请 5 个新用户填写基本信息后，邀请人会员状态自动变为 active。
- 清除本地数据后，同一微信用户重新进入仍可恢复会员状态。
- `/api/report/generate` 对未解锁后端用户返回 `402 MEMBERSHIP_REQUIRED`。
- 邀请去重有效：同一被邀请用户不会重复计数。

## 测试计划

- Node 单元测试：会员状态、邀请计数、自动解锁、订单状态流转、报告权益校验。
- 前端手工测试：未解锁、支付中、已解锁、邀请进度 0/3 到 3/3 四种状态。
- 微信支付沙箱或测试商户验证：下单、前端拉起支付、回调验签、订单查询补偿。
- 回归测试：现有聊天、测评、报告生成完成度检查不被破坏。

## 不在本次范围

- 多档会员、订阅制、按次购买。
- 优惠券、退款后台、发票。
- 家长账号体系。
- 管理后台。MVP 可先通过数据库和日志排查订单。
