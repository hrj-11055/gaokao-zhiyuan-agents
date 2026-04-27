<template>
  <view class="bubble-wrap" :class="[`bubble-${type}`]">
    <!-- AI 头像 -->
    <view v-if="type === 'ai'" class="avatar">
      <text class="avatar-text">峰</text>
    </view>

    <!-- 气泡内容 -->
    <view class="bubble" :class="[`bubble-${type}-inner`]">
      <text class="bubble-text" :class="{ 'text-streaming': isStreaming }">
        {{ content }}<text v-if="isStreaming" class="cursor" />
      </text>
      <text v-if="type === 'ai'" class="ai-label">AI 生成 · 仅供参考</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
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
  }
})
</script>

<style lang="scss" scoped>
.bubble-wrap {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24rpx;
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

.bubble {
  max-width: 75%;
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

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
