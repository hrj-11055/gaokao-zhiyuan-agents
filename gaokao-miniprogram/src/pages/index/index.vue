<template>
  <view class="page">
    <!-- 品牌 Header -->
    <view class="header">
      <view class="logo">
        <text class="logo-text">峰</text>
      </view>
      <text class="title">峰哥咨询参考</text>
      <text class="subtitle">AI 志愿填报助手，专业的高考志愿参考建议</text>
    </view>

    <!-- 考生信息填报 -->
    <view class="profile-card">
      <view class="card-header">
        <text class="card-title">2026 高考志愿模拟填报</text>
        <text class="save-status">{{ saveStatus }}</text>
      </view>

      <picker :range="provinces" :value="provinceIndex" @change="onProvinceChange">
        <view class="field-row">
          <text class="field-label">省份</text>
          <view class="field-value-wrap">
            <text class="field-value" :class="{ placeholder: !profile.province }">{{ profile.province || '请选择' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </picker>

      <picker :range="categories" :value="categoryIndex" @change="onCategoryChange">
        <view class="field-row">
          <text class="field-label">科目</text>
          <view class="field-value-wrap">
            <text class="field-value" :class="{ placeholder: !profile.category }">{{ profile.category || '请选择' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </picker>

      <view class="field-row">
        <text class="field-label">分数</text>
        <view class="field-value-wrap">
          <input
            class="field-input"
            type="number"
            maxlength="3"
            :value="profile.score"
            placeholder="请输入"
            placeholder-class="input-placeholder"
            @input="onScoreInput"
          />
          <text class="field-unit">分</text>
        </view>
      </view>

      <view class="field-row field-row-last">
        <text class="field-label">位次</text>
        <view class="field-value-wrap">
          <input
            class="field-input"
            type="number"
            maxlength="8"
            :value="profile.rank"
            placeholder="选填"
            placeholder-class="input-placeholder"
            @input="onRankInput"
          />
          <text class="field-unit">名</text>
        </view>
      </view>

      <view class="primary-btn" @click="onSmartFill">
        <text class="primary-btn-title">智能填报</text>
      </view>

      <text class="profile-hint">填写后，AI 咨询会自动带入你的省份、科目、分数和位次。</text>
    </view>

    <!-- 咨询入口 -->
    <view class="chat-entry" @click="goChat">
      <view class="chat-entry-content">
        <text class="chat-entry-title">免费咨询</text>
        <text class="chat-entry-sub">AI 实时对话 · 带着考生信息问更准</text>
      </view>
      <text class="chat-entry-arrow">›</text>
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">
      <text class="disclaimer-text">⚠️ 数据仅供参考，请以各省考试院公布信息为准</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadUserProfile, saveUserProfile, isProfileComplete } from '../../utils/storage.js'

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆'
]
const categories = ['物理类', '历史类']

const profile = ref(loadUserProfile())
const saveStatus = ref('自动保存')

const provinceIndex = computed(() => Math.max(0, provinces.indexOf(profile.value.province)))
const categoryIndex = computed(() => Math.max(0, categories.indexOf(profile.value.category)))

onShow(() => {
  profile.value = loadUserProfile()
})

function goChat() {
  uni.navigateTo({ url: '/pages/chat/chat' })
}

function persistProfile(nextProfile) {
  profile.value = saveUserProfile(nextProfile)
  saveStatus.value = '已自动保存'
}

function onProvinceChange(event) {
  const index = Number(event.detail.value)
  persistProfile({ ...profile.value, province: provinces[index] })
}

function onCategoryChange(event) {
  const index = Number(event.detail.value)
  persistProfile({ ...profile.value, category: categories[index] })
}

function onScoreInput(event) {
  persistProfile({ ...profile.value, score: event.detail.value })
}

function onRankInput(event) {
  persistProfile({ ...profile.value, rank: event.detail.value })
}

function onSmartFill() {
  if (!isProfileComplete(profile.value)) {
    uni.showToast({
      title: '请先填写省份、科目和分数',
      icon: 'none'
    })
    return
  }
  goChat()
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
  padding-top: 104rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.logo {
  width: 112rpx;
  height: 112rpx;
  background: $brand-primary;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.logo-text {
  color: #fff;
  font-size: 50rpx;
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

.profile-card {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 42rpx 32rpx 32rpx;
  box-shadow: 0 16rpx 40rpx rgba(249, 115, 22, 0.12);
  box-sizing: border-box;
  margin-bottom: 24rpx;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28rpx;
}

.card-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
}

.save-status {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.field-row {
  height: 104rpx;
  border-bottom: 2rpx solid $border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-row-last {
  border-bottom: none;
  margin-bottom: 28rpx;
}

.field-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
}

.field-value-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 260rpx;
}

.field-value {
  font-size: 30rpx;
  color: $text-secondary;
}

.placeholder,
.input-placeholder {
  color: $text-muted;
}

.chevron {
  margin-left: 18rpx;
  font-size: 46rpx;
  line-height: 1;
  color: $text-muted;
}

.field-input {
  width: 180rpx;
  text-align: right;
  font-size: 34rpx;
  color: $text-secondary;
}

.field-unit {
  margin-left: 14rpx;
  font-size: 28rpx;
  color: $text-secondary;
}

.primary-btn {
  width: 100%;
  background: $brand-primary;
  border-radius: $radius-full;
  height: 84rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 22rpx;
}

.primary-btn-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.profile-hint {
  display: block;
  text-align: center;
  font-size: 23rpx;
  color: $text-muted;
  line-height: 1.6;
}

.chat-entry {
  width: 100%;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(249, 115, 22, 0.16);
  border-radius: $radius-lg;
  padding: 28rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: auto;
  box-sizing: border-box;
}

.chat-entry-content {
  display: flex;
  flex-direction: column;
}

.chat-entry-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.chat-entry-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-secondary;
}

.chat-entry-arrow {
  font-size: 46rpx;
  color: $brand-primary;
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
