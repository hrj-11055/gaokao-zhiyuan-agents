<template>
  <view class="page">
    <!-- 轻量背景层 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 品牌 Header -->
    <view class="header">
      <view class="logo-outer">
        <view class="logo-glow" />
        <image class="logo-img" src="/static/logo.png" mode="aspectFit" />
      </view>
      <text class="title">峰哥咨询参考</text>
      <text class="subtitle">先整理考生信息，再生成可讨论的志愿参考</text>
    </view>

    <!-- 考生信息填报 -->
    <view class="profile-card">
      <view class="card-header">
        <view class="card-title-wrap">
          <text class="card-kicker">第 1 步</text>
          <text class="card-title">填写考生基础信息</text>
        </view>
        <view class="save-status-wrap">
          <text class="pulse-dot" />
          <text class="save-status">{{ saveStatus }}</text>
        </view>
      </view>

      <view class="fields-container">
        <!-- 省份选择 -->
        <picker :range="provinces" :value="provinceIndex" @change="onProvinceChange">
          <view class="field-row">
            <view class="field-label-wrap">
              <text class="field-icon">📍</text>
              <text class="field-label">目标省份</text>
            </view>
            <view class="field-value-wrap">
              <text class="field-value" :class="{ placeholder: !profile.province }">{{ profile.province || '点击选择' }}</text>
              <text class="chevron">›</text>
            </view>
          </view>
        </picker>

        <!-- 科目选择 -->
        <picker :range="categories" :value="categoryIndex" @change="onCategoryChange">
          <view class="field-row">
            <view class="field-label-wrap">
              <text class="field-icon">📚</text>
              <text class="field-label">考生科目</text>
            </view>
            <view class="field-value-wrap">
              <text class="field-value" :class="{ placeholder: !profile.category }">{{ profile.category || '点击选择' }}</text>
              <text class="chevron">›</text>
            </view>
          </view>
        </picker>

        <!-- 分数输入 -->
        <view class="field-row">
          <view class="field-label-wrap">
            <text class="field-icon">⚡</text>
            <text class="field-label">高考分数</text>
          </view>
          <view class="field-value-wrap">
            <input
              class="field-input"
              type="number"
              maxlength="3"
              :value="profile.score"
              placeholder="输入实考分"
              placeholder-class="input-placeholder"
              @input="onScoreInput"
            />
            <text class="field-unit">分</text>
          </view>
        </view>

        <!-- 位次输入 -->
        <view class="field-row field-row-last">
          <view class="field-label-wrap">
            <text class="field-icon">🎯</text>
            <text class="field-label">全省位次</text>
          </view>
          <view class="field-value-wrap">
            <input
              class="field-input"
              type="number"
              maxlength="8"
              :value="profile.rank"
              placeholder="选填"
              placeholder-class="input-placeholder"
              @input="onRankInput"
            />
            <text class="field-unit">名</text>
          </view>
        </view>
      </view>

      <view class="profile-progress">
        <view class="profile-progress-copy">
          <text class="profile-progress-title">{{ profileProgressTitle }}</text>
          <text class="profile-progress-sub">省份、科类和分数会同步到后续咨询与报告中。</text>
        </view>
        <text class="profile-progress-count">{{ profileCompletedCount }} / 3</text>
      </view>

      <view class="primary-btn" :class="{ disabled: !isProfileReady }" @click="onSmartFill">
        <text class="primary-btn-title">{{ isProfileReady ? '保存并开始咨询' : '补全后开始咨询' }}</text>
      </view>

      <text class="profile-hint">位次可选；如果暂时没有，可以先用分数开始咨询。</text>
    </view>

    <!-- 免费实时咨询 -->
    <view class="chat-entry" @click="goChat">
      <view class="chat-entry-left">
        <view class="ai-avatar-pulse">
          <text class="ai-avatar-emoji">💬</text>
          <view class="pulse-ring" />
        </view>
        <view class="chat-entry-content">
          <text class="chat-entry-title">免费咨询一个具体问题</text>
          <text class="chat-entry-sub">适合先问分数段、专业方向、院校取舍</text>
        </view>
      </view>
      <text class="chat-entry-arrow">›</text>
    </view>

    <!-- 测评卡片 -->
    <view class="assessments-section">
      <view class="assessments-header">
        <view class="assessments-title-wrap">
          <text class="section-title-icon">📊</text>
          <text class="assessments-title">报告准备进度</text>
        </view>
        <text class="assessments-count">{{ completedCount }} / 3 已完成</text>
      </view>

      <view class="assessments-grid">
        <!-- 五环问卷卡片 -->
        <view class="assessment-card" :class="{ completed: questionnaireCompleted }" @click="goQuestionnaire">
          <view class="assessment-card-left">
            <view class="assessment-icon">
              <text class="assessment-emoji">📋</text>
            </view>
            <view class="assessment-info">
              <text class="assessment-name">五环特征评测</text>
              <text class="assessment-desc">{{ questionnaireCompleted ? '学习与家庭信息已记录' : `已答 ${questionnaire.completedCount} / ${QUESTIONNAIRE_REQUIRED_COUNT} 题` }}</text>
            </view>
          </view>
          <view class="assessment-status" :class="{ completed: questionnaireCompleted }">
            <text class="status-text">{{ questionnaireCompleted ? '✓' : '›' }}</text>
          </view>
        </view>

        <!-- MBTI 卡片 -->
        <view class="assessment-card" :class="{ completed: assessments.mbti.completed }" @click="goMbti">
          <view class="assessment-card-left">
            <view class="assessment-icon">
              <text class="assessment-emoji">🧠</text>
            </view>
            <view class="assessment-info">
              <text class="assessment-name">MBTI 性格模型</text>
              <text class="assessment-desc">{{ assessments.mbti.completed ? `结果: ${assessments.mbti.type}` : '了解思考和决策偏好' }}</text>
            </view>
          </view>
          <view class="assessment-status" :class="{ completed: assessments.mbti.completed }">
            <text class="status-text">{{ assessments.mbti.completed ? '✓' : '›' }}</text>
          </view>
        </view>

        <!-- 霍兰德卡片 -->
        <view class="assessment-card" :class="{ completed: assessments.holland.completed }" @click="goHolland">
          <view class="assessment-card-left">
            <view class="assessment-icon">
              <text class="assessment-emoji">💼</text>
            </view>
            <view class="assessment-info">
              <text class="assessment-name">霍兰德兴趣矩阵</text>
              <text class="assessment-desc">{{ assessments.holland.completed ? `结果: ${assessments.holland.code}` : '梳理职业兴趣方向' }}</text>
            </view>
          </view>
          <view class="assessment-status" :class="{ completed: assessments.holland.completed }">
            <text class="status-text">{{ assessments.holland.completed ? '✓' : '›' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 报告入口 -->
    <view class="report-entry" :class="{ disabled: !allAssessmentsCompleted }" @click="goReport">
      <view class="report-entry-content">
        <text class="report-entry-title">生成综合志愿参考报告</text>
        <text class="report-entry-sub">{{ reportSubtitle }}</text>
      </view>
      <text class="report-entry-arrow" :class="{ disabled: !allAssessmentsCompleted }">{{ allAssessmentsCompleted ? '›' : '🔒' }}</text>
    </view>

    <!-- 免责声明与隐私保护 -->
    <view class="disclaimer">
      <text class="disclaimer-text">结果仅供志愿填报参考，请以各省教育考试院和高校官方信息为准。</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loadUserProfile, saveUserProfile, isProfileComplete, loadAssessments, loadQuestionnaire, QUESTIONNAIRE_REQUIRED_COUNT } from '../../utils/storage.js'
import { useMembershipStore } from '../../stores/membership.js'

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆'
]
const categories = ['物理类', '历史类']

