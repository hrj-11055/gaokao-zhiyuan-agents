<template>
  <view class="page">
    <!-- subtle radial gradient overlay -->
    <view class="bg-glow-soft" />

    <!-- brand -->
    <view class="brand">
      <image class="brand-logo" src="/static/logo.png" mode="aspectFit" />
      <text class="brand-name">峰哥咨询参考</text>
      <text class="brand-greeting">{{ greetingText }}</text>
    </view>

    <!-- progress card -->
    <view class="progress-card">
      <view class="progress-header">
        <text class="progress-title">我的志愿报告</text>
        <text class="progress-fraction">{{ completedSteps }}/4 步</text>
      </view>
      <view class="progress-bar-track">
        <view
          class="progress-bar-fill"
          :class="{ ready: isReady }"
          :style="{ width: progressPercent + '%' }"
        />
      </view>
      <text class="progress-hint">{{ progressHint }}</text>
    </view>

    <!-- step 1 -->
    <view
      class="step-card"
      :class="step1ClassObj"
      @click="onClickStep1"
    >
      <view class="step-icon" :class="step1ClassObj">
        <text class="step-icon-text">{{ step1IconText }}</text>
      </view>
      <view class="step-body">
        <text class="step-title">填写基础信息</text>
        <text class="step-desc" :class="step1ClassObj">{{ step1DescText }}</text>
      </view>
      <text v-if="statusFor(1) === StepStatus.ACTIVE" class="step-arrow">›</text>
    </view>

    <!-- step 2 -->
    <view
      class="step-card"
      :class="step2ClassObj"
      @click="onClickStep2"
    >
      <view class="step-icon" :class="step2ClassObj">
        <text class="step-icon-text">{{ step2IconText }}</text>
      </view>
      <view class="step-body">
        <text class="step-title">和峰哥聊聊志愿</text>
        <text class="step-desc" :class="step2ClassObj">{{ step2DescText }}</text>
      </view>
      <text v-if="statusFor(2) === StepStatus.ACTIVE" class="step-arrow">›</text>
    </view>

    <!-- step 3 -->
    <view
      class="step-card"
      :class="[step3ClassObj, { expanded: statusFor(3) === StepStatus.ACTIVE }]"
      @click="onClickStep3"
    >
      <view class="step-row-top">
        <view class="step-icon" :class="step3ClassObj">
          <text class="step-icon-text">{{ step3IconText }}</text>
        </view>
        <view class="step-body">
          <text class="step-title">完成 3 项测评</text>
          <text class="step-desc" :class="step3ClassObj">{{ step3DescText }}</text>
        </view>
        <text v-if="statusFor(3) === StepStatus.ACTIVE" class="step-arrow">›</text>
      </view>

      <!-- expanded assessment chips (only when active) -->
      <view v-if="statusFor(3) === StepStatus.ACTIVE" class="step-expanded">
        <view class="chips-row">
          <view class="chip" :class="{ done: questionnaireDone }">
            <text class="chip-text">五环 {{ chipStatus('questionnaire') }}</text>
          </view>
          <view class="chip" :class="{ done: mbtiDone }">
            <text class="chip-text">MBTI {{ chipStatus('mbti') }}</text>
          </view>
          <view class="chip" :class="{ done: hollandDone }">
            <text class="chip-text">霍兰德 {{ chipStatus('holland') }}</text>
          </view>
        </view>
        <view v-if="nextAssessment" class="cta-btn" @click.stop="onContinueAssessment">
          <text class="cta-btn-text">{{ nextAssessmentCtaText }}</text>
        </view>
      </view>
    </view>

    <!-- step 4 -->
    <view
      class="step-card"
      :class="step4ClassObj"
      @click="onClickStep4"
    >
      <view class="step-icon" :class="step4ClassObj">
        <text class="step-icon-text">{{ step4IconText }}</text>
      </view>
      <view class="step-body">
        <text class="step-title">生成志愿报告</text>
        <text class="step-desc" :class="step4ClassObj">{{ step4DescText }}</text>
      </view>
      <text v-if="step4Status === StepStatus.ACTIVE" class="step-arrow">›</text>
    </view>

    <!-- report hero (only when step3Done && !member) -->
    <view v-if="step3Done && !membershipStore.isActive" class="report-hero" @click="goReport">
      <view class="hero-glow" />
      <view class="hero-content">
        <text class="hero-price">¥29</text>
        <text class="hero-label">一次解锁</text>
      </view>
      <view class="hero-cta">
        <text class="hero-cta-text">立即生成报告</text>
      </view>
      <text class="hero-invite-hint">邀请 3 人免费</text>
    </view>

    <!-- disclaimer -->
    <view class="disclaimer">
      <text class="disclaimer-text">结果仅供志愿填报参考，请以各省教育考试院和高校官方信息为准。</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useHomeProgress, StepStatus } from '../../composables/useHomeProgress.js'
