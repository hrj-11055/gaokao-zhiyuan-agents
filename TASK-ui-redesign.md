# 任务：小程序 UI/IA 改版

## 状态：进行中

## 一句话描述
把首页从"4 个并列 CTA"改为"任务清单"模式，让新用户 3 秒内知道该做什么。

## 上下文文件
- 设计文档：`docs/superpowers/specs/2026-05-25-ui-redesign-design.md`（218 行）
- 实施计划：`docs/superpowers/plans/2026-05-25-ui-redesign.md`（1658 行，42 步，5 阶段）
- 首页代码：`gaokao-miniprogram/src/pages/index/index.vue`
- 报告页代码：`gaokao-miniprogram/src/pages/report/report.vue`
- 个人中心代码：`gaokao-miniprogram/src/pages/profile/profile.vue`
- 全局样式：`gaokao-miniprogram/src/uni.scss`
- 页面路由：`gaokao-miniprogram/src/pages.json`

## 当前进度
- [x] 设计文档撰写（任务清单式首页 + 三态报告页 + 个人中心瘦身）
- [x] 实施计划撰写（Phase 1-5，共 42 步）
- [x] Phase 1: tabbar 改造（首页/报告/我的）
- [ ] Phase 2: 首页任务清单（4 步进度卡 + 展开折叠）
- [ ] Phase 3: 报告 tab（未解锁/已就绪/已解锁 三态）
- [ ] Phase 4: 我的 tab（标准个人中心）
- [ ] Phase 5: 清理收尾（删废弃页面、换 icon）

## 下一步
执行 Phase 2 Task 2.1：提取「4 步进度」composable

## 关键决策
- 2026-05-25: 首页用"任务清单"结构，不用 dashboard → 新用户一眼看懂全流程
- 2026-05-25: 取消"测评"tab，测评变成首页第 3 步的子任务 → 减少 tab 数量，降低选择焦虑
- 2026-05-25: 付费引导从"我的"迁到"报告"tab → 用户想看报告时才被引导付费，更自然
- 2026-05-25: 同一时刻只有 1 个橙色 CTA → 聚焦当前步骤

## 阻塞 / 依赖
- 无

## 约束 / 注意事项
- 不要动后端代码（gaokao-proxy、gaokao-api）
- 不要动 data/ 目录
- 所有数据来源保持现有的 composable/store，不新增 API
- 构建命令：`cd gaokao-miniprogram && npm run dev:mp-weixin`
- 测试：微信开发者工具加载 `dist/dev/mp-weixin`
- 主色：橙色 #F97316，蓝色 #2563EB
