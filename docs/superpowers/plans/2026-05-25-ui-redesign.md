# 小程序 UI/IA 改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Historical note: this plan reflects the 2026-05-25 implementation pass. Do not use its embedded price or invite-count snippets as the current source of truth; use `docs/deployment/current-live-chain.md` and `docs/deployment/mvp-next-todo-2026-05-28.md`.

**Goal:** 把现有「四个并列 CTA」的首页改造为「任务清单首页」，并把报告 tab/我的 tab 配套重写。新人打开小程序 3 秒内能说出「我要做 4 件事」，当前报告转化路径以 19.9 元和 5 人邀请为准。

**Architecture:** 改造 `pages.json` 把测评 tab 从 tabbar 移除（保留页面供子路由访问）。重写 `index.vue` 为基于进度状态的任务清单。重写 `report.vue` 为三态视图（未解锁/已就绪未付费/已解锁）。瘦身 `profile.vue` 为标准个人中心。所有数据来源仍是现有的 `loadUserProfile/loadAssessments/loadQuestionnaire` + Pinia `useMembershipStore`，无需后端改动。

**Tech Stack:** UniApp + Vue 3 (Composition API) + Pinia + Sass。构建命令 `npm run build:mp-weixin`，开发预览 `npm run dev:mp-weixin` + 微信开发者工具加载 `dist/dev/mp-weixin`。

**Spec:** `docs/superpowers/specs/2026-05-25-ui-redesign-design.md`

**No test framework on the frontend.** Each task ends with a manual DevTools visual check + commit.

---

## File Structure

新增 / 修改的文件：

| 文件 | 操作 | 责任 |
|------|------|------|
| `gaokao-miniprogram/src/pages.json` | 改 | tabbar 由 3 项改为 `首页/报告/我的`；测评页路由保留 |
| `gaokao-miniprogram/src/composables/useHomeProgress.js` | 新 | 计算「4 步进度状态」的纯函数 composable |
| `gaokao-miniprogram/src/pages/index/index.vue` | 重写 template + style | 进度卡 + 4 步骤卡（含展开形态） |
| `gaokao-miniprogram/src/pages/report/report.vue` | 重写 template + style | 三态视图（未解锁/已就绪未付费/已解锁） |
| `gaokao-miniprogram/src/pages/profile/profile.vue` | 重写 template + style | 个人中心：头像 + 信息卡 + 两组菜单 |
| `gaokao-miniprogram/src/pages/assessments/assessments.vue` | 不改 | 由 tab 进入改为「我的 → 我的测评结果」子页进入 |

复用的现有 API（**不要改这些**）：

- `src/utils/storage.js` — `loadUserProfile / saveUserProfile / loadAssessments / loadQuestionnaire / QUESTIONNAIRE_REQUIRED_COUNT / isProfileComplete`
- `src/stores/membership.js` — `useMembershipStore`（含 `isActive / effectiveInviteCount / requiredInviteCount / login / loadStatus / openMembership`）
- `src/components/ChatBubble.vue`、`QuickQuestions.vue` — 不动

---

## Phase 1 · Foundation

### Task 1.1: tabbar 改造

**Files:**
- Modify: `gaokao-miniprogram/src/pages.json`

- [ ] **Step 1: 改 tabbar，把测评 tab 替换为报告 tab**

修改 `tabBar.list` 数组：

```json
"tabBar": {
  "color": "#9CA3AF",
  "selectedColor": "#F97316",
  "backgroundColor": "#FFFFFF",
  "borderStyle": "white",
  "list": [
    {
      "pagePath": "pages/index/index",
      "text": "首页",
      "iconPath": "static/tabbar/home.png",
      "selectedIconPath": "static/tabbar/home-active.png"
    },
    {
      "pagePath": "pages/report/report",
      "text": "报告",
      "iconPath": "static/tabbar/assess.png",
      "selectedIconPath": "static/tabbar/assess-active.png"
    },
    {
      "pagePath": "pages/profile/profile",
      "text": "我的",
      "iconPath": "static/tabbar/profile.png",
      "selectedIconPath": "static/tabbar/profile-active.png"
    }
  ]
}
```

注意：暂时复用 `assess.png / assess-active.png` 作为「报告」icon，后续可换。

- [ ] **Step 2: 构建并预览**

```bash
cd gaokao-miniprogram
npm run dev:mp-weixin
```

在微信开发者工具加载 `dist/dev/mp-weixin`。检查：底部 tabbar 是「首页 / 报告 / 我的」三项，点「报告」能进入 report 页（即使报告页内容现在还是旧版）。

- [ ] **Step 3: 提交**

```bash
git add gaokao-miniprogram/src/pages.json
git commit -m "feat(ia): tabbar 由 3 项改为 首页/报告/我的"
```

---

## Phase 2 · 首页 任务清单

### Task 2.1: 提取「4 步进度」composable

**Files:**
- Create: `gaokao-miniprogram/src/composables/useHomeProgress.js`

- [ ] **Step 1: 创建 composable 文件**

```javascript
// gaokao-miniprogram/src/composables/useHomeProgress.js
import { computed, ref } from 'vue'
import {
  loadUserProfile,
  loadAssessments,
  loadQuestionnaire,
  isProfileComplete,
  loadHistory,
  QUESTIONNAIRE_REQUIRED_COUNT,
} from '../utils/storage.js'

// 步骤状态枚举
export const StepStatus = {
  DONE: 'done',
  ACTIVE: 'active',
  LOCKED: 'locked',
}

// 步骤 2「已聊过」的阈值：用户至少有过 1 轮 user 提问
const CHAT_DONE_MIN_USER_MESSAGES = 1

export function useHomeProgress() {
  const profile = ref(loadUserProfile())
  const assessments = ref(loadAssessments())
  const questionnaire = ref(loadQuestionnaire())
  const chatRounds = ref(countUserMessages())

  function refresh() {
    profile.value = loadUserProfile()
    assessments.value = loadAssessments()
    questionnaire.value = loadQuestionnaire()
    chatRounds.value = countUserMessages()
  }

  function countUserMessages() {
    try {
      const history = loadHistory() || {}
      // history 结构：{ [conversationId]: messages[] }
      let total = 0
      Object.values(history).forEach((msgs) => {
        if (!Array.isArray(msgs)) return
        total += msgs.filter((m) => m && m.role === 'user').length
      })
      return total
    } catch {
      return 0
    }
  }

  const step1Done = computed(() => isProfileComplete(profile.value))
  const step2Done = computed(() => chatRounds.value >= CHAT_DONE_MIN_USER_MESSAGES)
  const questionnaireDone = computed(
    () => questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT
  )
  const mbtiDone = computed(() => assessments.value.mbti.completed)
  const hollandDone = computed(() => assessments.value.holland.completed)
  const step3Count = computed(() => {
    let n = 0
    if (questionnaireDone.value) n++
    if (mbtiDone.value) n++
    if (hollandDone.value) n++
    return n
  })
  const step3Done = computed(() => step3Count.value === 3)

  // 步骤 4 的「done」由 membership store 决定（此 composable 只算前 3 步）
  const completedSteps = computed(() => {
    let n = 0
    if (step1Done.value) n++
    if (step2Done.value) n++
    if (step3Done.value) n++
    return n
  })

  function statusFor(stepIndex) {
    // 锁定逻辑：只要上一步未完成，本步即 locked
    if (stepIndex === 1) {
      return step1Done.value ? StepStatus.DONE : StepStatus.ACTIVE
    }
    if (stepIndex === 2) {
      if (!step1Done.value) return StepStatus.LOCKED
      return step2Done.value ? StepStatus.DONE : StepStatus.ACTIVE
    }
    if (stepIndex === 3) {
      if (!step2Done.value) return StepStatus.LOCKED
      return step3Done.value ? StepStatus.DONE : StepStatus.ACTIVE
    }
    if (stepIndex === 4) {
      if (!step3Done.value) return StepStatus.LOCKED
      return StepStatus.ACTIVE // 步骤 4 done 与否在调用方判断（结合 membership）
    }
    return StepStatus.LOCKED
  }

  // 提示下一项未完成的测评：questionnaire → mbti → holland
  const nextAssessment = computed(() => {
    if (!questionnaireDone.value) return 'questionnaire'
    if (!mbtiDone.value) return 'mbti'
    if (!hollandDone.value) return 'holland'
    return null
  })

  return {
    profile,
    assessments,
    questionnaire,
    chatRounds,
    refresh,
    statusFor,
    step1Done,
    step2Done,
    step3Done,
    questionnaireDone,
    mbtiDone,
    hollandDone,
    step3Count,
    completedSteps,
    nextAssessment,
  }
}
```

