<template>
  <view class="report-page">
    <!-- subtle background glow -->
    <view class="bg-glow-soft" />

    <view class="page-title">我的志愿报告</view>

    <!-- ============================================================ -->
    <!-- State A / B : Locked / Ready hero card (no active membership) -->
    <!-- ============================================================ -->
    <view v-if="!membershipStore.isActive && !generating" class="lock-hero" :class="{ ready: allAssessmentsDone }">
      <!-- golden glow accent -->
      <view class="hero-glow" />

      <!-- badge -->
      <view v-if="!allAssessmentsDone" class="hero-badge incomplete">
        <text class="hero-badge-text">还差 {{ 3 - completedAssessments }} 项测评</text>
      </view>
      <view v-else class="hero-badge done">
        <text class="hero-badge-text">&#10003; 资料已就绪</text>
      </view>

      <text class="hero-title">综合志愿参考报告</text>
      <text class="hero-sub">
        {{
          allAssessmentsDone
            ? '资料已就绪，解锁后可生成完整报告并下载深度研究资料'
            : '完成测评后，可生成综合报告并查看院校/专业深度资料'
        }}
      </text>
      <view class="vip-benefit-list">
        <text class="vip-benefit">综合志愿报告</text>
        <text class="vip-benefit">院校深度 PDF</text>
        <text class="vip-benefit">专业研究 PDF</text>
        <text class="vip-benefit">家长分享</text>
      </view>
      <text class="hero-price">VIP 报告权益 · {{ MEMBERSHIP_PRICE_LABEL }}</text>
    </view>

    <!-- ============================================================ -->
    <!-- B: Unlock options (assessments done but unpaid)              -->
    <!-- ============================================================ -->
    <view v-if="allAssessmentsDone && !membershipStore.isActive && !generating" class="unlock-options">
      <view class="unlock-card primary" @click="onPayWithWechat">
        <view class="unlock-card-icon">&#128179;</view>
        <text class="unlock-card-title">解锁完整志愿报告</text>
        <text class="unlock-card-price">{{ MEMBERSHIP_PRICE_LABEL }}</text>
        <text class="unlock-card-hint">报告生成 + 深度 PDF 下载</text>
      </view>
      <view class="unlock-card invite" @click="onInviteFriends">
        <view class="unlock-card-icon">&#128101;</view>
        <text class="unlock-card-title">邀请 5 位新用户</text>
        <view class="invite-dots">
          <view
            v-for="i in membershipStore.requiredInviteCount"
            :key="i"
            class="invite-dot"
            :class="{ filled: i <= membershipStore.effectiveInviteCount }"
          />
        </view>
        <text class="unlock-card-hint">{{ membershipStore.inviteProgressText }}</text>
      </view>
      <view class="unlock-card code" @click="openUnlockSheet('code')">
        <view class="unlock-card-icon">&#127915;</view>
        <text class="unlock-card-title">输入会员邀请码</text>
        <text class="unlock-card-hint">已有邀请码可直接开通</text>
      </view>
    </view>

    <view v-if="showTrialUnlock" class="trial-unlock-card" @click="unlockTrialAndGenerate">
      <text class="trial-unlock-title">体验版解锁并生成</text>
      <text class="trial-unlock-desc">仅开发版/体验版可用，用于真机检查报告样式与稳定性</text>
    </view>

    <!-- ============================================================ -->
    <!-- A: Invite bar (assessments NOT done)                         -->
    <!-- ============================================================ -->
    <view v-if="!allAssessmentsDone && !membershipStore.isActive && !generating" class="invite-bar">
      <view class="invite-progress-row">
        <view
          v-for="i in 3"
          :key="i"
          class="invite-step-dot"
          :class="{
            filled: i <= completedAssessments,
            active: i === completedAssessments + 1,
          }"
        />
      </view>
      <text class="invite-bar-label">完成 {{ completedAssessments }}/3 项测评即可生成报告</text>
      <button class="invite-bar-cta" open-type="share">分享给同学</button>
    </view>

    <!-- ============================================================ -->
    <!-- A/B: 8-module preview grid                                   -->
    <!-- ============================================================ -->
    <view v-if="!membershipStore.isActive && !generating" class="preview-section">
      <text class="section-label">报告里有什么</text>
      <view class="preview-grid">
        <view v-for="(mod, idx) in modules" :key="idx" class="preview-item">
          <text class="preview-icon">{{ moduleIcons[idx] }}</text>
          <text class="preview-name">{{ mod }}</text>
        </view>
      </view>
    </view>

    <!-- ============================================================ -->
    <!-- C: Active membership — ready but no report yet               -->
    <!-- ============================================================ -->
    <view v-if="membershipStore.isActive && !latestReport && !generating" class="ready-card">
      <view class="ready-glow" />
      <text class="ready-icon">&#128203;</text>
      <text class="ready-title">报告已就绪</text>
      <text class="ready-sub">所有资料准备完毕，点击立即生成您的专属志愿报告</text>
      <button class="ready-cta" @click="onGenerate">立即生成报告</button>
    </view>

    <!-- ============================================================ -->
    <!-- Generating spinner                                           -->
    <!-- ============================================================ -->
    <view v-if="generating" class="loading-card">
      <view class="spinner-ring">
        <view class="spinner-circle" />
      </view>
      <text class="loading-title">正在生成志愿报告</text>
      <text class="loading-sub">正在整合考生信息、测评结果与对话记录</text>
      <text class="loading-tip">通常需要 1-2 分钟，请保持页面打开</text>
      <view class="loading-bar">
        <view class="loading-fill" />
      </view>
    </view>

    <!-- ============================================================ -->
    <!-- C: Unlocked — latest report card                             -->
    <!-- ============================================================ -->
    <view v-if="membershipStore.isActive && latestReport && !generating" class="latest-card">
      <view class="latest-glow" />
      <text class="latest-label">最新报告</text>
      <text class="latest-title">综合志愿参考报告</text>
      <text class="latest-time" v-if="latestReport.generatedAt">{{ formatTime(latestReport.generatedAt) }}</text>
      <view class="latest-actions">
        <button class="latest-btn primary" @click="openLatest">在线查看</button>
        <button class="latest-btn secondary" @click="shareLatest">分享给家长</button>
      </view>
    </view>

    <view v-if="membershipStore.isActive && latestReport && !generating" class="deep-report-package">
      <view class="package-header">
        <text class="package-title">深度资料包</text>
        <text class="package-quota">剩余下载次数 {{ membershipStore.downloadQuota.remaining }}/{{ membershipStore.downloadQuota.limit }}</text>
      </view>
      <view class="package-grid">
        <view class="package-item" @click="goDeepReportDownload('university')">
          <text class="package-name">院校深度研究报告</text>
          <text class="package-desc">查看学校定位、转专业、就业与风险</text>
        </view>
        <view class="package-item" @click="goDeepReportDownload('major')">
          <text class="package-name">专业研究报告</text>
          <text class="package-desc">查看课程难度、就业方向和适配风险</text>
        </view>
      </view>
    </view>

    <!-- ============================================================ -->
    <!-- C: History list                                              -->
    <!-- ============================================================ -->
    <view v-if="membershipStore.isActive && history.length > 0 && !generating" class="history-section">
      <text class="section-label">历史报告</text>
      <view v-for="(item, idx) in history" :key="idx" class="history-card" @click="openHistory(item)">
        <text class="history-icon">&#128196;</text>
        <view class="history-info">
          <text class="history-title">综合志愿报告</text>
          <text class="history-time">{{ formatTime(item.generatedAt) }}</text>
        </view>
        <text class="history-arrow">&#8250;</text>
      </view>
      <view class="regenerate-card" @click="onRegenerate">
        <text class="regenerate-plus">+</text>
        <text class="regenerate-text">重新生成报告</text>
      </view>
    </view>

    <view v-if="showUnlockSheet" class="unlock-sheet-mask" @click="closeUnlockSheet">
      <view class="unlock-sheet" @click.stop>
        <text class="sheet-title">生成完整志愿报告需要 VIP</text>
        <text class="sheet-desc">开通后可生成综合报告，并下载院校深度研究报告、专业研究报告。</text>
        <button class="sheet-primary" @click="onPayWithWechat">{{ MEMBERSHIP_PRICE_LABEL }} 开通 VIP</button>
        <button class="sheet-secondary" open-type="share">邀请 5 位新用户解锁</button>
        <view class="code-row">
          <input v-model.trim="unlockCode" class="code-input" placeholder="输入会员邀请码" />
          <button class="code-btn" @click="redeemCodeFromSheet">兑换</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useMembershipStore } from '../../stores/membership.js'
