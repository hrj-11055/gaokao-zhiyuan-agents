<template>
  <view class="profile-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 用户头部卡片 -->
    <view class="profile-header">
      <view class="avatar-outer">
        <view class="avatar-glow" />
        <view class="avatar">
          <text class="avatar-text">峰</text>
        </view>
      </view>
      <text class="user-title">我的志愿资料</text>
      <text class="user-subtitle">ID: {{ membershipStore.userId ? membershipStore.userId.slice(0,8).toUpperCase() : 'CLOUD-USER' }}</text>
    </view>

    <!-- 会员权益中心 -->
    <view class="membership-card">
      <!-- 流光质感背景线 -->
      <view class="card-glass-glow" />

      <view class="membership-top">
        <view class="membership-title-wrap">
          <text class="membership-title">综合报告会员</text>
          <text class="membership-subtitle">{{ membershipSubtitle }}</text>
        </view>
        <view class="membership-badge" :class="{ active: membershipStore.isActive }">
          <text class="badge-text">{{ membershipStatusText }}</text>
        </view>
      </view>

      <view class="price-row">
        <view class="price-main-wrap">
          <text class="currency">¥</text>
          <text class="price-val">29</text>
          <text class="price-period">/ 一次性解锁</text>
        </view>
        <text class="invite-hint-text">邀请 3 位同学免费开通</text>
      </view>
      <text v-if="!membershipStore.isActive && !membershipStore.isPaymentEnabled" class="payment-notice">
        {{ paymentUnavailableText }}
      </text>

      <!-- 核心权益 -->
      <view class="benefit-grid">
        <view class="benefit-item">
          <view class="benefit-header">
            <text class="benefit-icon">🏛️</text>
            <text class="benefit-title">院校深度研究</text>
          </view>
          <text class="benefit-desc">查看院校定位、优势与风险</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-header">
            <text class="benefit-icon">📋</text>
            <text class="benefit-title">智能志愿报告</text>
          </view>
          <text class="benefit-desc">整合分数、测评和对话记录</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-header">
            <text class="benefit-icon">📥</text>
            <text class="benefit-title">报告打印下载</text>
          </view>
          <text class="benefit-desc">方便保存、打印和转发</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-header">
            <text class="benefit-icon">🔗</text>
            <text class="benefit-title">家长多端同步</text>
          </view>
          <text class="benefit-desc">复制链接给家长共同查看</text>
        </view>
      </view>

      <!-- 邀请进度 -->
      <view class="invite-progress">
        <view class="progress-copy">
          <text class="progress-title">限时免费邀请开通进度</text>
          <text class="progress-desc">{{ membershipStore.effectiveInviteCount }} / {{ membershipStore.requiredInviteCount || 3 }} 人有效注册</text>
        </view>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: inviteProgressWidth }">
            <view class="progress-fill-glow" />
          </view>
        </view>
      </view>

      <view class="membership-actions">
        <button class="membership-btn primary" @click="openMembership">
          {{ membershipActionText }}
        </button>
        <button class="membership-btn secondary" open-type="share" @click="shareInvite">
          邀请好友免费解锁
        </button>
        <button class="membership-btn secondary" @click="copyInviteLink">
          复制邀请链接
        </button>
        <button class="membership-btn ghost" @click="refreshMembershipStatus">
          刷新邀请进度
        </button>
      </view>
    </view>

    <!-- 综合志愿报告 Card -->
    <view class="report-card" @click="goReport">
      <view class="report-card-glow" />
      <view class="report-icon-wrap">
        <text class="report-icon">▣</text>
      </view>
      <view class="report-content">
        <text class="report-title">生成/查看综合志愿报告</text>
        <text class="report-desc">{{ reportCardDesc }}</text>
      </view>
      <view class="report-status" :class="{ ready: canGenerateReport }">
        <text class="status-text">{{ canGenerateReport ? '就绪' : `已完 ${completedCount}/3` }}</text>
      </view>
      <text class="card-arrow">›</text>
    </view>

    <!-- 测评历史记录列表 -->
    <view class="section">
      <text class="section-title">测评同步记录</text>
      <view class="records-list">
        <!-- 五环问卷 -->
        <view class="record-item" @click="goQuestionnaire">
          <view class="record-icon-outer" :class="{ completed: isQuestionnaireComplete }">
            <text class="record-icon-text">✓</text>
          </view>
          <view class="record-content">
            <text class="record-title">五环特征评测</text>
            <text class="record-desc">{{ questionnaireRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>

        <!-- MBTI -->
        <view class="record-item" @click="goMbti">
          <view class="record-icon-outer" :class="{ completed: isMbtiComplete }">
            <text class="record-icon-text">✓</text>
          </view>
          <view class="record-content">
            <text class="record-title">MBTI 人格解码</text>
            <text class="record-desc">{{ mbtiRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>

        <!-- 霍兰德 -->
        <view class="record-item" @click="goHolland">
          <view class="record-icon-outer" :class="{ completed: isHollandComplete }">
            <text class="record-icon-text">✓</text>
          </view>
          <view class="record-content">
            <text class="record-title">霍兰德职业兴趣矩阵</text>
            <text class="record-desc">{{ hollandRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 系统控制中心 -->
    <view class="section">
      <text class="section-title">数据与系统安全</text>
      <view class="settings-list">
        <view class="setting-item" @click="clearData">
          <text class="setting-title">重置档案 (清除所有本地评测数据)</text>
          <text class="setting-arrow">›</text>
        </view>
        <view class="setting-item" @click="goPrivacy">
          <text class="setting-title">隐私保护指引</text>
          <text class="setting-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 底部安全提示 -->
    <view class="footer-hint">
      <text class="hint-text">峰哥咨询参考 · 报告仅供志愿填报参考</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
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
  getCompletedAssessmentsCount,
  QUESTIONNAIRE_REQUIRED_COUNT
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
  if (membershipStore.source === 'invite') return '邀请开通'
  if (membershipStore.source === 'payment') return '已付费'
  return '已解锁'
})
const membershipSubtitle = computed(() => {
  if (membershipStore.isActive) return '已解锁全部权益'
  return '解锁深度研究、志愿报告与多端协同'
})
const paymentUnavailableText = computed(() => membershipStore.paymentUnavailableText)
const membershipActionText = computed(() => {
  if (membershipStore.isActive) return '已开通会员权益'
  if (!membershipStore.isPaymentEnabled) return '备案中，先邀请解锁'
  return '¥29 解锁综合报告'
})
const invitePath = computed(() => `/pages/index/index?inviterId=${membershipStore.userId || ''}`)
const reportCardDesc = computed(() => {
  if (!canGenerateReport.value) return '请先完成全部 3 项测评'
  if (!membershipStore.isActive) return '解锁会员后即可生成完整报告'
  return '资料已就绪，可以查看或导出报告'
})

const isQuestionnaireComplete = computed(() => questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT)
const isMbtiComplete = computed(() => assessments.value.mbti.completed)
const isHollandComplete = computed(() => assessments.value.holland.completed)

const questionnaireRecordText = computed(() => {
  if (isQuestionnaireComplete.value) {
    return `完成同步 ${formatDate(questionnaire.value.updatedAt)}`
  }
  return questionnaire.value.completedCount > 0
    ? `已记录 ${questionnaire.value.completedCount} / ${QUESTIONNAIRE_REQUIRED_COUNT} 题`
    : '未录入特征'
})

const mbtiRecordText = computed(() => {
  if (isMbtiComplete.value) {
    const type = assessments.value.mbti.type || ''
    const typeStr = type ? ` · 类型 ${type}` : ''
    return `完成同步${typeStr} ${formatDate(assessments.value.mbti.completedAt)}`
  }
  return '未录入特征'
})

const hollandRecordText = computed(() => {
  if (isHollandComplete.value) {
    const code = assessments.value.holland.code || ''
    const codeStr = code ? ` · 代码[${code}]` : ''
    return `完成同步${codeStr} ${formatDate(assessments.value.holland.completedAt)}`
  }
  return '未录入特征'
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
    uni.showToast({ title: '会员权益已激活', icon: 'success' })
    return
  }

  if (!membershipStore.isPaymentEnabled) {
    uni.showModal({
      title: '支付暂未开放',
      content: paymentUnavailableText.value,
      confirmText: '复制邀请',
      cancelText: '知道了',
      success: (res) => {
        if (res.confirm) copyInviteLink()
      },
    })
    return
  }

  try {
    uni.showLoading({ title: '安全通道接入中...', mask: true })
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
      title: err.message || err.errMsg || '无法调起微信支付通道',
      icon: 'none',
      duration: 2200,
    })
  }
}

function shareInvite() {
  uni.showToast({
    title: '请点击右上角三个点分享给同学',
    icon: 'none',
  })
}

function copyInviteLink() {
  uni.setClipboardData({
    data: invitePath.value,
    success: () => uni.showToast({ title: '邀请链接已复制', icon: 'success' }),
  })
}

async function refreshMembershipStatus() {
  try {
    uni.showLoading({ title: '刷新中...' })
    await membershipStore.loadStatus()
    uni.hideLoading()
    uni.showToast({
      title: membershipStore.isActive ? '已解锁会员' : '邀请进度已刷新',
      icon: membershipStore.isActive ? 'success' : 'none',
    })
  } catch (err) {
    uni.hideLoading()
    uni.showToast({
      title: err.message || err.errMsg || '刷新失败，请稍后再试',
      icon: 'none',
    })
  }
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

function goPrivacy() {
  uni.navigateTo({ url: '/pages/privacy/privacy' })
}

function clearData() {
  uni.showModal({
    title: '危险操作提示',
    content: '确定要重置当前考生本地评测档案吗？本操作不可撤销，已生成的本地报告和问卷记录将完全清空。',
    confirmText: '坚决重置',
    confirmColor: '#EF4444',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        clearAllLocalData()
        loadData()
        uni.showToast({
          title: '已安全重置',
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
  title: '邀请你一起生成高考志愿参考报告',
  path: invitePath.value,
}))
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background:
    radial-gradient(90% 45% at 18% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  padding: 32rpx;
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
  left: -150rpx;
  pointer-events: none;
}
.cyber-glow-bg-orange {
  position: absolute;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.035) 0%, rgba(0, 0, 0, 0) 70%);
  bottom: 200rpx;
  right: -150rpx;
  pointer-events: none;
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20rpx;
  margin-bottom: 40rpx;
  z-index: 10;
}

.avatar-outer {
  position: relative;
  width: 128rpx;
  height: 128rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.avatar {
  width: 112rpx;
  height: 112rpx;
  background: $grad-royal;
  border-radius: $radius-xl;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(37, 99, 235, 0.20);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 2;
}

.avatar-text {
  color: #fff;
  font-size: 50rpx;
  font-weight: bold;
}

.avatar-glow {
  position: absolute;
  top: -6rpx;
  left: -6rpx;
  right: -6rpx;
  bottom: -6rpx;
  background: rgba(37, 99, 235, 0.14);
  border-radius: 36rpx;
  filter: blur(14rpx);
  z-index: 1;
}

.user-title {
  font-size: 38rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 10rpx;
  letter-spacing: 0;
}

.user-subtitle {
  font-size: 24rpx;
  color: $text-muted;
  letter-spacing: 0;
}

.membership-card {
  position: relative;
  border-radius: $radius-xl;
  padding: 42rpx 36rpx 36rpx;
  margin-bottom: 32rpx;
  overflow: hidden;
  box-sizing: border-box;
  z-index: 10;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid $border-light;
  box-shadow: 0 12rpx 36rpx -18rpx rgba(15, 23, 42, 0.16);
}

.card-glass-glow {
  position: absolute;
  top: -150rpx;
  right: -150rpx;
  width: 300rpx;
  height: 300rpx;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.12) 0%, rgba(255, 255, 255, 0) 70%);
  pointer-events: none;
}

.membership-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.membership-title-wrap {
  display: flex;
  flex-direction: column;
}

.membership-title {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 10rpx;
}

.membership-subtitle {
  display: block;
  max-width: 440rpx;
  font-size: 24rpx;
  line-height: 1.5;
  color: $text-secondary;
}

.membership-badge {
  flex-shrink: 0;
  padding: 8rpx 20rpx;
  border-radius: $radius-full;
  background: rgba(217, 119, 6, 0.06);
  border: 1px solid rgba(217, 119, 6, 0.15);
  color: #D97706;
  font-size: 22rpx;
  font-weight: 700;

  &.active {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.06));
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #059669;
  }
}

