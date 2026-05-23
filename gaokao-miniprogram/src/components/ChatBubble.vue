<template>
  <view class="bubble-wrap" :class="[`bubble-${type}`]">
    <!-- AI 炫彩头像 -->
    <view v-if="type === 'ai'" class="avatar-outer">
      <view class="avatar-glow" />
      <view class="avatar">
        <text class="avatar-text">峰</text>
      </view>
    </view>

    <!-- 气泡内容容器 -->
    <view class="bubble-container">
      <view class="bubble" :class="[`bubble-${type}-inner`]">
        <view class="bubble-text" :class="{ 'text-streaming': isStreaming }">
          <text v-if="showStreamingPlaceholder" class="streaming-placeholder">正在分析...</text>
          <rich-text v-else :nodes="contentHtml" />
          <text v-if="isStreaming" class="cursor" />
        </view>
        <text v-if="type === 'ai'" class="ai-label">AI 志愿咨询结果仅供参考，请结合官方信息核对</text>
      </view>

      <!-- AI 回复操作栏 -->
      <view v-if="type === 'ai' && !isStreaming" class="actions-bar">
        <view class="action-btn" :class="{ 'playing': isPlaying }" @click="onToggleAudio">
          <text class="action-icon">{{ isPlaying ? '⏸' : '🔊' }}</text>
          <text class="action-text">{{ isPlaying ? '停止朗读' : '朗读' }}</text>
        </view>
        <view class="action-divider" />
        <view class="action-btn" @click="onCopy">
          <text class="action-icon">📋</text>
          <text class="action-text">复制内容</text>
        </view>
        <view class="spacer" />
        
        <!-- 反馈状态 -->
        <text v-if="feedback !== 0" class="feedback-thanks">已收到反馈</text>
        
        <template v-else>
          <view class="action-btn feedback-btn" @click="onFeedback(1)">
            <text class="action-icon-fb">👍</text>
          </view>
          <view class="action-btn feedback-btn" @click="onFeedback(-1)">
            <text class="action-icon-fb">👎</text>
          </view>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, onUnmounted } from 'vue'
import { markdownToRichTextHtml } from '../utils/markdown.js'
import { fetchTTSAudio, sendFeedback } from '../api/dify.js'

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
  }
})

const contentHtml = computed(() => markdownToRichTextHtml(props.content))
const showStreamingPlaceholder = computed(() =>
  props.type === 'ai' && props.isStreaming && !String(props.content || '').trim()
)

// 状态管理
const isPlaying = ref(false)
const feedback = ref(0) // 0: 无, 1: 点赞, -1: 点踩
const localAudioPath = ref('') // 缓存本地音频路径
let audioContext = null

