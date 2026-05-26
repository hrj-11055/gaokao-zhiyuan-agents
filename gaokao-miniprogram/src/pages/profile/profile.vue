<template>
  <view class="profile-page">
    <!-- subtle orange glow at top -->
    <view class="bg-glow-soft" />

    <!-- Header: avatar + name + ID + VIP pill -->
    <view class="me-header">
      <view class="avatar-wrap">
        <view class="avatar">
          <text class="avatar-text">峰</text>
        </view>
      </view>
      <text class="user-name">志愿同学</text>
      <text class="user-id">ID: {{ shortUserId }}</text>
      <view class="vip-pill" :class="{ active: membershipStore.isActive }">
        <text class="vip-text">{{ membershipStore.isActive ? 'VIP · 报告已解锁' : '报告未解锁' }}</text>
      </view>
    </view>

    <!-- Exam info card -->
    <view class="info-card">
      <view class="info-card-header">
        <text class="info-label">考生信息</text>
        <view class="info-edit" @click="goEditProfile">
          <text class="info-edit-text">编辑</text>
          <text class="info-edit-arrow">›</text>
        </view>
      </view>
      <view class="info-grid">
        <view class="info-field">
          <text class="info-field-value">{{ profile.province || '未填写' }}</text>
          <text class="info-field-label">省份</text>
        </view>
        <view class="info-field">
          <text class="info-field-value">{{ profile.category || '未填写' }}</text>
          <text class="info-field-label">科目</text>
        </view>
        <view class="info-field">
          <text class="info-field-value">{{ profile.score || '未填写' }}</text>
          <text class="info-field-label">分数</text>
        </view>
      </view>
    </view>

    <!-- Business menu -->
    <view class="menu-list">
      <view class="menu-item" @click="goChat">
        <view class="menu-icon-wrap">
          <text class="menu-icon-emoji">💬</text>
        </view>
        <text class="menu-label">我的咨询记录</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goAssessments">
        <view class="menu-icon-wrap">
          <text class="menu-icon-emoji">🧠</text>
        </view>
        <text class="menu-label">我的测评结果</text>
        <view v-if="assessmentCount > 0" class="menu-badge">
          <text class="menu-badge-text">{{ assessmentCount }}/3</text>
        </view>
        <text v-else class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="onShare">
        <view class="menu-icon-wrap">
          <text class="menu-icon-emoji">👥</text>
        </view>
        <text class="menu-label">邀请好友</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- System menu -->
    <view class="menu-list">
      <view class="menu-item" @click="goPrivacy">
        <view class="menu-icon-wrap">
          <text class="menu-icon-emoji">🔒</text>
        </view>
        <text class="menu-label">隐私保护</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goFeedback">
        <view class="menu-icon-wrap">
          <text class="menu-icon-emoji">💌</text>
        </view>
        <text class="menu-label">反馈/客服</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goAbout">
        <view class="menu-icon-wrap">
          <text class="menu-icon-emoji">ⓘ</text>
        </view>
        <text class="menu-label">关于峰哥</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- Footer -->
    <view class="footer">
      <text class="footer-text">峰哥咨询参考 · 报告仅供志愿填报参考</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow, onShareAppMessage } from '@dcloudio/uni-app'
import { useMembershipStore } from '../../stores/membership.js'
import { loadUserProfile, loadAssessments, loadQuestionnaire, QUESTIONNAIRE_REQUIRED_COUNT } from '../../utils/storage.js'

const membershipStore = useMembershipStore()
const profile = ref(loadUserProfile())
const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())

const shortUserId = computed(() => (membershipStore.userId || 'CLOUD').slice(0, 8).toUpperCase())

const assessmentCount = computed(() => {
  let n = 0
  if (questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT) n++
  if (assessments.value.mbti.completed) n++
  if (assessments.value.holland.completed) n++
  return n
})