.price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 0;
  border-top: 1px solid rgba(217, 119, 6, 0.08);
  border-bottom: 1px solid rgba(217, 119, 6, 0.08);
  margin-bottom: 28rpx;
}

.price-main-wrap {
  display: flex;
  align-items: baseline;
}

.currency {
  font-size: 28rpx;
  color: #D97706;
  font-weight: 700;
  margin-right: 6rpx;
}

.price-val {
  font-size: 46rpx;
  font-weight: 900;
  color: #B45309;
  letter-spacing: 0;
}

.price-period {
  font-size: 24rpx;
  color: $text-secondary;
  margin-left: 8rpx;
}

.invite-hint-text {
  font-size: 24rpx;
  color: #B45309;
  background: rgba(245, 158, 11, 0.08);
  padding: 6rpx 18rpx;
  border-radius: $radius-xs;
  border: 1px solid rgba(245, 158, 11, 0.15);
}

.payment-notice {
  display: block;
  margin: -10rpx 0 24rpx;
  padding: 18rpx 20rpx;
  border-radius: $radius-md;
  background: rgba(37, 99, 235, 0.06);
  border: 1px solid rgba(37, 99, 235, 0.12);
  color: $text-secondary;
  font-size: 24rpx;
  line-height: 1.45;
}

.benefit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-bottom: 32rpx;
}

