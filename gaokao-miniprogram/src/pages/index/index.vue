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
  // 暂时跳到 questionnaire；正式的编辑表单将在 Task 2.4 加入
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
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