// Navigation
function goEditProfile() {
  uni.switchTab({ url: '/pages/index/index' })
  setTimeout(() => uni.$emit('open-profile-sheet'), 200)
}

function goChat() {
  uni.navigateTo({ url: '/pages/chat/chat' })
}

function goAssessments() {
  uni.navigateTo({ url: '/pages/assessments/assessments' })
}

function goPrivacy() {
  uni.navigateTo({ url: '/pages/privacy/privacy' })
}

function goFeedback() {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

function goAbout() {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

function onShare() {
  uni.showToast({ title: '请用右上角 ··· 分享', icon: 'none' })
}

onShow(() => {
  profile.value = loadUserProfile()
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
  membershipStore.loadStatus().catch(() => {})
})

onShareAppMessage(() => ({
  title: '邀请你一起生成高考志愿参考报告',
  path: `/pages/index/index?inviterId=${membershipStore.userId || ''}`,
}))
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff7ed 0%, #f9fafb 60%);
  padding: 0 32rpx;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.bg-glow-soft {
  position: absolute;
  top: -200rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.08) 0%, rgba(249, 115, 22, 0) 65%);
  pointer-events: none;
}

/* ---- Header ---- */
.me-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 48rpx;
  padding-bottom: 40rpx;
  position: relative;
  z-index: 2;
}

.avatar-wrap {
  margin-bottom: 20rpx;
}

.avatar {
  width: 112rpx;
  height: 112rpx;
  background: linear-gradient(135deg, #f97316, #ea580c);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(234, 88, 12, 0.25);
}

.avatar-text {
  color: #fff;
  font-size: 48rpx;
  font-weight: bold;
}

.user-name {
  font-size: 36rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.user-id {
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 16rpx;
}

.vip-pill {
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  background: #e5e7eb;

  &.active {
    background: linear-gradient(90deg, #fbbf24, #f59e0b);
  }
}

.vip-text {
  font-size: 22rpx;
  font-weight: 700;
  color: #6b7280;

  .vip-pill.active & {
    color: #78350f;
  }
}

/* ---- Info card ---- */
.info-card {
  background: #fff;
  border-radius: $radius-lg;
  padding: 28rpx 28rpx 24rpx;
  margin-bottom: 24rpx;
  border: 1px solid $border-light;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
  position: relative;
  z-index: 2;
}

.info-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.info-label {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.info-edit {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.info-edit-text {
  font-size: 26rpx;
  color: $brand-primary;
  font-weight: 600;
}

.info-edit-arrow {
  font-size: 32rpx;
  color: $brand-primary;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.info-field {
  background: #fafafa;
  border-radius: $radius-sm;
  padding: 20rpx 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.info-field-value {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.info-field-label {
  font-size: 22rpx;
  color: $text-muted;
}

/* ---- Menu list ---- */
.menu-list {
  background: #fff;
  border-radius: $radius-lg;
  margin-bottom: 24rpx;
  border: 1px solid $border-light;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
  overflow: hidden;
  position: relative;
  z-index: 2;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 28rpx 28rpx;
  border-bottom: 1px solid $border-light;
  transition: background-color 0.15s;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: rgba(15, 23, 42, 0.02);
  }
}

.menu-icon-wrap {
  width: 48rpx;
  height: 48rpx;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.menu-icon-emoji {
  font-size: 24rpx;
}

.menu-label {
  flex: 1;
  font-size: 29rpx;
  font-weight: 600;
  color: $text-primary;
}

.menu-arrow {
  font-size: 36rpx;
  color: $text-muted;
}

.menu-badge {
  background: #fef3c7;
  padding: 4rpx 16rpx;
  border-radius: $radius-full;

  .menu-badge-text {
    font-size: 22rpx;
    font-weight: 700;
    color: #92400e;
  }
}

/* ---- Footer ---- */
.footer {
  text-align: center;
  padding: 40rpx 0 24rpx;
}

.footer-text {
  font-size: 22rpx;
  color: $text-muted;
  line-height: 1.5;
}
</style>