.benefit-item {
  border: 1px solid rgba(217, 119, 6, 0.08);
  background: rgba(255, 255, 255, 0.6);
  border-radius: $radius-md;
  padding: 20rpx;
  box-sizing: border-box;
}

.benefit-header {
  display: flex;
  align-items: center;
  margin-bottom: 10rpx;
}

.benefit-icon {
  font-size: 28rpx;
  margin-right: 12rpx;
}

.benefit-title {
  font-size: 27rpx;
  font-weight: 700;
  color: $text-primary;
}

.benefit-desc {
  display: block;
  font-size: 24rpx;
  line-height: 1.4;
  color: $text-secondary;
}

.invite-progress {
  margin-bottom: 32rpx;
  background: rgba(217, 119, 6, 0.04);
  padding: 20rpx;
  border-radius: $radius-md;
  border: 1px solid rgba(217, 119, 6, 0.08);
}

.progress-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14rpx;
}

.progress-title {
  font-size: 26rpx;
  font-weight: 700;
  color: $text-primary;
}

.progress-desc {
  font-size: 24rpx;
  color: #B45309;
  font-weight: 600;
}

.progress-track {
  height: 10rpx;
  background: rgba(15, 23, 42, 0.06);
  border-radius: $radius-full;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #FBBF24 0%, #D97706 100%);
  border-radius: $radius-full;
  position: relative;
}

