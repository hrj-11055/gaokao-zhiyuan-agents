<template>
  <view class="report-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-violet" />
    <view class="cyber-glow-bg-orange" />

    <!-- 生成中 -->
    <view v-if="status === 'loading'" class="state-card loading-card">
      <view class="spinner-container">
        <view class="cyber-spinner-outer" />
        <view class="cyber-spinner-inner" />
        <view class="spinner-icon">⚡</view>
      </view>
      <text class="state-title">正在生成志愿参考报告</text>
      <text class="state-sub">正在整合考生信息、测评结果与对话记录</text>
      <text class="state-sub-tip">通常需要 15-30 秒，请保持页面打开。</text>
      <view class="loading-bar">
        <view class="loading-fill" />
      </view>
    </view>

    <!-- 测评未完成 -->
    <view v-else-if="status === 'assessment'" class="state-card action-card">
      <view class="error-icon-outer">
        <view class="error-glow" />
        <view class="error-icon">📋</view>
      </view>
      <text class="state-title">先完成测评再生成报告</text>
      <text class="state-sub">{{ errorMsg }}</text>
      <view class="requirement-panel">
        <view class="requirement-row">
          <text class="requirement-label">完成进度</text>
          <text class="requirement-value">{{ assessmentStore.completedCount }}/3</text>
        </view>
        <view class="requirement-track">
          <view class="requirement-fill" :style="{ width: `${Math.round((assessmentStore.completedCount / 3) * 100)}%` }" />
        </view>
      </view>
      <view class="actions-area">
        <button class="primary-action-btn" @click="goAssessments">去完成测评</button>
        <button class="secondary-action-btn" @click="goHome">返回首页</button>
      </view>
    </view>

    <!-- 会员锁定 -->
    <view v-else-if="status === 'locked'" class="state-card locked-card">
      <view class="lock-icon-outer">
        <view class="lock-glow" />
        <view class="lock-icon">🔒</view>
      </view>
      <text class="state-title">解锁综合志愿报告</text>
      <text class="state-sub">{{ errorMsg || '生成可给家长一起查看的完整志愿参考报告' }}</text>

      <view class="unlock-price">
        <text class="unlock-price-main">¥29 一次性解锁</text>
        <text class="unlock-price-sub">也可邀请 3 位新用户填写基础信息后免费解锁</text>
      </view>

      <view class="benefits-panel">
        <view class="benefit-item">
          <view class="benefit-bullet">✦</view>
          <text class="benefit-text">院校定位、优势专业与填报风险梳理</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-bullet">✦</view>
          <text class="benefit-text">结合测评结果分析适合和应回避的方向</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-bullet">✦</view>
          <text class="benefit-text">支持网页查看、PDF 下载和家庭讨论</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-bullet">✦</view>
          <text class="benefit-text">报告链接可复制给家长共同查看</text>
        </view>
      </view>

      <view class="actions-area">
        <button class="primary-action-btn" @click="unlockAndGenerate">{{ paymentActionText }}</button>
        <button class="secondary-action-btn" @click="goInvite">邀请 3 名好友免费解锁</button>
      </view>
    </view>

    <!-- 成功 -->
    <view v-else-if="status === 'done'" class="state-card success-card">
      <view class="success-icon-outer">
        <view class="success-glow" />
        <view class="success-icon">🏆</view>
      </view>
      <text class="state-title">志愿参考报告已生成</text>
      <text class="state-sub">{{ sourceDesc }}</text>
      <text class="state-time" v-if="reportStore.generatedAt">生成时间：{{ formatTime(reportStore.generatedAt) }}</text>

      <view class="divider" />

      <view class="benefits-panel success-panel">
        <view class="benefit-item">
          <view class="benefit-bullet success">✓</view>
          <text class="benefit-text">五环学业特质已纳入分析</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-bullet success">✓</view>
          <text class="benefit-text">专业方向匹配建议已生成</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-bullet success">✓</view>
          <text class="benefit-text">院校梯度和风险提示已整理</text>
        </view>
        <view class="benefit-item">
          <view class="benefit-bullet success">✓</view>
          <text class="benefit-text">可继续下载院校/专业深度 PDF</text>
        </view>
      </view>

      <view class="actions-area">
        <button class="primary-action-btn success-btn" @click="openInBrowser">查看报告</button>
        <button class="secondary-action-btn" @click="downloadPdf">下载 PDF</button>
        <button class="secondary-action-btn" @click="openDeepReportDownload">下载学校/专业深度 PDF</button>
        <button class="secondary-action-btn" @click="copyLink">复制链接发给家长</button>
      </view>

      <view class="regenerate-text-wrap" @click="generate(true)">
        <text class="regenerate-link">重新生成报告</text>
      </view>
    </view>

    <!-- 失败 -->
    <view v-else-if="status === 'error'" class="state-card error-card">
      <view class="error-icon-outer">
        <view class="error-glow" />
        <view class="error-icon">⚠️</view>
      </view>
      <text class="state-title">报告生成失败</text>
      <text class="state-sub">{{ errorMsg }}</text>
      <text v-if="draftId" class="state-sub-tip">已保留草稿：{{ draftId }}，可直接重试生成，无需重新填写资料。</text>
      <button class="primary-action-btn error-btn" @click="generate(true)">重试生成</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { requestBackend } from '../../api/backend.js'
