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

    <!-- 会员权益中心 -->
    <view class="membership-card">
      <view class="membership-top">
        <view>
          <text class="membership-title">深度填报会员</text>
          <text class="membership-subtitle">{{ membershipSubtitle }}</text>
        </view>
        <view class="membership-badge" :class="{ active: membershipStore.isActive }">
          <text>{{ membershipStatusText }}</text>
        </view>
      </view>

      <view class="price-row">
        <text class="price-text">¥29 一次性解锁</text>
        <text class="invite-text">或邀请 3 人免费解锁</text>
      </view>

      <view class="benefit-grid">
        <view class="benefit-item">
          <text class="benefit-title">大学深度研究</text>
          <text class="benefit-desc">院校实力、录取趋势、专业前景</text>
        </view>
        <view class="benefit-item">
          <text class="benefit-title">综合志愿报告</text>
          <text class="benefit-desc">结合测评、对话、分数生成方案</text>
        </view>
        <view class="benefit-item">
          <text class="benefit-title">PDF 下载</text>
          <text class="benefit-desc">方便打印、存档和线下讨论</text>
        </view>
        <view class="benefit-item">
          <text class="benefit-title">家长分享链接</text>
          <text class="benefit-desc">一键复制给家人共同查看</text>
        </view>
      </view>

      <view class="invite-progress">
        <view class="progress-copy">
          <text class="progress-title">邀请进度</text>
          <text class="progress-desc">{{ membershipStore.inviteProgressText }} 位有效新用户</text>
        </view>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: inviteProgressWidth }" />
        </view>
      </view>

      <view class="membership-actions">
        <button class="membership-btn primary" @click="openMembership">
          {{ membershipStore.isActive ? '已解锁会员权益' : '立即解锁会员' }}
        </button>
        <button class="membership-btn secondary" open-type="share" @click="shareInvite">
          邀请 3 人免费解锁
        </button>
      </view>
    </view>

    <!-- 综合志愿报告 Card -->
    <view class="report-card" @click="goReport">
      <view class="report-icon">▣</view>
      <view class="report-content">
        <text class="report-title">综合志愿报告</text>
        <text class="report-desc">{{ reportCardDesc }}</text>
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
import { onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { useMembershipStore } from '../../stores/membership.js'
import {
  clearAllLocalData,
  loadAssessments,
  loadQuestionnaire,
  getCompletedAssessmentsCount
} from '../../utils/storage.js'

const membershipStore = useMembershipStore()

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
const inviteProgressWidth = computed(() => {
  const required = membershipStore.requiredInviteCount || 3
  const progress = Math.min(membershipStore.effectiveInviteCount / required, 1)
  return `${Math.round(progress * 100)}%`
})
const membershipStatusText = computed(() => {
  if (!membershipStore.isActive) return '未解锁'
  if (membershipStore.source === 'invite') return '邀请解锁'
  if (membershipStore.source === 'payment') return '已付费'
  return '已解锁'
})
const membershipSubtitle = computed(() => {
  if (membershipStore.isActive) return '大学深度研究、综合报告、PDF 和家长分享已开放'
  return '解锁大学深度研究、综合报告生成、PDF 下载和家长分享'
})
const reportCardDesc = computed(() => {
  if (!canGenerateReport.value) return '完成全部测评后生成个性化报告'
  if (!membershipStore.isActive) return '会员解锁后生成深度综合报告'
  return '已具备生成深度综合报告条件'
})

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

async function openMembership() {
  if (membershipStore.isActive) {
    uni.showToast({ title: '会员权益已解锁', icon: 'success' })
    return
  }

  try {
    uni.showLoading({ title: '发起支付...' })
    await membershipStore.createPayment()
    await membershipStore.loadStatus()
    uni.hideLoading()
    uni.showToast({
      title: membershipStore.isActive ? '解锁成功' : '支付确认中，请稍后刷新',
      icon: membershipStore.isActive ? 'success' : 'none',
    })
  } catch (err) {
    uni.hideLoading()
    uni.showToast({
      title: err.message || err.errMsg || '暂时无法发起支付',
      icon: 'none',
      duration: 2200,
    })
  }
}

function shareInvite() {
  uni.showToast({
    title: '点击右上角分享给同学',
    icon: 'none',
  })
}

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (isMbtiComplete.value) {
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (isHollandComplete.value) {
    uni.navigateTo({ url: '/pages/holland/holland-result' })
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
        clearAllLocalData()
        loadData()
        uni.showToast({
          title: '已清除',
          icon: 'success'
        })
      }
    }
  })
}

onMounted(() => {
  loadData()
  membershipStore.loadStatus().catch(() => {})
  uni.setNavigationBarTitle({
    title: '我的'
  })
})

onShow(() => {
  loadData()
  membershipStore.loadStatus().catch(() => {})
})

onShareAppMessage(() => ({
  title: '邀请你一起解锁高考志愿深度报告',
  path: `/pages/index/index?inviterId=${membershipStore.userId || ''}`,
}))
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

.membership-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 32rpx;
  box-shadow: 0 8rpx 28rpx rgba(15, 23, 42, 0.08);
}

.membership-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.membership-title {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.membership-subtitle {
  display: block;
  max-width: 470rpx;
  font-size: 24rpx;
  line-height: 1.5;
  color: $text-muted;
}

.membership-badge {
  flex-shrink: 0;
  padding: 8rpx 18rpx;
  border-radius: $radius-full;
  background: #F3F4F6;
  color: $text-muted;
  font-size: 22rpx;
  font-weight: 600;
}

.membership-badge.active {
  background: #DCFCE7;
  color: #047857;
}

.price-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16rpx;
  padding: 24rpx 0;
  border-top: 2rpx solid $border-light;
  border-bottom: 2rpx solid $border-light;
  margin-bottom: 24rpx;
}

.price-text {
  font-size: 38rpx;
  font-weight: 800;
  color: $brand-primary;
}

.invite-text {
  font-size: 24rpx;
  color: $text-secondary;
}

.benefit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-bottom: 28rpx;
}

.benefit-item {
  min-height: 132rpx;
  border: 2rpx solid $border-light;
  border-radius: $radius-lg;
  padding: 20rpx;
  box-sizing: border-box;
}

.benefit-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.benefit-desc {
  display: block;
  font-size: 22rpx;
  line-height: 1.4;
  color: $text-muted;
}

.invite-progress {
  margin-bottom: 28rpx;
}

.progress-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.progress-title {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.progress-desc {
  font-size: 24rpx;
  color: $text-muted;
}

.progress-track {
  height: 12rpx;
  background: $border-light;
  border-radius: $radius-full;
  overflow: hidden;
}

.progress-fill {
  height: 12rpx;
  background: linear-gradient(90deg, $brand-primary, #10B981);
  border-radius: $radius-full;
}

.membership-actions {
  display: flex;
  gap: 16rpx;
}

.membership-btn {
  flex: 1;
  height: 80rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 80rpx;
  margin: 0;
  padding: 0 20rpx;
}

.membership-btn::after {
  border: none;
}

.membership-btn.primary {
  background: $brand-primary;
  color: #fff;
}

.membership-btn.secondary {
  background: #FFF7ED;
  color: $brand-primary;
}

.report-card {
  background: linear-gradient(135deg, #2563EB, #0F766E);
  border-radius: $radius-xl;
  padding: 28rpx 24rpx;
  display: flex;
  align-items: center;
  margin-bottom: 32rpx;
  box-shadow: 0 8rpx 24rpx rgba(37, 99, 235, 0.2);
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
