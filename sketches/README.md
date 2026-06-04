# 峰哥咨询参考 — UI 改版设计方案 + GPT-Image 2 提示词

> 生成时间：2026-06-25
> 用途：配合 GPT-Image 2 进行视觉设计探索，选定方向后由 Hermes 实现代码

---

## 一、三个首页方案概览

| 方案 | 风格 | 核心理念 | 适合用户 | 原型文件 |
|------|------|---------|---------|---------|
| A 引导式 | 温暖安心 | 每屏一个行动，逐步引导 | 首次使用的焦虑型家长/考生 | `sketches/001-guided-warm/` |
| B 仪表盘 | 专业高效 | 可视化进度，一目了然 | 理性决策型用户 | `sketches/002-dashboard-pro/` |
| C 对话优先 | 轻量互动 | AI 对话即首页 | 熟悉聊天界面的年轻人 | `sketches/003-chat-first/` |

---

## 二、GPT-Image 2 提示词

### 使用说明

1. **有参考截图时**：先上传当前小程序截图，再用下面的提示词
2. **无参考截图时**：直接用提示词生成
3. GPT-Image 2 的提示词建议用英文，生成效果更稳定
4. 每个提示词可以单独使用，也可以组合微调

---

### 📱 首页方案 A：引导式（温暖安心）

#### 提示词 1 — 整体风格定义

```
A mobile app home screen design for a Chinese college admission counseling 
service called "峰哥咨询参考". The design should feel WARM, REASSURING, and 
TRUSTWORTHY — like a friendly counselor guiding you through an important life 
decision.

Visual direction:
- Primary color: warm orange (#F97316) for accents and CTAs
- Secondary color: soft blue (#93C5FD) for trust and safety
- Background: warm light gradient from #FFF7ED to #FFFBF5
- Cards: white with 20px rounded corners and soft shadows
- Typography: clean Chinese system font (PingFang SC style)
- NO emoji as icons — use simple line icons (SVG style)

Layout (top to bottom):
1. Greeting header: "你好，同学" in 24px bold + today's date
2. A 3-step progress indicator (horizontal): 填信息 → 做测评 → 得报告
   - Current step highlighted in orange with filled circle
   - Completed steps show green checkmark
   - Future steps are gray outlined
3. One large card (takes 60% of screen) showing ONLY the current step:
   - Step 1: Simple form with province dropdown, subject selector, score input
   - Large warm orange button: "保存并开始"
4. Small link at bottom: "也可以随时免费咨询 AI"

Style references: Apple Health app, Duolingo lesson flow, Headspace onboarding.
Mobile UI, iOS style, 375px width, light mode.
```

#### 提示词 2 — Step 2 测评进度状态

```
Mobile app screen showing the "assessment progress" step of a Chinese college 
counseling app. Warm, reassuring design style.

The screen shows a card with 3 assessment items stacked vertically:
1. "五环性格评测" — completed (green checkmark, gray text showing "已记录")
2. "MBTI 性格模型" — completed (green checkmark, showing "类型: INTJ")  
3. "霍兰德职业兴趣" — not yet done (orange arrow, "梳理职业兴趣方向")

Each item is a horizontal row with:
- Left: colored circle icon with line icon inside
- Middle: title (14px bold) + subtitle (12px gray)
- Right: status indicator (checkmark or arrow)

Below the list: a warm orange gradient button "查看我的测评结果"

Background: warm off-white #FFF7ED. Cards: white with soft shadow.
Style: iOS mobile, 375px width, minimalist, professional counseling feel.
```

---

### 📱 首页方案 B：仪表盘（专业高效）

#### 提示词 3 — 整体风格定义

```
A mobile app dashboard home screen for a Chinese college admission counseling 
service called "峰哥咨询参考". The design should feel PROFESSIONAL, EFFICIENT, 
and DATA-DRIVEN — like a well-designed control center for an important decision.

Visual direction:
- Primary color: deep blue (#2563EB) for professionalism
- Accent color: orange (#F97316) for action buttons only
- Background: pure white (#FFFFFF) with subtle gray borders
- Cards: flat design with 1px borders, NO shadows
- Typography: clean, with large bold numbers for data points (28px/800)
- Icons: solid colored circles with white line icons inside

Layout (top to bottom):
1. Header: blue square logo "峰" + "峰哥咨询参考" + notification bell icon
2. Profile summary card (compact): 
   "浙江 · 理科 · 632分 · 位次 18,425" + edit button
3. Circular progress ring (CSS conic-gradient style):
   - 5 segments in different shades of blue
   - Center text: "2/5" in 28px bold
   - Label below: "已完成 2 步，还需 3 步"
4. 2x2 action grid with colored icon circles:
   - AI 咨询 (blue) | 五环评测 (green)
   - MBTI 测试 (purple) | 霍兰德测试 (orange)
5. Bottom: full-width button "生成综合志愿报告" (disabled gray when incomplete)

Style references: Linear app dashboard, Notion sidebar, Apple Wallet cards.
Mobile UI, iOS style, 375px width, light mode, data-first.
```

