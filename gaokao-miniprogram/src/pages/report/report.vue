<template>
  <view class="report-page">
    <view class="bg-glow-blue" />
    <view v-if="!latestReport" class="header-banner">
      <text class="page-title">{{ pageTitle }}</text>
    </view>

    <view class="main-content">
      <!-- 进度统计仪表板 -->
      <view class="progress-section" v-if="!generating && !latestReport">
        <view class="progress-header">
          <text class="progress-title">报告准备度</text>
          <text class="progress-count">{{ progressPercent }}%</text>
        </view>
        <view class="progress-bar-container">
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
          </view>
          <text class="progress-count-text">{{ completedSteps }} / 4 步已完成</text>
        </view>
      </view>

      <view class="requirements-section" v-if="!generating && !latestReport">
        <text class="section-title">生成前准备</text>
        <view class="requirement-item" :class="{ done: step1Done }" @click="goHomeProfile">
          <text class="requirement-mark">{{ step1Done ? '✓' : '1' }}</text>
          <view class="requirement-body">
            <text class="requirement-title">基础资料</text>
            <text class="requirement-desc">{{ profileStatusText }}</text>
          </view>
        </view>
        <view class="requirement-item" :class="{ done: step2Done }" @click="goChat">
          <text class="requirement-mark">{{ step2Done ? '✓' : '2' }}</text>
          <view class="requirement-body">
            <text class="requirement-title">AI 咨询</text>
            <text class="requirement-desc">{{ chatStatusText }}</text>
          </view>
        </view>
        <view class="requirement-item" :class="{ done: allAssessmentsDone }">
          <text class="requirement-mark">{{ allAssessmentsDone ? '✓' : '3' }}</text>
          <view class="requirement-body">
            <text class="requirement-title">两项测评</text>
            <text class="requirement-desc">{{ assessmentStatusText }}</text>
          </view>
        </view>
      </view>

      <!-- 测评卡片列表 -->
      <view class="assessments-list" v-if="!generating && !latestReport">
        <text class="section-title">基础测评列表</text>

        <view class="assessment-card" :class="{ completed: mbtiDone }" @click="goMbti" hover-class="card-hover">
          <view class="card-icon-wrap personality-logo" :class="{ completed: mbtiDone }">
            <view class="logo-pip personality-pip" />
            <LucideIcon name="BrainCircuit" size="36rpx" :color="mbtiDone ? '#0052d9' : '#2563eb'" />
          </view>
          <view class="card-content">
            <text class="card-title">性格类型定位</text>
            <text class="card-desc">沟通、判断方式偏好</text>
          </view>
          <view class="status-badge" :class="{ completed: mbtiDone }">
            {{ mbtiDone ? '已完成' : '去评测' }}
          </view>
        </view>

        <view class="assessment-card" :class="{ completed: hollandDone }" @click="goHolland" hover-class="card-hover">
          <view class="card-icon-wrap career-logo" :class="{ completed: hollandDone }">
            <view class="logo-pip career-pip" />
            <LucideIcon name="Target" size="36rpx" :color="hollandDone ? '#0052d9' : '#0891b2'" />
          </view>
          <view class="card-content">
            <text class="card-title">职业兴趣矩阵</text>
            <text class="card-desc">判断更适合的专业方向</text>
          </view>
          <view class="status-badge" :class="{ completed: hollandDone }">
            {{ hollandDone ? '已完成' : '去评测' }}
          </view>
        </view>
      </view>

      <!-- 生成按钮区域 -->
      <view v-if="!generating && !latestReport" class="generate-section">
        <button
          class="generate-btn"
          :class="{ ready: allPrerequisitesDone }"
          @click="onGenerateClick"
        >
          <text class="generate-btn-text">
            {{ generateButtonText }}
          </text>
        </button>
        <text v-if="generateHintText" class="generate-hint">{{ generateHintText }}</text>
      </view>

      <!-- 生成中加载 -->
      <view v-if="generating" class="loading-card">
        <view class="spinner-ring" />
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
      <template v-if="!generating && latestReport">
        <view class="hero-card">
          <view class="hero-deco-wrap">
            <view class="hero-deco-1"></view>
            <view class="hero-deco-2"></view>
          </view>

          <view class="hero-content">
            <text class="hero-title">{{ reportModeLabel }}</text>
            <text class="hero-time" v-if="latestReport.generatedAt">{{ formatTime(latestReport.generatedAt) }}</text>
            <button class="hero-btn" @click="openLatest" hover-class="hero-btn-hover">点击查看{{ reportModeLabel }}</button>
          </view>
        </view>

        <view class="sub-actions">
          <button class="sub-btn" @click="shareLatest" hover-class="sub-btn-hover">分享给家长</button>
          <button class="sub-btn" @click="onRegenerate" hover-class="sub-btn-hover">重新生成</button>
        </view>

        <!-- 基础测评回顾 -->
        <view class="section-container">
          <text class="section-header">基础测评结果</text>
          <view class="grid-2">
            <view class="grid-card" @click="goMbti" hover-class="grid-card-hover">
              <view class="grid-card-head">
                <view class="icon-box assessment-logo personality-logo">
                  <view class="logo-pip personality-pip" />
                  <LucideIcon name="BrainCircuit" size="30rpx" color="#2563eb" />
                </view>
                <text class="grid-card-title">性格测试</text>
              </view>
              <text class="grid-card-desc line-clamp-2">{{ mbtiDone ? '查看详细的性格特征解析' : '尚未评测，点击前往' }}</text>
            </view>

            <view class="grid-card" @click="goHolland" hover-class="grid-card-hover">
              <view class="grid-card-head">
                <view class="icon-box assessment-logo career-logo">
                  <view class="logo-pip career-pip" />
                  <LucideIcon name="Target" size="30rpx" color="#0891b2" />
                </view>
                <text class="grid-card-title">职业兴趣测评</text>
              </view>
              <text class="grid-card-desc line-clamp-2">{{ hollandDone ? '查看职业匹配与倾向报告' : '尚未评测，点击前往' }}</text>
            </view>

          </view>
        </view>

        <!-- 深度报告入口 -->
        <view v-if="membershipStore.canUseDeepReports" class="section-container deep-report-package">
          <view class="section-header-row">
            <view class="section-heading-copy">
              <text class="section-header">升学深度报告</text>
              <text class="section-subtitle">院校与专业资料库，1.3.0 免费开放在线阅读和 PDF 下载</text>
            </view>
            <view class="quota-badge">{{ deepReportAccessBadge }}</view>
          </view>

          <view class="grid-2">
            <view class="grid-card deep-card" @click="goDeepReportDownload('university')" hover-class="grid-card-hover">
              <view class="deep-card-top">
                <view class="icon-box-large university">
                  <LucideIcon name="Building2" size="34rpx" color="#2563eb" />
                </view>
                <view class="deep-arrow">
                  <LucideIcon name="ArrowRight" size="26rpx" color="#64748b" />
                </view>
              </view>
              <text class="grid-card-title block-title">院校研究报告</text>
              <text class="grid-card-desc line-clamp-2">看学校定位、录取风险、转专业机会</text>
              <view class="deep-card-tags">
                <text class="deep-tag">学校库</text>
                <text class="deep-tag">可下载 PDF</text>
              </view>
            </view>

            <view class="grid-card deep-card" @click="goDeepReportDownload('major')" hover-class="grid-card-hover">
              <view class="deep-card-top">
                <view class="icon-box-large major">
                  <view class="logo-pip major-pip" />
                  <LucideIcon name="BookOpen" size="34rpx" color="#0891b2" />
                </view>
                <view class="deep-arrow">
                  <LucideIcon name="ArrowRight" size="26rpx" color="#64748b" />
                </view>
              </view>
              <text class="grid-card-title block-title">专业研究报告</text>
              <text class="grid-card-desc line-clamp-2">看课程难度、就业方向、适配人群</text>
              <view class="deep-card-tags">
                <text class="deep-tag">专业库</text>
                <text class="deep-tag">在线阅读</text>
              </view>
            </view>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup>


