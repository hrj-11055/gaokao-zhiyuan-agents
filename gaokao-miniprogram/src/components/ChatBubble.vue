<template>
  <view class="bubble-wrap" :class="[`bubble-${type}`]">
    <view class="bubble-container" :class="[`bubble-container-${type}`]">
      <view class="bubble" :class="[`bubble-${type}-inner`]">
        <view class="bubble-text" :class="{ 'text-streaming': isStreaming }">
          <text v-if="showStreamingPlaceholder" class="streaming-placeholder">正在分析...</text>
          <rich-text v-else :nodes="contentHtml" />
          <text v-if="isStreaming" class="cursor" />
        </view>
        <text v-if="type === 'ai'" class="ai-label">AI 志愿咨询结果仅供参考，请结合官方信息核对</text>
      </view>

      <view v-if="type === 'ai' && !isStreaming && showActions" class="actions-bar">
        <view v-if="canRegenerate" class="action-btn refresh-btn" @click="onRegenerate">
          <LucideIcon name="RotateCcw" size="24rpx" color="#2563eb" />
          <text class="action-text refresh-text">重新生成</text>
        </view>

        <view class="action-btn" @click="onCopy">
          <LucideIcon name="Copy" size="24rpx" color="#64748b" />
          <text class="action-text">复制内容</text>
        </view>

        <view class="spacer" />

        <view
          class="action-btn feedback-btn"
          :class="{ 'action-btn-active': feedback === 1 }"
          @click="onFeedback(1)"
        >
          <LucideIcon name="ThumbsUp" size="24rpx" :color="feedback === 1 ? '#f97316' : '#64748b'" />
          <text class="feedback-label">有用</text>
        </view>
        <view
          class="action-btn feedback-btn"
          :class="{ 'action-btn-active': feedback === -1 }"
          @click="onFeedback(-1)"
        >
          <LucideIcon name="ThumbsDown" size="24rpx" :color="feedback === -1 ? '#f97316' : '#64748b'" />
          <text class="feedback-label">不准</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import LucideIcon from './LucideIcon.vue'
import { markdownToRichTextHtml } from '../utils/markdown.js'
import { sendFeedback } from '../api/dify.js'

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (v) => ['user', 'ai'].includes(v)
  },
  content: {
    type: String,
    default: ''
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  messageId: {
    type: String,
    default: ''
  },
  showActions: {
    type: Boolean,
    default: true
  },
  canRegenerate: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['regenerate'])

const contentHtml = computed(() => markdownToRichTextHtml(props.content))
const showStreamingPlaceholder = computed(() =>
  props.type === 'ai' && props.isStreaming && !String(props.content || '').trim()
)

const feedback = ref(0)

function onRegenerate() {
  emit('regenerate')
}

function onCopy() {
  uni.setClipboardData({
    data: props.content,
    success: () => {
      uni.showToast({ title: '已复制到剪贴板', icon: 'none' })
    }
  })
}

async function onFeedback(value) {
  if (feedback.value === value) return
  feedback.value = value

  try {
    const success = await sendFeedback({
      messageId: props.messageId,
      rating: value,
      query: '',
      answer: props.content
    })

    if (!success) {
      console.warn('[Feedback] Server failed to record feedback')
    }
  } catch (error) {
    console.error('[Feedback] Error:', error)
  }
}
</script>

<style lang="scss" scoped>
.bubble-wrap {
  display: flex;
  align-items: flex-start;
  width: 100%;
  padding: 0 32rpx;
  margin-bottom: 34rpx;
  box-sizing: border-box;
}

.bubble-user {
  justify-content: flex-end;
}

.bubble-ai {
  justify-content: flex-start;
}

.bubble-container {
  display: flex;
  flex-direction: column;
  max-width: 96%;
  min-width: 0;
}

.bubble-container-user {
  align-items: flex-end;
}

.bubble-container-ai {
  align-items: flex-start;
}

.bubble {
  padding: 24rpx 32rpx;
  line-height: 1.6;
  position: relative;
  box-sizing: border-box;
}

.bubble-user-inner {
  background: linear-gradient(135deg, #2dd4bf, #8b5cf6);
  border-radius: 18rpx 6rpx 18rpx 18rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 10rpx 24rpx rgba(139, 92, 246, 0.24);
}

.bubble-ai-inner {
  background: rgba(255, 255, 255, 0.88);
  border-radius: 6rpx 18rpx 18rpx 18rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10rpx 32rpx rgba(15, 23, 42, 0.05);
}

.bubble-text {
  font-size: 28rpx;
  line-height: 1.62;
  word-break: break-word;
}

.bubble-user-inner .bubble-text {
  color: #ffffff;
}

.bubble-ai-inner .bubble-text {
  color: #111827;
}

.streaming-placeholder {
  color: #8a94a6;
}

.cursor {
  display: inline-block;
  width: 6rpx;
  height: 34rpx;
  margin-left: 8rpx;
  vertical-align: text-bottom;
  background: #f97316;
  animation: blink 1s step-end infinite;
}

.ai-label {
  display: block;
  margin-top: 16rpx;
  padding-top: 12rpx;
  border-top: 2rpx solid rgba(15, 23, 42, 0.05);
  color: #9ca3af;
  font-size: 21rpx;
  line-height: 1.35;
}

.actions-bar {
  width: 100%;
  min-height: 52rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 14rpx;
  box-sizing: border-box;
}

.action-btn {
  min-height: 48rpx;
  padding: 0 18rpx;
  border-radius: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  background: rgba(255, 255, 255, 0.5);
  border: 2rpx solid rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
}

.action-btn:active,
.action-btn-active {
  background: rgba(255, 247, 237, 0.8);
  border-color: rgba(249, 115, 22, 0.2);
}

.action-text {
  color: #64748b;
  font-size: 21rpx;
  line-height: 1;
  font-weight: 600;
}

.refresh-text {
  color: #2563eb;
}

.spacer {
  flex: 1;
}

.feedback-btn {
  width: 52rpx;
  padding: 0;
}

.feedback-label {
  display: none;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