import { useHomeProgress } from '../../composables/useHomeProgress.js'
import { MEMBERSHIP_PRICE_LABEL } from '../../config.js'
import { generateReport } from '../../api/report.js'
import {
  loadAssessments,
  loadHistory,
  loadQuestionnaire,
  loadUserProfile,
  loadReport,
  saveReport,
  QUESTIONNAIRE_REQUIRED_COUNT,
} from '../../utils/storage.js'

// ---------------------------------------------------------------------------
// Stores & composables
// ---------------------------------------------------------------------------

const membershipStore = useMembershipStore()
const {
  questionnaireDone,
  mbtiDone,
  hollandDone,
  step3Done: allAssessmentsDone,
  step3Count: completedAssessments,
  refresh: refreshProgress,
} = useHomeProgress()

// ---------------------------------------------------------------------------
// Module data
// ---------------------------------------------------------------------------

const modules = [
  '院校定位分析',
  '专业匹配建议',
  '分数策略',
  '风险提示',
  'MBTI 匹配解读',
  '霍兰德兴趣对应',
  '专业冷热分析',
  '志愿组合建议',
]

const moduleIcons = ['🏛️', '🎯', '📊', '⚠️', '🧠', '🔍', '🔥', '📋']

// ---------------------------------------------------------------------------
// Reactive state
// ---------------------------------------------------------------------------