import { useMembershipStore } from '../../stores/membership.js'

const {
  profile,
  history,
  questionnaire,
  assessments,
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
} = useHomeProgress()

const membershipStore = useMembershipStore()

// ---------- greeting ----------

const greetingText = computed(() => {
  if (!step1Done.value) return '你好，先花 30 秒了解一下吧'
  const p = profile.value
  const base = `${p.province || ''} · ${p.category || ''} · ${p.score || ''}分`
  if (!step2Done.value) return `${base} · 已完成 ${completedSteps.value}/4`
  if (!step3Done.value) return `${base} · 已完成 ${completedSteps.value}/4`
  return `${base} · 已就绪`
})

// ---------- progress ----------

const progressPercent = computed(() => Math.min(100, (completedSteps.value / 4) * 100))

const progressHint = computed(() => {
  if (completedSteps.value === 0) return '从第 1 步开始'
  if (!step3Done.value) return `还差 ${4 - completedSteps.value} 步`
  return '准备就绪'
})

const isReady = computed(() => step3Done.value)

// ---------- chat message count ----------

const chatUserCount = computed(() => {
  if (!history.value || !Array.isArray(history.value.messages)) return 0
  return history.value.messages.filter((m) => m.role === 'user').length
})

// ---------- step status + class + icon + desc ----------

function classForStatus(status) {
  return {
    done: status === StepStatus.DONE,
    active: status === StepStatus.ACTIVE,
    locked: status === StepStatus.LOCKED,
  }
}

// step 1
const step1ClassObj = computed(() => classForStatus(statusFor(1)))
const step1IconText = computed(() => {
  const s = statusFor(1)
  if (s === StepStatus.DONE) return '✓'
  return '1'
})
const step1DescText = computed(() => {
  if (step1Done.value) {
    const p = profile.value
    return `${p.province} · ${p.category} · ${p.score}分`
  }
  return '省份、科类、分数'
})

// step 2
const step2ClassObj = computed(() => classForStatus(statusFor(2)))
const step2IconText = computed(() => {
  const s = statusFor(2)
  if (s === StepStatus.DONE) return '✓'
  return '2'
})
const step2DescText = computed(() => {
  if (step2Done.value) return `已聊 ${chatUserCount.value} 轮`
  return '免费咨询一个具体问题'
})

// step 3
const step3ClassObj = computed(() => classForStatus(statusFor(3)))
const step3IconText = computed(() => {
  const s = statusFor(3)
  if (s === StepStatus.DONE) return '✓'
  return '3'
})
const step3DescText = computed(() => {
  if (step3Done.value) return '3/3 测评已完成'
  return `让报告更准确 · 已完成 ${step3Count.value}/3`
})

// step 4
const step4Status = computed(() => {
  if (!step3Done.value) return StepStatus.LOCKED
  if (membershipStore.isActive) return StepStatus.DONE
  return StepStatus.ACTIVE
})
const step4ClassObj = computed(() => classForStatus(step4Status.value))
const step4IconText = computed(() => {
  if (step4Status.value === StepStatus.DONE) return '✓'
  return '4'
})
const step4DescText = computed(() => {
  if (step4Status.value === StepStatus.DONE) return '报告已生成'
  return '¥29 一次解锁 · 邀请 3 人免费'
})

