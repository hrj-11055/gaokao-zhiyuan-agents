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

      <view class="divider" />

      <view class="content-list">
        <text class="content-item">✓ 个人特质分析（五环框架）</text>
        <text class="content-item">✓ 专业匹配分析</text>
        <text class="content-item">✓ 专业深度研究</text>
        <text class="content-item">✓ 院校推荐（冲稳保）</text>
        <text class="content-item">✓ 综合志愿方案</text>
      </view>

      <view class="primary-btn" @click="copyLink">复制报告链接</view>
      <view class="secondary-btn" @click="openInBrowser">在浏览器中查看</view>
      <text class="hint-text">链接长期有效，可转发给家长查看</text>
    </view>

    <!-- 失败 -->
    <view v-else-if="status === 'error'" class="state-card">
      <view class="error-icon">⚠️</view>
      <text class="state-title">生成失败</text>
      <text class="state-sub">{{ errorMsg }}</text>
      <view class="primary-btn" @click="generate">重试</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { loadUserProfile, loadQuestionnaire, loadHistory, getUserId } from '../../utils/storage.js'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001'

const status = ref('loading')
const reportUrl = ref('')
const errorMsg = ref('')

const sourceDesc = computed(() => {
  const { completedCount } = loadQuestionnaire()
  const { conversationId } = loadHistory()
  const parts = []
  if (completedCount > 0) parts.push(`${completedCount} 道问卷`)
  if (conversationId) parts.push('AI 对话记录')
  return parts.length > 0 ? `基于 ${parts.join(' + ')} 生成` : '基于考生基本信息生成'
})

onMounted(() => {
  generate()
})

async function generate() {
  status.value = 'loading'
  errorMsg.value = ''

  const profile = loadUserProfile()
  const { answers } = loadQuestionnaire()
  const { conversationId } = loadHistory()

  try {
    const res = await uni.request({
      url: `${API_BASE}/api/report/generate`,
      method: 'POST',
      data: {
        userId: getUserId(),
        profile,
        questionnaire: answers || {},
        conversationId: conversationId || '',
      },
      header: { 'Content-Type': 'application/json' },
      timeout: 120000,
    })

    if (res.statusCode !== 200 || !res.data?.url) {
      throw new Error(res.data?.error || '服务暂时不可用')
    }

    reportUrl.value = res.data.url
    status.value = 'done'
  } catch (err) {
    status.value = 'error'
    errorMsg.value = err.message || '网络请求失败，请检查网络后重试'
  }
}

function copyLink() {
  uni.setClipboardData({
    data: reportUrl.value,
    success: () => uni.showToast({ title: '链接已复制', icon: 'success' })
  })
}

function openInBrowser() {
  uni.navigateTo({
    url: `/pages/report-view/report-view?url=${encodeURIComponent(reportUrl.value)}`
  })
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
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 8rpx;
  background: $border-light;
  border-radius: $radius-full;
  overflow: hidden;
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

.hint-text {
  font-size: 24rpx;
  color: $text-muted;
  text-align: center;
}
</style>