#### 提示词 4 — 环形进度图特写

```
Close-up of a circular progress indicator for a mobile app, 200px diameter.
The ring is divided into 5 segments showing completion of 5 steps.

Completed segments (2 out of 5) are filled with a blue gradient (#2563EB to #1D4ED8).
Incomplete segments are light gray (#E2E8F0).

Center of the ring shows "2/5" in 28px extra-bold dark text.
Below the number: "已完成" in 12px gray text.

Below the ring, a horizontal legend showing 5 small dots with labels:
基本信息 ✓ | 高考成绩 ✓ | 意向偏好 | 能力测评 | 综合报告

Clean, flat design, white background, iOS mobile style.
```

---

### 📱 首页方案 C：对话优先（轻量互动）

#### 提示词 5 — 整体风格定义

```
A mobile chat-first home screen for a Chinese college admission counseling 
app called "峰哥咨询参考". The ENTIRE home screen IS a chat interface — 
there is no separate dashboard or form page.

Visual direction:
- Primary color: orange (#F97316) for CTAs and user bubbles
- Background: very light gray (#F9FAFB)
- AI chat bubbles: white, with small border-radius on left, large on right
- User chat bubbles: orange gradient, small border-radius on right, large on left
- NO shadows, NO glow effects — ultra minimal
- Quick reply buttons: pill-shaped with 1px border, white background

Layout:
1. Minimal header: left "峰哥咨询" in small text, right user avatar circle
2. User info tag bar (horizontal): "广东 · 物理类 · 580分 · 位次 23000" 
   in a rounded pill, clickable to expand
3. Chat messages area:
   - AI bubble: "你好，我是你的高考志愿 AI 咨询师。在开始之前，我先了解一下你的情况——你在哪个省份参加高考？"
   - Followed by 2-3 more AI messages asking questions naturally
4. Quick reply pills (horizontally scrollable):
   "580分能上什么大学" | "推荐适合我的专业" | "冲稳保怎么选"
5. Bottom input bar: rounded text input + orange circle send button
6. Floating bubble (bottom right): "还有 2 个测评可以帮你更精准 →"

Style references: ChatGPT mobile, WeChat chat, Apple Messages.
Mobile UI, iOS style, 375px width, conversation-first, minimal.
```

---

### 💬 Chat 页面改版提示词

#### 提示词 6 — 对话页面优化

```
A mobile chat interface for a Chinese college admission AI counselor app.

Improvements over current design:
- Cleaner AI avatar: replace emoji with a small rounded-square logo icon (not emoji)
- AI messages use rich text formatting with proper headers, bullet points, 
  and bold emphasis for key information
- User profile strip at top is more compact: single line with edit icon
- Add "typing indicator" (three animated dots) when AI is generating
- Action bar below AI messages: 🎧 朗读 | 📋 复制 | 👍 👎 (more subtle, smaller)
- AI disclaimer text ("AI 志愿咨询结果仅供参考") in very small gray text, 
  less prominent than current design

Visual:
- Background: light gradient (#F8FAFC to #EEF6FF)
- AI bubbles: white glass-morphism with very subtle border
- User bubbles: blue gradient (#2563EB)
- Input bar: frosted glass effect, rounded pill input field
- Send button: orange gradient circle, activates when text is typed

Mobile UI, iOS style, 375px width. Clean, professional, trustworthy.
```

---

### 📊 测评页面改版提示词

#### 提示词 7 — MBTI 测试页面