const generating = ref(false)
const latestReport = ref(null)
const history = ref([])
const showUnlockSheet = ref(false)
const unlockCode = ref('')
const unlockSheetReason = ref('')
const showTrialUnlock = computed(() => (
  allAssessmentsDone.value &&
  !membershipStore.isActive &&
  membershipStore.canUseTrialUnlock &&
  !generating.value
))

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(async () => {
  await refreshPageState()
})

onShow(() => {
  refreshPageState()
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function loadExistingReports() {
  const data = loadReport()
  latestReport.value = null
  history.value = []
  if (data) {
    if (data.url) {
      latestReport.value = data
    }
    if (Array.isArray(data.history) && data.history.length > 0) {
      history.value = data.history
    }
  }
}

function persistReports() {
  const data = {
    ...(latestReport.value || {}),
    history: history.value,
  }
  saveReport(data)
}

async function refreshPageState() {
  refreshProgress()
  loadExistingReports()
  try {
    await membershipStore.loadStatus()
  } catch {
    // membership status fetch failed — stays inactive
  }
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function openUnlockSheet(reason = 'generate') {
  unlockSheetReason.value = reason
  showUnlockSheet.value = true
}

function closeUnlockSheet() {
  showUnlockSheet.value = false
  unlockCode.value = ''
}

async function redeemCodeFromSheet() {
  try {
    await membershipStore.redeemCode(unlockCode.value)
    await membershipStore.loadStatus()
    closeUnlockSheet()
    uni.showToast({ title: 'VIP 已开通', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message || '邀请码无效', icon: 'none' })
  }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function onGenerate() {
  if (!allAssessmentsDone.value) {
    uni.switchTab({ url: '/pages/assessments/assessments' })
    return
  }

  generating.value = true
  try {
    await membershipStore.ensureLogin()
    if (!membershipStore.isActive) {
      await membershipStore.loadStatus()
    }
    if (!membershipStore.isActive) {
      openUnlockSheet('generate')
      return
    }

    const profile = loadUserProfile()
    const questionnaire = loadQuestionnaire()
    const assessments = loadAssessments()
    const chatHistory = loadHistory()
    const questionnaireAnswers = questionnaire.answers || {}

    if (
      questionnaire.completedCount < QUESTIONNAIRE_REQUIRED_COUNT ||
      !assessments.mbti?.completed ||
      !assessments.holland?.completed
    ) {
      throw new Error('请先完成全部 3 项测评后再生成综合报告')
    }

    const result = await generateReport({
      profile,
      userId: membershipStore.userId,
      sessionToken: membershipStore.sessionToken,
      conversationId: chatHistory.conversationId || '',
      questionnaire: questionnaireAnswers,
      assessments,
    })
    const reportEntry = {
      url: result.url,
      generatedAt: result.generatedAt || Date.now(),
    }
    // push old latest into history
    if (latestReport.value?.url) {
      history.value.unshift({ ...latestReport.value })
    }
    latestReport.value = reportEntry
    persistReports()
  } catch (err) {
    const message = err.data?.draftId
      ? '生成失败，已保留草稿，可稍后重试'
      : (err.message || '生成失败')
    uni.showToast({ title: message, icon: 'none', duration: 2500 })
  } finally {
    generating.value = false
  }
}

async function unlockTrialAndGenerate() {
  generating.value = true
  try {
    await membershipStore.activateLimitedFree()
    await onGenerate()
  } catch (err) {
    uni.showToast({ title: err.message || '体验版解锁失败', icon: 'none', duration: 2500 })
  } finally {
    generating.value = false
  }
}

function onRegenerate() {
  uni.showModal({
    title: '重新生成',
    content: '确定要重新生成报告吗？当前报告将归入历史。',
    confirmText: '确定',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) onGenerate()
    },
  })
}

function openLatest() {
  if (!latestReport.value?.url) return
  uni.navigateTo({
    url: `/pages/report-view/report-view?url=${encodeURIComponent(latestReport.value.url)}`,
  })
}

function openHistory(item) {
  if (!item?.url) return
  uni.navigateTo({
    url: `/pages/report-view/report-view?url=${encodeURIComponent(item.url)}`,
  })
}

async function onPayWithWechat() {
  try {
    await membershipStore.openMembership()
    await membershipStore.loadStatus()
    closeUnlockSheet()
  } catch (err) {
    uni.showToast({ title: err.message || '支付暂时不可用', icon: 'none' })
  }
}

function shareLatest() {
  if (!latestReport.value?.url) return
  uni.setClipboardData({
    data: latestReport.value.url,
    success: () => uni.showToast({ title: '链接已复制', icon: 'success' }),
  })
}

function onInviteFriends() {
  uni.showToast({ title: '请用右上角 ··· 分享', icon: 'none', duration: 2000 })
}

function goDeepReportDownload(mode = 'university') {
  uni.navigateTo({
    url: `/pages/deep-report-download/deep-report-download?mode=${encodeURIComponent(mode)}`,
  })
}
</script>

<style lang="scss" scoped>
// ===========================================================================
// Page
// ===========================================================================

.report-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f3f4f6 0%, #ffffff 100%);
  padding: 0 32rpx 64rpx;
  box-sizing: border-box;
  position: relative;
}

.bg-glow-soft {
  position: fixed;
  top: -15%;
  left: -10%;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(49, 46, 129, 0.06) 0%, transparent 70%);
  z-index: 0;
  pointer-events: none;
}

