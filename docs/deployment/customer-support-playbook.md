# 客服处理话术与取证清单

更新日期：2026-06-01

客服微信号：`HRJ-11055`

## 通用取证

每次反馈先请用户提供：

- 用户 ID 或“小程序我的页”截图。
- 问题发生时间，精确到分钟更好。
- 当前页面截图或录屏。
- 若涉及支付，提供微信支付成功页截图、商户单号或微信支付订单号。

## 订单/会员手工查询命令

所有订单和会员排查优先在 47 服务器执行。默认数据库路径为 `/opt/gaokao-proxy/data/gaokao-commerce.sqlite`，如 `.env` 中 `COMMERCE_DB_PATH` 不同，以 `.env` 为准。

登录 47：

```bash
ssh -i /Users/MarkHuang/Downloads/mark123-.pem root@47.113.125.147
cd /opt/gaokao-proxy
```

按用户 ID 查：

```bash
npm run commerce-ops -- lookup --user-id u_xxx
```

按 openid 查：

```bash
npm run commerce-ops -- lookup --openid openid_xxx
```

按本地订单号查：

```bash
npm run commerce-ops -- lookup --order-id ord_xxx
```

按微信商户单号查：

```bash
npm run commerce-ops -- lookup --out-trade-no GKxxxxxxxx
```

按微信支付订单号查：

```bash
npm run commerce-ops -- lookup --transaction-id 420xxxxxxxx
```

机器可读输出加 `--json`。查询结果至少要核对：

- `user.userId` 和 `user.openid` 是否匹配用户截图。
- `membership.status` 是否为 `active`，`membership.source` 是否为 `payment`、`invite`、`vip_code` 或 `support_manual`。
- `orders[].status` 是否为 `paid`、`paying`、`created`、`expired` 或 `abnormal`。
- `orders[].amountCents` 是否等于正式价格 `1990`。
- `orders[].outTradeNo` 是否匹配用户提供的商户单号。
- `orders[].transactionId` 是否匹配微信支付订单号。
- `supportOperations` 是否已有补开会员或补偿码记录，避免重复补偿。

本地开发或临时数据库可显式传库路径：

```bash
npm run commerce-ops -- lookup --db /path/to/gaokao-commerce.sqlite --openid openid_xxx
```

## 补开会员 SOP

只在满足以下条件时补开：

- 用户提供的支付成功截图、商户单号或微信支付订单号能与查询结果对应。
- 用户确实应享受会员权益，但 `membership.status` 仍不是 `active`。
- 已排除重复支付、金额不一致、疑似伪造截图等风险。

执行前先查询并保存结果：

```bash
npm run commerce-ops -- lookup --out-trade-no GKxxxxxxxx --json
```

补开会员：

```bash
npm run commerce-ops -- activate-membership \
  --user-id u_xxx \
  --operator 客服姓名 \
  --reason "用户支付成功但回调未解锁，商户单号 GKxxxxxxxx，微信支付订单号 420xxxxxxxx"
```

也可以用 openid：

```bash
npm run commerce-ops -- activate-membership \
  --openid openid_xxx \
  --operator 客服姓名 \
  --reason "用户支付成功但回调未解锁，商户单号 GKxxxxxxxx"
```

补开后必须复查：

```bash
npm run commerce-ops -- lookup --user-id u_xxx
```

期望：

- `membership.status=active`。
- 新增一条 `support_operations`，类型为 `activate_membership`。
- 若用户原本已经是 `active/payment`、`active/invite` 或 `active/vip_code`，不要重复补开；只记录客服沟通结论。

## 补偿邀请码 SOP

适用场景：

- 支付状态无法当场确认，但客服决定先给用户权益补偿。
- 重复扣款、服务异常或人工活动需要发放一次性 VIP 解锁码。
- 不希望直接改某个用户会员状态，而是让用户在小程序内自行兑换。

发放一次性补偿码：

```bash
npm run commerce-ops -- issue-code \
  --recipient openid_or_user_note \
  --operator 客服姓名 \
  --reason "支付回调延迟补偿，客服工单 #123"
```

默认生成格式为 `COMP-YYYYMM-XXXXXX`，`max_uses=1`，有效期 30 天。需要自定义前缀或有效期：

```bash
npm run commerce-ops -- issue-code \
  --prefix COMP \
  --expires-days 7 \
  --recipient openid_or_user_note \
  --operator 客服姓名 \
  --reason "临时补偿"
```

发码后复查：

```bash
npm run vip-codes -- show --code COMP-YYYYMM-XXXXXX
```

期望：

- `status=active`。
- `used/max` 为 `0/1`。
- 用户兑换后 `redemptions` 出现该用户记录，会员状态变为 `active/vip_code`。

发给用户的话术：