const profile = ref(loadUserProfile())
const saveStatus = ref('安全同步中')
const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())
const membershipStore = useMembershipStore()

const provinceIndex = computed(() => Math.max(0, provinces.indexOf(profile.value.province)))
const categoryIndex = computed(() => Math.max(0, categories.indexOf(profile.value.category)))

const questionnaireCompleted = computed(() => questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT)
const profileCompletedCount = computed(() => {
  let count = 0
  if (profile.value.province) count++
  if (profile.value.category) count++
  if (profile.value.score) count++
  return count
})
const isProfileReady = computed(() => isProfileComplete(profile.value))
const profileProgressTitle = computed(() =>
  isProfileReady.value ? '基础信息已就绪' : '先补全省份、科类和分数'
)

const allAssessmentsCompleted = computed(() => {
  return (
    assessments.value.mbti.completed &&
    assessments.value.holland.completed &&
    questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT
  )
})

const completedCount = computed(() => {
  let count = 0
  if (questionnaireCompleted.value) count++
  if (assessments.value.mbti.completed) count++
  if (assessments.value.holland.completed) count++
  return count
})

const reportSubtitle = computed(() => {
  if (allAssessmentsCompleted.value) {
    return '测评已完成，可生成适合家长一起查看的报告'
  }
  return `请先完成 3 项测评，还差 ${3 - completedCount.value} 项`
})

