# Comprehensive Report Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Current implementation note: this is a historical execution plan. The live implementation now uses `https://gaokao.aicoming.cn`, member-gated report generation, PostgreSQL report data, DeepSeek report generation, and `SCORE_API_URL=http://159.75.110.157/score-api`. Use `docs/deployment/current-live-chain.md` before following any host or env value in this file.

**Goal:** 新增综合志愿报告生成功能：用户填写五环问卷（22 题）+ AI 对话记录作为数据源，调 Gemini Flash 生成个人化 HTML 报告，托管为可分享链接。

**Architecture:** 小程序新增问卷页（`pages/questionnaire`）和报告结果页（`pages/report`），问卷数据存 localStorage；proxy 新增 `POST /api/report/generate` 接口，读取预生成的专业/院校 `.md` 报告文件 + Dify 对话记录，拼接 prompt 调 Gemini Flash，把输出的 HTML 存为静态文件并返回 URL。

**Tech Stack:** UniApp Vue 3（小程序）、Express（proxy）、`@google/generative-ai` npm 包、Gemini 2.0 Flash API、Node.js `fs.promises`

**Spec:** `docs/superpowers/specs/2026-05-10-comprehensive-report-design.md`

---

## File Map

**新建：**
- `gaokao-miniprogram/src/pages/questionnaire/questionnaire.vue` — 22 题问卷页
- `gaokao-miniprogram/src/pages/report/report.vue` — 报告结果页（loading + 链接展示）
- `gaokao-proxy/lib/report-builder.js` — Gemini 调用 + 专业/院校报告匹配 + HTML 存盘

**修改：**
- `gaokao-miniprogram/src/utils/storage.js` — 新增 `saveQuestionnaire` / `loadQuestionnaire`
- `gaokao-miniprogram/src/pages.json` — 注册两个新页面
- `gaokao-miniprogram/src/pages/index/index.vue` — 新增报告入口卡片
- `gaokao-proxy/server.js` — 新增 `/api/report/generate` 端点 + 静态文件服务
- `gaokao-proxy/package.json` — 添加 `@google/generative-ai` 依赖
- `gaokao-proxy/.env.example` — 新增 5 个环境变量

---

## Task 1: questionnaire 存储函数

**Files:**
- Modify: `gaokao-miniprogram/src/utils/storage.js`

- [ ] **Step 1: 在 storage.js 末尾追加两个函数**

```js
const QUESTIONNAIRE_KEY = 'questionnaire'

/**
 * 保存问卷草稿（随时调用，允许部分填写）
 * @param {{ [id: string]: string | string[] }} answers
 */
export function saveQuestionnaire(answers) {
  const completed = Object.values(answers).filter(v => v !== '' && !(Array.isArray(v) && v.length === 0)).length
  uni.setStorageSync(QUESTIONNAIRE_KEY, JSON.stringify({
    answers,
    completedCount: completed,
    updatedAt: Date.now()
  }))
}

/**
 * 读取问卷草稿
 * @returns {{ answers: object, completedCount: number, updatedAt: number }}
 */
export function loadQuestionnaire() {
  const data = uni.getStorageSync(QUESTIONNAIRE_KEY)
  if (!data) return { answers: {}, completedCount: 0, updatedAt: 0 }
  try {
    return JSON.parse(data)
  } catch {
    return { answers: {}, completedCount: 0, updatedAt: 0 }
  }
}
```

- [ ] **Step 2: 验证 export 名称未冲突**

```bash
grep -n "saveQuestionnaire\|loadQuestionnaire\|QUESTIONNAIRE_KEY" gaokao-miniprogram/src/utils/storage.js
```

期望输出：3 行定义，无重复。

- [ ] **Step 3: Commit**

```bash
git add gaokao-miniprogram/src/utils/storage.js
git commit -m "feat: add saveQuestionnaire/loadQuestionnaire to storage"
```

---

## Task 2: 路由注册 + 首页入口卡片

**Files:**
- Modify: `gaokao-miniprogram/src/pages.json`
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

- [ ] **Step 1: 在 pages.json 的 pages 数组末尾追加两个路由**

在 `"path": "pages/chat/chat"` 块之后加：

```json
{
  "path": "pages/questionnaire/questionnaire",
  "style": {
    "navigationBarTitleText": "个人特质问卷",
    "navigationBarBackgroundColor": "#FFFFFF",
    "navigationBarTextStyle": "black"
  }
},
{
  "path": "pages/report/report",
  "style": {
    "navigationBarTitleText": "我的志愿报告",
    "navigationBarBackgroundColor": "#FFFFFF",
    "navigationBarTextStyle": "black"
  }
}
```