.progress-fill-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 12rpx;
  height: 100%;
  background: #fff;
  filter: blur(2rpx);
  opacity: 0.8;
}

.membership-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.membership-btn {
  flex: 1 1 calc(50% - 8rpx);
  min-width: 0;
  height: 84rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 84rpx;
  margin: 0;
  padding: 0 16rpx;
  transition: transform 0.1s;

  &:active {
    transform: scale(0.98);
  }
}

.membership-btn::after {
  border: none;
}

.membership-btn.primary {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  color: #FFFFFF;
  box-shadow: 0 8rpx 20rpx rgba(217, 119, 6, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.membership-btn.secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #B45309;
  border: 1px solid rgba(217, 119, 6, 0.25);
}

.membership-btn.ghost {
  background: #F8FAFC;
  color: $text-secondary;
  border: 1px solid $border-light;
}

.report-card {
  position: relative;
  background: $grad-vip;
  border-radius: $radius-xl;
  padding: 32rpx 28rpx;
  display: flex;
  align-items: center;
  margin-bottom: 36rpx;
  box-shadow: 0 12rpx 30rpx rgba(37, 99, 235, 0.20);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-sizing: border-box;
  z-index: 10;
  overflow: hidden;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.report-card-glow {
  position: absolute;
  top: -100rpx;
  left: -100rpx;
  width: 250rpx;
  height: 250rpx;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
  pointer-events: none;
}

.report-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  background: rgba(255, 255, 255, 0.12);
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 22rpx;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.report-icon {
  font-size: 40rpx;
  color: #fff;
}

.report-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.report-title {
  font-size: 31rpx;
  font-weight: 800;
  color: #fff;
  margin-bottom: 6rpx;
}

.report-desc {
  font-size: 23rpx;
  color: rgba(255, 255, 255, 0.85);
}

.report-status {
  padding: 8rpx 20rpx;
  background: rgba(255, 255, 255, 0.15);
  border-radius: $radius-full;
  margin-right: 12rpx;
  border: 1px solid rgba(255, 255, 255, 0.1);

  &.ready {
    background: $grad-success;
    border: none;
  }
}

.status-text {
  font-size: 21rpx;
  color: #fff;
  font-weight: 700;
}

.card-arrow {
  font-size: 46rpx;
  color: rgba(255, 255, 255, 0.85);
}

.section {
  margin-bottom: 36rpx;
  z-index: 10;
}

.section-title {
  font-size: 26rpx;
  font-weight: 700;
  color: $text-secondary;
  margin-bottom: 16rpx;
  margin-left: 8rpx;
  display: block;
  letter-spacing: 0;
}

.records-list,
.settings-list {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid $border-light;
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: 0 16rpx 48rpx -12rpx rgba(15, 23, 42, 0.05);
}

.record-item {
  display: flex;
  align-items: center;
  padding: 28rpx 28rpx;
  border-bottom: 1px solid $border-light;
  transition: background-color 0.2s;

  &:active {
    background: rgba(15, 23, 42, 0.02);
  }
}

.record-item:last-child {
  border-bottom: none;
}

.record-icon-outer {
  width: 50rpx;
  height: 50rpx;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 22rpx;
  transition: all 0.2s;

  &.completed {
    background: $grad-success;
    border: none;
  }
}

.record-icon-text {
  font-size: 24rpx;
  color: $text-muted;

  .completed & {
    color: #fff;
    font-weight: bold;
  }
}

.record-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.record-title {
  font-size: 29rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 6rpx;
}

.record-desc {
  font-size: 23rpx;
  color: $text-secondary;
}

.record-arrow {
  font-size: 40rpx;
  color: $text-muted;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 28rpx;
  border-bottom: 1px solid $border-light;
  transition: background-color 0.2s;

  &:active {
    background: rgba(255, 255, 255, 0.01);
  }

  &:last-child {
    border-bottom: none;
  }
}

.setting-title {
  font-size: 29rpx;
  color: $text-primary;
  font-weight: 500;
}

.setting-arrow {
  font-size: 40rpx;
  color: $text-muted;
}

.footer-hint {
  text-align: center;
  padding: 48rpx 0 24rpx;
}

.hint-text {
  font-size: 21rpx;
  color: $text-muted;
  line-height: 1.5;
  display: block;
  padding: 0 20rpx;
}

.privacy-link {
  display: block;
  font-size: 21rpx;
  color: $brand-violet;
  font-weight: 700;
  margin-top: 12rpx;
  text-decoration: underline;
}
</style>