import { useUserStore } from '../../stores/user.js'
import { useChatStore } from '../../stores/chat.js'
import { useAssessmentStore } from '../../stores/assessment.js'
import { useReportStore } from '../../stores/report.js'
import { useMembershipStore } from '../../stores/membership.js'
import { PAYMENT_ENABLED, PDF_DOWNLOAD_ENABLED } from '../../config.js'

const status = ref('loading')
const errorMsg = ref('')
const draftId = ref('')

const userStore = useUserStore()
const chatStore = useChatStore()
const assessmentStore = useAssessmentStore()
const reportStore = useReportStore()
const membershipStore = useMembershipStore()
const paymentUnavailableText = '支付功能正在备案配置中，请先邀请 3 位同学免费解锁。'
const downloadUnavailableText = 'PDF 下载正在等待 HTTPS 合法域名配置，备案完成前请先查看在线报告。'

const sourceDesc = computed(() => {
  const completedCount = assessmentStore.questionnaire?.completedCount || 0
  const conversationId = chatStore.conversationId
  const parts = []
  if (completedCount > 0) parts.push(`${completedCount} 道问卷`)
  if (assessmentStore.mbti?.completed && assessmentStore.mbti?.type) parts.push(`MBTI ${assessmentStore.mbti.type}`)
  if (assessmentStore.holland?.completed && assessmentStore.holland?.code) parts.push(`霍兰德 ${assessmentStore.holland.code}`)
  if (conversationId) parts.push('AI 对话记录')
  return parts.length > 0 ? `基于 ${parts.join(' + ')} 生成` : '基于考生基本信息生成'
})

const paymentActionText = computed(() => {
  if (!PAYMENT_ENABLED) return '支付备案中，先邀请解锁'
  return errorMsg.value && errorMsg.value.includes('支付暂未接入') ? '支付接入后可开通' : '¥29 解锁并生成报告'
})

onMounted(async () => {
  userStore.loadProfile()
  if (!userStore.userId) userStore.initUserId()
  chatStore.loadHistory()
  assessmentStore.loadAll()
  reportStore.loadReport()

  if (!assessmentStore.isAllCompleted) {
    status.value = 'assessment'
    errorMsg.value = `请先完成全部 3 项测评（当前 ${assessmentStore.completedCount}/3）`
    return
  }

  try {
    await membershipStore.loadStatus()
  } catch (err) {
    status.value = 'locked'
    errorMsg.value = err.message || err.errMsg || '请先登录微信身份后解锁会员权益'
    return
  }

  if (!membershipStore.isActive) {
    status.value = 'locked'
    errorMsg.value = '综合志愿报告属于会员权益，付费或邀请 3 位新用户后即可生成'
    return
  }

  if (reportStore.url) {
    status.value = 'done'
  } else {
    generate()
  }
})

