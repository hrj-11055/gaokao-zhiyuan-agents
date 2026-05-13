<template>
  <view class="profile-container">
    <view class="placeholder">
      <text class="placeholder-text">我的</text>
      <text class="placeholder-subtitle">敬请期待...</text>
    </view>
  </view>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  uni.setNavigationBarTitle({
    title: '我的'
  })
})
</script>

<style lang="scss" scoped>
.profile-container {
  min-height: 100vh;
  background-color: #F9FAFB;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder {
  text-align: center;
}

.placeholder-text {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #374151;
  margin-bottom: 20rpx;
}

.placeholder-subtitle {
  display: block;
  font-size: 28rpx;
  color: #9CA3AF;
}
</style>