- [ ] **Step 2: 在 index.vue 的 `goChat` 函数前新增 `goQuestionnaire` 函数**

```js
function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}
```

- [ ] **Step 3: 在 index.vue 模板的「免费咨询」卡片（`.chat-entry`）之后插入报告入口卡片**

```html
<!-- 报告入口 -->
<view class="report-entry" @click="goQuestionnaire">
  <view class="report-entry-content">
    <text class="report-entry-title">生成个人报告</text>
    <text class="report-entry-sub">填写测评 · AI 深度分析 · 可转发家长</text>
  </view>
  <text class="report-entry-arrow">›</text>
</view>
```

- [ ] **Step 4: 在 index.vue 的 `<style>` 末尾追加报告入口样式**

```scss
.report-entry {
  width: 100%;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border-radius: $radius-lg;
  padding: 28rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
  box-sizing: border-box;
}

.report-entry-content {
  display: flex;
  flex-direction: column;
}

.report-entry-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}

.report-entry-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.report-entry-arrow {
  font-size: 46rpx;
  color: #fff;
}
```

- [ ] **Step 5: 编译验证（终端直接运行，不在 Claude Code 会话中）**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin 2>&1 | tail -5
```

期望：无编译错误。

- [ ] **Step 6: Commit**

```bash
git add gaokao-miniprogram/src/pages.json gaokao-miniprogram/src/pages/index/index.vue
git commit -m "feat: add report entry card to home page and register new routes"
```

---

## Task 3: 问卷页 questionnaire.vue

**Files:**
- Create: `gaokao-miniprogram/src/pages/questionnaire/questionnaire.vue`

- [ ] **Step 1: 创建文件，写入完整问卷页代码**

```vue
<template>
  <view class="page">
    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-info">
        <text class="progress-text">已完成 {{ completedCount }}/22 题</text>
        <text class="progress-pct">{{ Math.round(completedCount / 22 * 100) }}%</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: (completedCount / 22 * 100) + '%' }" />
      </view>
    </view>

    <!-- 环选项卡 -->
    <scroll-view class="ring-tabs" scroll-x>
      <view
        v-for="ring in rings"
        :key="ring.id"
        class="ring-tab"
        :class="{ 'ring-tab-active': currentRing === ring.id }"
        @click="goToRing(ring.id)"
      >
        第{{ ring.label }}环
      </view>
    </scroll-view>

    <!-- 当前题目 -->
    <view class="question-card">
      <text class="ring-label">第{{ currentQ.ringName }}环 · {{ currentQ.ringDisplayName }}</text>
      <text class="question-text">{{ currentQ.text }}</text>
      <text v-if="currentQ.maxSelect" class="max-select-hint">最多选 {{ currentQ.maxSelect }} 个</text>

      <!-- 选项列表 -->
      <view class="options-list">
        <view
          v-for="opt in currentQ.options"
          :key="opt"
          class="option-item"
          :class="isSelected(currentQ.id, opt) ? 'option-selected' : ''"
          @click="toggleOption(currentQ.id, opt, currentQ.type, currentQ.maxSelect)"
        >
          <view class="option-check">
            <text v-if="isSelected(currentQ.id, opt)" class="check-icon">✓</text>
          </view>
          <text class="option-text">{{ opt }}</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">上一题</view>
      <view v-if="currentIndex < QUESTIONS.length - 1" class="nav-btn next-btn" @click="next">下一题</view>
      <view v-else class="nav-btn next-btn" @click="next">完成</view>
    </view>

    <!-- 生成报告悬浮按钮 -->
    <view class="generate-btn" @click="onGenerate">
      <text class="generate-text">生成报告</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { saveQuestionnaire, loadQuestionnaire } from '../../utils/storage.js'