// ---------- chip status ----------

function chipStatus(key) {
  if (key === 'questionnaire') return questionnaireDone.value ? '✓' : '→'
  if (key === 'mbti') return mbtiDone.value ? '✓' : '→'
  if (key === 'holland') return hollandDone.value ? '✓' : '—'
  return '—'
}

// ---------- next assessment CTA ----------

const nextAssessmentCtaText = computed(() => {
  if (nextAssessment.value === 'questionnaire') return '继续 五环测评 →'
  if (nextAssessment.value === 'mbti') return '继续 MBTI 测评 →'
  if (nextAssessment.value === 'holland') return '继续 霍兰德测评 →'
  return ''
})

// ---------- navigation ----------

function onClickStep1() {
  // placeholder — Task 2.3 will add a bottom sheet
  uni.showToast({ title: '请先点击步骤 1', icon: 'none' })
}

function onClickStep2() {
  if (statusFor(2) === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成上一步', icon: 'none' })
    return
  }
  uni.navigateTo({ url: '/pages/chat/chat' })
}

function onClickStep3() {
  if (statusFor(3) === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成上一步', icon: 'none' })
    return
  }
  // If already done, still navigate to assessments overview
  uni.navigateTo({ url: '/pages/assessments/assessments' })
}

function onContinueAssessment() {
  const routeMap = {
    questionnaire: '/pages/questionnaire/questionnaire',
    mbti: '/pages/mbti/mbti',
    holland: '/pages/holland/holland',
  }
  const url = routeMap[nextAssessment.value]
  if (url) uni.navigateTo({ url })
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

// ---------- lifecycle ----------

onLoad((options = {}) => {
  if (options.inviterId) {
    membershipStore.setInviterId(options.inviterId)
  }
  membershipStore.login().catch(() => {})
})

onShow(() => {
  refresh()
  membershipStore.loadStatus().catch(() => {})
})
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 25%, #f9fafb 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
  padding-top: calc(52rpx + env(safe-area-inset-top));
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

// ---------- bg glow ----------

.bg-glow-soft {
  position: absolute;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.08) 0%, rgba(255, 255, 255, 0) 70%);
  top: -180rpx;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

// ---------- brand ----------

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 36rpx;
  z-index: 10;
}

.brand-logo {
  width: 84rpx;
  height: 84rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #f97316, #ea580c);
  box-shadow: 0 6rpx 20rpx rgba(249, 115, 22, 0.25);
  margin-bottom: 16rpx;
}

.brand-name {
  font-size: 38rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 10rpx;
}

.brand-greeting {
  font-size: 25rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.4;
}

// ---------- progress card ----------

.progress-card {
  width: 100%;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 28rpx 30rpx 24rpx;
  margin-bottom: 28rpx;
  z-index: 10;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18rpx;
}

