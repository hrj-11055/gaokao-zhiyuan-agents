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
import { computed } from 'vue'

defineEmits(['select'])

const props = defineProps({
  profile: {
    type: Object,
    default: () => ({})
  }
})

const questions = computed(() => {
  const province = props.profile?.province || '广东'
  const category = props.profile?.category || '物理类'
  const score = props.profile?.score || '580'
  return [
    `我${province}${category}${score}分能考虑哪些学校？`,
    '这个分数段怎么安排冲稳保？',
    '计算机、法学和师范怎么取舍？',
    '如果不确定专业，应该先排除哪些方向？'
  ]
})
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
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: $radius-full;
  padding: 12rpx 28rpx;
}

.quick-text {
  font-size: 26rpx;
  color: $brand-violet;
}
</style>
