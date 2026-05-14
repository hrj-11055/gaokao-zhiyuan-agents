<template>
  <view class="page">
    <!-- 生成中 -->
    <view v-if="status === 'loading'" class="state-card">
      <view class="loading-icon">⏳</view>
      <text class="state-title">AI 正在生成报告</text>
      <text class="state-sub">分析问卷 + 对话记录，约需 15-30 秒</text>
      <view class="loading-bar">
        <view class="loading-fill" />
      </view>
    </view>

    <!-- 成功 -->
    <view v-else-if="status === 'done'" class="state-card">
      <view class="success-icon">📊</view>
      <text class="state-title">报告已生成</text>
      <text class="state-sub">{{ sourceDesc }}</text>
      <text class="state-time" v-if="reportStore.generatedAt">生成时间：{{ formatTime(reportStore.generatedAt) }}</text>

      <view class="divider" />

      <view class="content-list">
        <text class="content-item">✓ 个人特质分析（五环框架）</text>
        <text class="content-item">✓ 专业匹配分析</text>
        <text class="content-item">✓ 专业深度研究</text>
        <text class="content-item">✓ 院校推荐（冲稳保）</text>
        <text class="content-item">✓ 综合志愿方案</text>
      </view>

      <view class="primary-btn" @click="openInBrowser">查看报告</view>
      <view class="secondary-btn" @click="downloadPdf">下载 PDF</view>
      <view class="secondary-btn" @click="copyLink">复制链接给家长</view>
      
      <view class="regenerate-text" @click="generate(true)">
        <text>重新生成报告 (将消耗 AI 额度)</text>
      </view>
    </view>

    <!-- 失败 -->
    <view v-else-if="status === 'error'" class="state-card">
      <view class="error-icon">⚠️</view>
      <text class="state-title">生成失败</text>
      <text class="state-sub">{{ errorMsg }}</text>
      <view class="primary-btn" @click="generate(true)">重试</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../../stores/user.js'
import { useChatStore } from '../../stores/chat.js'
import { useAssessmentStore } from '../../stores/assessment.js'
import { useReportStore } from '../../stores/report.js'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://47.113.125.147'

const status = ref('loading')
const errorMsg = ref('')

const userStore = useUserStore()
const chatStore = useChatStore()
const assessmentStore = useAssessmentStore()
const reportStore = useReportStore()

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

onMounted(() => {
  userStore.loadProfile()
  if (!userStore.userId) userStore.initUserId()
  chatStore.loadHistory()
  assessmentStore.loadAll()
  reportStore.loadReport()

  if (!assessmentStore.isAllCompleted) {
    status.value = 'error'
    errorMsg.value = `请先完成全部 3 项测评（当前 ${assessmentStore.completedCount}/3）`
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
    status.value = 'error'
    errorMsg.value = `请先完成全部 3 项测评（当前 ${assessmentStore.completedCount}/3）`
    return
  }

  if (!force && reportStore.url) {
    status.value = 'done'
    return
  }
  
  status.value = 'loading'
  errorMsg.value = ''

  try {
    const res = await uni.request({
      url: `${API_BASE}/api/report/generate`,
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
      header: { 'Content-Type': 'application/json' },
      timeout: 120000,
    })

    if (res.statusCode !== 200 || !res.data?.url) {
      throw new Error(res.data?.error || '服务暂时不可用')
    }

    reportStore.saveReport(res.data.url)
    status.value = 'done'
  } catch (err) {
    status.value = 'error'
    errorMsg.value = err.message || err.errMsg || '网络请求失败，请检查网络后重试'
  }
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

function downloadPdf() {
  if (!reportStore.url) return
  
  uni.showLoading({ title: 'PDF 生成中...' })
  const pdfUrl = reportStore.url.replace('.html', '.pdf')
  
  uni.downloadFile({
    url: pdfUrl,
    success: (res) => {
      if (res.statusCode === 200) {
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
        uni.showToast({ title: '下载失败，请稍后重试', icon: 'none' })
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
.page {
  min-height: 100vh;
  background: $bg-page;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx 32rpx;
  box-sizing: border-box;
}

.state-card {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 64rpx 40rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.08);
}

.loading-icon, .success-icon, .error-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.state-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.state-sub {
  font-size: 26rpx;
  color: $text-muted;
  text-align: center;
  margin-bottom: 8rpx;
}

.state-time {
  font-size: 24rpx;
  color: #9CA3AF;
  text-align: center;
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 8rpx;
  background: $border-light;
  border-radius: $radius-full;
  overflow: hidden;
  margin-top: 24rpx;
}

.loading-fill {
  height: 8rpx;
  background: #7c3aed;
  border-radius: $radius-full;
  animation: loading-slide 2s ease-in-out infinite;
  width: 40%;
}

@keyframes loading-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}

.divider {
  width: 100%;
  height: 2rpx;
  background: $border-light;
  margin: 8rpx 0 28rpx;
}

.content-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 40rpx;
}

.content-item {
  font-size: 28rpx;
  color: $text-secondary;
}

.primary-btn {
  width: 100%;
  height: 88rpx;
  background: #7c3aed;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 20rpx;
}

.secondary-btn {
  width: 100%;
  height: 88rpx;
  background: $bg-white;
  border: 2rpx solid #7c3aed;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7c3aed;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 24rpx;
}

.regenerate-text {
  font-size: 26rpx;
  color: #9CA3AF;
  text-decoration: underline;
  margin-top: 16rpx;
  padding: 10rpx;
}
</style>
