<template>
  <view class="page">
    <!-- 品牌 Header -->
    <view class="header">
      <view class="logo">
        <text class="logo-text">峰</text>
      </view>
      <text class="title">峰哥报考参谋</text>
      <text class="subtitle">张雪峰风格的 AI 志愿填报助手</text>
    </view>

    <!-- 功能描述 -->
    <view class="desc-card">
      <text class="desc-text">问专业、问学校、问分数，AI 帮你分析志愿填报，免费不限次数。</text>
    </view>

    <!-- 核心入口 -->
    <view class="primary-btn" @click="goChat">
      <text class="primary-btn-icon">💬</text>
      <view class="primary-btn-content">
        <text class="primary-btn-title">免费咨询</text>
        <text class="primary-btn-sub">AI 实时对话 · 不限次数</text>
      </view>
    </view>

    <!-- 未来入口 -->
    <view class="future-row">
      <view class="future-card">
        <text class="future-text">📋 测评填表</text>
        <text class="future-hint">即将上线</text>
      </view>
      <view class="future-card">
        <text class="future-text">📊 综合报告</text>
        <text class="future-hint">即将上线</text>
      </view>
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">
      <text class="disclaimer-text">⚠️ 数据仅供参考，请以各省考试院公布信息为准</text>
    </view>
  </view>
</template>

<script setup>
function goChat() {
  uni.navigateTo({ url: '/pages/chat/chat' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(135deg, $brand-gradient-start 0%, $brand-gradient-end 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
  padding-top: 120rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 48rpx;
}

.logo {
  width: 128rpx;
  height: 128rpx;
  background: $brand-primary;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.logo-text {
  color: #fff;
  font-size: 56rpx;
  font-weight: bold;
}

.title {
  font-size: 40rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.subtitle {
  font-size: 26rpx;
  color: $text-secondary;
}

.desc-card {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-lg;
  padding: 28rpx 32rpx;
  margin-bottom: 28rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.desc-text {
  font-size: 28rpx;
  color: $text-secondary;
  line-height: 1.7;
}

.primary-btn {
  width: 100%;
  background: $brand-primary;
  border-radius: $radius-lg;
  padding: 32rpx;
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.primary-btn-icon {
  font-size: 44rpx;
  margin-right: 24rpx;
}

.primary-btn-content {
  display: flex;
  flex-direction: column;
}

.primary-btn-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #fff;
}

.primary-btn-sub {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 4rpx;
}

.future-row {
  width: 100%;
  display: flex;
  gap: 20rpx;
  margin-bottom: auto;
}

.future-card {
  flex: 1;
  background: $bg-white;
  border-radius: $radius-md;
  padding: 24rpx;
  opacity: 0.45;
  border: 2rpx dashed $border-light;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.future-text {
  font-size: 28rpx;
  color: $text-secondary;
}

.future-hint {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 4rpx;
}

.disclaimer {
  width: 100%;
  padding: 32rpx 0 48rpx;
  text-align: center;
}

.disclaimer-text {
  font-size: 22rpx;
  color: $text-muted;
}
</style>
