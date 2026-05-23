<template>
  <view class="assessments-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">测评与报告准备</text>
      <text class="page-subtitle">完成 3 项测评后，报告会更准确地结合学习方式、性格和职业兴趣。</text>
    </view>

    <!-- 进度统计仪表板 -->
    <view class="progress-section">
      <view class="progress-header">
        <text class="progress-title">报告准备度</text>
        <text class="progress-count">{{ progressPercent }}%</text>
      </view>
      <view class="progress-bar-container">
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }">
            <view class="progress-fill-glow" />
          </view>
        </view>
        <text class="progress-count-text">{{ completedCount }} / 3 项已完成</text>
      </view>
    </view>

    <!-- 测评卡片列表 -->
    <view class="assessments-list">
      <!-- 五环问卷 -->
      <view class="assessment-card" :class="{ completed: assessments.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT }" @click="goQuestionnaire">
        <view class="card-icon" :class="{ completed: assessments.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT }">
          <text class="icon-text">{{ assessments.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT ? '✓' : '1' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">五环特征综合评测</text>
            <view class="status-badge" :class="{ completed: assessments.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT }">
              <text class="status-text">{{ getStatusText('questionnaire') }}</text>
            </view>
          </view>
          <text class="card-desc">21 维全面学习风格，记录学习方式、学业压力、家庭期待和目标偏好</text>
          <text v-if="assessments.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT && assessments.questionnaire.completedCount > 0" class="completion-time">
            同步完成于 {{ formatDate(assessments.questionnaire.updatedAt) }}
          </text>
        </view>
        <text class="card-arrow">›</text>
      </view>

      <!-- MBTI 性格测试 -->
      <view class="assessment-card" :class="{ completed: assessments.mbti.completed }" @click="goMbti">
        <view class="card-icon" :class="{ completed: assessments.mbti.completed }">
          <text class="icon-text">{{ assessments.mbti.completed ? '✓' : '2' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">MBTI 16型人格定位</text>
            <view class="status-badge" :class="{ completed: assessments.mbti.completed }">
              <text class="status-text">{{ getStatusText('mbti') }}</text>
            </view>
          </view>
          <text class="card-desc">挖掘与生俱来的行为模式与最佳专业学习心智机制</text>
          <text v-if="assessments.mbti.completed" class="completion-time">
            同步完成于 {{ formatDate(assessments.mbti.completedAt) }}
          </text>
          <view v-if="assessments.mbti.completed" class="result-badges-row">
            <text class="result-badge">人格类型: {{ assessments.mbti.type }}</text>
            <text v-if="assessments.mbti.version" class="version-micro-tag" :class="assessments.mbti.version">
              {{ assessments.mbti.version === 'basic' ? '⚡ 精简版' : '🔬 完整版' }}
            </text>
          </view>
        </view>
        <text class="card-arrow">›</text>
      </view>

      <!-- 霍兰德职业兴趣 -->
      <view class="assessment-card" :class="{ completed: assessments.holland.completed }" @click="goHolland">
        <view class="card-icon" :class="{ completed: assessments.holland.completed }">
          <text class="icon-text">{{ assessments.holland.completed ? '✓' : '3' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">霍兰德 RIASEC 职业矩阵</text>
            <view class="status-badge" :class="{ completed: assessments.holland.completed }">
              <text class="status-text">{{ getStatusText('holland') }}</text>
            </view>
          </view>
          <text class="card-desc">从六类职业兴趣中判断更适合的专业方向</text>
          <text v-if="assessments.holland.completed" class="completion-time">
            同步完成于 {{ formatDate(assessments.holland.completedAt) }}
          </text>
          <view v-if="assessments.holland.completed" class="result-badges-row">
            <text class="result-badge">兴趣矩阵: {{ assessments.holland.code }}</text>
            <text v-if="assessments.holland.version" class="version-micro-tag" :class="assessments.holland.version">
              {{ assessments.holland.version === 'basic' ? '⚡ 精简版' : '🔬 完整版' }}
            </text>
          </view>
        </view>
        <text class="card-arrow">›</text>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="footer-hint">
      <view class="hint-icon">💡</view>
      <view class="hint-content">
        <text class="hint-title">为什么要先完成测评</text>
        <text class="hint-text">测评结果会用于补充“分数之外的信息”，帮助报告说明哪些专业更适合、哪些方向需要谨慎。</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadAssessments, QUESTIONNAIRE_REQUIRED_COUNT } from '../../utils/storage.js'

const assessments = ref({
  mbti: { completed: false, type: '', completedAt: 0 },
  holland: { completed: false, code: '', completedAt: 0 },
  questionnaire: { completedCount: 0, updatedAt: 0 }
})

const completedCount = computed(() => {
  let count = 0
  if (assessments.value.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT) count++
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
    return assessments.value.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT ? '匹配成功' : '去评测'
  }
  if (type === 'mbti') {
    return assessments.value.mbti.completed ? '已完成' : '去评测'
  }
  if (type === 'holland') {
    return assessments.value.holland.completed ? '已完成' : '去评测'
  }
  return '去评测'
}

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (assessments.value.mbti.completed) {
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (assessments.value.holland.completed) {
    uni.navigateTo({ url: '/pages/holland/holland-result' })
  } else {
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
  background:
    radial-gradient(90% 45% at 20% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  padding: 32rpx;
  padding-top: calc(32rpx + env(safe-area-inset-top));
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.cyber-glow-bg-indigo {
  position: absolute;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, rgba(0, 0, 0, 0) 70%);
  top: -100rpx;
  right: -150rpx;
  pointer-events: none;
}
.cyber-glow-bg-orange {
  position: absolute;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.035) 0%, rgba(0, 0, 0, 0) 70%);
  bottom: 200rpx;
  left: -150rpx;
  pointer-events: none;
}

.page-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20rpx;
  margin-bottom: 48rpx;
  z-index: 10;
}

.page-title {
  font-size: 42rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 12rpx;
  letter-spacing: 0;
}

.page-subtitle {
  font-size: 25rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.5;
  padding: 0 20rpx;
}

.assessments-list {
  margin-bottom: 32rpx;
  z-index: 10;
}

.progress-section {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 36rpx 36rpx;
  margin-bottom: 36rpx;
  z-index: 10;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.progress-title {
  font-size: 29rpx;
  font-weight: 700;
  color: $text-primary;
}

.progress-count {
  font-size: 32rpx;
  font-weight: 800;
  color: $brand-primary;
}

.progress-bar-container {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.progress-bar {
  height: 16rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.04);
}

.progress-fill {
  height: 100%;
  background: $grad-royal;
  border-radius: $radius-full;
  transition: width 0.4s cubic-bezier(0.1, 0.76, 0.55, 0.94);
  position: relative;
}

.progress-fill-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 20rpx;
  height: 100%;
  background: #fff;
  filter: blur(4rpx);
  opacity: 0.8;
}

.progress-count-text {
  font-size: 23rpx;
  color: $text-secondary;
  font-weight: 500;
}

.assessment-card {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 32rpx 28rpx;
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  position: relative;
  overflow: hidden;
  transition: all 0.25s;

  &:active {
    transform: scale(0.98);
  }

  &.completed {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(255, 255, 255, 0.9) 100%);
    border: 1px solid rgba(16, 185, 129, 0.25);
  }
}

.card-icon {
  width: 76rpx;
  height: 76rpx;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;
  transition: all 0.2s;

  &.completed {
    background: $grad-success;
    border: none;
  }
}

.icon-text {
  font-size: 30rpx;
  font-weight: 800;
  color: $text-secondary;

  .completed & {
    color: #fff;
  }
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
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.status-badge {
  padding: 6rpx 18rpx;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;

  &.completed {
    background: rgba(16, 185, 129, 0.08) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
  }
}

.status-text {
  font-size: 22rpx;
  color: $text-secondary;
}

.status-badge.completed .status-text {
  color: #10B981;
  font-weight: 600;
}

.card-desc {
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.5;
}

.completion-time {
  font-size: 21rpx;
  color: $text-muted;
  margin-top: 10rpx;
}

.result-badge {
  display: inline-block;
  margin-top: 12rpx;
  padding: 6rpx 18rpx;
  background: $grad-accent;
  border-radius: $radius-xs;
  font-size: 21rpx;
  color: #fff;
  font-weight: 700;
  align-self: flex-start;
  box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.25);
}

.card-arrow {
  font-size: 46rpx;
  color: $text-muted;
  margin-left: 16rpx;
  flex-shrink: 0;
}

.footer-hint {
  @include glass-panel;
  background: rgba(254, 243, 199, 0.5);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: $radius-xl;
  padding: 28rpx 32rpx;
  display: flex;
  align-items: flex-start;
  z-index: 10;
}

.hint-icon {
  font-size: 38rpx;
  margin-right: 18rpx;
  flex-shrink: 0;
}

.hint-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hint-title {
  font-size: 26rpx;
  font-weight: 700;
  color: #D97706;
  margin-bottom: 8rpx;
  letter-spacing: 0;
}

.hint-text {
  font-size: 23rpx;
  color: $text-secondary;
  line-height: 1.6;
}

.result-badges-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.version-micro-tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 14rpx;
  border-radius: $radius-full;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 0;

  &.basic {
    background: rgba(249, 115, 22, 0.1);
    border: 1px solid rgba(249, 115, 22, 0.2);
    color: #FB923C;
  }

  &.full {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: #34D399;
  }
}
</style>
