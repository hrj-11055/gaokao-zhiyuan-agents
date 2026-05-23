<template>
  <view class="chat-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 对话区域 -->
    <scroll-view
      class="chat-scroll"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
    >
      <view class="profile-strip">
        <view class="profile-strip-main">
          <text class="profile-strip-label">当前咨询档案</text>
          <text class="profile-strip-value">{{ profileSummary }}</text>
        </view>
        <text class="profile-strip-action" @click="goHome">修改</text>
      </view>

      <view v-if="!isProfileReady" class="profile-gate">
        <view class="profile-gate-copy">
          <text class="profile-gate-title">先补全核心档案</text>
          <text class="profile-gate-desc">省份、科类和分数会直接影响院校范围判断。补齐后再开始咨询，回答会更可靠。</text>
        </view>
        <view class="profile-gate-btn" @click="goHome">
          <text class="profile-gate-btn-text">去首页补全</text>
        </view>
      </view>

      <!-- AI 欢迎语 -->
      <ChatBubble type="ai" :content="welcomeMsg" />

      <!-- 快捷问题（仅首次显示，发送第一条消息后隐藏） -->
      <QuickQuestions v-if="messages.length === 0 && isProfileReady" :profile="profile" @select="onQuickSelect" />

      <!-- 消息列表 -->
      <template v-for="(msg, index) in messages" :key="index">
        <ChatBubble
          :type="msg.role"
          :content="msg.content"
          :messageId="msg.messageId"
          :isStreaming="isStreaming && index === messages.length - 1 && msg.role === 'ai'"
        />
        <!-- 截断重试提示：AI 消息回复中途被截断时显示 -->
        <view
          v-if="msg.role === 'ai' && msg.truncated && index === messages.length - 1"
          class="retry-bar"
        >
          <text class="retry-hint">这次回复不完整</text>
          <view class="retry-btn" @click="handleRetry">
            <text class="retry-btn-text">重新生成</text>
          </view>
        </view>
      </template>

      <!-- 底部间距 -->
      <view style="height: 48rpx;" />
    </scroll-view>

    <!-- 底部悬浮输入栏 -->
    <view class="input-bar">
      <input
        class="input-field"
        v-model="inputText"
        :placeholder="chatInputPlaceholder"
        placeholder-class="input-placeholder"
        :disabled="isStreaming || !isProfileReady"
        confirm-type="send"
        @confirm="handleSend"
      />
      <view
        class="send-btn"
        :class="{ 'send-btn-active': inputText.trim() && !isStreaming && isProfileReady }"
        @click="handleSend"
      >
        <text class="send-icon">↑</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import ChatBubble from '../../components/ChatBubble.vue'
import QuickQuestions from '../../components/QuickQuestions.vue'
import { useChat } from './useChat.js'
import { isProfileComplete, loadUserProfile } from '../../utils/storage.js'

const welcomeMsg = '你好，我会结合你的省份、科类和分数来回答。可以直接问院校范围、专业取舍、冲稳保思路，结果仅供志愿填报参考。'

const scrollTop = ref(0)
const profile = ref(loadUserProfile())
const { chatStore, inputText, isStreaming, onSend, onRetry } = useChat()
const messages = computed(() => chatStore.messages)
const isProfileReady = computed(() => isProfileComplete(profile.value))
const chatInputPlaceholder = computed(() =>
  isProfileReady.value ? '向 AI 咨询师提问（如：物理580能上什么大学）...' : '请先补全省份、科类和分数'
)
const profileSummary = computed(() => {
  const parts = []
  if (profile.value.province) parts.push(profile.value.province)
  if (profile.value.category) parts.push(profile.value.category)
  if (profile.value.score) parts.push(`${profile.value.score}分`)
  if (profile.value.rank) parts.push(`位次${profile.value.rank}`)
  return parts.length ? parts.join(' · ') : '未填写基础信息，建议先回首页补全'
})

// 页面显示时恢复历史
onShow(() => {
  profile.value = loadUserProfile()
  chatStore.loadHistory()
})

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    scrollTop.value = scrollTop.value === 0 ? 1 : 0
    setTimeout(() => {
      scrollTop.value = 999999
    }, 50)
  })
}

