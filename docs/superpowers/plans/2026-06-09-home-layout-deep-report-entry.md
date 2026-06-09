# 首页排版与深度报告快捷入口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 放大首页主要内容并增加院校、专业深度报告双列快捷入口，减少底部无效留白。

**Architecture:** 仅修改现有首页 Vue 单文件组件，复用深度报告页已有的 `mode` 查询参数。使用现有 Python 源码合同测试保护文案和导航行为，不新增运行时状态。

**Tech Stack:** Vue 3 Composition API、UniApp、SCSS、Python unittest

---

### Task 1: 增加首页快捷入口合同测试

**Files:**
- Modify: `tests/test_miniprogram_report_flow.py`

- [ ] 增加断言，验证首页包含“院校深度报告”“专业深度报告”及确认后的说明文案。
- [ ] 增加断言，验证首页导航到 `deep-report-download?mode=university` 和 `deep-report-download?mode=major`。
- [ ] 运行对应测试，确认新断言在实现前失败。

### Task 2: 实现首页双列快捷入口与排版放大

**Files:**
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

- [ ] 在四步流程和报告 hero 后加入“深度报告库”双列入口。
- [ ] 增加统一的深度报告导航函数，传入 `university` 或 `major`。
- [ ] 为双列入口增加蓝色、橙色视觉样式。
- [ ] 放大品牌、进度、步骤与免责声明的字号和间距。
- [ ] 运行对应合同测试，确认通过。

### Task 3: 验证

**Files:**
- Verify: `gaokao-miniprogram/src/pages/index/index.vue`
- Verify: `tests/test_miniprogram_report_flow.py`

- [ ] 运行 `python3 -m unittest tests.test_miniprogram_report_flow`。
- [ ] 运行 `npm run dev:mp-weixin`，确认开发构建成功后停止进程。
- [ ] 检查最终 diff，确认没有覆盖工作区中原有的无关修改。