.page-title {
  position: relative;
  z-index: 1;
  font-size: 40rpx;
  font-weight: 800;
  color: $text-primary;
  padding: 48rpx 0 12rpx;
}

// ===========================================================================
// Lock hero (State A / B)
// ===========================================================================

.lock-hero {
  position: relative;
  z-index: 1;
  background: linear-gradient(135deg, #1e1b4b, #312e81, #4338ca);
  border-radius: $radius-xl;
  padding: 52rpx 36rpx 44rpx;
  margin-top: 20rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;

  &.ready {
    background: linear-gradient(135deg, #312e81, #5b21b6);
  }
}

.hero-glow {
  position: absolute;
  top: -60rpx;
  right: -60rpx;
  width: 320rpx;
  height: 320rpx;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.18) 0%, transparent 70%);
  pointer-events: none;
}

.hero-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  margin-bottom: 28rpx;

  &.incomplete {
    background: rgba(255, 255, 255, 0.12);
  }

  &.done {
    background: rgba(34, 197, 94, 0.2);
  }
}

.hero-badge-text {
  font-size: 24rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
}

.hero-title {
  font-size: 38rpx;
  font-weight: 800;
  color: #fff;
  margin-bottom: 12rpx;
  text-align: center;
}

.hero-sub {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  line-height: 1.5;
  margin-bottom: 24rpx;
}

.hero-price {
  font-size: 34rpx;
  font-weight: 900;
  color: #fbbf24;
}

.vip-benefit-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.vip-benefit {
  padding: 8rpx 16rpx;
  border-radius: $radius-sm;
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.88);
  font-size: 22rpx;
  font-weight: 700;
}

// ===========================================================================
// Unlock options (State B)
// ===========================================================================

.unlock-options {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  margin-top: 24rpx;
}

.unlock-card {
  flex: 1 1 200rpx;
  min-width: 0;
  border-radius: $radius-lg;
  padding: 32rpx 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 2rpx solid transparent;
  transition: transform 0.15s;

  &:active {
    transform: scale(0.97);
  }

  &.primary {
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
    border-color: #fb923c;
  }

  &.invite {
    background: rgba(255, 255, 255, 0.96);
    border-color: $border-light;
    box-shadow: 0 8rpx 24rpx -12rpx rgba(15, 23, 42, 0.1);
  }

  &.code {
    flex-basis: 100%;
    background: #f8fafc;
    border-color: rgba(15, 23, 42, 0.08);
  }
}