.progress-title {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.progress-fraction {
  font-size: 40rpx;
  font-weight: 800;
  color: #f97316;
}

.progress-bar-track {
  width: 100%;
  height: 10rpx;
  background: #f3f4f6;
  border-radius: 10rpx;
  overflow: hidden;
  margin-bottom: 14rpx;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #f97316, #fb923c);
  border-radius: 10rpx;
  transition: width 0.4s ease;

  &.ready {
    background: linear-gradient(90deg, #10b981, #34d399);
  }
}

.progress-hint {
  font-size: 23rpx;
  color: $text-secondary;
}

// ---------- step card base ----------

.step-card {
  width: 100%;
  background: #ffffff;
  border-radius: 18rpx;
  padding: 28rpx 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  z-index: 10;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  transition: opacity 0.2s;

  &:active {
    transform: scale(0.985);
  }

  &.locked {
    opacity: 0.65;
  }

  &.expanded {
    flex-direction: column;
    align-items: stretch;
  }
}

.step-row-top {
  display: flex;
  align-items: center;
}

.step-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;
  transition: all 0.2s;

  &.done {
    background: #d1fae5;
  }

  &.active {
    background: linear-gradient(135deg, #f97316, #ea580c);
    box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.35);
  }

  &.locked {
    background: #f3f4f6;
  }
}

.step-icon-text {
  font-size: 26rpx;
  font-weight: 800;

  .done & {
    color: #059669;
  }

  .active & {
    color: #ffffff;
  }

  .locked & {
    color: #9ca3af;
  }
}

.step-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.step-title {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 6rpx;
}

.step-desc {
  font-size: 24rpx;
  line-height: 1.35;

  &.done {
    color: #059669;
  }

  &.active {
    color: #f97316;
  }

  &.locked {
    color: $text-muted;
  }
}

.step-arrow {
  font-size: 40rpx;
  color: #f97316;
  font-weight: bold;
  flex-shrink: 0;
  margin-left: 12rpx;
}

// ---------- step 3 expanded ----------

.step-expanded {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1px solid #f3f4f6;
}

.chips-row {
  display: flex;
  gap: 14rpx;
  margin-bottom: 20rpx;
}

.chip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14rpx 0;
  border-radius: 12rpx;
  background: #f9fafb;
  border: 1px solid #e5e7eb;

  &.done {
    background: #ecfdf5;
    border-color: rgba(16, 185, 129, 0.3);
  }
}

.chip-text {
  font-size: 23rpx;
  font-weight: 600;
  color: $text-secondary;

  .done & {
    color: #059669;
  }
}

.cta-btn {
  width: 100%;
  height: 84rpx;
  background: linear-gradient(135deg, #f97316, #ea580c);
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 18rpx rgba(249, 115, 22, 0.25);

  &:active {
    transform: scale(0.98);
    opacity: 0.95;
  }
}

.cta-btn-text {
  font-size: 29rpx;
  font-weight: 700;
  color: #ffffff;
}

// ---------- report hero ----------

.report-hero {
  width: 100%;
  background: linear-gradient(135deg, #f97316, #ea580c);
  border-radius: 20rpx;
  padding: 36rpx 34rpx;
  margin-bottom: 28rpx;
  position: relative;
  overflow: hidden;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.30);

  &:active {
    transform: scale(0.985);
    opacity: 0.95;
  }
}

.hero-glow {
  position: absolute;
  width: 300rpx;
  height: 300rpx;
  background: radial-gradient(circle, rgba(255, 215, 0, 0.18) 0%, rgba(255, 255, 255, 0) 70%);
  top: -80rpx;
  right: -60rpx;
  pointer-events: none;
}

.hero-content {
  display: flex;
  flex-direction: column;
  z-index: 2;
}

.hero-price {
  font-size: 44rpx;
  font-weight: 900;
  color: #ffffff;
}

.hero-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 4rpx;
}

.hero-cta {
  background: #ffffff;
  border-radius: 14rpx;
  padding: 18rpx 32rpx;
  z-index: 2;
}

.hero-cta-text {
  font-size: 28rpx;
  font-weight: 700;
  color: #ea580c;
}

.hero-invite-hint {
  position: absolute;
  bottom: 12rpx;
  right: 34rpx;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.6);
  z-index: 2;
}

// ---------- disclaimer ----------

.disclaimer {
  width: 100%;
  padding: 40rpx 0 24rpx;
  text-align: center;
  z-index: 10;
}

.disclaimer-text {
  font-size: 22rpx;
  color: $text-muted;
  line-height: 1.5;
  display: block;
  padding: 0 20rpx;
}

.privacy-link {
  display: block;
  font-size: 22rpx;
  color: #f97316;
  font-weight: 600;
  margin-top: 14rpx;
  text-decoration: underline;
}
</style>
