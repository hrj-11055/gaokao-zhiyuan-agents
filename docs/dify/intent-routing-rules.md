# 高考咨询问题路由规则与 100 题分类样本

> 当前设计前提：学生进入聊天前，已经补齐 `province`、`category`、`score` 三个核心字段。聊天中允许用户更新分数、位次、地域、预算、兴趣、职业目标等画像字段。

## 路由总原则

分数线事实必须走结构化 HTTP/API，不交给模型猜，也不依赖 Dify 知识库碰运气。Dify 负责解释、取舍、组织语言和风格化咨询；API 负责录取线、位次、冲稳保、学校/专业分数事实。

## 路由类别

| 路由 | 典型问题 | 数据依赖 | 处理规则 |
|------|----------|----------|----------|
| `profile_update` | “我是广东物理类600分”“位次2万” | 本地/后端 profile | 抽取并更新画像；如果存在 pending 原问题，更新后继续处理原问题 |
| `direct_school_score_lookup` | “中山大学在广东多少分”“华工计算机多少位次” | `school_scores` API | 直接查学校/专业分数线；结构化回答；没返回就说未覆盖 |
| `direct_match_recommendation` | “600分能上什么学校”“帮我排冲稳保” | `score_match` API + 画像 | 先检查深度画像；齐全后查 2025 分数线，输出/交给 Dify 形成冲稳保建议 |
| `score_context_strategy` | “工科还是理科”“哪些专业别盲冲”“省内还是外省” | `score_match` API + Dify | 查 2025 分数线作为事实底座，但不直接吐冲稳保模板；交给 Dify 做咨询判断 |
| `general_policy_advice` | “什么是平行志愿”“专业组是什么意思” | Dify 知识库/模型 | 不查分数线 API；解释规则、概念、流程 |
| `school_major_info` | “南方医科大怎么样”“计算机学什么” | 报告库/专业库/Dify | 查院校/专业资料或 Dify 知识库；只有涉及分数时再附加 score API |
| `product_report_membership` | “报告在哪下载”“会员怎么开” | 业务 API | 走会员、报告、支付、客服路径，不转 Dify |
| `safety_support` | “保证我录取”“帮我改成绩”“我要崩溃了” | 安全/客服规则 | 拒绝保证或违规请求；焦虑类先安抚再给下一步；必要时提示人工客服 |

## 路由判定顺序

1. 先做安全与业务路由：违规、支付、报告、客服问题不要进 Dify 志愿咨询。
2. 抽取 profile 更新：省份、科类、分数、位次、预算、地域、兴趣、目标。
3. 如果是学校/专业分数线查询，走 `direct_school_score_lookup`。
4. 如果是最终学校推荐/冲稳保，走 `direct_match_recommendation`。
5. 如果是专业取舍、风险避坑、城市预算、就业策略，走 `score_context_strategy`。
6. 如果是概念、政策、流程解释，走 `general_policy_advice`。
7. 如果是学校/专业介绍，走 `school_major_info`。
8. 兜底：作为一般咨询进入 Dify，但禁止编造分数线。

## 100 个高频问题分类样本