async function generate(force = false) {
  if (!assessmentStore.isAllCompleted) {
    status.value = 'assessment'
    errorMsg.value = `请先完成全部 3 项测评（当前 ${assessmentStore.completedCount}/3）`
    return
  }

  if (!force && reportStore.url) {
    status.value = 'done'
    return
  }

  if (!membershipStore.isActive) {
    status.value = 'locked'
    errorMsg.value = '综合志愿报告属于会员权益，付费或邀请 3 位新用户后即可生成'
    return
  }

  status.value = 'loading'
  errorMsg.value = ''
  draftId.value = ''

  try {
    const res = await requestBackend({
      path: '/api/report/generate',
      method: 'POST',
      data: {
        userId: userStore.userId,
        profile: userStore.profile,
        questionnaire: assessmentStore.questionnaire?.answers || {},
        assessments: {
          mbti: assessmentStore.mbti,
          holland: assessmentStore.holland,
        },
        conversationId: chatStore.conversationId || '',
      },
      header: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${membershipStore.sessionToken}`,
      },
      timeout: 120000,
    })

    if (res.statusCode === 402 || res.data?.code === 'MEMBERSHIP_REQUIRED') {
      status.value = 'locked'
      errorMsg.value = res.data?.error || '请先解锁会员后生成报告'
      return
    }

    if (res.statusCode !== 200 || !res.data?.url) {
      if (res.data?.draftId) draftId.value = res.data.draftId
      throw new Error(res.data?.error || '服务暂时不可用')
    }

    reportStore.saveReport(res.data.url)
    status.value = 'done'
  } catch (err) {
    status.value = 'error'
    errorMsg.value = err.message || err.errMsg || '网络请求失败，请检查网络后重试'
  }
}

async function unlockAndGenerate() {
  if (!PAYMENT_ENABLED) {
    uni.showModal({
      title: '支付暂未开放',
      content: paymentUnavailableText,
      confirmText: '去邀请',
      cancelText: '知道了',
      success: (res) => {
        if (res.confirm) goInvite()
      },
    })
    return
  }

  try {
    uni.showLoading({ title: '发起支付...' })
    await membershipStore.createPayment()
    await membershipStore.loadStatus()
    uni.hideLoading()
    if (membershipStore.isActive) {
      await generate(true)
    } else {
      status.value = 'locked'
      errorMsg.value = '支付确认中，请稍后刷新后生成报告'
    }
  } catch (err) {
    uni.hideLoading()
    const message = err.message || err.errMsg || ''
    if (message.includes('请求失败') || message.includes('fail')) {
      errorMsg.value = '支付暂未接入或支付参数未配置，当前不能通过付费解锁生成报告'
      status.value = 'locked'
    }
    uni.showToast({
      title: errorMsg.value || message || '暂时无法发起支付',
      icon: 'none',
      duration: 2200,
    })
  }
}

function goInvite() {
  uni.switchTab({ url: '/pages/profile/profile' })
}

function goAssessments() {
  uni.switchTab({ url: '/pages/assessments/assessments' })
}

function goHome() {
  uni.switchTab({ url: '/pages/index/index' })
}

function copyLink() {
  uni.setClipboardData({
    data: reportStore.url,
    success: () => uni.showToast({ title: '链接已复制', icon: 'success' })
  })
}

function openInBrowser() {
  uni.navigateTo({
    url: `/pages/report-view/report-view?url=${encodeURIComponent(reportStore.url)}`
  })
}

function openDeepReportDownload() {
  uni.navigateTo({
    url: '/pages/deep-report-download/deep-report-download'
  })
}

function getHeaderValue(headers, name) {
  if (!headers) return ''
  const lowerName = name.toLowerCase()
  const key = Object.keys(headers).find(item => item.toLowerCase() === lowerName)
  return key ? String(headers[key]) : ''
}

function downloadPdf() {
  if (!reportStore.url) return

  if (!PDF_DOWNLOAD_ENABLED) {
    uni.showModal({
      title: 'PDF 下载暂未开放',
      content: downloadUnavailableText,
      confirmText: '查看报告',
      cancelText: '知道了',
      success: (res) => {
        if (res.confirm) openInBrowser()
      },
    })
    return
  }

  uni.showLoading({ title: 'PDF 生成中...' })
  const pdfUrl = reportStore.url.replace('.html', '.pdf')

  uni.downloadFile({
    url: pdfUrl,
    success: (res) => {
      const contentType = getHeaderValue(res.header, 'content-type')
      if (res.statusCode === 200 && contentType.includes('application/pdf')) {
        uni.openDocument({
          filePath: res.tempFilePath,
          showMenu: true,
          success: () => uni.hideLoading(),
          fail: (err) => {
            uni.hideLoading()
            uni.showToast({ title: '打开 PDF 失败', icon: 'none' })
          }
        })
      } else {
        uni.hideLoading()
        uni.showToast({ title: 'PDF 未生成成功，请重新生成报告', icon: 'none' })
      }
    },
    fail: () => {
      uni.hideLoading()
      uni.showToast({ title: '网络请求失败', icon: 'none' })
    }
  })
}

function formatTime(ts) {
  if (!ts) return ''
  const date = new Date(ts)
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.report-page {
  min-height: 100vh;
  background:
    radial-gradient(90% 45% at 12% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 64%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 48rpx 32rpx;
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.cyber-glow-bg-violet {
  position: fixed;
  top: -10%;
  left: -20%;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, rgba(0, 0, 0, 0) 70%);
  z-index: 0;
  pointer-events: none;
}

.cyber-glow-bg-orange {
  position: fixed;
  bottom: -10%;
  right: -20%;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.05) 0%, rgba(0, 0, 0, 0) 70%);
  z-index: 0;
  pointer-events: none;
}

.state-card {
  position: relative;
  z-index: 1;
  width: 100%;
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: $radius-xl;
  padding: 56rpx 36rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s;
}

.spinner-container {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
}

.cyber-spinner-outer {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4rpx solid transparent;
  border-top-color: $brand-primary;
  border-bottom-color: $brand-violet;
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

.cyber-spinner-inner {
  position: absolute;
  width: 80%;
  height: 80%;
  border: 2rpx solid transparent;
  border-left-color: rgba(37, 99, 235, 0.16);
  border-right-color: rgba(255, 107, 0, 0.2);
  border-radius: 50%;
  animation: spin-reverse 1.2s linear infinite;
}

.spinner-icon {
  font-size: 56rpx;
  animation: pulse-glow 1.5s ease-in-out infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes spin-reverse {
  0% { transform: rotate(360deg); }
  100% { transform: rotate(0deg); }
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}

.state-title {
  font-size: 38rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 20rpx;
  text-align: center;
  letter-spacing: 0;
}

.state-sub {
  font-size: 26rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.5;
  margin-bottom: 8rpx;
}

.state-sub-tip {
  font-size: 23rpx;
  color: $text-muted;
  text-align: center;
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 10rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
  border: 1px solid $border-light;
}

.loading-fill {
  height: 100%;
  background: linear-gradient(90deg, $brand-violet, $brand-primary);
  border-radius: $radius-full;
  animation: loading-slide 2s ease-in-out infinite;
  width: 45%;
}

@keyframes loading-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(250%); }
}

.lock-icon-outer, .success-icon-outer, .error-icon-outer {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
}

.lock-glow {
  position: absolute;
  width: 120rpx;
  height: 120rpx;
  background: rgba(249, 115, 22, 0.14);
  border-radius: 50%;
  filter: blur(16rpx);
  z-index: 1;
}

.success-glow {
  position: absolute;
  width: 120rpx;
  height: 120rpx;
  background: rgba(37, 99, 235, 0.14);
  border-radius: 50%;
  filter: blur(16rpx);
  z-index: 1;
}

.error-glow {
  position: absolute;
  width: 120rpx;
  height: 120rpx;
  background: rgba(239, 68, 68, 0.14);
  border-radius: 50%;
  filter: blur(16rpx);
  z-index: 1;
}

.lock-icon, .success-icon, .error-icon {
  font-size: 72rpx;
  z-index: 2;
}

.unlock-price {
  width: 100%;
  background: rgba(249, 115, 22, 0.06);
  border: 1px solid rgba(249, 115, 22, 0.15);
  border-radius: $radius-lg;
  padding: 32rpx 24rpx;
  box-sizing: border-box;
  margin: 32rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: none;
}

.unlock-price-main {
  font-size: 40rpx;
  font-weight: 800;
  color: #FF8F3D;
  margin-bottom: 8rpx;
}

.unlock-price-sub {
  font-size: 24rpx;
  color: $text-secondary;
}

.benefits-panel {
  width: 100%;
  background: #F8FAFC;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  padding: 32rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-bottom: 48rpx;
}

.benefit-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.benefit-bullet {
  font-size: 26rpx;
  font-weight: 800;
  color: $brand-primary-light;
}

.benefit-bullet.success {
  color: #34D399;
}

.benefit-text {
  font-size: 27rpx;
  color: $text-primary;
  font-weight: 500;
}

.actions-area {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.primary-action-btn {
  width: 100%;
  height: 90rpx;
  background: linear-gradient(135deg, #FF6B00 0%, #EA580C 100%);
  color: #fff;
  font-size: 30rpx;
  font-weight: 800;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.24);
  transition: all 0.2s;

  &::after {
    border: none;
  }

  &:active {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.2);
  }
}

.secondary-action-btn {
  width: 100%;
  height: 90rpx;
  background: #F8FAFC;
  color: $text-primary;
  font-size: 30rpx;
  font-weight: 700;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid $border-light;
  transition: all 0.2s;

  &::after {
    border: none;
  }

  &:active {
    transform: scale(0.98);
    background: #EFF6FF;
  }
}

.success-card {
  .primary-action-btn.success-btn {
    background: linear-gradient(135deg, $brand-violet 0%, #4F46E5 100%);
    box-shadow: 0 8rpx 24rpx rgba(37, 99, 235, 0.24);

    &:active {
      box-shadow: 0 4rpx 12rpx rgba(99, 102, 241, 0.2);
    }
  }
}

.state-time {
  font-size: 24rpx;
  color: $text-muted;
  margin-top: 8rpx;
}

.divider {
  width: 100%;
  height: 1px;
  background: $border-light;
  margin: 32rpx 0;
}

.regenerate-text-wrap {
  margin-top: 32rpx;
  padding: 16rpx;
}

.regenerate-link {
  font-size: 25rpx;
  color: $text-muted;
  text-decoration: underline;
  font-weight: 500;

  &:active {
    color: $text-secondary;
  }
}

.error-card {
  .primary-action-btn.error-btn {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    box-shadow: 0 8rpx 24rpx rgba(239, 68, 68, 0.3);

    &:active {
      box-shadow: 0 4rpx 12rpx rgba(239, 68, 68, 0.2);
    }
  }
}

.action-card {
  .primary-action-btn {
    background: $grad-royal;
  }
}

.requirement-panel {
  width: 100%;
  margin-top: 28rpx;
  padding: 24rpx;
  border-radius: $radius-lg;
  background: rgba(248, 250, 252, 0.94);
  border: 1px solid $border-light;
  box-sizing: border-box;
}

.requirement-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14rpx;
}

.requirement-label {
  color: $text-secondary;
  font-size: 25rpx;
}

.requirement-value {
  color: $text-primary;
  font-size: 27rpx;
  font-weight: 850;
}

.requirement-track {
  width: 100%;
  height: 14rpx;
  border-radius: 999rpx;
  background: rgba(226, 232, 240, 0.92);
  overflow: hidden;
}

.requirement-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(135deg, $brand-violet 0%, #f97316 100%);
}
</style>
