<template>
  <view class="profile-page">
    <view class="bg-glow-blue" />

    <!-- Header: Avatar + Student ID Card -->
    <view class="student-id-card glass-panel">
      <view class="card-top">
        <view class="avatar-wrap">
          <view class="avatar">
            <image class="avatar-image" :src="profileIdentity.avatar" mode="aspectFill" />
          </view>
        </view>
        <view class="user-info">
          <text class="user-name">{{ profileIdentity.nickname }}</text>
          <view class="id-wrap">
            <text class="user-id">ID: {{ shortUserId }}</text>
          </view>
        </view>
        <view class="vip-badge" :class="{ active: reportAccessOpen }">
          {{ reportAccessOpen ? '报告开放' : '未开放' }}
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
          <text class="info-value highlight">{{ profileScoreDisplay }}</text>
          <text class="info-label">{{ profileScoreLabel }}</text>
        </view>
      </view>
    </view>

    <!-- Report Access Card -->
    <view class="vip-status-card active">
      <view class="vip-status-header">
        <text class="vip-status-title">志愿报告权益</text>
        <text class="vip-status-badge">{{ reportAccessOpen ? '已开放' : '未开放' }}</text>
      </view>
      <text class="vip-status-desc">
        {{ reportAccessDesc }}
      </text>
      <view class="vip-benefit-list">
        <text class="vip-benefit">完整志愿报告：学校/专业判断、风险提醒、下一步行动</text>
        <text class="vip-benefit">院校/专业深度阅读：1.3.0 免费开放在线阅读</text>
        <text class="vip-benefit">PDF 下载：当前版本开放下载，方便离线保存</text>
        <text class="vip-benefit">客服兜底：报告异常可联系 {{ CUSTOMER_WECHAT_ID }}</text>
      </view>
      <view class="vip-status-actions">
        <button class="vip-action primary" @click="goReport">查看报告</button>
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
             <view v-if="assessmentCount > 0" class="badge">{{ assessmentCount }}/2</view>
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

    <view v-if="showContactSheet" class="contact-sheet-mask" @click="closeContactSheet">
      <view class="contact-sheet" @click.stop>
        <view class="contact-sheet-head">
          <text class="contact-title">{{ contactSheetTitle }}</text>
          <text class="contact-close" @click="closeContactSheet">×</text>
        </view>
        <view v-if="contactSheetMode === 'about'" class="about-copy">
          <image
            class="about-logo"
            src="/static/yuanshuo-logo.png"
            mode="aspectFit"
          />
          <text class="about-paragraph">
            我们是深圳元说科技，一直在为高考志愿填报做准备。我们关注的不只是分数和院校，更希望每个家庭在关键选择前，都能获得真实、清晰、可理解的信息。
          </text>
          <text class="about-paragraph">
            很多家长和学生并不缺努力，缺的是足够透明的资料、可靠的判断，以及有人把复杂规则讲明白。我们希望用产品一点点抹平信息差，让志愿填报回到理性、坦诚和对孩子长期发展的尊重。
          </text>
          <text class="about-paragraph">
            我们设计 AI 咨询模块，也是在向张雪峰老师长期用真实话语普及升学信息的方式致敬。希望通过准确、直接、有用的回答，帮学生和家长多了解专业、学校、就业与风险，少走弯路，做出更踏实的选择。
          </text>
        </view>
        <view v-else>
          <text class="contact-desc">添加客服微信，发送用户 ID 或问题截图，我们会继续跟进。</text>
          <image
            class="contact-qr"
            :src="CUSTOMER_WECHAT_QR_IMAGE"
            mode="aspectFit"
            @click="previewCustomerWechatQr"
          />
          <text class="contact-tip">扫码上方二维码，或复制微信号添加好友。</text>
          <view class="contact-id-row">
            <text class="contact-id-label">微信号</text>
            <text class="contact-id">{{ CUSTOMER_WECHAT_ID }}</text>
          </view>
          <view class="contact-actions">
            <button class="contact-action primary" @click="copyCustomerWechatId">复制微信号</button>
            <button class="contact-action secondary" @click="previewCustomerWechatQr">查看二维码</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow, onShareAppMessage } from '@dcloudio/uni-app'
import { CUSTOMER_WECHAT_ID, CUSTOMER_WECHAT_QR_IMAGE, FREE_DEEP_REPORTS_ENABLED } from '../../config.js'
import { useMembershipStore } from '../../stores/membership.js'
import { getOrCreateProfileIdentity } from '../../utils/profile-identity.js'
import { getProfileReportMode, loadUserProfile, loadAssessments } from '../../utils/storage.js'

const membershipStore = useMembershipStore()
const profileIdentity = ref(getOrCreateProfileIdentity())
const profile = ref(loadUserProfile())
const assessments = ref(loadAssessments())
const showContactSheet = ref(false)
const contactSheetTitle = ref('添加客服微信')
const contactSheetMode = ref('contact')