- [ ] **Step 2: 构建确认无语法错误**

```bash
cd gaokao-miniprogram && npm run build:mp-weixin
```

期望：构建成功，无错误（首页还在用旧代码，所以视觉无变化）。

- [ ] **Step 3: 提交**

```bash
git add gaokao-miniprogram/src/composables/useHomeProgress.js
git commit -m "feat(home): 新增 useHomeProgress composable"
```

---

### Task 2.2: 重写首页 template + script

**Files:**
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

- [ ] **Step 1: 备份当前 index.vue 到 .superpowers/legacy/**

```bash
mkdir -p .superpowers/legacy
cp gaokao-miniprogram/src/pages/index/index.vue .superpowers/legacy/index.vue.bak
```

（备份是为了视觉走查时随时对照，**不入 git**。`.superpowers/` 已在 gitignore 范围内，如果没有请加上。）

- [ ] **Step 2: 全量重写 template 块**

替换 `index.vue` 的 `<template>` 整段为：

```vue
<template>
  <view class="page">
    <!-- 轻量背景 -->
    <view class="bg-glow-soft" />

    <!-- 顶部品牌 + 招呼 -->
    <view class="brand">
      <view class="logo">
        <image class="logo-img" src="/static/logo.png" mode="aspectFit" />
      </view>
      <text class="brand-name">峰哥咨询参考</text>
      <text class="brand-greet">{{ greetingText }}</text>
    </view>

    <!-- 顶部进度卡 -->
    <view class="progress-card" :class="{ ready: isReady }">
      <view class="progress-top">
        <text class="progress-label">我的志愿报告</text>
        <text class="progress-hint">{{ progressHint }}</text>
      </view>
      <view class="progress-stat">
        <text class="progress-frac">{{ completedSteps }}<text class="progress-total"> / 4 步</text></text>
      </view>
      <view class="progress-bar"><view class="progress-fill" :style="{ width: progressPercent + '%' }" /></view>
    </view>

    <!-- 步骤 1: 基础信息 -->
    <view class="step" :class="step1ClassObj" @click="onClickStep1">
      <view class="step-icon">{{ step1IconText }}</view>
      <view class="step-body">
        <text class="step-title">填写基础信息</text>
        <text class="step-desc">{{ step1DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>

    <!-- 步骤 2: 和峰哥聊聊 -->
    <view class="step" :class="step2ClassObj" @click="onClickStep2">
      <view class="step-icon">{{ step2IconText }}</view>
      <view class="step-body">
        <text class="step-title">和峰哥聊聊志愿</text>
        <text class="step-desc">{{ step2DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>

    <!-- 步骤 3: 3 项测评（active 时展开） -->
    <view v-if="step3Status !== 'active'" class="step" :class="step3ClassObj" @click="onClickStep3">
      <view class="step-icon">{{ step3IconText }}</view>
      <view class="step-body">
        <text class="step-title">3 项性格测评</text>
        <text class="step-desc">{{ step3DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>
    <view v-else class="step step-active step-expanded">
      <view class="step-top-row">
        <view class="step-icon active-icon">3</view>
        <view class="step-body">
          <text class="step-title">完成 3 项测评</text>
          <text class="step-desc active-desc">让报告更准确 · 已完成 {{ step3Count }}/3</text>
        </view>
      </view>
      <view class="chips">
        <view class="chip" :class="{ done: questionnaireDone, next: nextAssessment === 'questionnaire' }">
          <text class="chip-label">五环</text>
          <text class="chip-status">{{ chipStatus('questionnaire') }}</text>
        </view>
        <view class="chip" :class="{ done: mbtiDone, next: nextAssessment === 'mbti' }">
          <text class="chip-label">MBTI</text>
          <text class="chip-status">{{ chipStatus('mbti') }}</text>
        </view>
        <view class="chip" :class="{ done: hollandDone, next: nextAssessment === 'holland' }">
          <text class="chip-label">霍兰德</text>
          <text class="chip-status">{{ chipStatus('holland') }}</text>
        </view>
      </view>
      <view class="step-cta" @click.stop="onContinueAssessment">
        <text class="step-cta-text">{{ nextAssessmentCtaText }}</text>
      </view>
    </view>

    <!-- 步骤 4: 生成报告 -->
    <view class="step" :class="step4ClassObj" @click="onClickStep4">
      <view class="step-icon">{{ step4IconText }}</view>
      <view class="step-body">
        <text class="step-title">生成志愿报告</text>
        <text class="step-desc">{{ step4DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>

    <!-- 已就绪时底部的报告 hero -->
    <view v-if="step3Done && !membershipStore.isActive" class="report-hero" @click="goReport">
      <view class="report-hero-glow" />
      <view class="report-hero-content">
        <view class="report-hero-text">
          <text class="report-hero-title">志愿报告已就绪</text>
          <text class="report-hero-price"><text class="report-hero-currency">¥</text>29</text>
          <text class="report-hero-sub">19.9 元一次解锁 · 或邀请 5 人免费 ({{ membershipStore.effectiveInviteCount }}/5)</text>
        </view>
        <text class="report-hero-icon">📋</text>
      </view>
      <view class="report-hero-cta">立即生成报告 →</view>
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">
      <text class="disclaimer-text">结果仅供志愿填报参考，请以各省教育考试院和高校官方信息为准。</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
    </view>
  </view>
</template>
```

- [ ] **Step 3: 全量重写 script 块**

替换 `<script setup>` 整段为：

```vue
<script setup>
import { computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useHomeProgress, StepStatus } from '../../composables/useHomeProgress.js'
import { useMembershipStore } from '../../stores/membership.js'

const membershipStore = useMembershipStore()
const {
  profile,
  refresh,
  statusFor,
  step1Done,
  step2Done,
  step3Done,
  step3Count,
  completedSteps,
  questionnaireDone,
  mbtiDone,
  hollandDone,
  chatRounds,
  nextAssessment,
} = useHomeProgress()

// === 进度卡 ===
const isReady = computed(() => step3Done.value)
const progressPercent = computed(() => Math.round((completedSteps.value / 4) * 100))
const progressHint = computed(() => {
  if (completedSteps.value === 0) return '从第 1 步开始'
  if (completedSteps.value === 4) return '已生成报告'
  if (step3Done.value) return '准备就绪'
  return `还差 ${4 - completedSteps.value - (membershipStore.isActive ? 0 : 0)} 步`
})

// === 招呼语 ===
const greetingText = computed(() => {
  if (!step1Done.value) return '你好，先花 30 秒了解一下吧'
  const tail = step3Done.value ? '已就绪' : `已完成 ${completedSteps.value}/4`
  const cat = profile.value.category ? profile.value.category.replace('类', '') : ''
  return `${profile.value.province} · ${cat} · ${profile.value.score}分 · ${tail}`
})

// === 每个步骤的状态 / class / icon / desc ===
const step1Status = computed(() => statusFor(1))
const step2Status = computed(() => statusFor(2))
const step3Status = computed(() => statusFor(3))
const step4Status = computed(() => {
  if (!step3Done.value) return StepStatus.LOCKED
  return membershipStore.isActive ? StepStatus.DONE : StepStatus.ACTIVE
})

function classObj(status) {
  return {
    'step-done': status === StepStatus.DONE,
    'step-active': status === StepStatus.ACTIVE,
    'step-locked': status === StepStatus.LOCKED,
  }
}
const step1ClassObj = computed(() => classObj(step1Status.value))
const step2ClassObj = computed(() => classObj(step2Status.value))
const step3ClassObj = computed(() => classObj(step3Status.value))
const step4ClassObj = computed(() => classObj(step4Status.value))

const step1IconText = computed(() => (step1Status.value === StepStatus.DONE ? '✓' : '1'))
const step2IconText = computed(() =>
  step2Status.value === StepStatus.DONE ? '✓' : step2Status.value === StepStatus.LOCKED ? '🔒' : '2'
)
const step3IconText = computed(() =>
  step3Status.value === StepStatus.DONE ? '✓' : step3Status.value === StepStatus.LOCKED ? '🔒' : '3'
)
const step4IconText = computed(() =>
  step4Status.value === StepStatus.DONE ? '✓' : step4Status.value === StepStatus.LOCKED ? '🔒' : '4'
)

const step1DescText = computed(() => {
  if (step1Done.value) {
    const cat = profile.value.category ? profile.value.category : ''
    return `${profile.value.province} · ${cat} · ${profile.value.score}分`
  }
  return '省份、科目、分数 · 30 秒'
})

const step2DescText = computed(() => {
  if (step2Status.value === StepStatus.LOCKED) return '完成上一步后开始'
  if (step2Done.value) return `已聊 ${chatRounds.value} 轮 · 点击继续`
  return 'AI 帮你理清楚专业方向'
})

const step3DescText = computed(() => {
  if (step3Status.value === StepStatus.LOCKED) return '完成上一步后开始'
  if (step3Done.value) {
    const tags = []
    if (questionnaireDone.value) tags.push('五环')
    if (mbtiDone.value) tags.push('MBTI')
    if (hollandDone.value) tags.push('霍兰德')
    return `${tags.join(' / ')} 已记录`
  }
  return `让报告更准确 · 已完成 ${step3Count.value}/3`
})

const step4DescText = computed(() => {
  if (step4Status.value === StepStatus.LOCKED) return '完成测评后解锁'
  if (membershipStore.isActive) return '已生成 · 点击查看'
  return '¥19.9 一次解锁 · 邀请 5 人免费'
})

function chipStatus(key) {
  if (key === 'questionnaire') return questionnaireDone.value ? '✓' : nextAssessment.value === 'questionnaire' ? '→' : '—'
  if (key === 'mbti') return mbtiDone.value ? '✓' : nextAssessment.value === 'mbti' ? '→' : '—'
  if (key === 'holland') return hollandDone.value ? '✓' : nextAssessment.value === 'holland' ? '→' : '—'
  return '—'
}

const nextAssessmentCtaText = computed(() => {
  switch (nextAssessment.value) {
    case 'questionnaire':
      return '继续 五环测评 →'
    case 'mbti':
      return '继续 MBTI 测评 →'
    case 'holland':
      return '继续 霍兰德测评 →'
    default:
      return '查看测评结果 →'
  }
})

// === 跳转处理 ===
function onClickStep1() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire?focusProfile=1' })
  // 注：questionnaire 页本身不负责改 profile；这里临时复用为入口。
  // 如果有专门的「编辑基础信息」页面，请改成对应路由。
  // 现状下「填写基础信息」就是 index 页内 picker，这里改成：
  // 弹出 ActionSheet 引导用户向上滑回到 picker 区。但因 picker 已迁出，
  // 实施时应在本页内提供一个 modal 编辑表单（参见 Task 2.4）。
}
function onClickStep2() {
  if (step2Status.value === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成第 1 步', icon: 'none' })
    return
  }
  uni.navigateTo({ url: '/pages/chat/chat' })
}
function onClickStep3() {
  if (step3Status.value === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成第 2 步', icon: 'none' })
    return
  }
  // done 状态点开看测评结果
  uni.navigateTo({ url: '/pages/assessments/assessments' })
}
function onContinueAssessment() {
  switch (nextAssessment.value) {
    case 'questionnaire':
      uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
      break
    case 'mbti':
      uni.navigateTo({ url: '/pages/mbti/mbti' })
      break
    case 'holland':
      uni.navigateTo({ url: '/pages/holland/holland' })
      break
    default:
      uni.navigateTo({ url: '/pages/assessments/assessments' })
  }
}
function onClickStep4() {
  if (step4Status.value === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成测评', icon: 'none' })
    return
  }
  uni.switchTab({ url: '/pages/report/report' })
}
function goReport() {
  uni.switchTab({ url: '/pages/report/report' })
}
function goPrivacy() {
  uni.navigateTo({ url: '/pages/privacy/privacy' })
}

onLoad((options = {}) => {
  if (options.inviterId) membershipStore.setInviterId(options.inviterId)
  membershipStore.login().catch(() => {})
})
onShow(() => {
  refresh()
  membershipStore.loadStatus().catch(() => {})
})
</script>
```

- [ ] **Step 4: 重写 style 块（覆盖原全部 scoped 样式）**

替换 `<style lang="scss" scoped>` 整段为：

```scss
<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 25%, #f9fafb 100%);
  padding: 32rpx 28rpx 60rpx;
  position: relative;
  box-sizing: border-box;
}
.bg-glow-soft {
  position: absolute; top: 0; left: 0; right: 0; height: 320rpx;
  background: radial-gradient(circle at 50% 0%, rgba(249,115,22,0.12), transparent 60%);
  pointer-events: none;
}

/* === 顶部品牌 === */
.brand { text-align: center; padding: 16rpx 0 28rpx; position: relative; z-index: 1; }
.logo {
  width: 84rpx; height: 84rpx; margin: 0 auto 12rpx;
  border-radius: 50%; overflow: hidden;
  background: linear-gradient(135deg, #f97316, #ea580c);
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.28);
  display: flex; align-items: center; justify-content: center;
}
.logo-img { width: 64rpx; height: 64rpx; }
.brand-name { display: block; font-size: 36rpx; font-weight: 700; color: #111827; }
.brand-greet { display: block; font-size: 22rpx; color: #6b7280; margin-top: 6rpx; }

/* === 进度卡 === */
.progress-card {
  background: white; border-radius: 20rpx; padding: 24rpx 28rpx;
  box-shadow: 0 4rpx 14rpx rgba(17, 24, 39, 0.05);
  margin-bottom: 24rpx;
}
.progress-card.ready { background: linear-gradient(135deg, #ecfdf5, #ffffff); }
.progress-top { display: flex; justify-content: space-between; align-items: center; }
.progress-label { font-size: 24rpx; color: #6b7280; }
.progress-hint { font-size: 22rpx; color: #f97316; font-weight: 600; }
.progress-card.ready .progress-hint { color: #10b981; }
.progress-stat { margin-top: 6rpx; }
.progress-frac { font-size: 40rpx; font-weight: 800; color: #111827; }
.progress-card.ready .progress-frac { color: #10b981; }
.progress-total { font-size: 24rpx; font-weight: 500; color: #9ca3af; }
.progress-bar { height: 10rpx; background: #f3f4f6; border-radius: 99rpx; margin-top: 14rpx; overflow: hidden; }
.progress-fill {
  height: 100%; border-radius: 99rpx;
  background: linear-gradient(90deg, #f97316, #fb923c);
  transition: width 0.4s ease;
}
.progress-card.ready .progress-fill { background: linear-gradient(90deg, #10b981, #34d399); }

/* === 步骤卡 === */
.step {
  background: white; border-radius: 18rpx;
  padding: 22rpx 24rpx; margin-bottom: 14rpx;
  display: flex; align-items: center; gap: 18rpx;
  box-shadow: 0 2rpx 8rpx rgba(17, 24, 39, 0.04);
}
.step-icon {
  width: 56rpx; height: 56rpx; border-radius: 14rpx;
  background: #f3f4f6; color: #9ca3af;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 26rpx; flex-shrink: 0;
}
.step-body { flex: 1; min-width: 0; }
.step-title { display: block; font-size: 28rpx; font-weight: 600; color: #111827; }
.step-desc { display: block; font-size: 22rpx; color: #9ca3af; margin-top: 4rpx; }
.step-arrow { color: #d1d5db; font-size: 32rpx; }

.step-done .step-icon { background: #d1fae5; color: #059669; }
.step-done .step-desc { color: #059669; }
.step-active .step-icon {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: white;
  box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.35);
}
.step-active .step-desc { color: #f97316; }
.step-active .step-arrow { color: #f97316; }
.step-locked { opacity: 0.65; }
.step-locked .step-arrow { color: #d1d5db; }

/* === 展开形态 === */
.step-expanded {
  flex-direction: column; align-items: stretch;
  padding: 24rpx; gap: 0;
}
.step-expanded .step-top-row { display: flex; align-items: center; gap: 18rpx; }
.chips { display: flex; gap: 12rpx; margin-top: 18rpx; }
.chip {
  flex: 1; background: #f9fafb; border-radius: 10rpx;
  padding: 12rpx 6rpx; text-align: center;
  border: 1rpx solid #e5e7eb;
}
.chip-label { display: block; font-size: 22rpx; color: #6b7280; }
.chip-status { display: block; font-size: 22rpx; color: #9ca3af; margin-top: 4rpx; }
.chip.done { background: #ecfdf5; border-color: #a7f3d0; }
.chip.done .chip-status { color: #059669; font-weight: 700; }
.chip.next { background: #fff7ed; border-color: #fdba74; }
.chip.next .chip-status { color: #ea580c; font-weight: 700; }
.step-cta {
  margin-top: 18rpx; padding: 22rpx;
  background: linear-gradient(90deg, #f97316, #ea580c);
  color: white; text-align: center;
  font-size: 28rpx; font-weight: 600;
  border-radius: 14rpx;
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
}
.step-cta-text { color: white; }

/* === 报告 hero === */
.report-hero {
  margin-top: 28rpx; padding: 28rpx;
  background: linear-gradient(135deg, #f97316 0%, #ea580c 60%);
  border-radius: 22rpx; color: white; position: relative; overflow: hidden;
  box-shadow: 0 10rpx 28rpx rgba(249, 115, 22, 0.35);
}
.report-hero-glow { position: absolute; top: -40rpx; right: -40rpx; width: 200rpx; height: 200rpx; background: radial-gradient(circle, rgba(255,255,255,0.3), transparent 70%); }
.report-hero-content { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }
.report-hero-text { flex: 1; }
.report-hero-title { display: block; font-size: 26rpx; font-weight: 600; opacity: 0.92; }
.report-hero-price { display: block; font-size: 52rpx; font-weight: 800; margin: 4rpx 0; }
.report-hero-currency { font-size: 28rpx; font-weight: 600; opacity: 0.85; margin-right: 4rpx; }
.report-hero-sub { display: block; font-size: 20rpx; opacity: 0.85; }
.report-hero-icon { font-size: 56rpx; opacity: 0.95; }
.report-hero-cta {
  margin-top: 18rpx; background: white; color: #c2410c;
  text-align: center; padding: 18rpx; border-radius: 14rpx;
  font-weight: 700; font-size: 28rpx;
}

/* === 免责声明 === */
.disclaimer { margin-top: 40rpx; text-align: center; }
.disclaimer-text { display: block; font-size: 20rpx; color: #9ca3af; line-height: 1.6; }
.privacy-link { display: inline-block; font-size: 22rpx; color: #f97316; margin-top: 8rpx; }
</style>
```

- [ ] **Step 5: 解决 onClickStep1 的「编辑基础信息」问题**

Step 3 的 `onClickStep1` 标了 placeholder。在 Task 2.4 之前，暂时把它改为简单跳转：

```javascript
function onClickStep1() {
  // 暂时跳到 questionnaire；正式的编辑表单将在 Task 2.4 加入
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}
```

但 Task 2.4 会替换这里为 modal 编辑。

- [ ] **Step 6: 构建并预览**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin
```

在 DevTools 检查 4 种数据状态（你需要在 Storage 面板手动改）：
1. 清空所有 storage → 看到「全新用户」状态：4 步全展示，仅第 1 步橙色
2. 填基础信息 → 第 1 步变 ✓，第 2 步变橙色
3. 模拟有聊天记录 → 第 2 步 ✓，第 3 步展开成大卡
4. 模拟所有测评完成 → 进度卡变绿，底部出现橙色 hero

- [ ] **Step 7: 提交**

```bash
git add gaokao-miniprogram/src/pages/index/index.vue
git commit -m "feat(home): 重写首页为任务清单 + 进度卡（4 步状态）"
```

---

### Task 2.3: 在首页内提供「编辑基础信息」入口

**Files:**
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

> 现状的「省份 / 科目 / 分数」picker 直接在 index 页面里。重写后，这部分逻辑从首页 template 移除了，但用户点击「步骤 1」时仍需要能填/改。方案：用一个 `<view>` 容器实现底部弹起的 form sheet。

- [ ] **Step 1: 在 template 末尾增加 sheet 节点**

紧邻 `</view>` 关闭根节点之前，加上：

```vue
<!-- 编辑基础信息 sheet -->
<view v-if="showProfileSheet" class="sheet-mask" @click="closeProfileSheet" />
<view v-if="showProfileSheet" class="sheet">
  <view class="sheet-header">
    <text class="sheet-title">填写基础信息</text>
    <text class="sheet-close" @click="closeProfileSheet">✕</text>
  </view>
  <picker :range="provinces" :value="provinceIndex" @change="onProvinceChange">
    <view class="sheet-field">
      <text class="sheet-label">📍 目标省份</text>
      <text class="sheet-value">{{ draft.province || '点击选择' }} ›</text>
    </view>
  </picker>
  <picker :range="categories" :value="categoryIndex" @change="onCategoryChange">
    <view class="sheet-field">
      <text class="sheet-label">📚 考生科目</text>
      <text class="sheet-value">{{ draft.category || '点击选择' }} ›</text>
    </view>
  </picker>
  <view class="sheet-field">
    <text class="sheet-label">⚡ 高考分数</text>
    <input class="sheet-input" type="number" maxlength="3" :value="draft.score" @input="onDraftScoreInput" placeholder="输入实考分" />
  </view>
  <view class="sheet-field">
    <text class="sheet-label">🎯 全省位次（选填）</text>
    <input class="sheet-input" type="number" maxlength="8" :value="draft.rank" @input="onDraftRankInput" placeholder="选填" />
  </view>
  <view class="sheet-save" :class="{ disabled: !sheetReady }" @click="saveProfileSheet">
    <text class="sheet-save-text">{{ sheetReady ? '保存' : '请补全前 3 项' }}</text>
  </view>
</view>
```

- [ ] **Step 2: 在 script 顶部加入 imports 和 picker 数据**

在 `<script setup>` 内 `import { useMembershipStore }` 后面追加：

```javascript
import { ref } from 'vue'
import { saveUserProfile, loadUserProfile, isProfileComplete } from '../../utils/storage.js'

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆',
]
const categories = ['物理类', '历史类']

const showProfileSheet = ref(false)
const draft = ref({ province: '', category: '', score: '', rank: '' })

const provinceIndex = computed(() => Math.max(0, provinces.indexOf(draft.value.province)))
const categoryIndex = computed(() => Math.max(0, categories.indexOf(draft.value.category)))
const sheetReady = computed(() => isProfileComplete(draft.value))

function openProfileSheet() {
  draft.value = { ...loadUserProfile() }
  showProfileSheet.value = true
}
function closeProfileSheet() {
  showProfileSheet.value = false
}
function onProvinceChange(e) { draft.value.province = provinces[e.detail.value] }
function onCategoryChange(e) { draft.value.category = categories[e.detail.value] }
function onDraftScoreInput(e) { draft.value.score = e.detail.value }
function onDraftRankInput(e) { draft.value.rank = e.detail.value }
function saveProfileSheet() {
  if (!sheetReady.value) return
  saveUserProfile(draft.value)
  closeProfileSheet()
  refresh()
  uni.showToast({ title: '已保存', icon: 'success' })
}
```

- [ ] **Step 3: 改 `onClickStep1` 为打开 sheet**

```javascript
function onClickStep1() {
  openProfileSheet()
}
```

（删除 Task 2.2 Step 5 里的 placeholder 跳转）

- [ ] **Step 4: 加 sheet 的 scss 样式**

在 `<style lang="scss" scoped>` 内追加：

```scss
.sheet-mask {
  position: fixed; inset: 0; background: rgba(17, 24, 39, 0.45);
  z-index: 99;
}
.sheet {
  position: fixed; left: 0; right: 0; bottom: 0;
  background: white; border-radius: 28rpx 28rpx 0 0;
  padding: 28rpx 32rpx 60rpx;
  z-index: 100; box-shadow: 0 -8rpx 24rpx rgba(17, 24, 39, 0.1);
}
.sheet-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22rpx; }
.sheet-title { font-size: 32rpx; font-weight: 700; color: #111827; }
.sheet-close { font-size: 36rpx; color: #9ca3af; padding: 4rpx 12rpx; }
.sheet-field {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24rpx 0; border-bottom: 1rpx solid #f3f4f6;
}
.sheet-label { font-size: 26rpx; color: #374151; }
.sheet-value { font-size: 26rpx; color: #111827; font-weight: 500; }
.sheet-input {
  font-size: 26rpx; color: #111827; text-align: right;
  width: 280rpx;
}
.sheet-save {
  margin-top: 24rpx; padding: 26rpx;
  background: linear-gradient(90deg, #f97316, #ea580c);
  color: white; text-align: center; font-weight: 700; font-size: 30rpx;
  border-radius: 18rpx;
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
}
.sheet-save.disabled { background: #e5e7eb; color: #9ca3af; box-shadow: none; }
.sheet-save-text { color: inherit; }
```

- [ ] **Step 5: 构建并预览**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin
```

DevTools 检查：
- 点首页步骤 1 卡片，底部弹起 sheet
- 选省份/科目/输入分数后，「保存」按钮变亮
- 保存后 sheet 关闭，步骤 1 卡片变 ✓ 状态

- [ ] **Step 6: 提交**

```bash
git add gaokao-miniprogram/src/pages/index/index.vue
git commit -m "feat(home): 加入底部 sheet 编辑基础信息"
```

---

## Phase 3 · 报告 tab 三态

### Task 3.1: 重写 report.vue 三态结构

**Files:**
- Modify: `gaokao-miniprogram/src/pages/report/report.vue`

> 现有 report.vue 是「生成中 / 已完成 / 测评未完成」等过程状态。我们重新组织为「页面级三态」：未解锁 / 已就绪未付费 / 已解锁。生成过程作为 active 状态内的局部 loading 处理。

- [ ] **Step 1: 备份原 report.vue**

```bash
cp gaokao-miniprogram/src/pages/report/report.vue .superpowers/legacy/report.vue.bak
```

- [ ] **Step 2: 重写 template**

把 `<template>` 内的所有 `state-card` 节点替换为下面的三态结构（保留底部的 loading 视图作为生成期内嵌状态）：

```vue
<template>
  <view class="report-page">
    <view class="bg-glow-soft" />

    <!-- 顶部标题 -->
    <view class="page-title">我的志愿报告</view>

    <!-- A. 未解锁 / 已就绪未付费 共用：紫色锁屏 hero -->
    <view v-if="!membershipStore.isActive && !generating" class="lock-hero" :class="{ ready: allAssessmentsDone }">
      <view class="lock-hero-glow" />
      <view class="lock-hero-badge" :class="{ ready: allAssessmentsDone }">
        <text>{{ allAssessmentsDone ? '✓ 资料已就绪' : `还差 ${3 - completedAssessments} 项测评` }}</text>
      </view>
      <text class="lock-hero-title">{{ heroTitle }}</text>
      <text class="lock-hero-sub">{{ heroSub }}</text>
      <text class="lock-hero-price">¥19.9</text>
      <text class="lock-hero-price-sub">一次解锁，家长也能看</text>
    </view>

    <!-- 已就绪未付费：双 unlock 卡 -->
    <view v-if="allAssessmentsDone && !membershipStore.isActive && !generating" class="unlock-options">
      <view class="unlock-card primary" @click="onPayWithWechat">
        <text class="unlock-icon">💳</text>
        <text class="unlock-label">立即支付 ¥19.9</text>
        <text class="unlock-desc">微信支付，秒到</text>
      </view>
      <view class="unlock-card" @click="onInviteFriends">
        <text class="unlock-icon">👥</text>
        <text class="unlock-label">邀请 5 人免费</text>
        <text class="unlock-desc">已邀请 {{ membershipStore.effectiveInviteCount }} / 3</text>
      </view>
    </view>

    <!-- 未解锁（测评未完成）：邀请进度 -->
    <view v-if="!allAssessmentsDone && !membershipStore.isActive" class="invite-bar">
      <view class="invite-bar-top">
        <text class="invite-bar-label">邀请同学免费开通</text>
        <text class="invite-bar-num">{{ membershipStore.effectiveInviteCount }} / 3</text>
      </view>
      <view class="invite-dots">
        <view class="invite-dot" :class="{ filled: membershipStore.effectiveInviteCount >= 1 }" />
        <view class="invite-dot" :class="{ filled: membershipStore.effectiveInviteCount >= 2 }" />
        <view class="invite-dot" :class="{ filled: membershipStore.effectiveInviteCount >= 3 }" />
      </view>
      <view class="invite-cta" @click="onInviteFriends">分享给同学 →</view>
    </view>

    <!-- 报告内容预览 8 模块 -->
    <view v-if="!membershipStore.isActive && !generating" class="preview-section">
      <view class="preview-top">
        <text class="preview-title">报告里有什么</text>
        <text class="preview-sub">8 大模块</text>
      </view>
      <view class="preview-grid">
        <view class="preview-mod" v-for="m in modules" :key="m">{{ m }}</view>
      </view>
    </view>

    <!-- B. 已解锁但还没生成 -->
    <view v-if="membershipStore.isActive && !latestReport && !generating" class="ready-card">
      <text class="ready-title">资料齐全，等你生成报告</text>
      <text class="ready-sub">基于分数 + 测评结果 + 对话记录</text>
      <view class="ready-cta" @click="onGenerate">立即生成报告</view>
    </view>

    <!-- C. 生成中 -->
    <view v-if="generating" class="loading-card">
      <view class="spinner" />
      <text class="loading-title">正在生成志愿参考报告</text>
      <text class="loading-sub">整合考生信息、测评结果与对话记录</text>
      <text class="loading-tip">通常 1-2 分钟，请保持页面打开。</text>
    </view>

    <!-- D. 已解锁且有报告 -->
    <view v-if="membershipStore.isActive && latestReport && !generating" class="latest-card">
      <text class="latest-label">最新报告</text>
      <text class="latest-title">{{ latestReport.title }}</text>
      <text class="latest-meta">{{ latestReport.subtitle }}</text>
      <view class="latest-actions">
        <view class="latest-btn solid" @click="openLatest">在线查看</view>
        <button class="latest-btn" open-type="share">分享给家长</button>
      </view>
    </view>

    <view v-if="membershipStore.isActive && history.length > 0 && !generating" class="history-section">
      <text class="history-title">历史报告</text>
      <view class="history-card" v-for="(item, idx) in history" :key="item.id" @click="openHistory(item)">
        <view class="history-ico">📋</view>
        <view class="history-body">
          <text class="history-name">{{ item.title }}</text>
          <text class="history-date">{{ item.subtitle }}</text>
        </view>
        <text class="history-arrow">›</text>
      </view>
      <view class="regenerate" @click="onRegenerate">+ 重新生成报告（数据有更新）</view>
    </view>
  </view>
</template>
```

- [ ] **Step 3: 重写 script**

替换 `<script setup>` 整段为：

```vue
<script setup>
import { computed, ref } from 'vue'
import { onShow, onLoad } from '@dcloudio/uni-app'
import { useMembershipStore } from '../../stores/membership.js'
import { useHomeProgress } from '../../composables/useHomeProgress.js'
import { loadUserProfile, loadHistory, loadReport, saveReport } from '../../utils/storage.js'
import { generateReport } from '../../api/report.js'

const membershipStore = useMembershipStore()
const { questionnaireDone, mbtiDone, hollandDone, step3Done: allAssessmentsDone, step3Count: completedAssessments, refresh: refreshProgress } = useHomeProgress()

const modules = [
  '院校定位分析', '专业匹配建议', '分数策略', '风险提示',
  'MBTI 匹配解读', '霍兰德兴趣对应', '专业冷热分析', '志愿组合建议',
]

const generating = ref(false)
const latestReport = ref(null)
const history = ref([])

const heroTitle = computed(() => {
  if (allAssessmentsDone.value) return '立即生成你的志愿报告'
  return '报告正在等你'
})
const heroSub = computed(() => {
  if (allAssessmentsDone.value) {
    const p = loadUserProfile()
    return `基于 ${p.score || '？'}分 + 测评结果`
  }
  return '完成 3 项测评后即可一键生成'
})

function loadReports() {
  const stored = loadReport() // 现存 storage util；如果格式是单个 report，包成数组
  if (!stored) { latestReport.value = null; history.value = []; return }
  // 兼容旧格式（单个对象）和新格式（数组）
  const list = Array.isArray(stored) ? stored : [stored]
  list.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
  if (list.length > 0) {
    const head = list[0]
    latestReport.value = {
      url: head.url,
      title: head.title || `${head.profile?.province || ''}${head.profile?.category || ''} · ${head.profile?.score || ''}分`,
      subtitle: `生成于 ${formatDate(head.createdAt)} · ${head.modules || 8} 个模块`,
    }
    history.value = list.slice(1).map((r) => ({
      id: r.id || r.url,
      title: r.title || '历史版本',
      subtitle: `${formatDate(r.createdAt)}`,
      url: r.url,
    }))
  } else {
    latestReport.value = null; history.value = []
  }
}

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

async function onGenerate() {
  generating.value = true
  try {
    const profile = loadUserProfile()
    const result = await generateReport({ profile })
    const reportRecord = {
      id: result.id || `${Date.now()}`,
      url: result.url,
      title: `${profile.province}${profile.category} · ${profile.score}分`,
      createdAt: Date.now(),
      modules: 8,
      profile,
    }
    // 写回 storage（数组形式）
    const prev = loadReport()
    const list = Array.isArray(prev) ? prev : (prev ? [prev] : [])
    list.unshift(reportRecord)
    saveReport(list)
    loadReports()
    uni.showToast({ title: '报告已生成', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '生成失败，请重试', icon: 'none' })
  } finally {
    generating.value = false
  }
}

function onRegenerate() {
  uni.showModal({
    title: '重新生成',
    content: '会生成新版本，旧版本保留在历史里。',
    success: (r) => { if (r.confirm) onGenerate() },
  })
}

function openLatest() {
  if (!latestReport.value?.url) return
  uni.navigateTo({ url: `/pages/report-view/report-view?url=${encodeURIComponent(latestReport.value.url)}` })
}
function openHistory(item) {
  if (!item.url) return
  uni.navigateTo({ url: `/pages/report-view/report-view?url=${encodeURIComponent(item.url)}` })
}

function onPayWithWechat() {
  membershipStore.openMembership()
}
function onInviteFriends() {
  uni.showToast({ title: '请用右上角 ··· 分享', icon: 'none' })
}

onLoad(() => {
  membershipStore.login().catch(() => {})
})
onShow(() => {
  refreshProgress()
  membershipStore.loadStatus().catch(() => {})
  loadReports()
})
</script>
```

注：上面用了两个 storage util — `loadReport / saveReport`。**先确认它们存在**：

```bash
grep -E "export function (loadReport|saveReport)" gaokao-miniprogram/src/utils/storage.js
```

如果不存在，执行 Step 4。如果存在，跳过 Step 4。

- [ ] **Step 4: 如缺失则补充 storage util**

在 `gaokao-miniprogram/src/utils/storage.js` 内追加：

```javascript
export function saveReport(data) {
  try { uni.setStorageSync(REPORT_KEY, data) } catch {}
}
export function loadReport() {
  try { return uni.getStorageSync(REPORT_KEY) || null } catch { return null }
}
```

注：`REPORT_KEY` 在文件顶部已声明为 `'user_report'`。

- [ ] **Step 5: 改 / 新增 report 生成 API 封装**

确认 `gaokao-miniprogram/src/api/report.js` 存在且导出 `generateReport`：

```bash
grep -E "export.*generateReport" gaokao-miniprogram/src/api/report.js 2>/dev/null
```

如果不存在，新建：

```javascript
// gaokao-miniprogram/src/api/report.js
import { API_BASE } from '../config.js'

export function generateReport({ profile }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}/api/report/generate`,
      method: 'POST',
      data: { profile },
      timeout: 120000,
      success: (res) => {
        if (res.statusCode === 200 && res.data?.url) resolve(res.data)
        else reject(new Error(res.data?.message || '生成失败'))
      },
      fail: () => reject(new Error('网络异常')),
    })
  })
}
```

注：若现有 report.vue 里已有内联的 `uni.request` 报告生成逻辑，可以把它抽出到 `api/report.js`，无需新建。

- [ ] **Step 6: 重写 style**

把整段 `<style lang="scss" scoped>` 替换为：

```scss
<style lang="scss" scoped>
.report-page {
  min-height: 100vh; padding: 32rpx 28rpx 60rpx;
  background: linear-gradient(180deg, #f3f4f6 0%, #ffffff 100%);
  position: relative; box-sizing: border-box;
}
.bg-glow-soft {
  position: absolute; inset: 0 0 auto; height: 280rpx;
  background: radial-gradient(circle at 80% 0%, rgba(99, 102, 241, 0.18), transparent 60%);
  pointer-events: none;
}
.page-title { font-size: 32rpx; font-weight: 700; color: #111827; text-align: center; padding: 16rpx 0 24rpx; }

/* === Lock hero === */
.lock-hero {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%);
  border-radius: 24rpx; padding: 32rpx 28rpx; color: white; text-align: center;
  margin-bottom: 18rpx; position: relative; overflow: hidden;
}
.lock-hero.ready { background: linear-gradient(135deg, #312e81 0%, #5b21b6 100%); }
.lock-hero-glow { position: absolute; top: -50rpx; right: -50rpx; width: 240rpx; height: 240rpx; background: radial-gradient(circle, rgba(251,191,36,0.32), transparent 70%); }
.lock-hero-badge { display: inline-block; padding: 6rpx 18rpx; border-radius: 99rpx; background: rgba(251,191,36,0.18); color: #fcd34d; font-size: 22rpx; font-weight: 600; }
.lock-hero-badge.ready { background: rgba(52,211,153,0.22); color: #6ee7b7; }
.lock-hero-title { display: block; font-size: 32rpx; font-weight: 700; margin-top: 14rpx; }
.lock-hero-sub { display: block; font-size: 22rpx; opacity: 0.78; margin-top: 6rpx; }
.lock-hero-price { display: block; font-size: 56rpx; font-weight: 800; color: #fbbf24; margin-top: 18rpx; }
.lock-hero-price-sub { display: block; font-size: 20rpx; opacity: 0.7; }

/* === Unlock options === */
.unlock-options { display: grid; grid-template-columns: 1fr 1fr; gap: 14rpx; margin-bottom: 18rpx; }
.unlock-card {
  background: white; border: 2rpx solid #e5e7eb;
  border-radius: 18rpx; padding: 22rpx 16rpx; text-align: center;
}
.unlock-card.primary {
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border-color: #fb923c;
  box-shadow: 0 4rpx 14rpx rgba(249, 115, 22, 0.2);
}
.unlock-icon { display: block; font-size: 40rpx; }
.unlock-label { display: block; font-size: 26rpx; font-weight: 700; color: #111827; margin-top: 6rpx; }
.unlock-card.primary .unlock-label { color: #c2410c; }
.unlock-desc { display: block; font-size: 20rpx; color: #9ca3af; margin-top: 4rpx; }

/* === Invite bar === */
.invite-bar { background: white; border-radius: 18rpx; padding: 22rpx; margin-bottom: 18rpx; }
.invite-bar-top { display: flex; justify-content: space-between; }
.invite-bar-label { font-size: 24rpx; color: #6b7280; }
.invite-bar-num { font-size: 24rpx; color: #f97316; font-weight: 700; }
.invite-dots { display: flex; gap: 8rpx; margin-top: 14rpx; }
.invite-dot { flex: 1; height: 10rpx; border-radius: 99rpx; background: #f3f4f6; }
.invite-dot.filled { background: linear-gradient(90deg, #f97316, #fb923c); }
.invite-cta { margin-top: 16rpx; text-align: center; padding: 18rpx; background: #f97316; color: white; border-radius: 14rpx; font-weight: 700; font-size: 26rpx; }

/* === 8 modules preview === */
.preview-section { background: white; border-radius: 18rpx; padding: 22rpx; margin-bottom: 18rpx; }
.preview-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14rpx; }
.preview-title { font-size: 26rpx; font-weight: 700; color: #111827; }
.preview-sub { font-size: 22rpx; color: #9ca3af; }
.preview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10rpx; }
.preview-mod {
  background: #f9fafb; padding: 14rpx 16rpx; border-radius: 10rpx;
  font-size: 22rpx; color: #6b7280;
  border-left: 4rpx solid #f97316;
}

/* === Ready / Loading / Latest / History === */
.ready-card, .loading-card, .latest-card {
  background: linear-gradient(135deg, #f97316, #ea580c);
  border-radius: 22rpx; padding: 30rpx 26rpx; color: white; margin-bottom: 18rpx;
  box-shadow: 0 10rpx 28rpx rgba(249, 115, 22, 0.32);
}
.ready-title, .latest-title { display: block; font-size: 30rpx; font-weight: 700; }
.ready-sub, .latest-meta { display: block; font-size: 22rpx; opacity: 0.85; margin-top: 6rpx; }
.latest-label { display: block; font-size: 20rpx; opacity: 0.78; }
.ready-cta { margin-top: 18rpx; padding: 20rpx; background: white; color: #c2410c; border-radius: 14rpx; text-align: center; font-weight: 700; font-size: 28rpx; }
.latest-actions { display: flex; gap: 12rpx; margin-top: 18rpx; }
.latest-btn { flex: 1; padding: 16rpx; border-radius: 12rpx; background: rgba(255,255,255,0.22); color: white; text-align: center; font-weight: 600; font-size: 24rpx; line-height: 1.4; border: none; }
.latest-btn.solid { background: white; color: #c2410c; }

.loading-card { text-align: center; }
.spinner { width: 56rpx; height: 56rpx; border: 5rpx solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; margin: 0 auto 16rpx; animation: spin 0.9s linear infinite; }
.loading-title { display: block; font-size: 28rpx; font-weight: 700; }
.loading-sub { display: block; font-size: 22rpx; opacity: 0.85; margin-top: 4rpx; }
.loading-tip { display: block; font-size: 20rpx; opacity: 0.7; margin-top: 8rpx; }
@keyframes spin { to { transform: rotate(360deg); } }

.history-section { margin-top: 18rpx; }
.history-title { display: block; font-size: 24rpx; color: #6b7280; padding: 8rpx 4rpx 12rpx; font-weight: 600; }
.history-card { display: flex; align-items: center; gap: 16rpx; background: white; border-radius: 14rpx; padding: 18rpx; margin-bottom: 10rpx; }
.history-ico { width: 56rpx; height: 56rpx; background: #fff7ed; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; font-size: 28rpx; }
.history-body { flex: 1; min-width: 0; }
.history-name { display: block; font-size: 26rpx; color: #111827; font-weight: 600; }
.history-date { display: block; font-size: 22rpx; color: #9ca3af; margin-top: 2rpx; }
.history-arrow { color: #d1d5db; font-size: 32rpx; }
.regenerate { text-align: center; padding: 22rpx; margin-top: 12rpx; border: 2rpx dashed #fb923c; border-radius: 14rpx; color: #f97316; font-size: 26rpx; font-weight: 600; }
</style>
```

- [ ] **Step 7: 构建并预览**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin
```

DevTools 操作（通过 Storage 面板模拟数据）：
1. 清 storage → 进入「报告」tab → 看到「还差 3 项测评」紫色锁屏 + 邀请条 + 8 模块预览
2. 模拟测评全部完成（手动改 `assessments` / `questionnaire` storage）→ 看到「✓ 资料已就绪」+ 双 unlock 卡
3. 手动改 `membership_status` 为 `active` → 看到「立即生成报告」橙色卡
4. 触发 onGenerate（也可手动写一条 `user_report` 数组到 storage）→ 看到「最新报告 + 历史报告 + 重新生成」

- [ ] **Step 8: 提交**

```bash
git add gaokao-miniprogram/src/pages/report/report.vue gaokao-miniprogram/src/utils/storage.js gaokao-miniprogram/src/api/report.js
git commit -m "feat(report): 报告页三态重写（未解锁/已就绪/已解锁 + 历史列表）"
```

---

## Phase 4 · 我的 tab 瘦身

### Task 4.1: 重写 profile.vue

**Files:**
- Modify: `gaokao-miniprogram/src/pages/profile/profile.vue`

- [ ] **Step 1: 备份**

```bash
cp gaokao-miniprogram/src/pages/profile/profile.vue .superpowers/legacy/profile.vue.bak
```

- [ ] **Step 2: 重写 template**

```vue
<template>
  <view class="profile-page">
    <view class="bg-glow-soft" />

    <!-- 用户头部 -->
    <view class="me-header">
      <view class="avatar"><text class="avatar-text">峰</text></view>
      <text class="user-name">志愿同学</text>
      <text class="user-id">ID: {{ shortUserId }}</text>
      <view class="vip-pill" :class="{ gray: !membershipStore.isActive }">
        <text>{{ membershipStore.isActive ? 'VIP · 报告已解锁' : '普通用户' }}</text>
      </view>
    </view>

    <!-- 考生信息卡 -->
    <view class="info-card">
      <view class="info-top">
        <text class="info-label">考生信息</text>
        <text class="info-edit" @click="goEditProfile">编辑 ›</text>
      </view>
      <view class="info-grid">
        <view class="info-field"><text class="info-v">{{ profile.province || '—' }}</text><text class="info-k">省份</text></view>
        <view class="info-field"><text class="info-v">{{ profile.category ? profile.category.replace('类','') : '—' }}</text><text class="info-k">科目</text></view>
        <view class="info-field"><text class="info-v">{{ profile.score || '—' }}</text><text class="info-k">分数</text></view>
      </view>
    </view>

    <!-- 业务菜单 -->
    <view class="menu-list">
      <view class="menu-item" @click="goChat">
        <view class="menu-icon">💬</view>
        <text class="menu-label">我的咨询记录</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goAssessments">
        <view class="menu-icon">🧠</view>
        <text class="menu-label">我的测评结果</text>
        <view class="menu-badge">{{ assessmentCount }}/3</view>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="onShare">
        <view class="menu-icon">👥</view>
        <text class="menu-label">邀请好友</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- 系统菜单 -->
    <view class="menu-list">
      <view class="menu-item" @click="goPrivacy">
        <view class="menu-icon">🔒</view>
        <text class="menu-label">隐私保护</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goFeedback">
        <view class="menu-icon">💌</view>
        <text class="menu-label">反馈/客服</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goAbout">
        <view class="menu-icon">ⓘ</view>
        <text class="menu-label">关于峰哥</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>
  </view>
</template>
```

- [ ] **Step 3: 重写 script**

```vue
<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useMembershipStore } from '../../stores/membership.js'
import { loadUserProfile, loadAssessments, loadQuestionnaire, QUESTIONNAIRE_REQUIRED_COUNT } from '../../utils/storage.js'

const membershipStore = useMembershipStore()
const profile = ref(loadUserProfile())
const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())

const shortUserId = computed(() => (membershipStore.userId || 'CLOUD').slice(0, 8).toUpperCase())
const assessmentCount = computed(() => {
  let n = 0
  if (questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT) n++
  if (assessments.value.mbti.completed) n++
  if (assessments.value.holland.completed) n++
  return n
})

function goEditProfile() {
  // 跳回首页并自动弹出编辑 sheet（约定通过 query 参数）
  uni.switchTab({ url: '/pages/index/index' })
  setTimeout(() => uni.$emit('open-profile-sheet'), 200)
}
function goChat() { uni.navigateTo({ url: '/pages/chat/chat' }) }
function goAssessments() { uni.navigateTo({ url: '/pages/assessments/assessments' }) }
function goPrivacy() { uni.navigateTo({ url: '/pages/privacy/privacy' }) }
function goFeedback() { uni.showToast({ title: '功能开发中', icon: 'none' }) }
function goAbout() { uni.showToast({ title: '功能开发中', icon: 'none' }) }
function onShare() {
  uni.showToast({ title: '请用右上角 ··· 分享', icon: 'none' })
}

onShow(() => {
  profile.value = loadUserProfile()
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
  membershipStore.loadStatus().catch(() => {})
})
</script>
```

- [ ] **Step 4: 在 index.vue 内监听 `open-profile-sheet` 事件**

回到 `gaokao-miniprogram/src/pages/index/index.vue` 的 `<script setup>`，在 `onShow(() => {` 之前增加：

```javascript
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  uni.$on('open-profile-sheet', openProfileSheet)
})
onUnmounted(() => {
  uni.$off('open-profile-sheet', openProfileSheet)
})
```

注：`openProfileSheet` 已在 Task 2.3 Step 2 定义。

- [ ] **Step 5: 重写 profile.vue style**

```scss
<style lang="scss" scoped>
.profile-page {
  min-height: 100vh; padding: 32rpx 28rpx 60rpx;
  background: linear-gradient(180deg, #fff7ed 0%, #f9fafb 60%);
  position: relative; box-sizing: border-box;
}
.bg-glow-soft {
  position: absolute; inset: 0 0 auto; height: 280rpx;
  background: radial-gradient(circle at 50% 0%, rgba(249,115,22,0.18), transparent 60%);
  pointer-events: none;
}

.me-header { text-align: center; padding: 18rpx 0 28rpx; }
.avatar {
  width: 112rpx; height: 112rpx; border-radius: 50%;
  background: linear-gradient(135deg, #f97316, #ea580c);
  margin: 0 auto 14rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.32);
}
.avatar-text { color: white; font-weight: 700; font-size: 44rpx; }
.user-name { display: block; font-size: 32rpx; font-weight: 700; color: #111827; }
.user-id { display: block; font-size: 22rpx; color: #9ca3af; margin-top: 4rpx; }
.vip-pill {
  display: inline-block; margin-top: 14rpx; padding: 6rpx 22rpx;
  border-radius: 99rpx; font-size: 22rpx; font-weight: 700;
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
  color: #78350f;
}
.vip-pill.gray { background: #e5e7eb; color: #6b7280; }

.info-card { background: white; border-radius: 18rpx; padding: 22rpx; margin-bottom: 16rpx; }
.info-top { display: flex; justify-content: space-between; align-items: center; }
.info-label { font-size: 24rpx; color: #6b7280; }
.info-edit { font-size: 24rpx; color: #f97316; font-weight: 600; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14rpx; margin-top: 14rpx; }
.info-field { background: #fafafa; padding: 16rpx; border-radius: 12rpx; text-align: center; }
.info-v { display: block; font-size: 28rpx; font-weight: 700; color: #111827; }
.info-k { display: block; font-size: 20rpx; color: #9ca3af; margin-top: 4rpx; }

.menu-list { background: white; border-radius: 18rpx; margin-bottom: 16rpx; overflow: hidden; }
.menu-item { display: flex; align-items: center; gap: 16rpx; padding: 24rpx 22rpx; border-bottom: 1rpx solid #f3f4f6; }
.menu-item:last-child { border-bottom: none; }
.menu-icon { width: 48rpx; height: 48rpx; background: #f3f4f6; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; font-size: 26rpx; }
.menu-label { flex: 1; font-size: 26rpx; color: #374151; }
.menu-badge { background: #fef3c7; color: #92400e; padding: 4rpx 14rpx; border-radius: 99rpx; font-size: 20rpx; font-weight: 600; }
.menu-arrow { color: #d1d5db; font-size: 32rpx; }
</style>
```

- [ ] **Step 6: 构建并预览**

```bash
cd gaokao-miniprogram && npm run dev:mp-weixin
```

DevTools 检查：
- 「我的」tab 不再有大付费卡
- 头像下显示「普通用户」灰 pill，模拟付费后变金色 VIP pill
- 「我的测评结果」徽章正确显示 X/3
- 点「编辑 ›」回到首页并弹起 sheet

- [ ] **Step 7: 提交**

```bash
git add gaokao-miniprogram/src/pages/profile/profile.vue gaokao-miniprogram/src/pages/index/index.vue
git commit -m "feat(profile): 我的页瘦身为标准个人中心结构"
```

---

## Phase 5 · 联调走查

### Task 5.1: 全流程视觉走查

**Files:** 无代码改动

- [ ] **Step 1: 清空 DevTools storage，从全新用户开始走完一遍**

依次完成：
1. 进入首页 → 看到 4 步全展示、greeting「你好…」、进度卡 0/4
2. 点步骤 1 → sheet 弹起 → 选广东 / 物理 / 600 → 保存 → 步骤 1 变 ✓
3. 点步骤 2 → 进入聊天 → 发一条消息 → 返回首页 → 步骤 2 变 ✓
4. 点步骤 3 → 展开形态显示 → 点 CTA → 完成五环 → 返回首页 → chip 显示 ✓
5. 继续完成 MBTI、霍兰德 → 进度卡变绿，底部出现橙色 hero
6. 点底部 hero → 跳「报告」tab → 看到「✓ 资料已就绪」+ 双 unlock 卡
7. 手动改 membership_status 为 active → 报告 tab 显示「立即生成报告」
8. 模拟生成报告 → 显示最新报告 + 重新生成按钮
9. 检查「我的」tab 显示金色 VIP pill、各菜单可点

- [ ] **Step 2: 检查异常路径**

- 锁定步骤可点击：点步骤 2/3/4 在 locked 状态时只 toast，不跳转
- 数据缺失：清掉 profile 只留 chat history → 步骤 2 应回到 locked
- 测评只完成 1 项：步骤 3 展开正确显示 1/3 + chip 标记
- 不点 hero 直接进报告 tab，路径独立可达

- [ ] **Step 3: 移除 .superpowers/legacy/ 临时备份**

```bash
rm -rf .superpowers/legacy
```

- [ ] **Step 4: 终态提交**

```bash
git status
# 若有遗留改动（如 pages.json 顺序、注释清理）一并提交
git add -A gaokao-miniprogram/
git commit -m "chore(ui): UI 改版联调走查后清理" || echo "无需提交"
```

---

### Task 5.2: 视觉走查截图归档

**Files:**
- Create: `docs/ui-redesign-screenshots/` （4-6 张关键截图）

- [ ] **Step 1: 在 DevTools 截 6 张关键状态**

1. 首页 - 全新用户
2. 首页 - 进行中（步骤 3 展开）
3. 首页 - 已就绪（底部橙 hero）
4. 报告 tab - 未解锁
5. 报告 tab - 已解锁（最新 + 历史）
6. 我的 tab - VIP

- [ ] **Step 2: 保存到 docs/ui-redesign-screenshots/**

文件名：`01-home-new-user.png` / `02-home-in-progress.png` / `03-home-ready.png` / `04-report-locked.png` / `05-report-unlocked.png` / `06-profile-vip.png`

- [ ] **Step 3: 提交**

```bash
git add docs/ui-redesign-screenshots/
git commit -m "docs(ui): 改版后 UI 截图归档"
```

---

## Self-Review

走查计划本身：

1. **Spec 覆盖**：
   - § 1 问题诊断 → Phase 1-4 全部解决（重复 CTA、入口去重、tabbar 改造）
   - § 4 首页详细设计三态 → Task 2.1（composable）+ 2.2（template/script/style） + 2.3（sheet）
   - § 5 报告 tab 三态 → Task 3.1
   - § 6 我的 tab 结构 → Task 4.1
   - § 7 视觉风格 → 在每个 style 重写步骤里贯彻
   - § 11 验收标准 → Task 5.1 全流程走查覆盖

2. **Placeholder 扫描**：Task 2.2 Step 5 标注过 placeholder（onClickStep1 暂跳 questionnaire），由 Task 2.3 Step 3 显式替换为 sheet。无残留。

3. **类型一致性**：
   - `useHomeProgress` 导出的字段名（`step3Done` / `step3Count` / `nextAssessment`）在 index.vue 和 report.vue 都按相同名字消费 ✓
   - `StepStatus` 三个值贯穿前后 ✓
   - `latestReport / history` 在 report.vue 内部使用，无外部消费 ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-25-ui-redesign.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 我每个 Task 派一个全新 subagent，每个 Task 结束后两段式 review，跑得快、上下文干净。适合本计划这种「多个独立 Task、每个都有明确验收」的场景。

**2. Inline Execution** - 在本会话内顺序执行，每个 Phase 结束 checkpoint 给你看。上下文连续，但本会话已较长，可能进入压缩。

**哪个？**
