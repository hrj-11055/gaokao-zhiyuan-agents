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
      <ChatBubble
        v-for="(msg, index) in messages"
        :key="index"
        :type="msg.role"
        :content="msg.content"
        :isStreaming="isStreaming && index === messages.length - 1 && msg.role === 'ai'"
      />

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

  // 添加用户消息
  messages.value = appendMessage(conversationId.value, {
    role: 'user',
    content: text
  })
  inputText.value = ''
  scrollToBottom()

  // 添加空的 AI 消息占位
  const aiMsg = { role: 'ai', content: '', timestamp: Date.now() }
  messages.value = [...messages.value, aiMsg]
  isStreaming.value = true
  scrollToBottom()

  // 发送到 Dify
  currentAbort = sendMessageStream({
    query: text,
    conversationId: conversationId.value,
    user: getUserId(),
    inputs: buildProfileInputs(loadUserProfile()),
    onChunk(answerChunk, convId) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'ai') {
        lastMsg.content += answerChunk
        messages.value = [...messages.value]
      }
      if (convId && !conversationId.value) {
        conversationId.value = convId
      }
    },
    onEnd({ conversationId: convId }) {
      isStreaming.value = false
      if (convId) conversationId.value = convId
      const msgs = messages.value.filter(m => m.content.length > 0)
      saveHistory(conversationId.value, msgs)
      scrollToBottom()
    },
    onError(errMsg) {
      isStreaming.value = false
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'ai') {
        lastMsg.content = errMsg || '出了点问题，请稍后重试'
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
</style>