// 语音播放
async function onToggleAudio() {
  if (isPlaying.value) {
    stopAudio()
    return
  }

  // 1. 优先使用缓存
  if (localAudioPath.value) {
    playLocalFile(localAudioPath.value)
    return
  }

  const cleanText = props.content.replace(/[#*`]/g, '').slice(0, 500)

  try {
    uni.showLoading({ title: 'AI 语音合成中...', mask: true })
    const arrayBuffer = await fetchTTSAudio(cleanText)
    uni.hideLoading()

    if (arrayBuffer.byteLength < 100) {
      throw new Error('生成的音频数据过短')
    }

    const fs = uni.getFileSystemManager()
    const filePath = `${wx.env.USER_DATA_PATH}/tts_${props.messageId || Date.now()}.mp3`
    
    fs.writeFileSync(filePath, arrayBuffer, 'binary')
    
    localAudioPath.value = filePath // 存入缓存
    playLocalFile(filePath)
    
  } catch (err) {
    console.error('[TTS] Process Failed:', err)
    uni.hideLoading()
    uni.showToast({ title: err.message || '语音合成失败', icon: 'none' })
  }
}

function playLocalFile(path) {
  if (audioContext) {
    audioContext.destroy()
    audioContext = null
  }
  
  audioContext = uni.createInnerAudioContext()
  audioContext.src = path
  
  audioContext.onPlay(() => { 
    isPlaying.value = true 
  })
  audioContext.onEnded(() => { 
    isPlaying.value = false 
  })
  audioContext.onError((res) => {
    console.error('[TTS] Playback Error:', res)
    isPlaying.value = false
    localAudioPath.value = '' // 播放失败则清除缓存尝试重试
    uni.showToast({ title: '播放失败', icon: 'none' })
  })
  
  audioContext.play()
}

function stopAudio() {
  if (audioContext) {
    audioContext.stop()
    audioContext.destroy()
    audioContext = null
  }
  isPlaying.value = false
}

// 复制
function onCopy() {
  uni.setClipboardData({
    data: props.content,
    success: () => {
      uni.showToast({ title: '已复制到剪贴板', icon: 'none' })
    }
  })
}

// 反馈
async function onFeedback(val) {
  if (feedback.value !== 0) return
  
  // 先更新 UI 提升响应感
  feedback.value = val
  
  try {
    const success = await sendFeedback({
      messageId: props.messageId,
      rating: val,
      query: '', 
      answer: props.content
    })
    
    if (!success) {
      console.warn('[Feedback] Server failed to record feedback')
    }
  } catch (e) {
    console.error('[Feedback] Error:', e)
  }
}

onUnmounted(() => {
  stopAudio()
})
</script>

<style lang="scss" scoped>
.bubble-wrap {
  display: flex;
  align-items: flex-start;
  margin-bottom: 36rpx;
  padding: 0 32rpx;
}

.bubble-user {
  justify-content: flex-end;
}

.bubble-ai {
  justify-content: flex-start;
}

.avatar-outer {
  position: relative;
  width: 76rpx;
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.avatar {
  width: 68rpx;
  height: 68rpx;
  background: $grad-royal;
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 16rpx rgba(99, 102, 241, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.15);
  z-index: 2;
}

.avatar-text {
  color: #fff;
  font-size: 30rpx;
  font-weight: 900;
}

.avatar-glow {
  position: absolute;
  top: -4rpx;
  left: -4rpx;
  right: -4rpx;
  bottom: -4rpx;
  background: rgba(37, 99, 235, 0.16);
  border-radius: 22rpx;
  filter: blur(8rpx);
  z-index: 1;
}

.bubble-container {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.bubble {
  padding: 24rpx 32rpx;
  line-height: 1.6;
  position: relative;
  box-sizing: border-box;
}

.bubble-user-inner {
  background: $grad-royal;
  border-radius: $radius-md $radius-xs $radius-md $radius-md;
  box-shadow: 0 8rpx 22rpx rgba(37, 99, 235, 0.20);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.bubble-ai-inner {
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: $radius-xs $radius-md $radius-md $radius-md;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 8rpx 32rpx rgba(15, 23, 42, 0.03);
}

.bubble-text {
  font-size: 29rpx;
  word-break: break-word;
}

.bubble-user-inner .bubble-text {
  color: #fff;
}

.bubble-ai-inner .bubble-text {
  color: $text-primary;
}

.streaming-placeholder {
  color: $text-secondary;
}

.cursor {
  display: inline-block;
  width: 6rpx;
  height: 34rpx;
  background: $brand-primary;
  vertical-align: text-bottom;
  margin-left: 8rpx;
  animation: blink 1s step-end infinite;
}

.ai-label {
  display: block;
  font-size: 21rpx;
  color: $text-muted;
  margin-top: 14rpx;
  border-top: 1px solid rgba(15, 23, 42, 0.05);
  padding-top: 10rpx;
}

.actions-bar {
  display: flex;
  align-items: center;
  margin-top: 14rpx;
  padding: 4rpx 10rpx;
  min-height: 48rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 20rpx;
  border-radius: $radius-xs;
  background: rgba(15, 23, 42, 0.02);
  border: 1px solid rgba(15, 23, 42, 0.04);
  margin-right: 12rpx;
  transition: all 0.2s;

  &:active {
    background: rgba(15, 23, 42, 0.05);
  }
  
  &.playing {
    background: rgba(255, 107, 0, 0.08);
    border-color: rgba(255, 107, 0, 0.2);
    .action-icon, .action-text {
      color: $brand-primary;
    }
  }
}

.action-icon {
  font-size: 24rpx;
  color: $text-secondary;
}

.action-text {
  font-size: 21rpx;
  color: $text-secondary;
  font-weight: 500;
}

.action-divider {
  width: 2rpx;
  height: 20rpx;
  background: rgba(15, 23, 42, 0.08);
  margin: 0 10rpx;
}

.spacer {
  flex: 1;
}

.feedback-btn {
  margin-right: 0;
  margin-left: 12rpx;
  background: rgba(15, 23, 42, 0.02);
  padding: 8rpx 12rpx;
}

.action-icon-fb {
  font-size: 24rpx;
}

.feedback-thanks {
  font-size: 21rpx;
  color: $brand-primary;
  font-weight: 700;
  animation: fadeIn 0.3s ease;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4rpx); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