const shortUserId = computed(() => (membershipStore.userId || 'CLOUD').slice(0, 8).toUpperCase())
const reportAccessOpen = computed(() => FREE_DEEP_REPORTS_ENABLED || membershipStore.isActive)
const reportAccessDesc = computed(() => (
  FREE_DEEP_REPORTS_ENABLED
    ? '1.3.0 免费开放 · 无需支付或兑换码，可直接生成报告'
    : membershipStore.isActive
      ? `权益已解锁 · 剩余下载次数 ${membershipStore.downloadQuota.remaining}/${membershipStore.downloadQuota.limit}`
      : '报告权益暂未开放'
))
const profileReportMode = computed(() => getProfileReportMode(profile.value))
const profileScoreDisplay = computed(() => {
  if (profileReportMode.value === 'planning') {
    return profile.value.score || profile.value.score_range || profile.value.grade || '提前规划'
  }
  if (profileReportMode.value === 'estimated') {
    return profile.value.score || profile.value.score_range || '--'
  }
  return profile.value.score || '--'
})
const profileScoreLabel = computed(() => {
  if (profileReportMode.value === 'planning') return '规划'
  if (profileReportMode.value === 'estimated') return '预估分'
  return '分数'
})

const assessmentCount = computed(() => {
  let n = 0
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
  openContactSheet('投诉建议')
}

function goAbout() {
  openContactSheet('关于我们', 'about')
}

function onShare() {
  uni.showToast({ title: '请用右上角 ··· 分享', icon: 'none' })
}

function openContactSheet(title = '添加客服微信', mode = 'contact') {
  contactSheetTitle.value = title
  contactSheetMode.value = mode
  showContactSheet.value = true
}

function closeContactSheet() {
  showContactSheet.value = false
}

function copyCustomerWechatId() {
  uni.setClipboardData({
    data: CUSTOMER_WECHAT_ID,
    success() {
      uni.showToast({ title: '微信号已复制', icon: 'none' })
    },
  })
}

function previewCustomerWechatQr() {
  uni.previewImage({
    urls: [CUSTOMER_WECHAT_QR_IMAGE],
    current: CUSTOMER_WECHAT_QR_IMAGE,
  })
}

onShow(() => {
  profileIdentity.value = getOrCreateProfileIdentity()
  profile.value = loadUserProfile()
  assessments.value = loadAssessments()
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
  background: #fff;
  border-radius: 50%;
  overflow: hidden;
  border: 4rpx solid #fff;
  box-shadow: 0 8rpx 20rpx rgba(249, 115, 22, 0.2);
}

.avatar-image {
  width: 100%;
  height: 100%;
  display: block;
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

/* ---- Report Access Card ---- */
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

.vip-benefit-list {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-bottom: 18rpx;
}

.vip-benefit {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  font-size: 22rpx;
  line-height: 1.45;
  background: rgba(255, 255, 255, 0.1);
  border-radius: $radius-sm;
  padding: 10rpx 14rpx;
}

.invite-rule {
  display: block;
  color: rgba(255, 255, 255, 0.76);
  font-size: 22rpx;
  line-height: 1.5;
  margin-bottom: 20rpx;
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

.contact-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.42);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.contact-sheet {
  width: 100%;
  background: #ffffff;
  border-top-left-radius: $radius-xl;
  border-top-right-radius: $radius-xl;
  padding: 32rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.contact-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.contact-title {
  color: $text-primary;
  font-size: 34rpx;
  font-weight: 900;
}

.contact-close {
  color: $text-muted;
  font-size: 44rpx;
  line-height: 1;
}

.contact-desc,
.contact-tip {
  display: block;
  color: $text-secondary;
  font-size: 26rpx;
  line-height: 1.5;
}

.about-copy {
  padding: 4rpx 0 8rpx;
}

.about-logo {
  width: 144rpx;
  height: 144rpx;
  display: block;
  margin: 4rpx auto 28rpx;
}

.about-paragraph {
  display: block;
  color: $text-secondary;
  font-size: 28rpx;
  line-height: 1.72;
  margin-bottom: 20rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.contact-qr {
  width: 420rpx;
  height: 420rpx;
  margin: 28rpx auto 18rpx;
  display: block;
  border-radius: $radius-md;
  background: #ffffff;
}

.contact-tip {
  text-align: center;
  color: $text-muted;
  margin-bottom: 24rpx;
}

.contact-id-row {
  min-height: 76rpx;
  border-radius: $radius-md;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
  margin-bottom: 24rpx;
}

.contact-id-label {
  color: $text-secondary;
  font-size: 26rpx;
}

.contact-id {
  color: $text-primary;
  font-size: 28rpx;
  font-weight: 900;
  letter-spacing: 1rpx;
}

.contact-actions {
  display: flex;
  gap: 20rpx;
}

.contact-action {
  flex: 1;
  height: 78rpx;
  line-height: 78rpx;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 800;
  margin: 0;

  &::after { border: none; }

  &.primary {
    background: $grad-accent;
    color: #ffffff;
  }

  &.secondary {
    background: #f1f5f9;
    color: $text-secondary;
  }
}
</style>
