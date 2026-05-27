<template>
  <view class="page">
    <view class="bg-glow-teal" />
    <view class="bg-glow-purple" />

    <view class="brand">
      <view class="brand-top">
        <image class="brand-logo" src="/static/logo.png" mode="aspectFit" />
        <text class="brand-name">高考志愿通</text>
      </view>
      <text class="brand-greeting">{{ greetingText }}</text>
    </view>

    <!-- 总体进度 -->
    <view class="progress-section">
      <text class="progress-title">你的升学之路</text>
      <text class="progress-fraction">{{ completedSteps }}/4 步</text>
    </view>

    <view class="timeline-container">
      <view class="timeline-line">
        <view class="timeline-progress" :style="{ height: progressPercent + '%' }"></view>
      </view>

      <!-- step 1 -->
      <view class="timeline-item" @click="onClickStep1">
        <view class="timeline-dot" :class="step1ClassObj">
          <text v-if="statusFor(1) === StepStatus.DONE" class="dot-icon">✓</text>
        </view>
        <view class="step-card glass-card" :class="step1ClassObj">
          <view class="step-header">
            <text class="step-title">1. 完善个人信息</text>
            <view v-if="statusFor(1) === StepStatus.DONE" class="status-badge done">✓ 已完成</view>
          </view>
          <text class="step-desc">{{ step1DescText }}</text>
        </view>
      </view>

      <!-- step 2 -->
      <view class="timeline-item" @click="onClickStep2">
        <view class="timeline-dot" :class="step2ClassObj">
          <text v-if="statusFor(2) === StepStatus.DONE" class="dot-icon">✓</text>
        </view>
        <view class="step-card glass-card ai-card" :class="step2ClassObj">
          <view class="ai-card-content">
            <view class="ai-info">
              <text class="step-title">2. 与 AI 助手交流</text>
              <text class="step-desc">{{ step2DescText }}</text>
            </view>
            <view class="ai-avatar-wrapper">
              <view class="ai-avatar-glow"></view>
              <view class="ai-avatar">🤖</view>
            </view>
          </view>
          <view v-if="statusFor(2) === StepStatus.ACTIVE" class="cta-btn">
            <text class="cta-btn-text">开始对话</text>
          </view>
        </view>
      </view>

      <!-- step 3 -->
      <view class="timeline-item" @click="onClickStep3">
        <view class="timeline-dot" :class="step3ClassObj">
          <text v-if="statusFor(3) === StepStatus.DONE" class="dot-icon">✓</text>
        </view>
        <view class="step-card glass-card" :class="[step3ClassObj, { expanded: statusFor(3) === StepStatus.ACTIVE }]">
          <view class="step-header">
            <text class="step-title">3. 完成背景测试</text>
            <view v-if="statusFor(3) === StepStatus.DONE" class="status-badge done">✓ 已完成</view>
            <view v-else-if="statusFor(3) === StepStatus.LOCKED" class="status-badge locked">待解锁</view>
          </view>
          <text class="step-desc">{{ step3DescText }}</text>

          <view v-if="statusFor(3) === StepStatus.ACTIVE" class="step-expanded">
            <view class="chips-row">
              <view class="chip" :class="{ done: questionnaireDone }">
                <text class="chip-text">五环 {{ questionnaireDone ? '✓' : `已答 ${questionnaire.completedCount} / ${QUESTIONNAIRE_REQUIRED_COUNT} 题` }}</text>
              </view>
              <view class="chip" :class="{ done: mbtiDone }">
                <text class="chip-text">MBTI {{ chipStatus('mbti') }}</text>
              </view>
              <view class="chip" :class="{ done: hollandDone }">
                <text class="chip-text">霍兰德 {{ chipStatus('holland') }}</text>
              </view>
            </view>
            <view v-if="nextAssessment" class="cta-btn sm" @click.stop="onContinueAssessment">
              <text class="cta-btn-text">{{ nextAssessmentCtaText }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- step 4 -->
      <view class="timeline-item" @click="onClickStep4">
        <view class="timeline-dot" :class="step4ClassObj">
          <text v-if="step4Status === StepStatus.DONE" class="dot-icon">✓</text>
          <text v-else-if="step4Status === StepStatus.LOCKED" class="dot-icon locked">🔒</text>
        </view>
        <view class="step-card glass-card" :class="step4ClassObj">
          <view class="step-header">
            <text class="step-title">4. 生成专属报告</text>
            <view v-if="step4Status === StepStatus.DONE" class="status-badge done">✓ 已生成</view>
          </view>
          <text class="step-desc">{{ step4DescText }}</text>
          
          <!-- report hero embedded in step 4 -->
          <view v-if="step3Done && !membershipStore.isActive && step4Status !== StepStatus.DONE" class="report-hero" @click.stop="goReport">
            <view class="hero-content">
              <text class="hero-price">{{ MEMBERSHIP_PRICE_LABEL }}</text>
              <text class="hero-label">一次解锁</text>
            </view>
            <view class="hero-cta">
              <text class="hero-cta-text">立即生成</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- disclaimer -->
    <view class="disclaimer">
      <text class="disclaimer-text">结果仅供参考，请结合官方信息为准</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
    </view>

    <!-- profile sheet mask -->
    <view v-if="showProfileSheet" class="sheet-mask" @click="closeProfileSheet" />

    <!-- profile bottom sheet -->
    <view v-if="showProfileSheet" class="sheet">
      <view class="sheet-header">
        <text class="sheet-title">完善个人信息</text>
        <text class="sheet-close" @click="closeProfileSheet">✕</text>
      </view>

      <view class="sheet-field">
        <text class="sheet-label">📍 目标省份</text>
        <picker :range="provinces" @change="onProvinceChange">
          <text class="sheet-value">{{ draft.province || '点击选择' }}</text>
        </picker>
      </view>

      <view class="sheet-field">
        <text class="sheet-label">📚 考生科目</text>
        <picker :range="categories" @change="onCategoryChange">
          <text class="sheet-value">{{ draft.category || '点击选择' }}</text>
        </picker>
      </view>

      <view class="sheet-field">
        <text class="sheet-label">⚡ 高考分数</text>
        <input class="sheet-input" type="number" :value="draft.score" maxlength="3" placeholder="输入分数" placeholder-class="sheet-value" @input="onDraftScoreInput" />
      </view>

      <view class="sheet-field">
        <text class="sheet-label">🎯 全省位次（选填）</text>
        <input class="sheet-input" type="number" :value="draft.rank" maxlength="8" placeholder="输入位次" placeholder-class="sheet-value" @input="onDraftRankInput" />
      </view>

      <view class="sheet-save" :class="{ disabled: !sheetReady }" @click="saveProfileSheet">
        <text style="color: inherit; font-weight: inherit; font-size: inherit;">保存并继续</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useHomeProgress, StepStatus } from '../../composables/useHomeProgress.js'
