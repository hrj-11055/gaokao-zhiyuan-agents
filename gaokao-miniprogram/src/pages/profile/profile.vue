<template>
  <view class="profile-page">
    <view class="bg-glow-blue" />

    <!-- Header: Avatar + Student ID Card -->
    <view class="student-id-card glass-panel">
      <view class="card-top">
        <view class="avatar-wrap">
          <view class="avatar">
            <text class="avatar-text">峰</text>
          </view>
        </view>
        <view class="user-info">
          <text class="user-name">志愿同学</text>
          <view class="id-wrap">
            <text class="user-id">ID: {{ shortUserId }}</text>
          </view>
        </view>
        <view class="vip-badge" :class="{ active: membershipStore.isActive }">
          {{ membershipStore.isActive ? '尊享 VIP' : '未解锁' }}
        </view>
      </view>

      <view class="card-bottom">
        <view class="info-field" @click="goEditProfile">
          <text class="info-value">{{ profile.province || '--' }}</text>
          <text class="info-label">省份</text>
        </view>
        <view class="info-divider"></view>
        <view class="info-field" @click="goEditProfile">
          <text class="info-value">{{ profile.category || '--' }}</text>
          <text class="info-label">科目</text>
        </view>
        <view class="info-divider"></view>
        <view class="info-field" @click="goEditProfile">
          <text class="info-value highlight">{{ profile.score || '--' }}</text>
          <text class="info-label">分数</text>
        </view>
      </view>
    </view>

    <!-- VIP Status Card -->
    <view class="vip-status-card" :class="{ active: membershipStore.isActive }">
      <view class="vip-status-header">
        <text class="vip-status-title">志愿填报 VIP</text>
        <text class="vip-status-badge">{{ membershipStore.isActive ? '已开通' : '未开通' }}</text>
      </view>
      <text class="vip-status-desc">
        {{ membershipStore.isActive
           ? `剩余下载次数 ${membershipStore.downloadQuota.remaining}/${membershipStore.downloadQuota.limit}`
           : `量身定制推荐院校与志愿 · ${membershipStore.inviteProgressText}` }}
      </text>
      <view class="vip-status-actions">
        <button class="vip-action primary" @click="goReport">
          {{ membershipStore.isActive ? '查看报告' : '立即开通' }}
        </button>
        <button v-if="!membershipStore.isActive" class="vip-action outline" open-type="share">邀请好友</button>
      </view>
    </view>

    <!-- Common Features Grid -->
    <view class="menu-section">
      <text class="section-title">常用功能</text>
      <view class="grid-menu">
        <view class="grid-item" @click="goChat">
          <view class="grid-icon bg-blue"><text class="emoji">💬</text></view>
          <text class="grid-label">咨询记录</text>
        </view>
        <view class="grid-item" @click="goAssessments">
          <view class="grid-icon bg-orange">
             <text class="emoji">🧠</text>
             <view v-if="assessmentCount > 0" class="badge">{{ assessmentCount }}/3</view>
          </view>
          <text class="grid-label">我的测评</text>
        </view>
        <view class="grid-item" @click="onShare">
          <view class="grid-icon bg-green"><text class="emoji">👥</text></view>
          <text class="grid-label">邀请好友</text>
        </view>
        <view class="grid-item" @click="goEditProfile">
          <view class="grid-icon bg-purple"><text class="emoji">📝</text></view>
          <text class="grid-label">修改档案</text>
        </view>
      </view>
    </view>

    <!-- Settings Grid -->
    <view class="menu-section">
      <text class="section-title">设置</text>
      <view class="grid-menu cols-4">
        <view class="grid-item" @click="goFeedback">
          <view class="grid-icon basic"><text class="emoji">💌</text></view>
          <text class="grid-label">投诉建议</text>
        </view>
        <view class="grid-item" @click="goAbout">
          <view class="grid-icon basic"><text class="emoji">ⓘ</text></view>
          <text class="grid-label">关于我们</text>
        </view>
        <view class="grid-item" @click="goPrivacy">
          <view class="grid-icon basic"><text class="emoji">🔒</text></view>
          <text class="grid-label">隐私政策</text>
        </view>
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
import { CUSTOMER_WECHAT_ID } from '../../config.js'
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
  uni.switchTab({ url: '/pages/chat/chat' })
}

function goAssessments() {
  uni.switchTab({ url: '/pages/report/report' })
}

function goReport() {
  uni.switchTab({ url: '/pages/report/report' })
}

function goPrivacy() {
  uni.navigateTo({ url: '/pages/privacy/privacy' })
}

