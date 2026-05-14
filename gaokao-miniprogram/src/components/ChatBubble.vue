<template>
  <view class="bubble-wrap" :class="[`bubble-${type}`]">
    <!-- AI 头像 -->
    <view v-if="type === 'ai'" class="avatar">
      <text class="avatar-text">峰</text>
    </view>

    <!-- 气泡内容容器 -->
    <view class="bubble-container">
      <view class="bubble" :class="[`bubble-${type}-inner`]">
        <view class="bubble-text" :class="{ 'text-streaming': isStreaming }">
          <rich-text :nodes="contentHtml" />
          <text v-if="isStreaming" class="cursor" />
        </view>
        <text v-if="type === 'ai'" class="ai-label">AI 生成 · 仅供参考</text>
      </view>

      <!-- 操作栏 (仅 AI 回复显示) -->
      <view v-if="type === 'ai' && !isStreaming" class="actions-bar">
        <view class="action-btn" :class="{ 'playing': isPlaying }" @click="onToggleAudio">
          <text class="action-icon">{{ isPlaying ? '⏸' : '🔊' }}</text>
          <text class="action-text">{{ isPlaying ? '停止' : '朗读' }}</text>
        </view>
        <view class="action-divider" />
        <view class="action-btn" @click="onCopy">
          <text class="action-icon">📋</text>
          <text class="action-text">复制</text>
        </view>
        <view class="spacer" />
        
        <!-- 反馈成功后的状态 -->
        <text v-if="feedback !== 0" class="feedback-thanks">感谢评价</text>
        
        <template v-else>
          <view class="action-btn feedback-btn" @click="onFeedback(1)">
            <text class="action-icon">👍</text>
          </view>
          <view class="action-btn feedback-btn" @click="onFeedback(-1)">
            <text class="action-icon">👎</text>
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

// 状态管理
const isPlaying = ref(false)
const feedback = ref(0) // 0: 无, 1: 点赞, -1: 点踩
const localAudioPath = ref('') // 新增：缓存本地音频路径
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
    uni.showLoading({ title: '语音合成中...', mask: true })
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
    isPlaying.value = false
  }
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
  margin-bottom: 32rpx;
  padding: 0 24rpx;
}

.bubble-user {
  justify-content: flex-end;
}

.bubble-ai {
  justify-content: flex-start;
}

.avatar {
  width: 64rpx;
  height: 64rpx;
  background: $brand-primary;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 16rpx;
}

.avatar-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: bold;
}

.bubble-container {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.bubble {
  padding: 20rpx 28rpx;
  line-height: 1.6;
}

.bubble-user-inner {
  background: $brand-primary;
  border-radius: $radius-lg 4rpx $radius-lg $radius-lg;
}

.bubble-ai-inner {
  background: $bg-white;
  border-radius: 4rpx $radius-lg $radius-lg $radius-lg;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.bubble-text {
  font-size: 30rpx;
  word-break: break-word;
}

.bubble-user-inner .bubble-text {
  color: #fff;
}

.bubble-ai-inner .bubble-text {
  color: $text-primary;
}

.cursor {
  display: inline-block;
  width: 4rpx;
  height: 32rpx;
  background: $brand-primary;
  vertical-align: text-bottom;
  margin-left: 4rpx;
  animation: blink 1s step-end infinite;
}

.ai-label {
  display: block;
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 8rpx;
}

.actions-bar {
  display: flex;
  align-items: center;
  margin-top: 12rpx;
  padding: 4rpx 8rpx;
  min-height: 48rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 8rpx 16rpx;
  border-radius: $radius-sm;
  background: rgba(0,0,0,0.02);
  margin-right: 8rpx;

  &:active {
    background: rgba(0,0,0,0.05);
  }
  
  &.playing {
    background: rgba($brand-primary, 0.1);
    .action-icon, .action-text {
      color: $brand-primary;
    }
  }
}

.action-icon {
  font-size: 24rpx;
  color: $text-muted;
}

.action-text {
  font-size: 22rpx;
  color: $text-muted;
}

.action-divider {
  width: 2rpx;
  height: 20rpx;
  background: $border-light;
  margin: 0 8rpx;
}

.spacer {
  flex: 1;
}

.feedback-btn {
  margin-right: 0;
  margin-left: 8rpx;
  background: none;
  padding: 8rpx;
}

.feedback-thanks {
  font-size: 22rpx;
  color: $brand-primary;
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
