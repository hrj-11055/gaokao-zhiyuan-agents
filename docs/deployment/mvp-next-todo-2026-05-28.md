# MVP 收口待办规划（2026-05-28）

目标：围绕 19.9 元会员 MVP，把邀请码、登录、模型、PDF、客服反馈和邀请 5 人解锁收成可发布状态。

## 当前确认

- 小程序前端价格展示已配置为 `¥19.9`。
- 本地代码默认会员价格已对齐为 `MEMBERSHIP_PRICE_CENTS=1990`。
- 2026-05-28 已将 47 服务器 `MEMBERSHIP_PRICE_CENTS` 改为 `1990`，并用生产库探针订单确认新订单金额为 `1990`；探针订单已标记为 `expired`。
- 2026-05-28 已将 47 服务器 `DEEPSEEK_MODEL` 改为 `deepseek-v4-pro`，并重启 `gaokao-proxy --update-env`。
- 当前登录链路是静默 `uni.login` -> 后端 `jscode2session` -> 用 `openid` upsert 用户，不需要头像/昵称授权。
- 邀请码表 `vip_invite_codes`、兑换表 `vip_code_redemptions` 代码和生产库都已存在。
- 邀请 5 人后端链路已具备：被邀请人完成资料后计为有效邀请，满 5 人后邀请人会员 `source=invite`。

## 多智能体排查分工与结果

| 智能体 | 范围 | 结果 |
| --- | --- | --- |
| Sartre | 微信登录/注册 | 确认无头像昵称授权；首页会触发 `uni.login`；后端按 `openid` 创建用户。 |
| Aristotle | DeepSeek/PDF | 确认报告代码支持 `deepseek-v4-pro`，但线上 env 当前是旧的 `deepseek-chat`；PDF 已改为静态打印版 + A4 print layout，不再依赖 Vue/Tailwind CDN 才能输出正文。 |
| Lorentz | 邀请码/邀请 5 人 | 确认生产库已有邀请码表和兑换记录；邀请 5 人后端逻辑可用；报告页分享已补齐带参闭环。 |

## P0：上线前阻塞

- [x] 将 47 服务器 `/opt/gaokao-proxy/.env` 改为 `MEMBERSHIP_PRICE_CENTS=1990`。
- [x] 将 47 服务器 `/opt/gaokao-proxy/.env` 改为 `DEEPSEEK_MODEL=deepseek-v4-pro`。
- [x] `pm2 restart gaokao-proxy --update-env`。
- [ ] 用新测试账号真机支付 19.9 元，确认微信收银台、订单 `amount_cents=1990`、会员 `active/payment`。
- [ ] 重新生成综合报告，确认 DeepSeek 报告生成成功。
- [ ] 下载综合 PDF 和深度 PDF，确认排版、中文字体、分页、剩余次数扣减。

## P1：邀请码正式可运营

- [x] 增加 `gaokao-proxy/scripts/manage-vip-codes.js`。
- [x] 增加 `npm run vip-codes`。
- [x] 支持 `generate/list/show/disable/enable`。
- [x] 支持 `--max-uses`、`--expires-days`、`--json`、`--dry-run`。
- [x] 部署脚本到 47 服务器，并确认 `npm run vip-codes -- list --limit 3` 可查询生产邀请码。
- [ ] 生成 3 个测试码，真机兑换，确认会员 `source=vip_code`。
- [ ] 生成正式发放码，单独保存发放记录，不提交 Git。

## P1：邀请 5 人解锁

- [x] 我的页分享带 `inviterId`。
- [x] 首页接收 `inviterId` 并登录上报。
- [x] 保存资料后会触发 `completeProfile`，有效邀请计数。
- [x] 报告页邀请按钮补齐 `onShareAppMessage`，确保也带 `inviterId`。
- [ ] 用 1 个邀请人 + 5 个新微信账号真机跑完。
- [ ] 确认邀请人 `effectiveInviteCount=5`，会员 `source=invite`。
- [ ] 增加运营提示：邀请必须是新用户，并完成基础资料才有效。

## P1：PDF 排版优化

- [x] PDF 生成器改用 print media、A4 CSS、专用版本 `print-layout-v4`，旧 PDF 会自动重新生成。
- [x] 综合报告增加静态打印版，PDF 不再依赖 Vue/Tailwind CDN 才能显示正文。
- [x] 深度报告取消每个章节强制新开页，减少大面积空白。
- [ ] 抽样 3 份综合报告、3 份学校深度报告、3 份专业深度报告。
- [ ] 根据样张继续微调字号、页边距、标题间距和表格换页。

## P2：客服反馈流程

- [x] 我的页“投诉建议”展示客服微信号 `HRJ-11055`。
- [x] 用户可一键复制微信号。
- [x] 客服话术补齐：支付成功未解锁、重复扣款、邀请码无效、PDF 次数耗尽、报告生成失败，见 `docs/deployment/customer-support-playbook.md`。
- [x] 明确客服需要用户提供：用户 ID、支付截图、问题截图、发生时间，见 `docs/deployment/customer-support-playbook.md`。

## P2：登录真机验证

- [x] 正式体验版确认未设置 `VITE_WECHAT_LOGIN_MOCK=true`，默认使用真实微信登录。
- [x] 47 服务器确认 `WECHAT_LOGIN_MOCK=0`。
- [ ] 真机打开首页后检查 47 日志能看到真实 `openid`，不是 `mock_openid_dev_*`。
- [ ] 清除本地缓存后重新进入，同一个微信用户能恢复会员状态。

## 常用命令

```bash
cd gaokao-proxy
npm run vip-codes -- generate --count 5 --prefix FG --max-uses 1 --expires-days 30
npm run vip-codes -- list --status active
npm run vip-codes -- show --code FG-202605-XXXXXX
npm run vip-codes -- disable --code FG-202605-XXXXXX
```