const QUESTIONS = [
  { id: 'q1', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '学习新内容时你更偏向？',
    options: ['先理解原理，再做题', '大量刷题，从中归纳规律', '跟着老师走，课后复习'] },
  { id: 'q2', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '遇到难题时你会？',
    options: ['反复拆解，直到搞懂', '先跳过，找会的做', '找同学或老师讨论'] },
  { id: 'q3', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '记公式和知识点时你更擅长？',
    options: ['用逻辑规律推导记忆', '反复抄写背诵', '做题时自然记住'] },
  { id: 'q4', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '上课时你通常？',
    options: ['紧跟老师思路认真记笔记', '自己推演，不喜欢抄', '听懂大意，课后再补'] },
  { id: 'q5', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '你最高效的学习时段？',
    options: ['早晨', '下午', '深夜'] },
  { id: 'q6', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'multi',
    text: '你的优势学科（可多选）',
    options: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'] },
  { id: 'q7', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'multi',
    text: '你的薄弱学科（可多选）',
    options: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'] },
  { id: 'q8', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'single',
    text: '你当前的主要压力来源？',
    options: ['来自同学竞争', '来自父母期望', '来自自我高要求', '备考本身的压力'] },
  { id: 'q9', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'single',
    text: '你的成绩在班级大概位置？',
    options: ['前 10%', '前 30%', '中等水平', '偏后'] },
  { id: 'q10', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'single',
    text: '父母的职业背景？',
    options: ['体制内（公务员/教师/医生）', '企业职员', '自营生意', '其他'] },
  { id: 'q11', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'multi',
    text: '家庭对专业选择的期望（可多选）',
    options: ['好就业', '收入高', '体面稳定', '尊重孩子兴趣', '没有明确要求'] },
  { id: 'q12', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'single',
    text: '家庭对就读城市的偏好？',
    options: ['本省优先', '北上广深', '不限制'] },
  { id: 'q13', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'single',
    text: '家庭经济状况？',
    options: ['宽裕', '小康', '普通', '偏紧'] },
  { id: 'q14', ring: 4, ringName: '第四', ringDisplayName: '能力特质', type: 'multi', maxSelect: 3,
    text: '你最突出的能力（最多选 3 个）',
    options: ['逻辑推理', '动手实验', '语言表达', '创意设计', '记忆背诵', '数据分析'] },
  { id: 'q15', ring: 4, ringName: '第四', ringDisplayName: '能力特质', type: 'multi',
    text: '你最感兴趣的领域（可多选）',
    options: ['理工技术', '医学健康', '人文社科', '商科管理', '艺术传媒', '法律政治'] },
  { id: 'q16', ring: 4, ringName: '第四', ringDisplayName: '能力特质', type: 'multi',
    text: '你最排斥的方向（可多选）',
    options: ['纯理论研究', '大量背诵', '对人服务', '户外体力工作', '高风险行业'] },
  { id: 'q17', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '什么让你最有成就感？',
    options: ['解出一道难题', '帮助了他人', '作品被认可', '团队协调成功', '赚到钱'] },
  { id: 'q18', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '工作中你最看重什么？',
    options: ['收入高', '稳定安全', '有意义有价值', '自由灵活', '社会地位'] },
  { id: 'q19', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '你更倾向于哪种工作方式？',
    options: ['独立深度工作', '团队协作项目'] },
  { id: 'q20', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '你最感兴趣的行业？',
    options: ['互联网/科技', '金融', '医疗', '教育', '制造/工程', '传媒/艺术', '政府/公务', '法律'] },
  { id: 'q21', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '毕业后你的首选方向？',
    options: ['直接就业', '国内考研', '出国留学', '考公/考编', '还没想好'] },
  { id: 'q22', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '你对工作城市的偏好？',
    options: ['回家乡', '留在读书城市', '去一线城市', '无所谓'] },
]

const rings = [
  { id: 1, label: '一' },
  { id: 2, label: '二' },
  { id: 3, label: '三' },
  { id: 4, label: '四' },
  { id: 5, label: '五' },
]

const RING_START_INDEX = { 1: 0, 2: 5, 3: 9, 4: 13, 5: 16 }

const currentIndex = ref(0)
const answers = ref({})

const currentQ = computed(() => QUESTIONS[currentIndex.value])
const currentRing = computed(() => currentQ.value.ring)
const completedCount = computed(() =>
  Object.entries(answers.value).filter(([, v]) => v !== '' && !(Array.isArray(v) && v.length === 0)).length
)

onShow(() => {
  const saved = loadQuestionnaire()
  answers.value = saved.answers || {}
})

function isSelected(id, opt) {
  const val = answers.value[id]
  if (!val) return false
  return Array.isArray(val) ? val.includes(opt) : val === opt
}

function toggleOption(id, opt, type, maxSelect) {
  if (type === 'single') {
    answers.value = { ...answers.value, [id]: opt }
    saveQuestionnaire(answers.value)
    // 单选自动跳下一题
    if (currentIndex.value < QUESTIONS.length - 1) {
      setTimeout(() => { currentIndex.value++ }, 200)
    }
    return
  }
  // multi
  const current = Array.isArray(answers.value[id]) ? [...answers.value[id]] : []
  const idx = current.indexOf(opt)
  if (idx === -1) {
    if (maxSelect && current.length >= maxSelect) {
      uni.showToast({ title: `最多选 ${maxSelect} 个`, icon: 'none' })
      return
    }
    current.push(opt)
  } else {
    current.splice(idx, 1)
  }
  answers.value = { ...answers.value, [id]: current }
  saveQuestionnaire(answers.value)
}

function prev() {
  if (currentIndex.value > 0) currentIndex.value--
}

function next() {
  if (currentIndex.value < QUESTIONS.length - 1) {
    currentIndex.value++
  } else {
    onGenerate()
  }
}

function goToRing(ringId) {
  currentIndex.value = RING_START_INDEX[ringId]
}

function onGenerate() {
  uni.navigateTo({ url: '/pages/report/report' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 24rpx 32rpx 200rpx;
  box-sizing: border-box;
}

.progress-bar-wrap {
  margin-bottom: 24rpx;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.progress-text, .progress-pct {
  font-size: 24rpx;
  color: $text-muted;
}

.progress-track {
  background: $border-light;
  border-radius: $radius-full;
  height: 8rpx;
}

.progress-fill {
  background: #7c3aed;
  border-radius: $radius-full;
  height: 8rpx;
  transition: width 0.3s;
}

.ring-tabs {
  white-space: nowrap;
  margin-bottom: 24rpx;
}

.ring-tab {
  display: inline-block;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  font-size: 24rpx;
  color: $text-muted;
  background: $bg-white;
  margin-right: 12rpx;
  border: 2rpx solid $border-light;
}

.ring-tab-active {
  background: #7c3aed;
  color: #fff;
  border-color: #7c3aed;
}

.question-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.ring-label {
  font-size: 22rpx;
  color: #7c3aed;
  font-weight: 600;
  display: block;
  margin-bottom: 12rpx;
}

.question-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
  margin-bottom: 8rpx;
  line-height: 1.5;
}

.max-select-hint {
  font-size: 22rpx;
  color: $text-muted;
  display: block;
  margin-bottom: 24rpx;
}

.options-list {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  border-radius: $radius-lg;
  border: 2rpx solid $border-light;
  background: $bg-page;
}

.option-selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}

.option-check {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 2rpx solid $border-light;
  background: $bg-white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .option-selected & {
    background: #7c3aed;
    border-color: #7c3aed;
  }
}

.check-icon {
  color: #fff;
  font-size: 20rpx;
}

.option-text {
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.4;
}

.footer {
  position: fixed;
  bottom: calc(120rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
  display: flex;
  gap: 16rpx;
}

.nav-btn {
  flex: 1;
  height: 80rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
}

.prev-btn {
  background: $bg-white;
  color: $text-secondary;
  border: 2rpx solid $border-light;
}

.next-btn {
  background: #7c3aed;
  color: #fff;
}

.disabled {
  opacity: 0.4;
}

.generate-btn {
  position: fixed;
  bottom: calc(32rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
  height: 88rpx;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(124, 58, 237, 0.4);
}

.generate-text {
  color: #fff;
  font-size: 32rpx;
  font-weight: 700;
}
</style>
```

- [ ] **Step 2: 编译验证**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin 2>&1 | tail -5
```

期望：无编译错误。

- [ ] **Step 3: Commit**

```bash
git add gaokao-miniprogram/src/pages/questionnaire/
git commit -m "feat: add questionnaire page with 22-question five-ring survey"
```

---

## Task 4: 报告结果页 report.vue

**Files:**
- Create: `gaokao-miniprogram/src/pages/report/report.vue`

- [ ] **Step 1: 创建文件**

```vue
<template>
  <view class="page">
    <!-- 生成中 -->
    <view v-if="status === 'loading'" class="state-card">
      <view class="loading-icon">⏳</view>
      <text class="state-title">AI 正在生成报告</text>
      <text class="state-sub">分析问卷 + 对话记录，约需 15-30 秒</text>
      <view class="loading-bar">
        <view class="loading-fill" />
      </view>
    </view>

    <!-- 成功 -->
    <view v-else-if="status === 'done'" class="state-card">
      <view class="success-icon">📊</view>
      <text class="state-title">报告已生成</text>
      <text class="state-sub">{{ sourceDesc }}</text>

      <view class="divider" />

      <view class="content-list">
        <text class="content-item">✓ 个人特质分析（五环框架）</text>
        <text class="content-item">✓ 专业匹配分析</text>
        <text class="content-item">✓ 专业深度研究</text>
        <text class="content-item">✓ 院校推荐（冲稳保）</text>
        <text class="content-item">✓ 综合志愿方案</text>
      </view>

      <view class="primary-btn" @click="copyLink">复制报告链接</view>
      <view class="secondary-btn" @click="openInBrowser">在浏览器中查看</view>
      <text class="hint-text">链接长期有效，可转发给家长查看</text>
    </view>

    <!-- 失败 -->
    <view v-else-if="status === 'error'" class="state-card">
      <view class="error-icon">⚠️</view>
      <text class="state-title">生成失败</text>
      <text class="state-sub">{{ errorMsg }}</text>
      <view class="primary-btn" @click="generate">重试</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { loadUserProfile, loadQuestionnaire, loadHistory } from '../../utils/storage.js'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001'

const status = ref('loading')
const reportUrl = ref('')
const errorMsg = ref('')

const completedQuestions = computed(() => {
  const { completedCount } = loadQuestionnaire()
  return completedCount || 0
})

const sourceDesc = computed(() => {
  const qCount = completedQuestions.value
  const hasChat = !!loadHistory().conversationId
  const parts = []
  if (qCount > 0) parts.push(`${qCount} 道问卷`)
  if (hasChat) parts.push('AI 对话记录')
  return parts.length > 0 ? `基于 ${parts.join(' + ')} 生成` : '基于考生基本信息生成'
})

onMounted(() => {
  generate()
})

async function generate() {
  status.value = 'loading'
  errorMsg.value = ''

  const profile = loadUserProfile()
  const { answers } = loadQuestionnaire()
  const { conversationId } = loadHistory()

  try {
    const res = await uni.request({
      url: `${API_BASE}/api/report/generate`,
      method: 'POST',
      data: {
        userId: profile.userId || ('user_' + Date.now()),
        profile,
        questionnaire: answers || {},
        conversationId: conversationId || '',
      },
      header: { 'Content-Type': 'application/json' },
      timeout: 120000,
    })

    if (res.statusCode !== 200 || !res.data.url) {
      throw new Error(res.data?.error || '服务暂时不可用')
    }

    reportUrl.value = res.data.url
    status.value = 'done'
  } catch (err) {
    status.value = 'error'
    errorMsg.value = err.message || '网络请求失败，请检查网络后重试'
  }
}

function copyLink() {
  uni.setClipboardData({
    data: reportUrl.value,
    success: () => uni.showToast({ title: '链接已复制', icon: 'success' })
  })
}

function openInBrowser() {
  // #ifdef MP-WEIXIN
  uni.navigateTo({ url: reportUrl.value })
  // #endif
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx 32rpx;
  box-sizing: border-box;
}

.state-card {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 64rpx 40rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.08);
}

.loading-icon, .success-icon, .error-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.state-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.state-sub {
  font-size: 26rpx;
  color: $text-muted;
  text-align: center;
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 8rpx;
  background: $border-light;
  border-radius: $radius-full;
  overflow: hidden;
}

.loading-fill {
  height: 8rpx;
  background: #7c3aed;
  border-radius: $radius-full;
  animation: loading-slide 2s ease-in-out infinite;
  width: 40%;
}

@keyframes loading-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}

.divider {
  width: 100%;
  height: 2rpx;
  background: $border-light;
  margin: 8rpx 0 28rpx;
}

.content-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 40rpx;
}

.content-item {
  font-size: 28rpx;
  color: $text-secondary;
}

.primary-btn {
  width: 100%;
  height: 88rpx;
  background: #7c3aed;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 20rpx;
}

.secondary-btn {
  width: 100%;
  height: 88rpx;
  background: $bg-white;
  border: 2rpx solid #7c3aed;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7c3aed;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 24rpx;
}

.hint-text {
  font-size: 24rpx;
  color: $text-muted;
  text-align: center;
}
</style>
```

- [ ] **Step 2: 编译验证**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add gaokao-miniprogram/src/pages/report/
git commit -m "feat: add report result page with loading/success/error states"
```

---

## Task 5: 安装 Gemini SDK

**Files:**
- Modify: `gaokao-proxy/package.json`

- [ ] **Step 1: 安装依赖**

```bash
cd gaokao-proxy && npm install @google/generative-ai
```

- [ ] **Step 2: 验证安装**

```bash
node -e "const {GoogleGenerativeAI} = require('@google/generative-ai'); console.log('ok')"
```

期望输出：`ok`

- [ ] **Step 3: Commit**

```bash
git add gaokao-proxy/package.json gaokao-proxy/package-lock.json
git commit -m "chore: add @google/generative-ai dependency to proxy"
```

---

## Task 6: report-builder.js

**Files:**
- Create: `gaokao-proxy/lib/report-builder.js`

- [ ] **Step 1: 创建 `gaokao-proxy/lib/` 目录并写入文件**

```js
'use strict'
const fs = require('fs').promises
const path = require('path')
const { GoogleGenerativeAI } = require('@google/generative-ai')

const MAJOR_REPORTS_DIR = process.env.MAJOR_REPORTS_DIR ||
  path.join(__dirname, '../../data/专业评估报告')
const UNIV_REPORTS_DIR = process.env.UNIV_REPORTS_DIR ||
  path.join(__dirname, '../../data/大学评估报告')
const REPORTS_DIR = process.env.REPORTS_DIR ||
  path.join(__dirname, '../reports')
const SCORE_API_URL = process.env.SCORE_API_URL || 'http://159.75.110.157/score-api'
const GEMINI_MODEL = process.env.GEMINI_MODEL || 'gemini-2.0-flash'

// 兴趣领域 → 专业门类代码前缀
const INTEREST_TO_CODES = {
  '理工技术': ['07', '08'],
  '医学健康': ['09', '10'],
  '人文社科': ['01', '05', '06'],
  '商科管理': ['02', '12'],
  '艺术传媒': ['05', '13'],
  '法律政治': ['03'],
}

// 目标行业 → 专业门类代码前缀
const INDUSTRY_TO_CODES = {
  '互联网/科技': ['08'],
  '金融': ['02', '12'],
  '医疗': ['10'],
  '教育': ['04'],
  '制造/工程': ['08'],
  '传媒/艺术': ['13'],
  '政府/公务': ['03', '12'],
  '法律': ['03'],
}

async function matchMajorReports(questionnaire) {
  const interests = Array.isArray(questionnaire.q15) ? questionnaire.q15 : []
  const industry = questionnaire.q20 || ''

  const codes = new Set()
  ;(INDUSTRY_TO_CODES[industry] || []).forEach(c => codes.add(c))
  interests.forEach(i => (INTEREST_TO_CODES[i] || []).forEach(c => codes.add(c)))

  if (codes.size === 0) return []

  let files
  try {
    files = await fs.readdir(MAJOR_REPORTS_DIR)
  } catch {
    return []
  }

  const matched = files
    .filter(f => f.endsWith('.md') && Array.from(codes).some(code => f.startsWith(code)))
    .slice(0, 3)

  return Promise.all(
    matched.map(async f => {
      const content = await fs.readFile(path.join(MAJOR_REPORTS_DIR, f), 'utf8')
      return `### 专业：${f.replace('.md', '')}\n${content.slice(0, 3000)}`
    })
  )
}

async function matchUnivReports(profile) {
  const { province, score, category } = profile || {}
  if (!province || !score) return []

  let univNames = []
  try {
    const url = `${SCORE_API_URL}/api/recommend?province=${encodeURIComponent(province)}&score=${score}&category=${encodeURIComponent(category || '')}&year=2024&limit=10`
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      univNames = (data.recommendations || [])
        .map(r => r.school_name || r.name)
        .filter(Boolean)
    }
  } catch {
    // Flask API 不可用时跳过
  }

  if (univNames.length === 0) return []

  let files
  try {
    files = await fs.readdir(UNIV_REPORTS_DIR)
  } catch {
    return []
  }

  const fileSet = new Set(files.map(f => f.replace('.md', '')))
  const matched = univNames.filter(name => fileSet.has(name)).slice(0, 5)

  return Promise.all(
    matched.map(async name => {
      const content = await fs.readFile(path.join(UNIV_REPORTS_DIR, `${name}.md`), 'utf8')
      return `### 院校：${name}\n${content.slice(0, 3000)}`
    })
  )
}

async function fetchDifyMessages(conversationId, difyApiUrl, difyApiKey) {
  if (!conversationId || !difyApiUrl || !difyApiKey) return []
  try {
    const res = await fetch(
      `${difyApiUrl}/v1/messages?conversation_id=${conversationId}&limit=50&user=report-gen`,
      {
        headers: { 'Authorization': `Bearer ${difyApiKey}` },
        signal: AbortSignal.timeout(5000),
      }
    )
    if (!res.ok) return []
    const data = await res.json()
    return (data.data || []).map(m => ({
      role: m.role === 'user' ? '用户' : 'AI',
      content: m.query || m.answer || '',
    }))
  } catch {
    return []
  }
}

function buildPrompt(profile, questionnaire, messages, majorReports, univReports) {
  const q = questionnaire || {}
  const arr = v => (Array.isArray(v) ? v.join('、') : v || '未作答')

  const msgText = messages.length > 0
    ? messages.slice(-20).map(m => `${m.role}：${m.content}`).join('\n')
    : '（暂无对话记录）'

  const majorText = majorReports.length > 0
    ? majorReports.join('\n\n')
    : '（暂无专业研究资料，请根据考生兴趣自行分析）'

  const univText = univReports.length > 0
    ? univReports.join('\n\n')
    : '（暂无院校研究资料，请根据考生分数自行推荐）'

  return `你是一位专业的高考志愿填报顾问，风格参考张雪峰：直接、有态度、给具体可操作的建议。根据以下考生完整信息，生成一份个人化的综合志愿分析 HTML 报告。

【考生基本信息】
省份：${profile.province || '未填写'} | 科目：${profile.category || '未填写'} | 分数：${profile.score || '未填写'} | 位次：${profile.rank || '未填写'}

【问卷答案（五环框架）】
第一环-学习风格：Q1=${q.q1 || '未作答'} | Q2=${q.q2 || '未作答'} | Q3=${q.q3 || '未作答'} | Q4=${q.q4 || '未作答'} | Q5=${q.q5 || '未作答'}
第二环-学业现状：优势科目=${arr(q.q6)} | 薄弱科目=${arr(q.q7)} | 压力来源=${q.q8 || '未作答'} | 班级位置=${q.q9 || '未作答'}
第三环-家庭背景：父母职业=${q.q10 || '未作答'} | 家庭期望=${arr(q.q11)} | 城市偏好=${q.q12 || '未作答'} | 经济状况=${q.q13 || '未作答'}
第四环-能力特质：突出能力=${arr(q.q14)} | 兴趣领域=${arr(q.q15)} | 排斥方向=${arr(q.q16)}
第五环-职业期望：成就感=${q.q17 || '未作答'} | 价值观=${q.q18 || '未作答'} | 工作方式=${q.q19 || '未作答'} | 目标行业=${q.q20 || '未作答'} | 毕业方向=${q.q21 || '未作答'} | 城市偏好=${q.q22 || '未作答'}

【AI 对话记录（最近 20 条）】
${msgText}

【专业深度研究资料（Tab 4 直接引用，不得编造数据）】
${majorText}

【院校深度研究资料（Tab 5 直接引用，不得编造数据）】
${univText}

输出要求：
- 直接输出完整 HTML 文本，不要任何代码块标记
- 包含 6 个 Tab：自我评估总结、个人特质分析、专业匹配分析、专业深度研究、大学深度研究、综合决策报告
- Tab 4 专业深度研究和 Tab 5 大学深度研究必须基于上方提供的预生成资料，内容具体
- 使用 ECharts（CDN: https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js）绘制六维能力雷达图
- 顶部深色渐变背景（#0f1419 → #1a2332），内容区白色圆角卡片
- Tab 切换用纯 JavaScript 实现`
}

async function generateReport({ profile, questionnaire, conversationId, difyApiUrl, difyApiKey }) {
  const [majorReports, univReports, messages] = await Promise.all([
    matchMajorReports(questionnaire),
    matchUnivReports(profile),
    fetchDifyMessages(conversationId, difyApiUrl, difyApiKey),
  ])

  const prompt = buildPrompt(profile, questionnaire, messages, majorReports, univReports)

  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)
  const model = genAI.getGenerativeModel({
    model: GEMINI_MODEL,
    generationConfig: { maxOutputTokens: 8192, temperature: 0.7 },
  })

  const result = await model.generateContent(prompt)
  return result.response.text()
}

async function saveReport(userId, html) {
  await fs.mkdir(REPORTS_DIR, { recursive: true })
  const filename = `${userId}-${Date.now()}.html`
  await fs.writeFile(path.join(REPORTS_DIR, filename), html, 'utf8')
  return filename
}

module.exports = { generateReport, saveReport, REPORTS_DIR }
```

- [ ] **Step 2: 语法验证**

```bash
cd gaokao-proxy && node -e "require('./lib/report-builder'); console.log('syntax ok')"
```

期望：`syntax ok`

- [ ] **Step 3: Commit**

```bash
git add gaokao-proxy/lib/report-builder.js
git commit -m "feat: add report-builder with Gemini call, major/univ matching, and HTML saving"
```

---

## Task 7: server.js — 新增报告端点

**Files:**
- Modify: `gaokao-proxy/server.js`

- [ ] **Step 1: 在 server.js 顶部引入 report-builder（在 `require('dotenv').config()` 之后的 require 块末尾）**

```js
const { generateReport, saveReport, REPORTS_DIR } = require('./lib/report-builder')
```

- [ ] **Step 2: 在 `const rateLimitBuckets = new Map()` 一行之后新增报告限流 Map**

```js
const reportCooldowns = new Map()  // userId → lastGeneratedAt timestamp
const REPORT_COOLDOWN_MS = 10 * 60 * 1000  // 10 分钟
```

- [ ] **Step 3: 在 `app.listen` 调用之前新增静态文件服务和报告端点**

```js
// 静态报告文件
app.use('/reports', require('express').static(REPORTS_DIR))

// 报告生成端点
app.post('/api/report/generate', async (req, res) => {
  const { userId, profile, questionnaire, conversationId } = req.body || {}

  if (!userId || typeof userId !== 'string' || userId.length > 128) {
    return res.status(400).json({ error: 'userId is required' })
  }

  // 10 分钟冷却
  const lastAt = reportCooldowns.get(userId) || 0
  if (Date.now() - lastAt < REPORT_COOLDOWN_MS) {
    const waitSec = Math.ceil((REPORT_COOLDOWN_MS - (Date.now() - lastAt)) / 1000)
    return res.status(429).json({ error: `请 ${waitSec} 秒后再试` })
  }

  reportCooldowns.set(userId, Date.now())

  try {
    const html = await generateReport({
      profile: profile || {},
      questionnaire: questionnaire || {},
      conversationId: conversationId || '',
      difyApiUrl: DIFY_API_URL,
      difyApiKey: DIFY_API_KEY,
    })

    const filename = await saveReport(userId, html)
    const baseUrl = process.env.REPORT_BASE_URL || `http://localhost:${PORT}`
    res.json({ url: `${baseUrl}/reports/${filename}` })
  } catch (err) {
    console.error('Report generation error:', err.message)
    reportCooldowns.delete(userId)  // 失败时重置冷却，允许重试
    res.status(500).json({ error: '报告生成失败，请稍后重试' })
  }
})
```

- [ ] **Step 4: 语法验证**

```bash
cd gaokao-proxy && DIFY_API_KEY=test node -e "require('./server')" 2>&1 | head -3
```

期望：打印 `Proxy server running on port ...`（服务器启动），无语法错误。按 Ctrl+C 退出。

- [ ] **Step 5: Commit**

```bash
git add gaokao-proxy/server.js
git commit -m "feat: add /api/report/generate endpoint and /reports static serving"
```

---

## Task 8: 更新 .env.example

**Files:**
- Modify: `gaokao-proxy/.env.example`

- [ ] **Step 1: 在 .env.example 末尾追加新变量**

```bash
# Report generation (Gemini)
# GEMINI_API_KEY=your-gemini-api-key
# GEMINI_MODEL=gemini-2.0-flash
# REPORT_BASE_URL=https://gaokao.aicoming.cn
# REPORTS_DIR=/var/www/reports
# MAJOR_REPORTS_DIR=/opt/gaokao-data/专业评估报告
# UNIV_REPORTS_DIR=/opt/gaokao-data/大学评估报告
# SCORE_API_URL=http://159.75.110.157/score-api
```

- [ ] **Step 2: Commit**

```bash
git add gaokao-proxy/.env.example
git commit -m "chore: document new env vars for report generation"
```

---

## Task 9: 端到端集成测试

- [ ] **Step 1: 启动 proxy 服务器（本地开发）**

在 `gaokao-proxy/.env` 中确认已设置 `GEMINI_API_KEY`，然后：

```bash
cd gaokao-proxy && npm run dev
```

- [ ] **Step 2: 用 curl 测试报告端点（新建终端）**

```bash
curl -s -X POST http://localhost:3001/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test_user_001",
    "profile": { "province": "广东", "category": "物理类", "score": 600 },
    "questionnaire": {
      "q1": "先理解原理，再做题",
      "q15": ["理工技术"],
      "q20": "互联网/科技",
      "q21": "国内考研"
    },
    "conversationId": ""
  }' | python3 -m json.tool
```

期望：返回 `{ "url": "http://localhost:3001/reports/test_user_001-XXXX.html" }`

- [ ] **Step 3: 在浏览器打开返回的 URL，验证 HTML 报告**

期望：
- 页面正常渲染，有顶部深色渐变
- 6 个 Tab 可切换
- ECharts 雷达图显示（可能需要等待 CDN 加载）
- 内容包含"广东"、"物理类"、"600"等考生信息

- [ ] **Step 4: 在微信开发者工具中验证小程序流程**

```
首页 → 点击"生成个人报告" → 问卷页（进度条 0/22）
→ 选择几道题（进度条更新）→ 点击"生成报告"
→ 报告结果页（loading 动画）→ 生成完成（显示链接）
→ 点击"复制报告链接" → 粘贴到浏览器验证 URL 可访问
```

- [ ] **Step 5: 验证 10 分钟冷却限制**

```bash
# 立即重复请求同一 userId
curl -s -X POST http://localhost:3001/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"userId":"test_user_001","profile":{},"questionnaire":{},"conversationId":""}' \
  | python3 -m json.tool
```

期望：返回 `429 { "error": "请 XXX 秒后再试" }`

- [ ] **Step 6: 最终 Commit**

```bash
git add .
git commit -m "feat: complete comprehensive report generation feature (questionnaire + Gemini + static hosting)"
```
