<template>
  <view class="report-page">
    <view class="bg-glow-soft" />

    <view class="page-title">{{ latestReport ? '我的志愿报告' : '测评与报告准备' }}</view>

    <!-- 进度统计仪表板 -->
    <view class="progress-section" v-if="!generating && !latestReport">
      <view class="progress-header">
        <text class="progress-title">报告准备度</text>
        <text class="progress-count">{{ progressPercent }}%</text>
      </view>
      <view class="progress-bar-container">
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }">
            <view class="progress-fill-glow" />
          </view>
        </view>
        <text class="progress-count-text">{{ completedAssessments }} / 3 项测评已完成</text>
      </view>
    </view>

    <!-- 测评卡片列表 -->
    <view class="assessments-list" v-if="!generating && !latestReport">
      <!-- 五环问卷 -->
      <view class="assessment-card" :class="{ completed: questionnaireDone }" @click="goQuestionnaire">
        <view class="card-icon" :class="{ completed: questionnaireDone }">
          <text class="icon-text">{{ questionnaireDone ? '✓' : '1' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">五环特征综合评测</text>
            <view class="status-badge" :class="{ completed: questionnaireDone }">
              <text class="status-text">{{ questionnaireDone ? '匹配成功' : '去评测' }}</text>
            </view>
          </view>
          <text class="card-desc">21 维全面学习风格，记录学习方式、目标偏好</text>
        </view>
        <text class="card-arrow">›</text>
      </view>

      <!-- 性格测试 -->
      <view class="assessment-card" :class="{ completed: mbtiDone }" @click="goMbti">
        <view class="card-icon" :class="{ completed: mbtiDone }">
          <text class="icon-text">{{ mbtiDone ? '✓' : '2' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">性格类型定位</text>
            <view class="status-badge" :class="{ completed: mbtiDone }">
              <text class="status-text">{{ mbtiDone ? '已完成' : '去评测' }}</text>
            </view>
          </view>
          <text class="card-desc">了解沟通、信息处理、判断方式和生活节奏偏好</text>
        </view>
        <text class="card-arrow">›</text>
      </view>

      <!-- 霍兰德职业兴趣 -->
      <view class="assessment-card" :class="{ completed: hollandDone }" @click="goHolland">
        <view class="card-icon" :class="{ completed: hollandDone }">
          <text class="icon-text">{{ hollandDone ? '✓' : '3' }}</text>
        </view>
        <view class="card-content">
          <view class="card-header-row">
            <text class="card-title">霍兰德 RIASEC 职业矩阵</text>
            <view class="status-badge" :class="{ completed: hollandDone }">
              <text class="status-text">{{ hollandDone ? '已完成' : '去评测' }}</text>
            </view>
          </view>
          <text class="card-desc">从六类职业兴趣中判断更适合的专业方向</text>
        </view>
        <text class="card-arrow">›</text>
      </view>
    </view>

    <!-- 生成按钮区域 -->
    <view v-if="!generating && !latestReport" class="generate-section">
      <button
        class="generate-btn"
        :class="{ ready: allAssessmentsDone }"
        @click="onGenerateClick"
      >
        <text class="generate-btn-text">
          {{ allAssessmentsDone ? '立即生成综合报告' : '需先完成上方 3 项测评' }}
        </text>
      </button>
      <text v-if="!allAssessmentsDone" class="generate-hint">测评结果会用于补充“分数之外的信息”，帮助报告更准确。</text>
      <text v-else-if="!membershipStore.isActive" class="generate-hint">生成完整报告需要使用 VIP 权限</text>
    </view>

    <!-- 生成中加载 -->
    <view v-if="generating" class="loading-card">
      <view class="spinner-ring">
        <view class="spinner-circle" />
      </view>
      <text class="loading-title">{{ progressTitle }}</text>
      <text class="loading-sub">{{ progressSub }}</text>
      <text class="loading-tip">{{ progressTip }}</text>
      <view class="loading-bar">
        <view v-if="isFakeProgressActive" class="fake-progress-fill" :style="{ width: fakeProgress + '%' }" />
        <view v-else class="loading-fill" />
      </view>
      <text class="loading-percent" v-if="isFakeProgressActive">{{ fakeProgress }}%</text>
    </view>

    <!-- 生成完毕：综合报告大入口 -->
    <view v-if="!generating && latestReport" class="latest-card large-hero">
      <view class="latest-glow" />
      <text class="latest-label">你的专属方案</text>
      <text class="latest-title">综合志愿参考报告</text>
      <text class="latest-time" v-if="latestReport.generatedAt">{{ formatTime(latestReport.generatedAt) }}</text>

      <button class="latest-btn primary giant" @click="openLatest">点击查看综合报告</button>

      <view class="latest-actions">
        <button class="latest-btn secondary" @click="shareLatest">分享给家长</button>
        <button class="latest-btn secondary outline" @click="onRegenerate">重新生成</button>
      </view>
    </view>

    <!-- VIP 深度包 (生成后显示) -->
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

    <!-- 解锁弹窗 -->
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
import { onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { useMembershipStore } from '../../stores/membership.js'
import { useHomeProgress } from '../../composables/useHomeProgress.js'
import { MEMBERSHIP_PRICE_LABEL } from '../../config.js'
import { generateReport } from '../../api/report.js'
import { checkPregenerateStatus } from '../../api/pregenerate.js'
import { useReportPregen } from '../../composables/useReportPregen.js'
import {
  loadAssessments,
  loadHistory,
  loadQuestionnaire,
  loadUserProfile,
  loadReport,
  saveReport,
  QUESTIONNAIRE_REQUIRED_COUNT,
} from '../../utils/storage.js'

const membershipStore = useMembershipStore()
const {
  questionnaireDone,
  mbtiDone,
  hollandDone,
  step3Done: allAssessmentsDone,
  step3Count: completedAssessments,
  refresh: refreshProgress,
} = useHomeProgress()

const progressPercent = computed(() => {
  return Math.round((completedAssessments.value / 3) * 100)
})

const generating = ref(false)
const latestReport = ref(null)
const history = ref([])
const showUnlockSheet = ref(false)
const unlockCode = ref('')
const unlockSheetReason = ref('')

const { tryTriggerPregenerate } = useReportPregen()

const fakeProgress = ref(0)
const progressTitle = ref('正在生成志愿报告')
const progressSub = ref('正在整合考生信息、测评结果与对话记录')
const progressTip = ref('通常需要 1-2 分钟，请保持页面打开')
const isFakeProgressActive = ref(false)

onMounted(async () => {
  await refreshPageState()
})

onShow(() => {
  refreshPageState()
  tryTriggerPregenerate()
})

onShareAppMessage(() => ({
  title: '邀请你一起生成高考志愿参考报告',
  path: `/pages/index/index?inviterId=${membershipStore.userId || ''}`,
}))

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
    // membership status fetch failed
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

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (mbtiDone.value) {
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (hollandDone.value) {
    uni.navigateTo({ url: '/pages/holland/holland-result' })
  } else {
    uni.navigateTo({ url: '/pages/holland/holland' })
  }
}

async function onGenerateClick() {
  if (!allAssessmentsDone.value) {
    uni.showToast({ title: '请先完成上方 3 项测评', icon: 'none' })
    return
  }
  onGenerate()
}

function runFakeProgressBar(cachedUrl) {
  isFakeProgressActive.value = true
  generating.value = true
  fakeProgress.value = 0
  progressTitle.value = '正在整合分析结果…'
  progressSub.value = '正在整合性格特质与RIASEC职业兴趣...'
  progressTip.value = '即将为您呈现深度个人发展建议'

  // Step 1: 1s -> 30%
  setTimeout(() => {
    fakeProgress.value = 30
    progressTitle.value = '整合考生数据…'
    progressSub.value = '计算学业现状五环数据与学科偏好...'
  }, 1000)

  // Step 2: 2.5s -> 60%
  setTimeout(() => {
    fakeProgress.value = 60
    progressTitle.value = 'AI 深度分析中…'
    progressSub.value = '正在提炼核心避坑指南与行动方案...'
  }, 2500)

  // Step 3: 4s -> 90%
  setTimeout(() => {
    fakeProgress.value = 90
    progressTitle.value = '生成报告排版…'
    progressSub.value = '美化专属图表并构建可视化方案...'
  }, 4000)

  // Step 4: 5s -> 100%
  setTimeout(() => {
    fakeProgress.value = 100
    progressTitle.value = '报告生成完毕！'
    progressSub.value = '欢迎进入属于你的志愿报告'
  }, 5000)

  // Step 5: 5.5s -> navigate and reset
  setTimeout(() => {
    const reportEntry = {
      url: cachedUrl,
      generatedAt: Date.now(),
    }
    if (latestReport.value?.url) {
      history.value.unshift({ ...latestReport.value })
    }
    latestReport.value = reportEntry
    persistReports()

    generating.value = false
    isFakeProgressActive.value = false

    // open the report view page!
    openLatest()
  }, 5500)
}

async function onGenerate() {
  generating.value = true

  // Reset loader variables
  isFakeProgressActive.value = false
  fakeProgress.value = 0
  progressTitle.value = '正在生成志愿报告'
  progressSub.value = '正在整合考生信息、测评结果与对话记录'
  progressTip.value = '通常需要 1-2 分钟，请保持页面打开'

  try {
    await membershipStore.ensureLogin()
    if (!membershipStore.isActive) {
      await membershipStore.loadStatus()
    }
    if (!membershipStore.isActive) {
      openUnlockSheet('generate')
      generating.value = false
      return
    }

    // Check pre-generation status
    try {
      const pregenStatus = await checkPregenerateStatus({
        sessionToken: membershipStore.sessionToken,
      })
      if (pregenStatus && pregenStatus.status === 'ready' && pregenStatus.url) {
        console.log('[Pregen] Cache hit! Running fake progress bar UX.')
        runFakeProgressBar(pregenStatus.url)
        return
      }
      console.log('[Pregen] Pre-generation status:', pregenStatus?.status || 'unknown')
    } catch (pregenErr) {
      console.warn('[Pregen] Failed to check pre-generate status:', pregenErr)
    }

    // Fallback to normal generation
    const profile = loadUserProfile()
    const questionnaire = loadQuestionnaire()
    const assessments = loadAssessments()
    const chatHistory = loadHistory()
    const questionnaireAnswers = questionnaire.answers || {}

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
    if (!isFakeProgressActive.value) {
      generating.value = false
    }
  }
}

function onRegenerate() {
  uni.showModal({
    title: '重新生成',
    content: '确定要重新生成报告吗？当前报告将归入历史。',
    confirmText: '确定',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        latestReport.value = null // clear current to show generate UI
        onGenerateClick()
      }
    },
  })
}

function openLatest() {
  if (!latestReport.value?.url) return
  uni.navigateTo({
    url: `/pages/report-view/report-view?url=${encodeURIComponent(latestReport.value.url)}`,
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

function goDeepReportDownload(mode = 'university') {
  uni.navigateTo({
    url: `/pages/deep-report-download/deep-report-download?mode=${encodeURIComponent(mode)}`,
  })
}
</script>

<style lang="scss" scoped>
.report-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  padding: 0 32rpx 64rpx;
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.bg-glow-soft {
  position: fixed;
  top: -15%;
  left: -10%;
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.08) 0%, transparent 70%);
  z-index: 0;
  pointer-events: none;
}

.page-title {
  position: relative;
  z-index: 1;
  font-size: 40rpx;
  font-weight: 800;
  color: $text-primary;
  padding: 48rpx 0 24rpx;
}

/* ================== 进度统计 ================== */
.progress-section {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(15, 23, 42, 0.05);
  border-radius: $radius-xl;
  padding: 36rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(15, 23, 42, 0.02);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.progress-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.progress-count {
  font-size: 32rpx;
  font-weight: 800;
  color: $brand-primary;
}

.progress-bar-container {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.progress-bar {
  height: 16rpx;
  background: #f1f5f9;
  border-radius: $radius-full;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: $grad-primary;
  border-radius: $radius-full;
  transition: width 0.4s cubic-bezier(0.1, 0.76, 0.55, 0.94);
  position: relative;
}

.progress-fill-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 20rpx;
  height: 100%;
  background: #fff;
  filter: blur(4rpx);
  opacity: 0.5;
}

.progress-count-text {
  font-size: 22rpx;
  color: $text-secondary;
}

/* ================== 测评卡片 ================== */
.assessments-list {
  position: relative;
  z-index: 1;
  margin-bottom: 40rpx;
}

.assessment-card {
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: $radius-xl;
  padding: 32rpx 28rpx;
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.02);
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }

  &.completed {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.04) 0%, #fff 100%);
    border-color: rgba(16, 185, 129, 0.2);
  }
}

.card-icon {
  width: 72rpx;
  height: 72rpx;
  background: #f1f5f9;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;

  &.completed {
    background: $grad-success;
  }
}

.icon-text {
  font-size: 30rpx;
  font-weight: 800;
  color: $text-secondary;

  .completed & {
    color: #fff;
  }
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.card-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.status-badge {
  padding: 4rpx 16rpx;
  background: #f1f5f9;
  border-radius: $radius-full;

  &.completed {
    background: rgba(16, 185, 129, 0.1);
  }
}

.status-text {
  font-size: 22rpx;
  color: $text-secondary;
  font-weight: 600;

  .completed & {
    color: #10b981;
  }
}

.card-desc {
  font-size: 22rpx;
  color: $text-secondary;
  line-height: 1.4;
}

.card-arrow {
  font-size: 40rpx;
  color: #cbd5e1;
  margin-left: 16rpx;
}

/* ================== 生成按钮区域 ================== */
.generate-section {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20rpx;
}

.generate-btn {
  width: 100%;
  height: 96rpx;
  border-radius: $radius-full;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;

  &::after { border: none; }

  &.ready {
    background: $grad-primary;
    box-shadow: 0 8rpx 24rpx rgba(37, 99, 235, 0.3);
  }
}

.generate-btn-text {
  font-size: 32rpx;
  font-weight: 800;
  color: #94a3b8;

  .ready & {
    color: #fff;
  }
}

.generate-hint {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 20rpx;
  text-align: center;
}

/* ================== 加载中 ================== */
.loading-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  border-radius: $radius-xl;
  padding: 60rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 12rpx 48rpx rgba(15, 23, 42, 0.05);
  margin-top: 40rpx;
}

.spinner-ring {
  width: 100rpx;
  height: 100rpx;
  border: 8rpx solid #e0e7ff;
  border-top-color: $brand-primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 32rpx;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-title {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.loading-sub {
  font-size: 24rpx;
  color: $text-secondary;
  margin-bottom: 8rpx;
}

.loading-tip {
  font-size: 22rpx;
  color: $text-muted;
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 8rpx;
  background: #f1f5f9;
  border-radius: 4rpx;
  overflow: hidden;
}

.loading-fill {
  width: 30%;
  height: 100%;
  background: $grad-primary;
  border-radius: 4rpx;
  animation: loading-bar-anim 2s ease-in-out infinite alternate;
}

.fake-progress-fill {
  height: 100%;
  background: $grad-primary;
  border-radius: 4rpx;
  transition: width 0.3s ease-out;
}

.loading-percent {
  font-size: 28rpx;
  color: #2563eb;
  font-weight: bold;
  margin-top: 16rpx;
  display: block;
  text-align: center;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

@keyframes loading-bar-anim {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(330%); }
}

/* ================== 综合报告大入口 ================== */
.latest-card {
  position: relative;
  z-index: 1;
  background: linear-gradient(135deg, #1e3a8a, #1d4ed8);
  border-radius: $radius-xl;
  padding: 48rpx 36rpx;
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 12rpx 32rpx rgba(37, 99, 235, 0.25);
  overflow: hidden;
}

.latest-glow {
  position: absolute;
  top: -100rpx;
  right: -100rpx;
  width: 300rpx;
  height: 300rpx;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
}

.latest-label {
  font-size: 24rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 8rpx;
}

.latest-title {
  font-size: 44rpx;
  font-weight: 900;
  color: #fff;
  margin-bottom: 12rpx;
}

.latest-time {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40rpx;
}

.giant {
  width: 100%;
  height: 96rpx;
  border-radius: $radius-full;
  font-size: 32rpx;
  font-weight: 800;
  background: #fff;
  color: $brand-primary;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.latest-actions {
  display: flex;
  gap: 20rpx;
  width: 100%;
}

.latest-btn {
  &.secondary {
    flex: 1;
    height: 72rpx;
    border-radius: $radius-full;
    font-size: 26rpx;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.15);
    color: #fff;

    &.outline {
      background: transparent;
      border: 1px solid rgba(255, 255, 255, 0.3);
    }
  }
}

/* ================== 深度包 ================== */
.deep-report-package {
  position: relative;
  z-index: 1;
  background: #fff;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-top: 32rpx;
  box-shadow: 0 4rpx 20rpx rgba(15, 23, 42, 0.03);
  border: 1px solid rgba(15, 23, 42, 0.04);
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.package-title {
  font-size: 30rpx;
  font-weight: 800;
  color: $text-primary;
}

.package-quota {
  font-size: 24rpx;
  font-weight: 600;
  color: $brand-primary;
  background: rgba(37, 99, 235, 0.1);
  padding: 6rpx 16rpx;
  border-radius: $radius-full;
}

.package-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.package-item {
  background: #f8fafc;
  border-radius: $radius-lg;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  transition: transform 0.15s;

  &:active {
    transform: scale(0.97);
  }
}

.package-name {
  font-size: 26rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.package-desc {
  font-size: 20rpx;
  color: $text-secondary;
  line-height: 1.4;
}

/* ================== 解锁弹窗 ================== */
.unlock-sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}

.unlock-sheet {
  width: 100%;
  background: #fff;
  border-radius: 40rpx 40rpx 0 0;
  padding: 48rpx 40rpx calc(48rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
}

.sheet-title {
  font-size: 36rpx;
  font-weight: 900;
  color: $text-primary;
  margin-bottom: 16rpx;
}

.sheet-desc {
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.5;
  margin-bottom: 40rpx;
}

.sheet-primary {
  height: 90rpx;
  border-radius: $radius-full;
  background: $grad-primary;
  color: #fff;
  font-size: 30rpx;
  font-weight: 800;
  margin-bottom: 24rpx;
}

.sheet-secondary {
  height: 90rpx;
  border-radius: $radius-full;
  background: #f1f5f9;
  color: $text-primary;
  font-size: 30rpx;
  font-weight: 700;
  margin-bottom: 40rpx;
  border: none;
  &::after { border: none; }
}

.code-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.code-input {
  flex: 1;
  height: 80rpx;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: $radius-full;
  padding: 0 32rpx;
  font-size: 28rpx;
}

.code-btn {
  width: 140rpx;
  height: 80rpx;
  background: #e2e8f0;
  color: $text-primary;
  font-size: 28rpx;
  font-weight: 700;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  &::after { border: none; }
}
</style>
