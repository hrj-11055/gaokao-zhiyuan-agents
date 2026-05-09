# 张雪峰高考志愿填报 Agent — 开发路线图

> 创建时间：2026-04-16
> 更新时间：2026-04-27（v2：按实际进度重写）
> 预计总工期：6 周（至 2026-05-25）

---

## 排期总览

```
Week 1 (04/14-04/20)  ██████████ ✅   基础设施 + Dify 智能体搭建
Week 2 (04/21-04/27)  ██████████ ✅   数据研究 80% + 小程序骨架
Week 3 (04/28-05/04)  ████░░░░░░ 五一  专业补齐 + 院校评估 + KB 上传
Week 4 (05/05-05/11)  ██████████ 核心  MVP 端到端联调（个人信息+报告）
Week 5 (05/12-05/18)  ████████░░ 收尾  质量验收 + MBTI/APSET 测评
Week 6 (05/19-05/25)  ██████░░░░ 上线  提审 + 种子用户运营
```

## 已知问题（影响 W4）

```
🔴 gaokao-api PG 连接断开 → W4 Day 1 修复
🔴 gaokao-proxy 未部署到服务器 → W4 Day 1 部署
🟡 proxy 缺报告生成接口 → W4 Day 2-3 新增
🟡 HTTPS + 备案域名确认 → W4 Day 1
```

## 依赖关系

```
[W1 ✅] 服务器 + Dify ──→ [W2 ✅] 对话页 + 小程序骨架
                                        │
[W3 五一] 专业补齐 + 院校评估 ──→ 知识库完善 ──┐
                                                │
[W4 核心] 基础设施修复 ──→ 个人信息页 ──┐       │
              │                         │       │
              └──→ proxy 报告接口 ──────┤       │
                                        │       │
              ┌─────────────────────────┘       │
              ▼                                 ▼
         Dify 报告 Workflow ──→ 报告页 UI ──→ MVP 端到端
                                              │
                                    ┌─────────┴──────────┐
                                    ▼                     ▼
                              [W5] 20题测试          [W5] MBTI/APSET
                              + Prompt调优           测评模块
                                    │                     │
                                    └─────────┬───────────┘
                                              ▼
                                    [W6] 提审 + 运营
```

## 当前进度（截至 04/27）

### 已完成
- ✅ 服务器环境（Dify 12 容器 + Nginx + HTTPS）
- ✅ Dify 智能体（9 节点 Workflow + DeepSeek-V3 + RAG）
- ✅ 张雪峰语料库 KB-1 + 金句库 KB-6
- ✅ 广东分数线 KB-2 + 专业百科 KB-3（668 条）
- ✅ 小程序脚手架（UniApp，appid 已注册）
- ✅ 首页 UI（品牌设计 + 免费咨询 + "即将上线"卡片）
- ✅ 对话页（SSE 流式 + 历史记录 + QuickQuestions）
- ✅ Node 代理服务器（本地，限流 + 校验 + 30s 超时）
- ✅ Flask 分数查询 API（gaokao-api，Docker 部署，但 PG 连接异常）

### 未完成（W3 任务）
- ⬜ 专业研究 248 条（经济学/法学/文学/工学/管理学/艺术学）
- ⬜ 院校评估（全国 1365 所，0%）
- ⬜ 知识库上传

### 未开始（W4+ 任务）
- ⬜ 服务器基础设施修复（gaokao-api PG + proxy 部署）
- ⬜ 个人信息表单页
- ⬜ Dify 报告 Workflow（新建应用）
- ⬜ 综合报告页 UI
- ⬜ 个人信息 → 对话上下文传递
- ⬜ 端到端联调
- ⬜ MBTI/APSET 测评模块
- ⬜ 20 题标准测试

## W4 MVP 端到端 — 详细拆解

### 用户流程

```
首页
 ├──→ 💬 免费咨询（已完成）
 │      └── 对话智能体（Dify SSE，带用户画像上下文）
 │
 ├──→ 📋 填写信息（新增）
 │      └── 个人信息表单 → 保存到 storage
 │              │
 │              └──→ 📊 生成报告（新增）
 │                      └── 报告页（预览+完整）
 │
 └──→ 📊 我的报告（新增）
        └── 如已填写信息 → 显示报告
            如未填写 → 引导去填写信息
```

### 新增页面/接口

| 类型 | 名称 | 说明 |
|------|------|------|
| 页面 | `pages/profile/profile.vue` | 个人信息表单 |
| 页面 | `pages/report/report.vue` | 综合报告（Markdown 渲染） |
| 接口 | `POST /api/report/generate` | 触发 Dify Workflow 生成报告 |
| 接口 | `GET /api/report/:id` | 查询已生成的报告 |
| Dify | 报告生成 Workflow（新应用） | 6 节点：查分→RAG专业→RAG院校→LLM生成 |
| 修改 | `dify.js` 增加 `inputs` 参数 | 对话时传入用户画像 |

### 日级排期

| 日期 | 上午 | 下午 | 晚上 |
|------|------|------|------|
| 05/05 | 修复 PG + 部署 proxy | 个人信息表单 UI | 表单校验 |
| 05/06 | inputs 透传 + Dify 变量 | 报告 Workflow 设计 | 联调 |
| 05/07 | proxy 报告接口 | 报告 Prompt v1 | 测试 |
| 05/08 | 报告页 UI + Markdown | 首页入口更新 | 端到端 |
| 05/09 | 5 画像测试 | Prompt v2 迭代 | 质量验证 |
| 05/10 | 边界 + Bug 修复 | 性能优化 | 回顾 |
| 05/11 | Buffer | Buffer | W5 准备 |

### 验收标准

- [ ] 小程序真机可对话（Dify SSE 流式正常）
- [ ] 对话智能体知道用户省份/分数（无需用户重复说）
- [ ] 用户可填写个人信息并保存
- [ ] 点击"生成报告"后 30s 内显示完整报告
- [ ] 报告含 5 个章节：画像 + 专业 + 院校 + 避坑 + 行动
- [ ] 报告数据来自真实分数线和专业研究（无编造）
- [ ] 免费预览显示摘要，完整内容前端遮罩

## 文档索引

| 文档 | 任务 | 状态 |
|------|------|------|
| [01-test-analysis.md](01-test-analysis.md) | Phase 2.1 测试分析 | ✅ |
| [02-kb2-integration.md](02-kb2-integration.md) | Phase 2.2 KB-2 接入 | ✅ |
| [03-prompt-tuning.md](03-prompt-tuning.md) | Phase 2.3 Prompt 调优 | ✅ |
| [04-knowledge-expansion.md](04-knowledge-expansion.md) | Phase 3.1 知识库补全 | 🔄 W3 |
| [05-multi-turn-dialog.md](05-multi-turn-dialog.md) | Phase 3.2 多轮对话优化 | ✅ |
| [06-safety-guardrails.md](06-safety-guardrails.md) | Phase 3.3 安全护栏 | ⬜ W5 |
| [07-intent-routing.md](07-intent-routing.md) | Phase 4.1 意图识别 | ⬜ W5 |
| [08-wechat-miniprogram.md](08-wechat-miniprogram.md) | Phase 4.2 小程序接入 | 🔄 进行中 |
| [09-analytics-dashboard.md](09-analytics-dashboard.md) | Phase 5.1 使用统计 | ⬜ W6 |
| [10-province-expansion.md](10-province-expansion.md) | Phase 5.2 省份扩展 | ⬜ W6 |
