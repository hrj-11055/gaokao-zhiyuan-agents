<template>
  <view class="personality-guide">
    <text class="personality-guide-kicker">补充分数之外的信息</text>
    <text class="personality-guide-title">还不确定自己适合什么方向？</text>
    <text class="personality-guide-desc">
      做一份约 3 分钟的性格测试，我后面的专业建议会更贴合你的思考和决策方式。
    </text>
    <view class="personality-guide-actions">
      <view class="personality-guide-primary" @click="emit('start')">
        <text class="personality-guide-primary-text">
          {{ started ? '继续性格测试' : '去做性格测试' }}
        </text>
        <text class="personality-guide-arrow">›</text>
      </view>
      <view class="personality-guide-dismiss" @click="emit('dismiss')">
        <text class="personality-guide-dismiss-text">稍后再说</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  started: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['start', 'dismiss'])
</script>

<style lang="scss" scoped>
.personality-guide {
  margin: -18rpx 32rpx 30rpx 128rpx;
  padding: 24rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, rgba(255, 247, 237, 0.98) 0%, rgba(255, 255, 255, 0.94) 100%);
  border: 2rpx solid rgba(249, 115, 22, 0.2);
  box-shadow: 0 12rpx 32rpx rgba(124, 45, 18, 0.08);
  box-sizing: border-box;
}

.personality-guide-kicker,
.personality-guide-title,
.personality-guide-desc {
  display: block;
}

.personality-guide-kicker {
  color: #ea580c;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 800;
}

.personality-guide-title {
  margin-top: 8rpx;
  color: #1f2937;
  font-size: 28rpx;
  line-height: 1.4;
  font-weight: 900;
}

.personality-guide-desc {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.55;
}

.personality-guide-actions {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.personality-guide-primary {
  height: 72rpx;
  padding: 0 24rpx;
  border-radius: 14rpx;
  background: #f97316;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 8rpx 18rpx rgba(249, 115, 22, 0.2);
}

.personality-guide-primary:active {
  background: #ea580c;
}

.personality-guide-primary-text,
.personality-guide-arrow {
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 800;
}

.personality-guide-arrow {
  font-size: 36rpx;
  line-height: 1;
}

.personality-guide-dismiss {
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.personality-guide-dismiss-text {
  color: #8a94a6;
  font-size: 23rpx;
  font-weight: 700;
}
</style>
