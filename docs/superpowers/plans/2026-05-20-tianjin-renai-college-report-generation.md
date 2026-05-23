# 天津仁爱学院深度研究报告执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一篇 8000 字以上的天津仁爱学院深度研究报告。

**Architecture:** 采用分模块调研、分模块撰写、最终整合润色的策略。利用子代理（Sub-agents）并行处理学术、录取、就业、生活四大维度的深度数据挖掘，确保各章节字数充足且内容专业。

**Tech Stack:** Python (数据处理脚本), Google Search (历史数据), Firecrawl (官网内容提取), Markdown (报告输出)。

---

### Task 1: 学术资本与师资深度研究 (Module 1 & 5)

**Files:**
- Create: `tmp/research_academic.md`
- Test: 检查字数是否超过 2000 字，是否涵盖天大渊源、二级学院明细、顶级人才数据。

- [ ] **Step 1: 搜索 2024-2025 师资招聘及人才引进计划**
    - 关注 100 万年薪岗位明细。
- [ ] **Step 2: 深入挖掘 10 个二级学院的专业设置与实验室资源**
    - 特别是“精益智造产业学院”、“华为云学院鲲鹏中心”。
- [ ] **Step 3: 收集国际化合作数据**
    - 交换生、境外深造比例及具体去向高校。
- [ ] **Step 4: 撰写初稿并保存至 `tmp/research_academic.md`**

---

### Task 2: 录取生源与区位产业研究 (Module 2 & 4)

**Files:**
- Create: `tmp/research_admissions_location.md`
- Test: 验证是否包含 2023-2025 至少 5 个高考大省的分数位次对比表。

- [ ] **Step 1: 汇总 2023-2025 各省（天津、河北、山东、河南、江苏等）录取数据**
- [ ] **Step 2: 分析团泊新城区域规划及对学校实习就业的影响**
- [ ] **Step 3: 撰写初稿并保存至 `tmp/research_admissions_location.md`**

---

### Task 3: 毕业生出路深度分析 (Module 3)

**Files:**
- Create: `tmp/research_career.md`
- Test: 验证字数是否超过 1500 字，是否包含考研名校清单、重点就业企业清单。

- [ ] **Step 1: 提取 2024 届就业质量报告中的行业流向数据**
- [ ] **Step 2: 追踪 8.19% 深造率的具体去向（整理考取天大、南开等校的人数）**
- [ ] **Step 3: 撰写初稿并保存至 `tmp/research_career.md`**

---

### Task 4: 校园生态与风险提示 (Module 6 & 7)

**Files:**
- Create: `tmp/research_campus_risks.md`
- Test: 验证是否包含转专业政策细节、宿舍食堂真实评价、办学风险分析。

- [ ] **Step 1: 搜集学生对“转专业”、“二食堂”、“住宿条件”的真实社交平台反馈**
- [ ] **Step 2: 分析转设后的品牌风险及学费承受力问题**
- [ ] **Step 3: 撰写初稿并保存至 `tmp/research_campus_risks.md`**

---

### Task 5: 报告整合、润色与打分 (Module 8 & Overall)

**Files:**
- Create: `data/大学评估报告/13596_天津仁爱学院_深度研究报告.md`
- Test: 最终文件字数校验（>8000 字），Markdown 格式校验。

- [ ] **Step 1: 整合各模块内容，添加全局背景与 8 个标准模块标题**
- [ ] **Step 2: 进行六维打分（学术、出路、区位、国际化、生态、声誉）**
- [ ] **Step 3: 添加与同类院校（如天津中德、珠海科技学院）的横向对比分析**
- [ ] **Step 4: 扩充内容，确保字数达标且逻辑连贯，保存至最终路径**
