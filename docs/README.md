# 文档入口与当前口径

最后更新：2026-06-02

本目录里有上线文档、历史方案、迁移记录、周报和执行计划。做当前开发、部署或验收时，先看下面的 source-of-truth 文档，不要直接按旧 plan/spec/周报执行。

## 当前必须优先看的文档

| 场景 | 使用文档 |
| --- | --- |
| 线上服务器、域名、API Base、模型、会员 env | `docs/deployment/current-live-chain.md` |
| 正式上线前待办、验收表、支付/邀请码/PDF 状态 | `docs/deployment/production-launch-todo.md` |
| 2026-05-28 MVP 收口清单和多智能体排查结论 | `docs/deployment/mvp-next-todo-2026-05-28.md` |
| 上线纠错、发布门禁、版本迭代方法论 | `docs/deployment/release-readiness-and-iteration-methodology.md` |
| 支付上线流程与微信支付参数 | `docs/deployment/wechat-pay-launch-flow.md` |
| 客服订单/会员排查、补开会员、补偿邀请码 SOP | `docs/deployment/customer-support-playbook.md` |
| 系统架构与 API 合约 | `docs/architecture-and-apis.md` |
| 小程序调用链排障 | `docs/miniprogram-call-chain-visual.md` |
| 漂移检测和预防规则 | `docs/drift-resolution-guide.md` |

## 当前关键事实

- 小程序 API Base：`https://gaokao.aicoming.cn`。
- 47 服务器：`gaokao-proxy`、会员/支付、综合报告生成、静态报告/PDF。
- 159 服务器：Dify、Dify 依赖栈、`gaokao-api`、报告 PostgreSQL 数据。
- 正式会员价格：`¥19.9`，后端金额 `MEMBERSHIP_PRICE_CENTS=1990`。
- 会员替代解锁：邀请 5 位有效新用户，或兑换后台发放的邀请码。
- 当前报告生成前置测评：只要求性格类型定位（MBTI 结果摘要）和霍兰德职业兴趣（RIASEC code/scores/indicators）。五环问卷入口已关闭，旧五环数据保留但不再参与报告准备度、接口校验、专业资料抓取或最终 prompt。
- 综合报告目标模型：`REPORT_DEEPSEEK_MODEL=deepseek-v4-flash`。
- 深度报告在线阅读免费；深度 PDF 下载需要会员并消耗额度。
- 客服反馈微信号：`HRJ-11055`。
- 订单/会员人工排查：47 服务器 `/opt/gaokao-proxy` 下使用 `npm run commerce-ops -- lookup ...`。

## 历史文档边界

- `docs/superpowers/plans/*` 和 `docs/superpowers/specs/*` 多数是当时的执行计划或设计草稿，只供追溯。
- 旧迁移文档和旧提示词已归档或标注归档，不代表当前线上链路。
- 周报记录当周事实，不能替代当前部署文档。
- 如果历史文档和上面的 source-of-truth 冲突，一律以上面的 source-of-truth 为准。
