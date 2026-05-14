<template>
  <view class="chat-page">
    <!-- 对话区域 -->
    <scroll-view
      class="chat-scroll"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
    >
      <!-- AI 欢迎语 -->
      <ChatBubble type="ai" :content="welcomeMsg" />

      <!-- 快捷问题（仅首次显示，发送第一条消息后隐藏） -->
      <QuickQuestions v-if="messages.length === 0" @select="onQuickSelect" />

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
          <text class="retry-hint">回复未完整</text>
          <view class="retry-btn" @click="handleRetry">重新生成</view>
        </view>
      </template>

      <!-- 底部间距 -->
      <view style="height: 24rpx;" />
    </scroll-view>

    <!-- 底部输入栏 -->
    <view class="input-bar">
      <input
        class="input-field"
        v-model="inputText"
        placeholder="输入你想问的..."
        placeholder-class="input-placeholder"
        :disabled="isStreaming"
        confirm-type="send"
        @confirm="handleSend"
      />
      <view
        class="send-btn"
        :class="{ 'send-btn-active': inputText.trim() && !isStreaming }"
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

const welcomeMsg = '同学你好！我是峰哥咨询参考，你的 AI 志愿填报助手。有什么想问的？分数、学校、专业，都可以聊 👋'

const scrollTop = ref(0)
const { chatStore, inputText, isStreaming, onSend, onRetry } = useChat()
const messages = computed(() => chatStore.messages)

// 页面显示时恢复历史
onShow(() => {
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
const handleSend = () => onSend({ onScrollToBottom: scrollToBottom })
const handleRetry = () => onRetry({ onScrollToBottom: scrollToBottom })

</script>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-page;
}

.chat-scroll {
  flex: 1;
  padding-top: 16rpx;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: $bg-white;
  border-top: 2rpx solid $border-light;
}

.input-field {
  flex: 1;
  background: $bg-input;
  border-radius: $radius-full;
  padding: 18rpx 32rpx;
  font-size: 30rpx;
}

.input-placeholder {
  color: $text-muted;
}

.send-btn {
  width: 72rpx;
  height: 72rpx;
  background: $bg-input;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.send-btn-active {
  background: $brand-primary;
}

.send-icon {
  color: $text-muted;
  font-size: 32rpx;
}

.send-btn-active .send-icon {
  color: #fff;
}

.retry-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 8rpx 32rpx 20rpx;
}

.retry-hint {
  font-size: 24rpx;
  color: $text-muted;
}

.retry-btn {
  font-size: 24rpx;
  color: $brand-primary;
  padding: 6rpx 20rpx;
  border: 2rpx solid $brand-primary;
  border-radius: $radius-full;
}
</style>
