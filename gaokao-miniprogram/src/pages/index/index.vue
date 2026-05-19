<template>
  <view class="page">
    <!-- 品牌 Header -->
    <view class="header">
      <view class="logo">
        <text class="logo-text">峰</text>
      </view>
      <text class="title">峰哥咨询参考</text>
      <text class="subtitle">AI 志愿填报助手，专业的高考志愿参考建议</text>
    </view>

    <!-- 考生信息填报 -->
    <view class="profile-card">
      <view class="card-header">
        <text class="card-title">2026 高考志愿模拟填报</text>
        <text class="save-status">{{ saveStatus }}</text>
      </view>

      <picker :range="provinces" :value="provinceIndex" @change="onProvinceChange">
        <view class="field-row">
          <text class="field-label">省份</text>
          <view class="field-value-wrap">
            <text class="field-value" :class="{ placeholder: !profile.province }">{{ profile.province || '请选择' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </picker>

      <picker :range="categories" :value="categoryIndex" @change="onCategoryChange">
        <view class="field-row">
          <text class="field-label">科目</text>
          <view class="field-value-wrap">
            <text class="field-value" :class="{ placeholder: !profile.category }">{{ profile.category || '请选择' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </picker>

      <view class="field-row">
        <text class="field-label">分数</text>
        <view class="field-value-wrap">
          <input
            class="field-input"
            type="number"
            maxlength="3"
            :value="profile.score"
            placeholder="请输入"
            placeholder-class="input-placeholder"
            @input="onScoreInput"
          />
          <text class="field-unit">分</text>
        </view>
      </view>

      <view class="field-row field-row-last">
        <text class="field-label">位次</text>
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

      <view class="primary-btn" @click="onSmartFill">
        <text class="primary-btn-title">智能填报</text>
      </view>

      <text class="profile-hint">填写后，AI 咨询会自动带入你的省份、科目、分数和位次。</text>
    </view>

    <!-- 咨询入口 -->
    <view class="chat-entry" @click="goChat">
      <view class="chat-entry-content">
        <text class="chat-entry-title">免费咨询</text>
        <text class="chat-entry-sub">AI 实时对话 · 带着考生信息问更准</text>
      </view>
      <text class="chat-entry-arrow">›</text>
    </view>

    <!-- 测评卡片区 -->
    <view class="assessments-section">
      <view class="assessments-header">
        <text class="assessments-title">专业测评</text>
        <text class="assessments-count">{{ completedCount }}/3 已完成</text>
      </view>

      <!-- 五环问卷卡片 -->
      <view class="assessment-card" :class="{ completed: questionnaireCompleted }" @click="goQuestionnaire">
        <view class="assessment-card-left">
          <view class="assessment-icon">
            <text class="assessment-emoji">📋</text>
          </view>
          <view class="assessment-info">
            <text class="assessment-name">五环问卷</text>
            <text class="assessment-desc">{{ questionnaireCompleted ? '已完成' : `${questionnaire.completedCount}/22 题` }}</text>
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
            <text class="assessment-name">MBTI 性格测评</text>
            <text class="assessment-desc">{{ assessments.mbti.completed ? `已测出: ${assessments.mbti.type}` : '未完成' }}</text>
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
            <text class="assessment-name">霍兰德兴趣测评</text>
            <text class="assessment-desc">{{ assessments.holland.completed ? `已测出: ${assessments.holland.code}` : '未完成' }}</text>
          </view>
        </view>
        <view class="assessment-status" :class="{ completed: assessments.holland.completed }">
          <text class="status-text">{{ assessments.holland.completed ? '✓' : '›' }}</text>
        </view>
      </view>
    </view>

    <!-- 报告入口 -->
    <view class="report-entry" :class="{ disabled: !allAssessmentsCompleted }" @click="goReport">
      <view class="report-entry-content">
        <text class="report-entry-title">生成个人报告</text>
        <text class="report-entry-sub">{{ reportSubtitle }}</text>
      </view>
      <text class="report-entry-arrow" :class="{ disabled: !allAssessmentsCompleted }">{{ allAssessmentsCompleted ? '›' : '🔒' }}</text>
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">
      <text class="disclaimer-text">⚠️ 数据仅供参考，请以各省考试院公布信息为准</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { loadUserProfile, saveUserProfile, isProfileComplete, loadAssessments, loadQuestionnaire } from '../../utils/storage.js'
import { useMembershipStore } from '../../stores/membership.js'

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆'
]
const categories = ['物理类', '历史类']

const profile = ref(loadUserProfile())
const saveStatus = ref('自动保存')
const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())
const membershipStore = useMembershipStore()

const provinceIndex = computed(() => Math.max(0, provinces.indexOf(profile.value.province)))
const categoryIndex = computed(() => Math.max(0, categories.indexOf(profile.value.category)))

const questionnaireCompleted = computed(() => questionnaire.value.completedCount >= 22)

const allAssessmentsCompleted = computed(() => {
  return (
    assessments.value.mbti.completed &&
    assessments.value.holland.completed &&
    questionnaire.value.completedCount >= 22
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
    return '全部测评已完成 · 可生成深度报告'
  }
  return `还差 ${3 - completedCount.value} 个测评完成`
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
    membershipStore.markProfileCompleted(profile.value).catch(() => {})
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
  background: linear-gradient(135deg, $brand-gradient-start 0%, $brand-gradient-end 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
  padding-top: 104rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.logo {
  width: 112rpx;
  height: 112rpx;
  background: $brand-primary;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.logo-text {
  color: #fff;
  font-size: 50rpx;
  font-weight: bold;
}

.title {
  font-size: 40rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.subtitle {
  font-size: 26rpx;
  color: $text-secondary;
}

.profile-card {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 42rpx 32rpx 32rpx;
  box-shadow: 0 16rpx 40rpx rgba(249, 115, 22, 0.12);
  box-sizing: border-box;
  margin-bottom: 24rpx;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28rpx;
}

.card-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
}

.save-status {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.field-row {
  height: 104rpx;
  border-bottom: 2rpx solid $border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-row-last {
  border-bottom: none;
  margin-bottom: 28rpx;
}

.field-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
}

.field-value-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 260rpx;
}

.field-value {
  font-size: 30rpx;
  color: $text-secondary;
}

.placeholder,
.input-placeholder {
  color: $text-muted;
}

.chevron {
  margin-left: 18rpx;
  font-size: 46rpx;
  line-height: 1;
  color: $text-muted;
}

.field-input {
  width: 180rpx;
  text-align: right;
  font-size: 34rpx;
  color: $text-secondary;
}

.field-unit {
  margin-left: 14rpx;
  font-size: 28rpx;
  color: $text-secondary;
}

.primary-btn {
  width: 100%;
  background: $brand-primary;
  border-radius: $radius-full;
  height: 84rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 22rpx;
}

.primary-btn-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.profile-hint {
  display: block;
  text-align: center;
  font-size: 23rpx;
  color: $text-muted;
  line-height: 1.6;
}

.chat-entry {
  width: 100%;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(249, 115, 22, 0.16);
  border-radius: $radius-lg;
  padding: 28rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
  box-sizing: border-box;
}

.chat-entry-content {
  display: flex;
  flex-direction: column;
}

.chat-entry-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.chat-entry-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-secondary;
}

.chat-entry-arrow {
  font-size: 46rpx;
  color: $brand-primary;
}

.assessments-section {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  box-sizing: border-box;
}

.assessments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
  padding: 0 8rpx;
}

.assessments-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.assessments-count {
  font-size: 24rpx;
  color: $text-secondary;
  background: #F3F4F6;
  padding: 6rpx 16rpx;
  border-radius: $radius-full;
}

.assessment-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 16rpx;
  border-radius: $radius-lg;
  margin-bottom: 12rpx;
  background: #F9FAFB;
  transition: background-color 0.2s;
}

.assessment-card:last-child {
  margin-bottom: 0;
}

.assessment-card.completed {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.08));
  border: 1rpx solid rgba(16, 185, 129, 0.2);
}

.assessment-card-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.assessment-icon {
  width: 64rpx;
  height: 64rpx;
  background: rgba(249, 115, 22, 0.1);
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
}

.assessment-emoji {
  font-size: 32rpx;
}

.assessment-info {
  display: flex;
  flex-direction: column;
}

.assessment-name {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-primary;
  margin-bottom: 4rpx;
}

.assessment-desc {
  font-size: 23rpx;
  color: $text-secondary;
}

.assessment-status {
  width: 48rpx;
  height: 48rpx;
  background: $bg-white;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
}

.assessment-status.completed {
  background: linear-gradient(135deg, #10b981, #059669);
}

.status-text {
  font-size: 28rpx;
  color: $text-muted;
}

.assessment-status.completed .status-text {
  color: #fff;
  font-weight: 600;
}

.report-entry.disabled {
  opacity: 0.6;
}

.report-entry-arrow.disabled {
  opacity: 0.7;
}

.disclaimer {
  width: 100%;
  padding: 32rpx 0 48rpx;
  text-align: center;
}

.disclaimer-text {
  font-size: 22rpx;
  color: $text-muted;
}

.privacy-link {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 8rpx;
}

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
</style>