```
A mobile personality test (MBTI) interface for a Chinese college counseling app.

Current issues to fix: boring plain list of questions, no visual engagement.

New design:
- Top: progress bar showing current question / total (e.g., "12 / 60") 
  with smooth gradient fill
- Question card in center with large readable text (18px bold):
  "在社交聚会中，你通常会："
- Two answer option cards below (not radio buttons):
  - Option A: "主动与陌生人攀谈" (with subtle icon)
  - Option B: "更愿意和熟悉的朋友交流" (with subtle icon)
  - Selected option has orange border + light orange background
- Bottom: "上一题" and "下一题" navigation buttons
- Overall: calm blue-gray tones, not too playful, not too clinical

Mobile UI, iOS style, 375px width, card-based, encouraging but professional.
```

#### 提示词 8 — 测评结果页面

```
A mobile personality test result page for a Chinese college counseling app.

Shows MBTI test result "INTJ — 建筑师" with:
- Large type code "INTJ" in 48px bold with colorful gradient
- Type name "建筑师" below in 20px
- A radar/spider chart showing 4 dimension scores (I-E, N-S, T-F, J-P)
- Brief description card (3-4 lines)
- "推荐专业方向" section with 3-4 major cards:
  "计算机科学" "金融工程" "数学" each in a small pill/tag
- "适合的职业方向" section with tags
- Bottom CTA: "生成综合志愿报告" orange button
- Share button: "分享给家长查看"

Mobile UI, iOS style, 375px width. Celebration feel but not childish. 
Professional presentation of personal insights.
```

---

### 📋 问卷页面改版提示词

#### 提示词 9 — 五环问卷优化

```
A mobile questionnaire interface for a Chinese college admission app.

The "五环特征评测" (Five-Ring Character Assessment) asks about student's 
study habits, family background, and preferences.

Design improvements:
- Group questions by theme (学习习惯 / 家庭环境 / 个人偏好) with section headers
- Each question is a card with:
  - Question text (16px bold)
  - 5-point scale with emoji-free icons (1-5 circles, tap to select)
  - Or multiple choice with selectable tag pills
- Progress indicator at top: segmented bar (5 segments, each = one theme)
- Completion animation when finishing a section
- Estimated time remaining: "还需约 3 分钟"

Background: light warm gradient. Cards: white with subtle shadow.
Mobile UI, iOS style, 375px width. Encouraging, not tedious.
```

---

## 三、设计方案对比表

### 首页三个方案对比

| 维度 | A 引导式（温暖） | B 仪表盘（专业） | C 对话优先（轻量） |
|------|:---:|:---:|:---:|
| **信息密度** | 低 — 每屏只看一步 | 高 — 所有信息一屏 | 中 — 对话自然展开 |
| **认知负荷** | 最低 | 中等 | 低 |
| **首屏行动点** | 1 个 | 4+ 个 | 1 个（输入框） |
| **完成率预期** | 最高（强制引导） | 中等 | 取决于 AI 引导质量 |
| **适合新手** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **适合回头用户** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **开发复杂度** | 低 | 中（环形图） | 中（对话引擎） |
| **与现有代码差异** | 大（需重构首页） | 中（可复用卡片） | 大（需改首页逻辑） |
| **信任感** | 高（像有人引导） | 高（数据专业） | 中（可能感觉不够正式） |

---

## 四、如何使用这些提示词

### Step 1：先用 GPT-Image 2 生成方向图
1. 打开 ChatGPT，上传你小程序的当前截图
2. 复制上面的提示词（选你感兴趣的方向）
3. 在提示词前面加上：
   ```
   Based on this screenshot of my current mini-program, 
   please redesign it with the following direction:
   [粘贴提示词]
   ```

### Step 2：对比选择
1. 把 GPT-Image 生成的图和我的 HTML 原型放在一起看
2. 也可以直接在浏览器打开 HTML 原型：
   - 方案 A：`open sketches/001-guided-warm/index.html`
   - 方案 B：`open sketches/002-dashboard-pro/index.html`
   - 方案 C：`open sketches/003-chat-first/index.html`

### Step 3：确定方向后，告诉我
- 选哪个方案（A/B/C）
- 你从 GPT-Image 图中看到的喜欢的细节
- 我直接改小程序代码实现

---

## 五、推荐路径

**如果不确定选哪个，我推荐 A（引导式）**，理由：

1. 你的用户是高考生/家长 — 这是焦虑场景，越简单越好
2. 现有首页信息过多 — A 方案直接解决认知过载
3. 可以和 C 方案混合 — 首页用引导式，点「开始咨询」后进入对话式
4. 开发成本最低 — 主要是重组现有组件，不需要新写对话引擎

**混合方案建议**：A（首页引导）+ C 的对话体验（聊天页面）+ B 的进度可视化（测评中心）