// 快捷问题点击
const onQuickSelect = (question) => {
  inputText.value = question
  handleSend()
}

// 代理回调
const handleSend = () => {
  if (!isProfileReady.value) {
    uni.showToast({ title: '请先补全省份、科类和分数', icon: 'none' })
    return
  }
  onSend({ onScrollToBottom: scrollToBottom })
}
const handleRetry = () => onRetry({ onScrollToBottom: scrollToBottom })

function goHome() {
  uni.switchTab({ url: '/pages/index/index' })
}

</script>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background:
    radial-gradient(80% 45% at 20% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EEF6FF 100%);
  position: relative;
  overflow: hidden;
}

.cyber-glow-bg-indigo {
  position: absolute;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.05) 0%, rgba(255, 255, 255, 0) 70%);
  top: -100rpx;
  left: -150rpx;
  pointer-events: none;
}
.cyber-glow-bg-orange {
  position: absolute;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.025) 0%, rgba(255, 255, 255, 0) 70%);
  bottom: 200rpx;
  right: -150rpx;
  pointer-events: none;
}

.chat-scroll {
  flex: 1;
  padding-top: 24rpx;
  z-index: 10;
}

.profile-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin: 0 32rpx 24rpx;
  padding: 22rpx 26rpx;
  border-radius: $radius-lg;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid $border-light;
  box-shadow: 0 8rpx 28rpx rgba(15, 23, 42, 0.06);
}

.profile-strip-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.profile-strip-label {
  font-size: 22rpx;
  color: $text-muted;
  margin-bottom: 6rpx;
}

.profile-strip-value {
  font-size: 27rpx;
  color: $text-primary;
  font-weight: 700;
  line-height: 1.35;
}

.profile-strip-action {
  flex-shrink: 0;
  color: $brand-violet;
  font-size: 25rpx;
  font-weight: 700;
}

.profile-gate {
  margin: 0 32rpx 24rpx;
  padding: 26rpx;
  border-radius: $radius-lg;
  background: #FFF7ED;
  border: 1px solid rgba(249, 115, 22, 0.22);
  display: flex;
  flex-direction: column;
  gap: 22rpx;
  z-index: 10;
}

.profile-gate-copy {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.profile-gate-title {
  font-size: 29rpx;
  font-weight: 800;
  color: $text-primary;
}

.profile-gate-desc {
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.5;
}

.profile-gate-btn {
  height: 72rpx;
  border-radius: $radius-full;
  background: $grad-accent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-gate-btn-text {
  color: #fff;
  font-size: 27rpx;
  font-weight: 800;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  z-index: 20;
  box-shadow: 0 -12rpx 48rpx rgba(15, 23, 42, 0.04);
}

.input-field {
  flex: 1;
  background: rgba(241, 245, 249, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: $radius-full;
  padding: 20rpx 36rpx;
  font-size: 28rpx;
  color: $text-primary;
  transition: all 0.2s;

  &:focus {
    border-color: rgba(37, 99, 235, 0.25);
    background: #fff;
  }
}

.input-placeholder {
  color: $text-muted;
}

.send-btn {
  width: 80rpx;
  height: 80rpx;
  background: #F1F5F9;
  border: 1px solid $border-light;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;

  &:active {
    transform: scale(0.95);
  }
}

.send-btn-active {
  background: $grad-accent;
  border: none;
  box-shadow: 0 8rpx 20rpx rgba(249, 115, 22, 0.24);
}

.send-icon {
  color: $text-muted;
  font-size: 38rpx;
  font-weight: 900;
}

.send-btn-active .send-icon {
  color: #fff;
}

// 重新生成提示条
.retry-bar {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 8rpx 36rpx 24rpx;
  z-index: 10;
}

.retry-hint {
  font-size: 23rpx;
  color: $text-muted;
}

.retry-btn {
  background: #FFF7ED;
  border: 1px solid rgba(255, 107, 0, 0.3);
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  transition: all 0.2s;

  &:active {
    background: rgba(255, 107, 0, 0.1);
  }
}

.retry-btn-text {
  font-size: 22rpx;
  color: $brand-primary;
  font-weight: 700;
}
</style>