onLoad((options = {}) => {
  if (options.inviterId) {
    membershipStore.setInviterId(options.inviterId)
  }
  membershipStore.login().catch(() => {})
})

onShow(() => {
  profile.value = loadUserProfile()
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
  membershipStore.loadStatus().catch(() => {})
})

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  uni.navigateTo({ url: '/pages/mbti/mbti' })
}

function goHolland() {
  uni.navigateTo({ url: '/pages/holland/holland' })
}

function goReport() {
  if (!allAssessmentsCompleted.value) {
    uni.showToast({
      title: `还差 ${3 - completedCount.value} 个测评完成`,
      icon: 'none'
    })
    return
  }
  uni.navigateTo({ url: '/pages/report/report' })
}

function goPrivacy() {
  uni.navigateTo({ url: '/pages/privacy/privacy' })
}

function goChat() {
  uni.navigateTo({ url: '/pages/chat/chat' })
}

function persistProfile(nextProfile) {
  profile.value = saveUserProfile(nextProfile)
  saveStatus.value = '已自动保存'
  if (isProfileComplete(profile.value)) {
    membershipStore.syncProfile(profile.value).catch(() => {
      membershipStore.markProfileCompleted().catch(() => {})
    })
  }
}

function onProvinceChange(event) {
  const index = Number(event.detail.value)
  persistProfile({ ...profile.value, province: provinces[index] })
}

function onCategoryChange(event) {
  const index = Number(event.detail.value)
  persistProfile({ ...profile.value, category: categories[index] })
}

function onScoreInput(event) {
  persistProfile({ ...profile.value, score: event.detail.value })
}

function onRankInput(event) {
  persistProfile({ ...profile.value, rank: event.detail.value })
}

function onSmartFill() {
  if (!isProfileComplete(profile.value)) {
    uni.showToast({
      title: '请先填写省份、科目和分数',
      icon: 'none'
    })
    return
  }
  goChat()
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background:
    radial-gradient(95% 45% at 20% 0%, rgba(37, 99, 235, 0.08) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
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

.cyber-glow-bg-indigo,
.cyber-glow-bg-orange {
  position: absolute;
  width: 460rpx;
  height: 460rpx;
  pointer-events: none;
}

.cyber-glow-bg-indigo {
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, rgba(255, 255, 255, 0) 70%);
  top: -120rpx;
  left: -160rpx;
}

.cyber-glow-bg-orange {
  background: radial-gradient(circle, rgba(249, 115, 22, 0.035) 0%, rgba(255, 255, 255, 0) 70%);
  top: 360rpx;
  right: -160rpx;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28rpx;
  z-index: 10;
}

.logo-outer {
  position: relative;
  width: 96rpx;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18rpx;
}

.logo-img {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.10);
  border: 1px solid rgba(15, 23, 42, 0.06);
  z-index: 2;
}