| # | 高频问题 | 路由 |
|---|----------|------|
| 1 | 我是广东物理类600分，能上什么学校？ | `direct_match_recommendation` |
| 2 | 广东物理类590分，帮我排一下冲稳保。 | `direct_match_recommendation` |
| 3 | 物理类600分适合什么学校层次？ | `direct_match_recommendation` |
| 4 | 我这个分数能不能冲985？ | `direct_match_recommendation` |
| 5 | 这个分数上211有希望吗？ | `direct_match_recommendation` |
| 6 | 580分能报哪些公办本科？ | `direct_match_recommendation` |
| 7 | 我想优先广东省内，怎么填志愿？ | `direct_match_recommendation` |
| 8 | 广东600分稳妥学校有哪些？ | `direct_match_recommendation` |
| 9 | 我这个位次能不能冲中山大学？ | `direct_match_recommendation` |
| 10 | 分数刚过本科线，怎么保底？ | `direct_match_recommendation` |
| 11 | 中山大学在广东物理类多少分？ | `direct_school_score_lookup` |
| 12 | 华南理工计算机在广东最低位次是多少？ | `direct_school_score_lookup` |
| 13 | 南方医科大学口腔医学要多少分？ | `direct_school_score_lookup` |
| 14 | 深圳大学去年在广东投档线是多少？ | `direct_school_score_lookup` |
| 15 | 广东工业大学计算机录取线高吗？ | `direct_school_score_lookup` |
| 16 | 暨南大学在广东历史类最低分是多少？ | `direct_school_score_lookup` |
| 17 | 山东大学在广东物理类分数线是多少？ | `direct_school_score_lookup` |
| 18 | 武汉理工电子信息广东要多少位次？ | `direct_school_score_lookup` |
| 19 | 华东理工大学广东物理类专业分数线？ | `direct_school_score_lookup` |
| 20 | 北京师范大学心理学广东多少分？ | `direct_school_score_lookup` |
| 21 | 物理类更适合工科还是理科？ | `score_context_strategy` |
| 22 | 我数学物理还可以，选计算机还是电子信息？ | `score_context_strategy` |
| 23 | 普通家庭适不适合学金融？ | `score_context_strategy` |
| 24 | 哪些专业看起来体面但风险高？ | `score_context_strategy` |
| 25 | 生化环材到底能不能报？ | `score_context_strategy` |
| 26 | 医学、计算机、师范哪个更稳？ | `score_context_strategy` |
| 27 | 想留珠三角，专业应该怎么选？ | `score_context_strategy` |
| 28 | 预算敏感，要不要考虑中外合作？ | `score_context_strategy` |
| 29 | 民办本科值得读吗？ | `score_context_strategy` |
| 30 | 省内普通一本和外省211怎么选？ | `score_context_strategy` |
| 31 | 城市重要还是学校重要？ | `score_context_strategy` |
| 32 | 专业优先还是学校优先？ | `score_context_strategy` |
| 33 | 想考公，专业怎么选？ | `score_context_strategy` |
| 34 | 想本科就业，哪些专业更务实？ | `score_context_strategy` |
| 35 | 我不想考研，哪些专业要避开？ | `score_context_strategy` |
| 36 | 数学不好能学计算机吗？ | `score_context_strategy` |
| 37 | 女生学电气会不会吃亏？ | `score_context_strategy` |
| 38 | 物理类学法学合适吗？ | `score_context_strategy` |
| 39 | 历史类选法学、财经还是师范？ | `score_context_strategy` |
| 40 | 哪些选择看起来高大上但就业一般？ | `score_context_strategy` |
| 41 | 什么是平行志愿？ | `general_policy_advice` |
| 42 | 专业组是什么意思？ | `general_policy_advice` |
| 43 | 服从调剂是什么意思？ | `general_policy_advice` |
| 44 | 什么叫滑档和退档？ | `general_policy_advice` |
| 45 | 冲稳保比例怎么理解？ | `general_policy_advice` |
| 46 | 新高考和老高考志愿有什么区别？ | `general_policy_advice` |
| 47 | 院校专业组怎么填？ | `general_policy_advice` |
| 48 | 提前批是什么意思？ | `general_policy_advice` |
| 49 | 强基计划适合什么学生？ | `general_policy_advice` |
| 50 | 国家专项和地方专项有什么区别？ | `general_policy_advice` |
| 51 | 什么是一分一段表？ | `general_policy_advice` |
| 52 | 位次比分数更重要吗？ | `general_policy_advice` |
| 53 | 投档线和录取线有什么区别？ | `general_policy_advice` |
| 54 | 专业调剂会调到很差的专业吗？ | `general_policy_advice` |
| 55 | 怎么查学校招生计划？ | `general_policy_advice` |
| 56 | 计算机专业主要学什么？ | `school_major_info` |
| 57 | 电子信息类和通信工程有什么区别？ | `school_major_info` |
| 58 | 自动化专业就业怎么样？ | `school_major_info` |
| 59 | 临床医学和口腔医学怎么选？ | `school_major_info` |
| 60 | 法学专业是不是很卷？ | `school_major_info` |
| 61 | 会计学还有前途吗？ | `school_major_info` |
| 62 | 电气工程适合普通家庭吗？ | `school_major_info` |
| 63 | 人工智能专业是不是虚火？ | `school_major_info` |
| 64 | 数据科学和计算机哪个更好？ | `school_major_info` |
| 65 | 师范类专业还能报吗？ | `school_major_info` |
| 66 | 南方医科大学怎么样？ | `school_major_info` |
| 67 | 广东工业大学值得报吗？ | `school_major_info` |
| 68 | 深圳大学就业认可度怎么样？ | `school_major_info` |
| 69 | 华东理工大学强在哪？ | `school_major_info` |
| 70 | 西安电子科技大学适合去吗？ | `school_major_info` |
| 71 | 我的位次是20000，帮我记一下。 | `profile_update` |
| 72 | 我优先广东，不想去东北。 | `profile_update` |
| 73 | 家里预算一般，不考虑高收费。 | `profile_update` |
| 74 | 我能接受中外合作，但最好别太贵。 | `profile_update` |
| 75 | 我喜欢数学和物理。 | `profile_update` |
| 76 | 我讨厌生物化学。 | `profile_update` |
| 77 | 我想本科毕业直接就业。 | `profile_update` |
| 78 | 我未来想考研。 | `profile_update` |
| 79 | 父母在电力系统，有资源。 | `profile_update` |
| 80 | 我分数改成610分了。 | `profile_update` |
| 81 | 综合报告在哪里生成？ | `product_report_membership` |
| 82 | PDF 下载为什么要会员？ | `product_report_membership` |
| 83 | 会员多少钱？ | `product_report_membership` |
| 84 | 邀请码怎么用？ | `product_report_membership` |
| 85 | 我已经付款了为什么没解锁？ | `product_report_membership` |
| 86 | 报告生成失败怎么办？ | `product_report_membership` |
| 87 | 深度专业报告在哪里看？ | `product_report_membership` |
| 88 | 怎么联系客服？ | `product_report_membership` |
| 89 | 我能免费试看报告吗？ | `product_report_membership` |
| 90 | 会员可以下载几次 PDF？ | `product_report_membership` |
| 91 | 保证我一定录取。 | `safety_support` |
| 92 | 你直接告诉我哪个学校必中。 | `safety_support` |
| 93 | 帮我伪造成绩单。 | `safety_support` |
| 94 | 我太焦虑了，感觉完蛋了。 | `safety_support` |
| 95 | 我爸妈逼我报不喜欢的专业怎么办？ | `safety_support` |
| 96 | 我不想读大学了怎么办？ | `safety_support` |
| 97 | 能不能走关系进好学校？ | `safety_support` |
| 98 | 帮我骗家长说这个专业好。 | `safety_support` |
| 99 | 我对填志愿完全没方向。 | `general_policy_advice` |
| 100 | 你先带我一步步分析。 | `general_policy_advice` |

## 实现建议

### 后端路由

`gaokao-proxy` 应暴露一个纯函数，例如 `classifyGaokaoIntent(query, inputs)`，返回：

```js
{
  route: 'score_context_strategy',
  needsScoreApi: true,
  directAnswer: false,
  needsDify: true,
  needsProfileGate: false
}
```

### Dify 入参

进入 Dify 前统一注入：

- 当前时间：2026 年 6 月
- 服务对象：2026 年高考生
- 已知档案：省份、科类、分数、位次、预算、兴趣、地域、目标
- API 结果：仅 `direct_match_recommendation` 和 `score_context_strategy` 注入 2025 年分数线结果

### 测试要求

每个路由至少保留 10 个样本断言。尤其要固定以下边界：

- “中山大学在广东多少分”必须是 `direct_school_score_lookup`
- “600分能上什么学校”必须是 `direct_match_recommendation`
- “物理类更适合工科还是理科”必须是 `score_context_strategy`
- “什么是平行志愿”必须是 `general_policy_advice`
- “报告生成失败怎么办”必须是 `product_report_membership`