function goFeedback() {
  uni.showModal({
    title: '投诉建议',
    content: `请添加客服微信 ${CUSTOMER_WECHAT_ID}，发送付款截图、用户 ID 或问题截图，我们会继续跟进。`,
    confirmText: '复制微信号',
    cancelText: '关闭',
    success(res) {
      if (!res.confirm) return
      uni.setClipboardData({
        data: CUSTOMER_WECHAT_ID,
        success() {
          uni.showToast({ title: '微信号已复制', icon: 'none' })
        },
      })
    },
  })
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
  background: $bg-page;
  padding: 0 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.bg-glow-blue {
  position: absolute;
  top: -200rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 700rpx;
  height: 700rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.08) 0%, rgba(37, 99, 235, 0) 65%);
  pointer-events: none;
}

/* ---- Student ID Card ---- */
.glass-panel {
  @include glass-panel;
}

.student-id-card {
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 24rpx;
  position: relative;
  z-index: 2;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.99);
  }
}

.card-top {
  display: flex;
  align-items: center;
  margin-bottom: 32rpx;
  position: relative;
}

.avatar-wrap {
  margin-right: 24rpx;
}

.avatar {
  width: 100rpx;
  height: 100rpx;
  background: $grad-primary;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(37, 99, 235, 0.25);
}

.avatar-text {
  color: #fff;
  font-size: 40rpx;
  font-weight: 800;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.user-name {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.id-wrap {
  display: flex;
  align-items: center;
}

.user-id {
  font-size: 24rpx;
  color: $text-muted;
  background: rgba(15, 23, 42, 0.04);
  padding: 4rpx 12rpx;
  border-radius: $radius-sm;
}

.vip-badge {
  position: absolute;
  top: 0;
  right: 0;
  padding: 8rpx 20rpx;
  border-radius: $radius-full;
  background: #F1F5F9;
  color: $text-secondary;
  font-size: 22rpx;
  font-weight: 700;

  &.active {
    background: linear-gradient(90deg, #F59E0B, #F97316);
    color: #fff;
    box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.3);
  }
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #F1F5F9;
  border-radius: $radius-md;
  padding: 24rpx 32rpx;
}

.info-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.info-value {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 6rpx;

  &.highlight {
    color: $brand-primary;
  }
}

.info-label {
  font-size: 22rpx;
  color: $text-muted;
}

.info-divider {
  width: 1px;
  height: 48rpx;
  background: #E2E8F0;
}

/* ---- VIP Card ---- */
.vip-status-card {
  background: $grad-vip;
  border-radius: $radius-lg;
  padding: 32rpx;
  margin-bottom: 32rpx;
  position: relative;
  z-index: 2;
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.15);

  &.active {
    background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%);
  }
}

.vip-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.vip-status-title {
  font-size: 32rpx;
  font-weight: 900;
  color: #fff;
  letter-spacing: 1px;
}

.vip-status-badge {
  padding: 6rpx 16rpx;
  border-radius: $radius-full;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 22rpx;
  font-weight: 800;

  .vip-status-card.active & {
    background: #F59E0B;
    color: #fff;
  }
}

.vip-status-desc {
  display: block;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin-bottom: 24rpx;
}

.vip-status-actions {
  display: flex;
  gap: 16rpx;
}

.vip-action {
  flex: 1;
  height: 72rpx;
  border-radius: $radius-full;
  font-size: 26rpx;
  font-weight: 800;
  line-height: 72rpx;
  margin: 0;

  &::after { border: none; }

  &.primary {
    background: $grad-accent;
    color: #fff;
  }

  &.outline {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
  }
}

/* ---- Menu Sections ---- */
.menu-section {
  margin-bottom: 32rpx;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 20rpx;
  padding-left: 8rpx;
}

.grid-menu {
  background: #fff;
  border-radius: $radius-lg;
  padding: 24rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
  border: 1px solid $border-light;

  &.cols-4 {
    grid-template-columns: repeat(4, 1fr);
  }
}

.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
  border-radius: $radius-md;
  transition: background-color 0.15s;

  &:active {
    background: #F8FAFC;
  }
}

.grid-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 30%; // slightly rounded square
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
  position: relative;

  &.bg-blue { background: #DBEAFE; }
  &.bg-orange { background: #FFEDD5; }
  &.bg-green { background: #D1FAE5; }
  &.bg-purple { background: #F3E8FF; }
  &.basic { background: #F1F5F9; }
}

.emoji {
  font-size: 36rpx;
}

.badge {
  position: absolute;
  top: -8rpx;
  right: -12rpx;
  background: #EF4444;
  color: #fff;
  font-size: 20rpx;
  font-weight: 800;
  padding: 2rpx 10rpx;
  border-radius: $radius-full;
  border: 4rpx solid #fff;
}

.grid-label {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-primary;
}

/* ---- Footer ---- */
.footer {
  text-align: center;
  padding: 32rpx 0;
}

.footer-text {
  font-size: 22rpx;
  color: $text-muted;
  line-height: 1.5;
}
</style>