.logo-glow {
  position: absolute;
  top: -8rpx;
  right: -8rpx;
  bottom: -8rpx;
  left: -8rpx;
  background: rgba(37, 99, 235, 0.14);
  border-radius: 50%;
  filter: blur(12rpx);
  z-index: 1;
}

.title {
  font-size: 40rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 12rpx;
  letter-spacing: 0;
}

.subtitle {
  font-size: 26rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.45;
}

.profile-card {
  width: 100%;
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 36rpx 32rpx 34rpx;
  z-index: 10;
  margin-bottom: 28rpx;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 28rpx;
  border-bottom: 1px solid $border-light;
  padding-bottom: 22rpx;
}

.card-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.card-kicker {
  font-size: 22rpx;
  color: $brand-primary;
  font-weight: 800;
}

.card-title {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
}

.save-status-wrap {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  background: #F8FAFC;
  padding: 6rpx 16rpx;
  border-radius: $radius-full;
  border: 1px solid $border-light;
}

.pulse-dot {
  width: 10rpx;
  height: 10rpx;
  background-color: #059669;
  border-radius: 50%;
  margin-right: 10rpx;
}

.save-status {
  font-size: 22rpx;
  color: $text-secondary;
}

.fields-container {
  display: flex;
  flex-direction: column;
  background: $bg-input;
  border-radius: $radius-md;
  border: 1px solid $border-light;
  margin-bottom: 24rpx;
  overflow: hidden;
}

.field-row {
  min-height: 104rpx;
  border-bottom: 1px solid $border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 0 28rpx;
  transition: background-color 0.2s;

  &:active {
    background: rgba(37, 99, 235, 0.04);
  }
}

.field-row-last {
  border-bottom: none;
}

.field-label-wrap,
.field-value-wrap {
  display: flex;
  align-items: center;
}

.field-icon {
  font-size: 30rpx;
  margin-right: 18rpx;
}

.field-label {
  font-size: 29rpx;
  font-weight: 600;
  color: $text-primary;
}

.field-value-wrap {
  justify-content: flex-end;
  min-width: 260rpx;
}

.field-value {
  font-size: 29rpx;
  color: $text-primary;
  font-weight: 500;
}

.placeholder,
.input-placeholder {
  color: $text-muted;
}

.chevron {
  margin-left: 18rpx;
  font-size: 40rpx;
  line-height: 1;
  color: $text-muted;
}

.field-input {
  width: 220rpx;
  text-align: right;
  font-size: 34rpx;
  font-weight: 700;
  color: $brand-primary;
}

.field-unit {
  margin-left: 14rpx;
  font-size: 26rpx;
  color: $text-secondary;
}

.profile-progress {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 22rpx 24rpx;
  margin-bottom: 24rpx;
  border-radius: $radius-md;
  background: #FFF7ED;
  border: 1px solid rgba(249, 115, 22, 0.18);
}

.profile-progress-copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.profile-progress-title {
  color: $text-primary;
  font-size: 27rpx;
  font-weight: 800;
}

.profile-progress-sub {
  color: $text-secondary;
  font-size: 23rpx;
  line-height: 1.4;
}

.profile-progress-count {
  flex-shrink: 0;
  color: $brand-primary;
  font-size: 28rpx;
  font-weight: 900;
}

.primary-btn {
  width: 100%;
  background: $grad-accent;
  border-radius: $radius-full;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.12);
  transition: transform 0.1s;

  &:active {
    transform: scale(0.98);
    opacity: 0.95;
  }
}

.primary-btn.disabled {
  background: #CBD5E1;
  box-shadow: none;
}

.primary-btn-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
}

.profile-hint {
  display: block;
  text-align: center;
  font-size: 23rpx;
  color: $text-muted;
  line-height: 1.6;
  padding: 0 10rpx;
}

.chat-entry,
.assessments-section {
  width: 100%;
  @include glass-panel;
  box-sizing: border-box;
  z-index: 10;
}

.chat-entry {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: $radius-lg;
  padding: 30rpx 36rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28rpx;
  transition: transform 0.1s;

  &:active {
    transform: scale(0.98);
    background: #EFF6FF;
  }
}