import { computed, ref, onMounted } from 'vue'
import LucideIcon from '../../components/LucideIcon.vue'
import { onShareAppMessage, onShow } from '@dcloudio/uni-app'
import pinia from '../../stores'
import { useMembershipStore } from '../../stores/membership.js'
import { useHomeProgress } from '../../composables/useHomeProgress.js'
import { CUSTOMER_WECHAT_ID, FREE_DEEP_REPORTS_ENABLED } from '../../config.js'
import { generateReport } from '../../api/report.js'
import { checkPregenerateStatus } from '../../api/pregenerate.js'
import { useReportPregen } from '../../composables/useReportPregen.js'
import { buildReportAssessmentPayload } from '../../utils/report-assessments.js'
import { waitForPregeneratedReport } from '../../utils/report-pregen-wait.js'
import {
  getProfileReportMode,
  loadHistory,
  loadUserProfile,
  loadReport,
  saveReport,
} from '../../utils/storage.js'

const membershipStore = useMembershipStore(pinia)
const {
  profile: progressProfile,
  step1Done,
  step2Done,
  mbtiDone,
  hollandDone,
  step3Done: allAssessmentsDone,
  step3Count: completedAssessments,
  completedSteps,
  refresh: refreshProgress,
} = useHomeProgress()

const currentProfile = computed(() => progressProfile.value || loadUserProfile())
const reportMode = computed(() => getProfileReportMode(currentProfile.value))
const reportModeLabel = computed(() => {
  if (reportMode.value === 'planning') return '专业规划报告'
  if (reportMode.value === 'estimated') return '预估定位报告'
  return '院校定位报告'
})
const pageTitle = computed(() => (
  latestReport.value ? '测评与报告中心' : `${reportModeLabel.value}准备`
))
const progressPercent = computed(() => {
  return Math.round((completedSteps.value / 4) * 100)
})
const allPrerequisitesDone = computed(() => step1Done.value && step2Done.value && allAssessmentsDone.value)
const profileStatusText = computed(() => {
  if (!step1Done.value) return '请先补充省份和科类，可暂不填正式分数'
  if (reportMode.value === 'planning') return '基础资料已记录，可先生成专业规划报告'
  if (reportMode.value === 'estimated') return '预估分已记录，正式分/位次出来后再校准'
  return '省份、科类和正式分数已记录'
})
const chatStatusText = computed(() => (
  step2Done.value ? '已完成至少 1 轮咨询' : '先聊 1 轮，让报告纳入现实约束'
))
const assessmentStatusText = computed(() => (
  allAssessmentsDone.value ? '两项测评已完成' : `已完成 ${completedAssessments.value}/2`
))
const generateButtonText = computed(() => {
  if (!step1Done.value) return '先补充基础资料'
  if (!step2Done.value) return '先完成 1 轮 AI 咨询'
  if (!allAssessmentsDone.value) return '需先完成上方 2 项测评'
  if (!membershipStore.canUseDeepReports) return '报告功能暂未开放'
  return `立即生成${reportModeLabel.value}`
})
const generateHintText = computed(() => {
  if (!step1Done.value) return '基础资料决定报告口径：无分数看专业规划，有分数看院校定位。'
  if (!step2Done.value) return 'AI 咨询会补充城市、专业、预算和家庭约束。'
  if (!allAssessmentsDone.value) return '测评结果会用于补充“分数之外的信息”，帮助报告更准确。'
  if (!membershipStore.canUseDeepReports) return '当前版本报告生成暂未开放，请联系客服处理。'
  return '报告通常需要 1-2 分钟，请保持页面打开。'
})
const deepReportAccessBadge = computed(() => (
  FREE_DEEP_REPORTS_ENABLED
    ? '1.3.0 免费开放'
    : `PDF 剩余 ${membershipStore.downloadQuota.remaining}/${membershipStore.downloadQuota.limit}`
))

