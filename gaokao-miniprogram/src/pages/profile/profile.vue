<template>
  <view class="profile-page">
    <!-- Header with avatar -->
    <view class="profile-header">
      <view class="avatar">
        <text class="avatar-text">峰</text>
      </view>
      <text class="user-title">峰哥咨询参考</text>
      <text class="user-subtitle">AI 志愿填报助手</text>
    </view>

    <!-- 综合志愿报告 Card -->
    <view class="report-card" @click="goReport">
      <view class="report-icon">📊</view>
      <view class="report-content">
        <text class="report-title">综合志愿报告</text>
        <text class="report-desc">完成全部测评后生成个性化报告</text>
      </view>
      <view class="report-status" :class="{ ready: canGenerateReport }">
        <text class="status-text">{{ canGenerateReport ? '可生成' : `${completedCount}/3` }}</text>
      </view>
      <text class="card-arrow">›</text>
    </view>

    <!-- 测评记录列表 -->
    <view class="section">
      <text class="section-title">测评记录</text>
      <view class="records-list">
        <!-- 五环问卷 -->
        <view class="record-item" @click="goQuestionnaire">
          <view class="record-icon" :class="{ completed: isQuestionnaireComplete }">
            <text class="icon-text">✓</text>
          </view>
          <view class="record-content">
            <text class="record-title">五环问卷</text>
            <text class="record-desc">{{ questionnaireRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>

        <!-- MBTI -->
        <view class="record-item" @click="goMbti">
          <view class="record-icon" :class="{ completed: isMbtiComplete }">
            <text class="icon-text">✓</text>
          </view>
          <view class="record-content">
            <text class="record-title">MBTI 性格测试</text>
            <text class="record-desc">{{ mbtiRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>

        <!-- 霍兰德 -->
        <view class="record-item" @click="goHolland">
          <view class="record-icon" :class="{ completed: isHollandComplete }">
            <text class="icon-text">✓</text>
          </view>
          <view class="record-content">
            <text class="record-title">霍兰德职业兴趣</text>
            <text class="record-desc">{{ hollandRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 设置区域 -->
    <view class="section">
      <text class="section-title">设置</text>
      <view class="settings-list">
        <view class="setting-item" @click="clearData">
          <text class="setting-title">清除数据</text>
          <text class="setting-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="footer-hint">
      <text class="hint-text">数据仅供参考，请以各省考试院公布信息为准</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadAssessments, loadQuestionnaire, getCompletedAssessmentsCount } from '../../utils/storage.js'

const assessments = ref({
  mbti: { completed: false, type: '', completedAt: 0 },
  holland: { completed: false, code: '', completedAt: 0 },
  questionnaire: { completedCount: 0, updatedAt: 0 }
})

const questionnaire = ref({
  answers: {},
  completedCount: 0,
  updatedAt: 0
})

const completedCount = ref(0)

const canGenerateReport = computed(() => completedCount.value >= 3)

const isQuestionnaireComplete = computed(() => questionnaire.value.completedCount >= 22)
const isMbtiComplete = computed(() => assessments.value.mbti.completed)
const isHollandComplete = computed(() => assessments.value.holland.completed)

const questionnaireRecordText = computed(() => {
  if (isQuestionnaireComplete.value) {
    return `已完成 ${formatDate(questionnaire.value.updatedAt)}`
  }
  return questionnaire.value.completedCount > 0
    ? `已完成 ${questionnaire.value.completedCount}/22 题`
    : '未开始'
})

const mbtiRecordText = computed(() => {
  if (isMbtiComplete.value) {
    const type = assessments.value.mbti.type || ''
    const typeStr = type ? ` · ${type}型` : ''
    return `已完成${typeStr} ${formatDate(assessments.value.mbti.completedAt)}`
  }
  return '未开始'
})

const hollandRecordText = computed(() => {
  if (isHollandComplete.value) {
    const code = assessments.value.holland.code || ''
    const codeStr = code ? ` · ${code}型` : ''
    return `已完成${codeStr} ${formatDate(assessments.value.holland.completedAt)}`
  }
  return '未开始'
})

function loadData() {
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
  completedCount.value = getCompletedAssessmentsCount()
}

function formatDate(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

function goReport() {
  if (!canGenerateReport.value) {
    uni.showToast({
      title: `请先完成全部测评 (${completedCount.value}/3)`,
      icon: 'none',
      duration: 2000
    })
    return
  }
  uni.navigateTo({ url: '/pages/report/report' })
}

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (isMbtiComplete.value) {
    uni.navigateTo({ url: '/pages/mbti/result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (isHollandComplete.value) {
    uni.navigateTo({ url: '/pages/holland/result' })
  } else {
    uni.navigateTo({ url: '/pages/holland/holland' })
  }
}

function clearData() {
  uni.showModal({
    title: '清除数据',
    content: '确定要清除所有本地数据吗？此操作不可恢复。',
    confirmText: '清除',
    confirmColor: '#F97316',
    success: (res) => {
      if (res.confirm) {
        // TODO: 实现清除数据逻辑
        uni.showToast({
          title: '功能开发中',
          icon: 'none'
        })
      }
    }
  })
}

onMounted(() => {
  loadData()
  uni.setNavigationBarTitle({
    title: '我的'
  })
})

onShow(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: $bg-page;
  padding: 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40rpx;
  padding-top: 20rpx;
}

.avatar {
  width: 112rpx;
  height: 112rpx;
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  border-radius: $radius-xl;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.3);
}

.avatar-text {
  color: #fff;
  font-size: 50rpx;
  font-weight: bold;
}

.user-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.user-subtitle {
  font-size: 26rpx;
  color: $text-muted;
}

.report-card {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border-radius: $radius-xl;
  padding: 28rpx 24rpx;
  display: flex;
  align-items: center;
  margin-bottom: 32rpx;
  box-shadow: 0 8rpx 24rpx rgba(124, 58, 237, 0.3);
}

.report-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}

.report-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.report-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
  margin-bottom: 6rpx;
}

.report-desc {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.report-status {
  padding: 8rpx 20rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: $radius-full;
  margin-right: 12rpx;
}

.report-status.ready {
  background: rgba(16, 185, 129, 0.9);
}

.status-text {
  font-size: 22rpx;
  color: #fff;
  font-weight: 500;
}

.card-arrow {
  font-size: 48rpx;
  color: rgba(255, 255, 255, 0.8);
}

.section {
  margin-bottom: 32rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 16rpx;
  display: block;
}

.records-list {
  background: $bg-white;
  border-radius: $radius-xl;
  overflow: hidden;
}

.record-item {
  display: flex;
  align-items: center;
  padding: 28rpx 24rpx;
  border-bottom: 2rpx solid $border-light;
}

.record-item:last-child {
  border-bottom: none;
}

.record-icon {
  width: 48rpx;
  height: 48rpx;
  background: $bg-input;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.record-icon.completed {
  background: linear-gradient(135deg, #10B981, #059669);
}

.icon-text {
  font-size: 24rpx;
  color: $text-muted;
}

.record-icon.completed .icon-text {
  color: #fff;
  font-weight: 600;
}

.record-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.record-title {
  font-size: 30rpx;
  font-weight: 500;
  color: $text-primary;
  margin-bottom: 6rpx;
}

.record-desc {
  font-size: 24rpx;
  color: $text-muted;
}

.record-arrow {
  font-size: 40rpx;
  color: $text-muted;
}

.settings-list {
  background: $bg-white;
  border-radius: $radius-xl;
  overflow: hidden;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 24rpx;
}

.setting-title {
  font-size: 30rpx;
  color: $text-primary;
}

.setting-arrow {
  font-size: 40rpx;
  color: $text-muted;
}

.footer-hint {
  text-align: center;
  padding: 32rpx 0;
}

.hint-text {
  font-size: 22rpx;
  color: $text-muted;
}
</style>
