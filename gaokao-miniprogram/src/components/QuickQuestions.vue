<template>
  <view class="quick-wrap">
    <view
      v-for="(q, index) in questions"
      :key="index"
      class="quick-chip"
      @click="$emit('select', q)"
    >
      <text class="quick-text">{{ q }}</text>
    </view>
  </view>
</template>

<script setup>
defineEmits(['select'])

const questions = [
  '我广东省物理类580分能上什么学校？',
  '计算机还值得报吗？',
  '法学就业怎么样？',
  '怎么专业最适合 INTP'
]
</script>

<style lang="scss" scoped>
.quick-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  padding: 0 24rpx 24rpx;
}

.quick-chip {
  background: $bg-white;
  border: 2rpx solid $brand-primary;
  border-radius: $radius-full;
  padding: 12rpx 28rpx;
}

.quick-text {
  font-size: 26rpx;
  color: $brand-primary;
}
</style>
