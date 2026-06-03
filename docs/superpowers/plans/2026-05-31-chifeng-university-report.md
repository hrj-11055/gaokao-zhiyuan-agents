# Chifeng University (赤峰大学) Deep Research Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a high-quality, 8,000+ word deep research report on Chifeng University (recently renamed Chifeng University/赤峰大学), covering academic strength, admissions, employment, location, internationalization, campus life, and risks.

**Architecture:** Systematic research using Firecrawl CLI followed by iterative writing of report sections. Each section will be drafted with detailed analysis and data support.

**Tech Stack:** Firecrawl CLI for research, Google Search for supplemental data, Python/Markdown for report generation.

---

### Task 1: Deep Research Phase

**Files:**
- Create: `.firecrawl/chifeng_history.json`
- Create: `.firecrawl/chifeng_academics.json`
- Create: `.firecrawl/chifeng_admissions.json`
- Create: `.firecrawl/chifeng_employment.json`
- Create: `.firecrawl/chifeng_campus.json`

- [ ] **Step 1: Research historical evolution and renaming to 赤峰大学**
Run: `firecrawl search "赤峰学院 发展历史 2026 更名 赤峰大学 历程" --scrape -o .firecrawl/chifeng_history.json --json`

- [ ] **Step 2: Research academic strengths,硕士点, labs**
Run: `firecrawl search "赤峰大学 优势学科 硕士点 博士点 建设 重点实验室" --scrape -o .firecrawl/chifeng_academics.json --json`

- [ ] **Step 3: Gather admission data (2023-2025) for multiple provinces**
Run: `firecrawl search "赤峰大学 2025 2024 2023 录取分数线 位次 汇总 各省" --scrape -o .firecrawl/chifeng_admissions.json --json`

- [ ] **Step 4: Research employment quality and industry ties**
Run: `firecrawl search "赤峰大学 就业质量报告 2024 2025 全文 行业 薪资" --scrape -o .firecrawl/chifeng_employment.json --json`

- [ ] **Step 5: Research campus life, canteens, dorms, and reputation**
Run: `firecrawl search "赤峰大学 校园生活 宿舍 食堂 评价 知乎 贴吧" --scrape -o .firecrawl/chifeng_campus.json --json`

### Task 2: Draft Report - Academic Strength (1500+ words)

**Files:**
- Create: `大学深度研究报告_赤峰大学_2026版.md`

- [ ] **Step 1: Write history and evolution section**
- [ ] **Step 2: Write王牌专业 and academic resources section**
- [ ] **Step 3: Analyze学科布局 and future potential (博士点建设)**

### Task 3: Draft Report - Admissions & Students (1500+ words)

**Files:**
- Modify: `大学深度研究报告_赤峰大学_2026版.md`

- [ ] **Step 1: Detail 2023-2025 data across provinces**
- [ ] **Step 2: Analyze competitive provinces vs. high-value provinces**
- [ ] **Step 3: Compare different major groups' scores**

### Task 4: Draft Report - Graduate Outcomes & Economy (1500+ words)

**Files:**
- Modify: `大学深度研究报告_赤峰大学_2026版.md`

- [ ] **Step 1: Break down employment industries and salaries**
- [ ] **Step 2: Analyze local Chifeng industry ties (Medicine, Education, Mining/Archaeology)**
- [ ] **Step 3: Compare with peer institutions in Inner Mongolia**

### Task 5: Draft Report - Campus Life, Internationalization & Risks (1500+ words)

**Files:**
- Modify: `大学深度研究报告_赤峰大学_2026版.md`

- [ ] **Step 1: Detailed campus life description (Dorms, Canteens, Activities)**
- [ ] **Step 2: International cooperation and exchange programs**
- [ ] **Step 3: Identify risks and negative reputation factors**

### Task 6: Finalization & Evaluation (1000+ words)

**Files:**
- Modify: `大学深度研究报告_赤峰大学_2026版.md`

- [ ] **Step 1: Quantitative scoring (6 dimensions)**
- [ ] **Step 2: Lateral comparison with a similar school**
- [ ] **Step 3: Final candidate suggestions and wrap-up**