.trial-unlock-card {
  position: relative;
  z-index: 1;
  background: #fff7ed;
  border: 1px solid rgba(249, 115, 22, 0.24);
  border-radius: $radius-lg;
  padding: 24rpx 28rpx;
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.trial-unlock-title {
  font-size: 28rpx;
  font-weight: 800;
  color: #9a3412;
}

.trial-unlock-desc {
  font-size: 23rpx;
  color: #9a3412;
  line-height: 1.45;
}

.unlock-card-icon {
  font-size: 48rpx;
  margin-bottom: 12rpx;
}

.unlock-card-title {
  font-size: 28rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 6rpx;
}

.unlock-card-price {
  font-size: 36rpx;
  font-weight: 900;
  color: #ea580c;
  margin-bottom: 4rpx;
}

.unlock-card-hint {
  font-size: 22rpx;
  color: $text-muted;
}

.invite-dots {
  display: flex;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.invite-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: #e2e8f0;
  transition: background 0.2s;

  &.filled {
    background: $brand-primary;
  }
}

// ===========================================================================
// Invite bar (State A only)
// ===========================================================================

.invite-bar {
  position: relative;
  z-index: 1;
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 32rpx 28rpx;
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.invite-progress-row {
  display: flex;
  gap: 20rpx;
  margin-bottom: 16rpx;
}

.invite-step-dot {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  background: #e2e8f0;
  transition: all 0.2s;

  &.filled {
    background: $brand-violet;
  }

  &.active {
    background: #a5b4fc;
    box-shadow: 0 0 0 6rpx rgba(37, 99, 235, 0.15);
  }
}

.invite-bar-label {
  font-size: 24rpx;
  color: $text-secondary;
  margin-bottom: 20rpx;
}

.invite-bar-cta {
  width: 100%;
  height: 80rpx;
  background: linear-gradient(135deg, $brand-violet, #4338ca);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;

  &::after {
    border: none;
  }
}

// ===========================================================================
// 8-module preview
// ===========================================================================

.preview-section {
  position: relative;
  z-index: 1;
  margin-top: 32rpx;
}

.section-label {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 20rpx;
}

.preview-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.preview-item {
  width: calc(25% - 12rpx);
  @include glass-panel;
  border-radius: $radius-md;
  padding: 20rpx 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.preview-icon {
  font-size: 36rpx;
}

.preview-name {
  font-size: 20rpx;
  font-weight: 600;
  color: $text-secondary;
  text-align: center;
  line-height: 1.3;
}

// ===========================================================================
// Ready card (C — no report yet)
// ===========================================================================

.ready-card {
  position: relative;
  z-index: 1;
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 52rpx 36rpx;
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

.ready-glow {
  position: absolute;
  bottom: -60rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 300rpx;
  height: 200rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.ready-icon {
  font-size: 64rpx;
  margin-bottom: 20rpx;
}

.ready-title {
  font-size: 36rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 10rpx;
}

.ready-sub {
  font-size: 26rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.5;
  margin-bottom: 32rpx;
}

.ready-cta {
  width: 100%;
  height: 90rpx;
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  font-size: 30rpx;
  font-weight: 800;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.24);

  &::after {
    border: none;
  }

  &:active {
    transform: scale(0.98);
  }
}

// ===========================================================================
// Generating (loading)
// ===========================================================================

.loading-card {
  position: relative;
  z-index: 1;
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 64rpx 36rpx 48rpx;
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.spinner-ring {
  width: 100rpx;
  height: 100rpx;
  position: relative;
  margin-bottom: 32rpx;
}

.spinner-circle {
  width: 100%;
  height: 100%;
  border: 6rpx solid #e2e8f0;
  border-top-color: $brand-violet;
  border-right-color: $brand-primary-light;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-title {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.loading-sub {
  font-size: 26rpx;
  color: $text-secondary;
  text-align: center;
  margin-bottom: 8rpx;
}

.loading-tip {
  font-size: 22rpx;
  color: $text-muted;
  text-align: center;
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 8rpx;
  background: #f1f5f9;
  border-radius: $radius-full;
  overflow: hidden;
}

.loading-fill {
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, $brand-violet, $brand-primary-light);
  border-radius: $radius-full;
  animation: loading-slide 2s ease-in-out infinite;
}

@keyframes loading-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(280%); }
}

// ===========================================================================
// Latest report card (C — unlocked)
// ===========================================================================

.latest-card {
  position: relative;
  z-index: 1;
  background: linear-gradient(135deg, #f97316, #ea580c);
  border-radius: $radius-xl;
  padding: 44rpx 36rpx;
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.latest-glow {
  position: absolute;
  top: -40rpx;
  right: -40rpx;
  width: 240rpx;
  height: 240rpx;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.latest-label {
  font-size: 22rpx;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8rpx;
}

.latest-title {
  font-size: 34rpx;
  font-weight: 800;
  color: #fff;
  margin-bottom: 4rpx;
}

.latest-time {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 28rpx;
}

.latest-actions {
  display: flex;
  gap: 16rpx;
}

.latest-btn {
  flex: 1;
  height: 76rpx;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;

  &::after {
    border: none;
  }

  &.primary {
    background: #fff;
    color: #ea580c;
  }

  &.secondary {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
  }

  &:active {
    opacity: 0.85;
  }
}

// ===========================================================================
// Deep report package
// ===========================================================================

.deep-report-package {
  position: relative;
  z-index: 1;
  margin-top: 24rpx;
  padding: 28rpx;
  border-radius: $radius-lg;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.05);
}

.package-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.package-title {
  font-size: 30rpx;
  font-weight: 800;
  color: $text-primary;
}

.package-quota {
  font-size: 22rpx;
  font-weight: 700;
  color: #0f766e;
  background: rgba(20, 184, 166, 0.1);
  border-radius: $radius-sm;
  padding: 6rpx 12rpx;
}

.package-grid {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.package-item {
  padding: 24rpx;
  border-radius: $radius-md;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  gap: 8rpx;

  &:active {
    background: #f1f5f9;
  }
}

.package-name {
  font-size: 28rpx;
  font-weight: 800;
  color: $text-primary;
}

.package-desc {
  font-size: 23rpx;
  color: $text-secondary;
  line-height: 1.45;
}

// ===========================================================================
// History section
// ===========================================================================

.history-section {
  position: relative;
  z-index: 1;
  margin-top: 40rpx;
}

.history-card {
  @include glass-panel;
  border-radius: $radius-lg;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  display: flex;
  align-items: center;
  transition: transform 0.12s;

  &:active {
    transform: scale(0.98);
  }
}

.history-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.history-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.history-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.history-time {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 4rpx;
}

.history-arrow {
  font-size: 36rpx;
  color: $text-muted;
}

.regenerate-card {
  margin-top: 16rpx;
  border: 2rpx dashed #fb923c;
  border-radius: $radius-lg;
  padding: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  transition: background 0.15s;

  &:active {
    background: rgba(249, 115, 22, 0.06);
  }
}

.regenerate-plus {
  font-size: 36rpx;
  font-weight: 700;
  color: $brand-primary;
}

.regenerate-text {
  font-size: 28rpx;
  font-weight: 700;
  color: $brand-primary;
}

// ===========================================================================
// Unlock sheet
// ===========================================================================

.unlock-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: rgba(15, 23, 42, 0.48);
  display: flex;
  align-items: flex-end;
  padding: 28rpx;
  box-sizing: border-box;
}

.unlock-sheet {
  width: 100%;
  border-radius: $radius-lg;
  background: #fff;
  padding: 34rpx 28rpx calc(34rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.sheet-title {
  font-size: 34rpx;
  font-weight: 900;
  color: $text-primary;
}

.sheet-desc {
  font-size: 25rpx;
  color: $text-secondary;
  line-height: 1.5;
}

.sheet-primary,
.sheet-secondary,
.code-btn {
  border: none;
  border-radius: $radius-md;
  height: 84rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;

  &::after {
    border: none;
  }
}

.sheet-primary {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
}

.sheet-secondary {
  background: #f8fafc;
  color: $text-primary;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.code-row {
  display: flex;
  gap: 12rpx;
}

.code-input {
  flex: 1;
  min-width: 0;
  height: 84rpx;
  border-radius: $radius-md;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 0 20rpx;
  box-sizing: border-box;
  font-size: 26rpx;
  color: $text-primary;
}

.code-btn {
  width: 132rpx;
  background: #111827;
  color: #fff;
}
</style>
