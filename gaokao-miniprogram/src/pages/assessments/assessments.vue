<template>
  <view class="assessments-page">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">测评中心</text>
      <text class="page-subtitle">完成全部测评后，可生成个性化志愿报告</text>
    </view>

    <!-- 测评卡片列表 -->
    <view class="assessments-list">
      <!-- 五环问卷 -->
      <view class="assessment-card" @click="goQuestionnaire">
        <view class="card-icon" :class="{ completed: assessments.questionnaire.completedCount >= 22 }">
          <text class="icon-text">{{ assessments.questionnaire.completedCount >= 22 ? '✓' : '1' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">五环问卷</text>
            <view class="status-badge" :class="{ completed: assessments.questionnaire.completedCount >= 22 }">
              <text class="status-text">{{ getStatusText('questionnaire') }}</text>
            </view>
          </view>
          <text class="card-desc">22 题深度评估，了解你的兴趣、性格、能力</text>
          <text v-if="assessments.questionnaire.completedCount >= 22 && assessments.questionnaire.completedCount > 0" class="completion-time">
            完成于 {{ formatDate(assessments.questionnaire.updatedAt) }}
          </text>
        </view>
        <text class="card-arrow">›</text>
      </view>

      <!-- MBTI 性格测试 -->
      <view class="assessment-card" @click="goMbti">
        <view class="card-icon" :class="{ completed: assessments.mbti.completed }">
          <text class="icon-text">{{ assessments.mbti.completed ? '✓' : '2' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">MBTI 性格测试</text>
            <view class="status-badge" :class="{ completed: assessments.mbti.completed }">
              <text class="status-text">{{ getStatusText('mbti') }}</text>
            </view>
          </view>
          <text class="card-desc">16 型人格分析，发现你的职业倾向</text>
          <text v-if="assessments.mbti.completed" class="completion-time">
            完成于 {{ formatDate(assessments.mbti.completedAt) }}
          </text>
          <text v-if="assessments.mbti.completed && assessments.mbti.type" class="result-badge">
            {{ assessments.mbti.type }} 型
          </text>
        </view>
        <text class="card-arrow">›</text>
      </view>

      <!-- 霍兰德职业兴趣 -->
      <view class="assessment-card" @click="goHolland">
        <view class="card-icon" :class="{ completed: assessments.holland.completed }">
          <text class="icon-text">{{ assessments.holland.completed ? '✓' : '3' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">霍兰德职业兴趣</text>
            <view class="status-badge" :class="{ completed: assessments.holland.completed }">
              <text class="status-text">{{ getStatusText('holland') }}</text>
            </view>
          </view>
          <text class="card-desc">RIASEC 六大类型，匹配适合的专业方向</text>
          <text v-if="assessments.holland.completed" class="completion-time">
            完成于 {{ formatDate(assessments.holland.completedAt) }}
          </text>
          <text v-if="assessments.holland.completed && assessments.holland.code" class="result-badge">
            {{ assessments.holland.code }} 型
          </text>
        </view>
        <text class="card-arrow">›</text>
      </view>
    </view>

    <!-- 进度统计 -->
    <view class="progress-section">
      <view class="progress-header">
        <text class="progress-title">测评进度</text>
        <text class="progress-count">{{ completedCount }} / 3</text>
      </view>
      <view class="progress-bar">
        <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="footer-hint">
      <view class="hint-icon">💡</view>
      <view class="hint-content">
        <text class="hint-title">完成全部测评后</text>
        <text class="hint-text">可在首页生成个性化志愿报告，AI 会根据你的测评结果推荐专业和院校</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadAssessments } from '../../utils/storage.js'

const assessments = ref({
  mbti: { completed: false, type: '', completedAt: 0 },
  holland: { completed: false, code: '', completedAt: 0 },
  questionnaire: { completedCount: 0, updatedAt: 0 }
})

const completedCount = computed(() => {
  let count = 0
  if (assessments.value.questionnaire.completedCount >= 22) count++
  if (assessments.value.mbti.completed) count++
  if (assessments.value.holland.completed) count++
  return count
})

const progressPercent = computed(() => {
  return Math.round((completedCount.value / 3) * 100)
})

function loadAssessmentsData() {
  assessments.value = loadAssessments()
}

function formatDate(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

function getStatusText(type) {
  if (type === 'questionnaire') {
    return assessments.value.questionnaire.completedCount >= 22 ? '已完成' : '去测试'
  }
  if (type === 'mbti') {
    return assessments.value.mbti.completed ? '已完成' : '去测试'
  }
  if (type === 'holland') {
    return assessments.value.holland.completed ? '已完成' : '去测试'
  }
  return '去测试'
}

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (assessments.value.mbti.completed) {
    // 已完成，跳转到结果页
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    // 未完成，跳转到测评页
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (assessments.value.holland.completed) {
    // 已完成，跳转到结果页
    uni.navigateTo({ url: '/pages/holland/holland-result' })
  } else {
    // 未完成，跳转到测评页
    uni.navigateTo({ url: '/pages/holland/holland' })
  }
}

onMounted(() => {
  loadAssessmentsData()
  uni.setNavigationBarTitle({
    title: '测评'
  })
})

onShow(() => {
  loadAssessmentsData()
})
</script>

<style lang="scss" scoped>
.assessments-page {
  min-height: 100vh;
  background: $bg-page;
  padding: 32rpx;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40rpx;
}

.page-title {
  font-size: 40rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.page-subtitle {
  font-size: 26rpx;
  color: $text-secondary;
  text-align: center;
}

.assessments-list {
  margin-bottom: 32rpx;
}

.assessment-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 28rpx 24rpx;
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
  position: relative;
  overflow: hidden;
}

.card-icon {
  width: 64rpx;
  height: 64rpx;
  background: $bg-input;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.card-icon.completed {
  background: linear-gradient(135deg, #10B981, #059669);
}

.icon-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
}

.card-icon.completed .icon-text {
  color: #fff;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
}

.status-badge {
  padding: 6rpx 16rpx;
  background: $bg-input;
  border-radius: $radius-full;
}

.status-badge.completed {
  background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
}

.status-text {
  font-size: 22rpx;
  color: $text-secondary;
}

.status-badge.completed .status-text {
  color: #059669;
  font-weight: 500;
}

.card-desc {
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 6rpx;
}

.completion-time {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 4rpx;
}

.result-badge {
  display: inline-block;
  margin-top: 6rpx;
  padding: 4rpx 12rpx;
  background: linear-gradient(135deg, $brand-primary-light, $brand-primary);
  border-radius: $radius-sm;
  font-size: 20rpx;
  color: #fff;
  font-weight: 500;
  align-self: flex-start;
}

.card-arrow {
  font-size: 48rpx;
  color: $text-muted;
  margin-left: 12rpx;
  flex-shrink: 0;
}

.progress-section {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 28rpx 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.progress-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.progress-count {
  font-size: 26rpx;
  font-weight: 600;
  color: $brand-primary;
}

.progress-bar {
  height: 12rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, $brand-primary, $brand-primary-dark);
  border-radius: $radius-full;
  transition: width 0.3s ease;
}

.footer-hint {
  background: linear-gradient(135deg, #FEF3C7, #FDE68A);
  border-radius: $radius-xl;
  padding: 24rpx 28rpx;
  display: flex;
  align-items: flex-start;
}

.hint-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.hint-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hint-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #92400E;
  margin-bottom: 6rpx;
}

.hint-text {
  font-size: 24rpx;
  color: #B45309;
  line-height: 1.6;
}
</style>