const generating = ref(false)
const latestReport = ref(null)
const history = ref([])

const { tryTriggerPregenerate } = useReportPregen()

const fakeProgress = ref(0)
const progressTitle = ref('正在生成综合报告')
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
  title: `邀请你一起生成${reportModeLabel.value}`,
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
  const blocker = getReadinessBlocker()
  if (blocker) {
    uni.showToast({ title: blocker.toast, icon: 'none' })
    if (blocker.action) blocker.action()
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
  progressTip.value = `即将为你呈现${reportModeLabel.value}`

  // Step 1: 1s -> 30%
  setTimeout(() => {
    fakeProgress.value = 30
    progressTitle.value = '整合考生数据…'
    progressSub.value = '整合性格类型与职业兴趣指标...'
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
    progressSub.value = `欢迎进入属于你的${reportModeLabel.value}`
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

function startSlowProgress() {
  isFakeProgressActive.value = true
  fakeProgress.value = 0

  const slowTimers = [
    { delay: 2000, pct: 10, title: '正在收集考生资料…', sub: '整合基础信息与测评数据' },
    { delay: 8000, pct: 25, title: 'AI 深度分析中…', sub: '匹配院校与专业方向' },
    { delay: 20000, pct: 40, title: '正在生成志愿方案…', sub: '构建个性化推荐与风险分析' },
    { delay: 40000, pct: 55, title: '深度分析中…', sub: '正在提炼核心建议与行动方案' },
    { delay: 70000, pct: 70, title: '报告撰写中…', sub: '排版优化与内容整合' },
    { delay: 100000, pct: 88, title: '即将完成…', sub: '正在等待 AI 返回报告结果' },
    { delay: 170000, pct: 92, title: '仍在处理中…', sub: '复杂报告需要更久，请保持页面打开' },
    { delay: 240000, pct: 96, title: '最后校验中…', sub: '正在等待服务端返回报告链接' },
  ]

  slowTimers.forEach(({ delay, pct, title, sub }) => {
    setTimeout(() => {
      if (!generating.value) return
      if (fakeProgress.value < pct) {
        fakeProgress.value = pct
        progressTitle.value = title
        progressSub.value = sub
      }
    }, delay)
  })
}

function saveGeneratedReportResult(result) {
  const reportEntry = {
    url: result.url,
    generatedAt: result.generatedAt || result.completedAt || Date.now(),
  }
  if (latestReport.value?.url) {
    history.value.unshift({ ...latestReport.value })
  }
  latestReport.value = reportEntry
  persistReports()
  isFakeProgressActive.value = false
}

async function claimPregeneratedReport() {
  const profile = loadUserProfile()
  const assessments = buildReportAssessmentPayload()
  const chatHistory = loadHistory()

  return generateReport({
    profile,
    userId: membershipStore.userId,
    sessionToken: membershipStore.sessionToken,
    conversationId: chatHistory.conversationId || '',
    assessments,
    skipExpansion: true,
  })
}

async function onGenerate() {
  const blocker = getReadinessBlocker()
  if (blocker) {
    uni.showToast({ title: blocker.toast, icon: 'none' })
    if (blocker.action) blocker.action()
    return
  }

  generating.value = true

  // Reset loader variables
  isFakeProgressActive.value = false
  fakeProgress.value = 0
  progressTitle.value = `正在生成${reportModeLabel.value}`
  progressSub.value = '正在整合考生信息、测评结果与对话记录'
  progressTip.value = '通常需要 1-2 分钟，请保持页面打开'

  try {
    await membershipStore.ensureLogin()
    if (!membershipStore.canUseDeepReports) {
      await membershipStore.loadStatus()
    }
    if (!membershipStore.canUseDeepReports) {
      showSupportModal('报告功能暂未开放', '当前版本暂未开放报告生成，请联系客服处理。')
      generating.value = false
      return
    }

    let slowProgressStarted = false

    // Prefer the background task so WeChat does not hold a multi-minute request open.
    try {
      const pregenStatus = await tryTriggerPregenerate({ force: true })
      if (pregenStatus?.status === 'ready' && pregenStatus.url) {
        console.log('[Pregen] Cache hit! Running fake progress bar UX.')
        const claimedReport = await claimPregeneratedReport()
        runFakeProgressBar(claimedReport.url)
        return
      }

      if (pregenStatus?.status === 'started' || pregenStatus?.status === 'pending') {
        startSlowProgress()
        slowProgressStarted = true
        const readyReport = await waitForPregeneratedReport({
          checkStatus: () => checkPregenerateStatus({
            sessionToken: membershipStore.sessionToken,
          }),
        })
        if (readyReport?.url) {
          const claimedReport = await claimPregeneratedReport()
          saveGeneratedReportResult(claimedReport)
          return
        }
      }

      console.log('[Pregen] Falling back from status:', pregenStatus?.status || 'unknown')
    } catch (pregenErr) {
      console.warn('[Pregen] Failed to check pre-generate status:', pregenErr)
      if (pregenErr.code === 'PREGEN_FAILED' || pregenErr.code === 'PREGEN_TIMEOUT') {
        throw pregenErr
      }
    }

    if (!slowProgressStarted) {
      startSlowProgress()
    }

    // Fallback to normal generation when no background task is available.
    const result = await claimPregeneratedReport()
    saveGeneratedReportResult(result)
  } catch (err) {
    const isCooldown = err.statusCode === 429
    if (isCooldown) {
      uni.showToast({ title: err.data?.error || '请稍后再试', icon: 'none', duration: 3000 })
      // Revert: restore latestReport if we just cleared it via onRegenerate
      if (!latestReport.value?.url) {
        const stored = loadReport()
        if (stored?.url) latestReport.value = stored
      }
    } else {
      const message = err.data?.draftId
        ? '生成失败，已保留草稿，可稍后重试'
        : (err.message || '生成失败')
      showSupportModal('报告生成失败', `${message}\n\n请稍后重试；如仍失败，请联系客服并发送用户 ID、失败截图和发生时间。`)
    }
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

function getReadinessBlocker() {
  if (!step1Done.value) {
    return { toast: '请先补充基础资料', action: goHomeProfile }
  }
  if (!step2Done.value) {
    return { toast: '请先完成 1 轮 AI 咨询', action: goChat }
  }
  if (!allAssessmentsDone.value) {
    return { toast: '请先完成上方 2 项测评', action: null }
  }
  return null
}

function goHomeProfile() {
  uni.switchTab({ url: '/pages/index/index' })
  setTimeout(() => uni.$emit('open-profile-sheet'), 200)
}

function goChat() {
  uni.switchTab({ url: '/pages/chat/chat' })
}

function showSupportModal(title, message) {
  uni.showModal({
    title,
    content: `${message}\n\n客服微信：${CUSTOMER_WECHAT_ID}`,
    confirmText: '复制微信',
    cancelText: '关闭',
    success(res) {
      if (!res.confirm) return
      uni.setClipboardData({
        data: CUSTOMER_WECHAT_ID,
        success: () => uni.showToast({ title: '微信号已复制', icon: 'none' }),
      })
    },
  })
}


</script>


<style lang="scss">
page {
  background-color: $bg-page;
}
</style>

<style lang="scss" scoped>
.bg-glow-blue {
  position: absolute;
  top: -100rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 700rpx;
  height: 700rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, rgba(37, 99, 235, 0) 65%);
  pointer-events: none;
  z-index: 0;
}

.report-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
}

.header-banner {
  padding-top: 48rpx;
  padding-bottom: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  position: sticky;
  top: 0;
  z-index: 20;
  background-color: rgba(248, 250, 252, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.page-title {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  letter-spacing: 1rpx;
  padding-top: 8rpx;
}

.main-content {
  padding: 0 32rpx 48rpx 32rpx;
  position: relative;
  z-index: 1;
}

.progress-section {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 32rpx;
  margin-top: 16rpx;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.progress-title {
  font-size: 30rpx;
  font-weight: 800;
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
  gap: 16rpx;
}

.progress-bar {
  height: 12rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: $grad-primary;
  border-radius: $radius-full;
  transition: width 0.4s ease;
}

.progress-count-text {
  font-size: 24rpx;
  color: $text-muted;
}

.requirements-section {
  margin-bottom: 32rpx;
}

.requirement-item {
  background-color: #ffffff;
  border: 1px solid #e3e8f0;
  border-radius: 14rpx;
  padding: 20rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.02);

  &.done {
    border-color: #86efac;
    background-color: #f0fdf4;
  }
}

.requirement-mark {
  width: 48rpx;
  height: 48rpx;
  border-radius: 12rpx;
  background: #f1f5f9;
  color: $text-muted;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 800;
  flex-shrink: 0;

  .requirement-item.done & {
    background: #dcfce7;
    color: #16a34a;
  }
}

.requirement-body {
  flex: 1;
  min-width: 0;
}

.requirement-title {
  display: block;
  font-size: 26rpx;
  color: $text-primary;
  font-weight: 800;
}

.requirement-desc {
  display: block;
  font-size: 22rpx;
  color: $text-muted;
  line-height: 1.45;
  margin-top: 4rpx;
}

.section-title, .section-header {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 24rpx;
  display: block;
  padding-left: 8rpx;
}

.assessment-card {
  @include glass-panel;
  border-radius: $radius-lg;
  padding: 24rpx 32rpx;
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid transparent; // for active state

  &:active {
    transform: scale(0.98);
  }

  &.completed {
    background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(240,253,244,0.6) 100%);
    border-color: rgba(16, 185, 129, 0.2);
  }
}

.card-hover {
  background-color: rgba(255, 255, 255, 0.9);
}

.card-icon-wrap {
  width: 80rpx;
  height: 80rpx;
  background-color: $bg-input;
  border-radius: 30%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;

  &.completed {
    background-color: #D1FAE5;
  }
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.card-desc {
  font-size: 24rpx;
  color: $text-muted;
}

.status-badge {
  font-size: 24rpx;
  padding: 8rpx 16rpx;
  background-color: $bg-input;
  color: $text-muted;
  border-radius: $radius-sm;
  font-weight: 600;

  &.completed {
    background-color: transparent;
    color: #059669;
  }
}

.generate-section {
  margin-top: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.generate-btn {
  width: 100%;
  height: 88rpx;
  border-radius: $radius-full;
  background-color: $bg-input;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;

  &::after { border: none; }

  &.ready {
    background: $grad-accent;
    @include neon-shadow;
  }
}

.generate-btn-text {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-muted;

  .ready & {
    color: #ffffff;
  }
}

.generate-hint {
  font-size: 24rpx;
  color: $text-muted;
  margin-top: 24rpx;
}

.hero-card {
  background: $grad-primary;
  border-radius: $radius-xl;
  padding: 48rpx 40rpx;
  color: #ffffff;
  margin-bottom: 40rpx;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12rpx 32rpx rgba(37, 99, 235, 0.25);
  margin-top: 24rpx;
}

.hero-deco-wrap {
  position: absolute;
  right: 0;
  top: 0;
  width: 256rpx;
  height: 256rpx;
  opacity: 0.15;
  pointer-events: none;
  transform: translateX(32rpx);
}

.hero-deco-1 {
  width: 256rpx;
  height: 256rpx;
  background-color: #ffffff;
  border-radius: 40rpx;
  transform: rotate(15deg) skewX(10deg);
}

.hero-deco-2 {
  position: absolute;
  left: -40rpx;
  top: 20rpx;
  width: 120rpx;
  height: 32rpx;
  background-color: #ffffff;
  border-radius: 16rpx;
  transform: rotate(15deg);
}

.hero-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.hero-title {
  font-size: 46rpx;
  font-weight: 900;
  margin-bottom: 12rpx;
  letter-spacing: 2rpx;
  display: flex;
  text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.hero-time {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  font-family: monospace;
  margin-bottom: 40rpx;
}

.hero-btn {
  width: 100%;
  height: 88rpx;
  background: #ffffff;
  color: $brand-primary-dark;
  font-weight: 800;
  font-size: 30rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.1);
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }

  &::after { border: none; }
}

.hero-btn-hover {
  background-color: #f8fafc;
}

.sub-actions {
  display: flex;
  gap: 24rpx;
  margin-bottom: 48rpx;
}

.sub-btn {
  flex: 1;
  height: 80rpx;
  border-radius: $radius-full;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  color: $text-secondary;
  font-size: 28rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.02);
  transition: background-color 0.2s;

  &::after { border: none; }
}

.sub-btn-hover {
  background-color: #f8fafc;
}

.section-container {
  margin-bottom: 48rpx;
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
  padding-left: 8rpx;
  gap: 16rpx;
}

.section-header-row .section-header {
  margin-bottom: 6rpx;
  padding-left: 0;
}

.section-heading-copy {
  min-width: 0;
  flex: 1;
}

.section-subtitle {
  display: block;
  font-size: 22rpx;
  line-height: 1.45;
  color: #64748b;
}

.quota-badge {
  flex-shrink: 0;
  font-size: 22rpx;
  padding: 8rpx 18rpx;
  background-color: #e0f2fe;
  color: #075985;
  border-radius: $radius-full;
  font-weight: 700;
  line-height: 1;
  border: 1px solid rgba(14, 165, 233, 0.18);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24rpx;
}

.grid-card {
  @include glass-panel;
  border-radius: $radius-lg;
  padding: 32rpx 24rpx;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.grid-card-hover {
  background-color: #F8FAFC;
}

.grid-card-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.icon-box {
  width: 56rpx;
  height: 56rpx;
  border-radius: 30%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #DBEAFE;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.icon-box-large {
  width: 80rpx;
  height: 80rpx;
  border-radius: 30%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #DBEAFE;
  margin-bottom: 24rpx;
  position: relative;
  overflow: hidden;
}

.assessment-logo::before,
.icon-box-large::before {
  content: '';
  position: absolute;
  right: -10rpx;
  top: -12rpx;
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.72);
}

.assessment-logo::after,
.icon-box-large::after {
  content: '';
  position: absolute;
  left: 10rpx;
  bottom: 8rpx;
  width: 18rpx;
  height: 6rpx;
  border-radius: $radius-full;
  background: rgba(255, 255, 255, 0.64);
  transform: rotate(-18deg);
}

.assessment-logo :deep(.lucide-icon),
.icon-box-large :deep(.lucide-icon) {
  position: relative;
  z-index: 2;
}

.personality-logo {
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 58%, #f0f9ff 100%);
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.08);
}

.career-logo {
  background: linear-gradient(135deg, #ccfbf1 0%, #ecfeff 62%, #f0fdfa 100%);
  box-shadow: inset 0 0 0 1px rgba(8, 145, 178, 0.1);
}

.logo-pip {
  position: absolute;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  z-index: 1;
}

.personality-pip {
  left: 10rpx;
  top: 12rpx;
  background: #93c5fd;
}

.career-pip {
  right: 10rpx;
  bottom: 12rpx;
  background: #67e8f9;
}

.major-pip {
  right: 12rpx;
  bottom: 12rpx;
  background: #67e8f9;
}

.grid-card-title {
  font-size: 28rpx;
  font-weight: 800;
  color: $text-primary;
}

.block-title {
  display: block;
  font-size: 30rpx;
  margin-bottom: 12rpx;
}

.grid-card-desc {
  font-size: 22rpx;
  color: $text-muted;
  line-height: 1.5;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.deep-report-package {
  margin-top: 8rpx;

  .grid-card {
    background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
    border: 1px solid rgba(37, 99, 235, 0.12);
    box-shadow: 0 10rpx 30rpx rgba(37, 99, 235, 0.08);
  }

  .grid-card-title {
    color: #0f172a;
  }

  .grid-card-desc {
    color: #64748b;
  }

  .icon-box-large {
    margin-bottom: 0;
    border-radius: 24rpx;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.72);

    &.university {
      background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
    }

    &.major {
      background: linear-gradient(135deg, #cffafe 0%, #ecfeff 100%);
    }
  }

  .grid-card-hover {
    background: #f8fafc;
  }
}

.deep-card {
  min-height: 238rpx;
  padding: 28rpx 22rpx 24rpx;
  justify-content: space-between;
}

.deep-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.deep-arrow {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.deep-card-tags {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-wrap: wrap;
  margin-top: 18rpx;
}

.deep-tag {
  display: flex;
  align-items: center;
  height: 34rpx;
  padding: 0 12rpx;
  border-radius: $radius-full;
  background: #eef6ff;
  color: #2563eb;
  font-size: 20rpx;
  font-weight: 700;
  line-height: 34rpx;
}

/* 生成中加载 */
.loading-card {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 64rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 24rpx;
}

.spinner-ring {
  width: 72rpx;
  height: 72rpx;
  border: 6rpx solid $bg-input;
  border-top-color: $brand-primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 32rpx;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-title {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 16rpx;
}

.loading-sub {
  font-size: 26rpx;
  color: $text-secondary;
  margin-bottom: 8rpx;
  text-align: center;
}

.loading-tip {
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 32rpx;
}

.loading-bar {
  width: 100%;
  height: 12rpx;
  background-color: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
  position: relative;
  margin-bottom: 16rpx;
}

.loading-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 30%;
  background: $grad-primary;
  border-radius: $radius-full;
  animation: load 2s infinite ease-in-out;
}

.fake-progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: $grad-primary;
  border-radius: $radius-full;
  transition: width 0.5s ease-in-out;
}

.loading-percent {
  font-size: 24rpx;
  color: $brand-primary;
  font-weight: 800;
}

@keyframes load {
  0% { left: -30%; width: 30%; }
  50% { left: 30%; width: 50%; }
  100% { left: 100%; width: 30%; }
}

</style>
