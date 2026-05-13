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
          <view class="retry-btn" @click="onRetry">重新生成</view>
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
        @confirm="onSend"
      />
      <view
        class="send-btn"
        :class="{ 'send-btn-active': inputText.trim() && !isStreaming }"
        @click="onSend"
      >
        <text class="send-icon">↑</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import ChatBubble from '../../components/ChatBubble.vue'
import QuickQuestions from '../../components/QuickQuestions.vue'
import { sendMessageStream } from '../../api/dify.js'
import { getUserId, loadHistory, saveHistory, appendMessage, loadUserProfile, buildProfileInputs } from '../../utils/storage.js'

const welcomeMsg = '同学你好！我是峰哥咨询参考，你的 AI 志愿填报助手。有什么想问的？分数、学校、专业，都可以聊 👋'

const messages = ref([])
const inputText = ref('')
const isStreaming = ref(false)
const scrollTop = ref(0)
const conversationId = ref('')

let currentAbort = null
let lastQuery = ''

// 页面显示时恢复历史
onShow(() => {
  const history = loadHistory()
  conversationId.value = history.conversationId
  messages.value = history.messages
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
function onQuickSelect(question) {
  inputText.value = question
  onSend()
}

// 发送消息
function onSend() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return
  sendQuery(text)
}

// 重试：移除上一条截断的 AI 消息，重新发送
function onRetry() {
  if (!lastQuery || isStreaming.value) return
  const msgs = messages.value
  if (msgs.length > 0 && msgs[msgs.length - 1].role === 'ai') {
    messages.value = msgs.slice(0, -1)
  }
  sendQuery(lastQuery)
}

function sendQuery(text) {
  lastQuery = text

  // 添加用户消息（重试时不重复添加）
  const lastMsg = messages.value[messages.value.length - 1]
  if (!lastMsg || lastMsg.role !== 'user' || lastMsg.content !== text) {
    messages.value = appendMessage(conversationId.value, { role: 'user', content: text })
    inputText.value = ''
  }
  scrollToBottom()

  // 添加空的 AI 消息占位
  messages.value = [...messages.value, { role: 'ai', content: '', timestamp: Date.now() }]
  isStreaming.value = true
  scrollToBottom()

  currentAbort = sendMessageStream({
    query: text,
    conversationId: conversationId.value,
    user: getUserId(),
    inputs: buildProfileInputs(loadUserProfile()),
    onChunk(answerChunk, convId, msgId) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai') {
        last.content += answerChunk
        if (msgId) last.messageId = msgId
        messages.value = [...messages.value]
      }
      if (convId && !conversationId.value) {
        conversationId.value = convId
      }
    },
    onEnd({ conversationId: convId, messageId: msgId }) {
      isStreaming.value = false
      if (convId) conversationId.value = convId
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai' && msgId) {
        last.messageId = msgId
      }
      const msgs = messages.value.filter(m => m.content.length > 0)
      saveHistory(conversationId.value, msgs)
      scrollToBottom()
    },
    onError(errMsg) {
      isStreaming.value = false
      const last = messages.value[messages.value.length - 1]
      if (!last || last.role !== 'ai') return

      if (last.content.length > 0) {
        // 流中途截断：保留已有内容，标记为可重试
        last.truncated = true
        messages.value = [...messages.value]
      } else {
        // 未收到任何内容就失败：显示错误文字
        last.content = errMsg || '出了点问题，请稍后重试'
        messages.value = [...messages.value]
      }
      scrollToBottom()
    }
  })
}
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