> 已为您生成一次性会员补偿码：`COMP-YYYYMM-XXXXXX`。请在小程序报告页的会员邀请码入口兑换，兑换后即可解锁会员权益。该码仅限一次使用，请勿转发。

## 支付成功但未解锁

话术：

> 您好，先别重复支付。请把支付成功截图、用户 ID 和发生时间发给我们，我们会核对支付回调和会员状态。若确认已支付成功，会为您补开会员权益。

排查重点：

- 订单是否 `paid`。
- 会员状态是否 `active`，来源是否 `payment`。
- 微信回调是否延迟、验签失败或金额不一致。
- 先用 `commerce-ops lookup` 查询订单和会员；确认应解锁但未解锁时，按“补开会员 SOP”处理。

## 重复扣款

话术：

> 您好，请把两笔支付截图和用户 ID 发给我们。我们会核对订单记录；如确认为重复支付，会按微信支付规则处理退款或权益补偿。

排查重点：

- 是否同一用户存在多笔 `paid` 订单。
- 是否已有会员后再次发起支付。
- 是否为微信支付显示延迟导致的误判。
- 若确认用户权益受损但退款不能即时完成，可先按“补偿邀请码 SOP”发放一次性码，并在工单里记录后续退款处理。

## 邀请码无效

话术：

> 您好，请确认邀请码没有空格，并使用最新发放的完整邀请码。如果仍提示无效，请把邀请码、用户 ID 和截图发给我们核对。

排查重点：

- 邀请码是否存在、是否 `active`。
- 是否已过期。
- 是否已达到最大使用次数。
- 当前用户是否已兑换过同一邀请码。
- 使用 `npm run vip-codes -- show --code 用户提供的邀请码` 查询邀请码状态和兑换记录。

## PDF 下载次数耗尽

话术：

> 您好，深度报告在线阅读不限次数，PDF 下载会消耗会员下载额度。若页面提示次数已用完，可以继续在线阅读；如您认为次数异常，请把用户 ID、报告名称和截图发给我们核对。

排查重点：

- 会员 `downloadQuota.remaining`。
- `deep_report_downloads` 中该用户下载记录。
- 是否重复点击或网络重试造成多次下载。
- 使用 `commerce-ops lookup --user-id u_xxx` 查看会员下载额度摘要；必要时再查 SQLite 下载明细。

## 报告生成失败

话术：

> 您好，报告生成失败时系统会尽量保留草稿。请稍后重试一次；如果仍失败，请把用户 ID、填写资料截图、失败提示截图和发生时间发给我们，我们会排查模型生成或服务状态。

排查重点：

- `/api/report/generate` 是否返回 `draftId` 或具体错误。
- DeepSeek 模型配置是否为 `deepseek-v4-pro`。
- 用户两项测评（性格类型定位 + 霍兰德职业兴趣）和基础资料是否完整。
- PM2 日志中同一时间是否有模型、PDF 或数据库错误。

## 邀请人数没有增加

话术：

> 您好，有效邀请需要满足“新用户通过您的分享进入，并完成省份、科类、分数基础资料”。如果对方只是打开小程序、没有补全资料，或不是新用户，系统不会计入有效邀请。请把您的用户 ID、对方完成资料的截图和大概时间发给我们核对。

排查重点：

- 邀请人用户 ID 是否正确。
- 被邀请人是否通过带 `inviterId` 的分享路径进入。
- 被邀请人是否为新用户，且不是邀请人本人。
- 被邀请人是否调用过 `/api/profile/complete`。
- `invites` 表中该 invitee 是否已经给其他 inviter 计数。

## 用户认为报告不值 19.9 元

话术：

> 您好，我们很重视报告质量。请把报告链接、考生省份/科类/分数、您认为不准确或没有帮助的部分截图发给我们。我们会核对输入资料、生成记录和报告内容；如确实生成异常或明显缺失关键判断，会协助重新生成或给出后续处理方案。

排查重点：

- 报告是否成功打开，是否存在空白、过短、缺少风险提醒或行动建议。
- 用户基础资料是否填写错误，例如省份、科类、分数。
- 模型生成日志是否超时、截断或使用草稿。
- 是否需要为用户补发新版报告或补偿邀请码。

## 退款或支付异常咨询

话术：

> 您好，请先不要重复支付。请提供微信支付成功页截图、用户 ID、支付时间和订单号。我们会核对订单和会员状态；如确认重复扣款或支付成功但权益未到账，会按微信支付规则处理退款、补开权益或补偿。

排查重点：

- 是否存在多笔 `paid` 订单。
- 订单金额是否为 `1990` 分。
- 会员是否已经 `active`。
- 微信回调是否成功验签并落库。
- 是否需要补开会员、发放补偿邀请码或发起退款。