.chat-entry-left {
  display: flex;
  align-items: center;
  min-width: 0;
}

.ai-avatar-pulse {
  position: relative;
  width: 72rpx;
  height: 72rpx;
  background: #DBEAFE;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  border: 1px solid rgba(37, 99, 235, 0.16);
  flex-shrink: 0;
}

.ai-avatar-emoji {
  font-size: 34rpx;
  z-index: 2;
}

.pulse-ring {
  display: none;
}

.chat-entry-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-entry-title {
  font-size: 31rpx;
  font-weight: 700;
  color: $text-primary;
}

.chat-entry-sub {
  margin-top: 8rpx;
  font-size: 23rpx;
  color: $text-secondary;
  line-height: 1.35;
}

.chat-entry-arrow {
  font-size: 46rpx;
  color: $brand-violet;
  font-weight: bold;
  flex-shrink: 0;
}

.assessments-section {
  border-radius: $radius-xl;
  padding: 32rpx 28rpx;
  margin-bottom: 28rpx;
}

.assessments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 28rpx;
  padding: 0 8rpx;
}

.assessments-title-wrap {
  display: flex;
  align-items: center;
}

.section-title-icon {
  font-size: 30rpx;
  margin-right: 14rpx;
}

.assessments-title {
  font-size: 31rpx;
  font-weight: 700;
  color: $text-primary;
}

.assessments-count {
  flex-shrink: 0;
  font-size: 23rpx;
  font-weight: 600;
  color: #047857;
  background: rgba(16, 185, 129, 0.10);
  border: 1px solid rgba(16, 185, 129, 0.20);
  padding: 6rpx 20rpx;
  border-radius: $radius-full;
}

.assessments-grid {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.assessment-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  border-radius: $radius-md;
  background: #F8FAFC;
  border: 1px solid $border-light;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
  }

  &.completed {
    background: #ECFDF5;
    border-color: rgba(16, 185, 129, 0.24);
  }
}

.assessment-card-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.assessment-icon {
  width: 72rpx;
  height: 72rpx;
  background: #FFFFFF;
  border: 1px solid $border-light;
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 22rpx;
  flex-shrink: 0;
}

.assessment-emoji {
  font-size: 34rpx;
}

.assessment-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.assessment-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 6rpx;
}

.assessment-desc {
  font-size: 23rpx;
  color: $text-secondary;
  line-height: 1.35;
}

.assessment-status {
  width: 48rpx;
  height: 48rpx;
  background: #FFFFFF;
  border: 1px solid $border-light;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 16rpx;
  transition: all 0.2s;
  flex-shrink: 0;

  &.completed {
    background: $grad-success;
    border: none;
  }
}

.status-text {
  font-size: 26rpx;
  color: $text-secondary;
  font-weight: bold;
}

.assessment-status.completed .status-text {
  color: #fff;
  font-size: 24rpx;
}

.report-entry {
  width: 100%;
  background: $grad-royal;
  border-radius: $radius-lg;
  padding: 36rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  margin-top: 12rpx;
  z-index: 10;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 12rpx 30rpx rgba(37, 99, 235, 0.20);
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
    opacity: 0.95;
  }

  &.disabled {
    background: #FFFFFF !important;
    border: 1px solid $border-light;
    box-shadow: none;
    opacity: 1;
  }
}

.report-entry-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.report-entry-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #fff;
}

.report-entry-sub {
  margin-top: 8rpx;
  font-size: 23rpx;
  color: rgba(255, 255, 255, 0.88);
  line-height: 1.35;

  .disabled & {
    color: $text-secondary;
  }
}

.report-entry.disabled .report-entry-title {
  color: $text-primary;
}

.report-entry-arrow {
  font-size: 46rpx;
  color: #fff;
  font-weight: bold;
  flex-shrink: 0;

  &.disabled {
    color: $text-muted;
  }
}

.disclaimer {
  width: 100%;
  padding: 48rpx 0 24rpx;
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
  color: $brand-violet;
  font-weight: 600;
  margin-top: 14rpx;
  text-decoration: underline;
}
</style>