import { useMembershipStore } from '../../stores/membership.js'
import { MEMBERSHIP_PRICE_LABEL } from '../../config.js'
import {
  saveUserProfile,
  loadUserProfile,
  isProfileComplete,
  QUESTIONNAIRE_REQUIRED_COUNT,
} from '../../utils/storage.js'

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
  reportDone,
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
  if (!reportDone.value) return `${base} · 待生成报告`
  return `${base} · 报告已生成`
})

// ---------- progress ----------

const progressPercent = computed(() => Math.min(100, (completedSteps.value / 4) * 100))

const progressHint = computed(() => {
  if (completedSteps.value === 0) return '从第 1 步开始'
  if (!step3Done.value) return `还差 ${4 - completedSteps.value} 步`
  if (!reportDone.value) return '资料已就绪，下一步生成报告'
  return '报告已生成'
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
  return statusFor(4)
})
const step4ClassObj = computed(() => classForStatus(step4Status.value))
const step4IconText = computed(() => {
  if (step4Status.value === StepStatus.DONE) return '✓'
  return '4'
})
const step4DescText = computed(() => {
  if (step4Status.value === StepStatus.DONE) return '报告已生成'
  if (membershipStore.isActive) return '已解锁，点击生成报告'
  return `${MEMBERSHIP_PRICE_LABEL} 一次解锁 · 邀请 5 人免费`
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
  openProfileSheet()
}

// ---------- profile sheet ----------

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆'
]
const categories = ['物理类', '历史类']

const showProfileSheet = ref(false)
const draft = ref({ province: '', category: '', score: '', rank: '' })

const provinceIndex = computed(() => provinces.indexOf(draft.value.province))
const categoryIndex = computed(() => categories.indexOf(draft.value.category))
const sheetReady = computed(() => isProfileComplete(draft.value))

function openProfileSheet() {
  const saved = loadUserProfile()
  draft.value = {
    province: saved.province || '',
    category: saved.category || '',
    score: saved.score !== '' ? String(saved.score) : '',
    rank: saved.rank !== '' ? String(saved.rank) : ''
  }
  showProfileSheet.value = true
}

function closeProfileSheet() {
  showProfileSheet.value = false
}

function onProvinceChange(e) {
  draft.value.province = provinces[e.detail.value] || ''
}

function onCategoryChange(e) {
  draft.value.category = categories[e.detail.value] || ''
}

function onDraftScoreInput(e) {
  draft.value.score = e.detail.value
}

function onDraftRankInput(e) {
  draft.value.rank = e.detail.value
}

function saveProfileSheet() {
  if (!sheetReady.value) return
  const saved = saveUserProfile({
    province: draft.value.province,
    category: draft.value.category,
    score: draft.value.score,
    rank: draft.value.rank
  })
  profile.value = saved
  membershipStore.syncProfile(profile.value).catch(() => {
    membershipStore.markProfileCompleted().catch(() => {})
  })
  closeProfileSheet()
  refresh()
  uni.showToast({ title: '保存成功', icon: 'success' })
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

onMounted(() => {
  uni.$on('open-profile-sheet', openProfileSheet)
})

onUnmounted(() => {
  uni.$off('open-profile-sheet', openProfileSheet)
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

// ---------- profile sheet ----------

.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  z-index: 99;
}

.sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  border-radius: 28rpx 28rpx 0 0;
  padding: 28rpx 32rpx 60rpx;
  z-index: 100;
  box-shadow: 0 -8rpx 24rpx rgba(17, 24, 39, 0.1);
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22rpx;
}

.sheet-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #111827;
}

.sheet-close {
  font-size: 36rpx;
  color: #9ca3af;
  padding: 4rpx 12rpx;
}

.sheet-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f3f4f6;
}

.sheet-label {
  font-size: 26rpx;
  color: #374151;
}

.sheet-value {
  font-size: 26rpx;
  color: #111827;
  font-weight: 500;
}

.sheet-input {
  font-size: 26rpx;
  color: #111827;
  text-align: right;
  width: 280rpx;
}

.sheet-save {
  margin-top: 24rpx;
  padding: 26rpx;
  background: linear-gradient(90deg, #f97316, #ea580c);
  color: white;
  text-align: center;
  font-weight: 700;
  font-size: 30rpx;
  border-radius: 18rpx;
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);

  &.disabled {
    background: #e5e7eb;
    color: #9ca3af;
    box-shadow: none;
  }
}
</style>
