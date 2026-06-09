<template>
  <view class="page">
    <!-- 轻量背景 -->
    <view class="bg-glow-soft" />

    <!-- 顶部品牌 + 招呼 -->
    <view class="brand">
      <view class="logo">
        <image class="logo-img" src="/static/logo.png" mode="aspectFit" />
      </view>
      <text class="brand-name">峰哥咨询参考</text>
      <text class="brand-greet">{{ greetingText }}</text>
    </view>

    <!-- 顶部进度卡 -->
    <view class="progress-card">
      <view class="progress-top">
        <text class="progress-label">规划进度</text>
        <text class="progress-hint">{{ nextActionText }}</text>
      </view>
      <view class="progress-stat">
        <text class="progress-frac">{{ completedSteps }}<text class="progress-total"> / 4 步</text></text>
      </view>
      <view class="progress-bar"><view class="progress-fill" :style="{ width: progressPercent + '%' }" /></view>
      <text class="progress-guide">无分数看专业规划，有分数看院校定位</text>
    </view>

    <!-- 步骤 1: 基础信息 -->
    <view class="step" :class="step1ClassObj" @click="onClickStep1">
      <view class="step-icon">{{ step1IconText }}</view>
      <view class="step-body">
        <text class="step-title">填写基础信息</text>
        <text class="step-desc">{{ step1DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>

    <!-- 步骤 2: 和峰哥聊聊 -->
    <view class="step" :class="step2ClassObj" @click="onClickStep2">
      <view class="step-icon">{{ step2IconText }}</view>
      <view class="step-body">
        <text class="step-title">和峰哥聊聊志愿</text>
        <text class="step-desc">{{ step2DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>

    <!-- 步骤 3: 2 项测评（active 时展开） -->
    <view v-if="step3Status !== 'active'" class="step" :class="step3ClassObj" @click="onClickStep3">
      <view class="step-icon">{{ step3IconText }}</view>
      <view class="step-body">
        <text class="step-title">2 项性格测评</text>
        <text class="step-desc">{{ step3DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>
    <view v-else class="step step-active step-expanded">
      <view class="step-top-row">
        <view class="step-icon active-icon">3</view>
        <view class="step-body">
          <text class="step-title">完成 2 项测评</text>
          <text class="step-desc active-desc">让报告更准确 · 已完成 {{ step3Count }}/2</text>
        </view>
      </view>
      <view class="chips">
        <view class="chip" :class="{ done: mbtiDone, next: nextAssessment === 'mbti' }">
          <text class="chip-label">MBTI</text>
          <text class="chip-status">{{ chipStatus('mbti') }}</text>
        </view>
        <view class="chip" :class="{ done: hollandDone, next: nextAssessment === 'holland' }">
          <text class="chip-label">霍兰德</text>
          <text class="chip-status">{{ chipStatus('holland') }}</text>
        </view>
      </view>
      <view class="step-cta" @click.stop="onContinueAssessment">
        <text class="step-cta-text">{{ nextAssessmentCtaText }}</text>
      </view>
    </view>

    <!-- 步骤 4: 生成报告 -->
    <view class="step" :class="step4ClassObj" @click="onClickStep4">
      <view class="step-icon">{{ step4IconText }}</view>
      <view class="step-body">
        <text class="step-title">生成志愿报告</text>
        <text class="step-desc">{{ step4DescText }}</text>
      </view>
      <text class="step-arrow">›</text>
    </view>

    <!-- 已就绪时底部的报告 hero -->
    <view v-if="step3Done && !reportDone" class="report-hero" @click="goReport">
      <view class="report-hero-glow" />
      <view class="report-hero-content">
        <view class="report-hero-text">
          <text class="report-hero-title">志愿报告可以生成了</text>
          <text class="report-hero-price">1.3.0 免费开放</text>
          <text class="report-hero-sub">完整报告 + 深度阅读 + PDF 下载额度</text>
          <text class="report-hero-sub">无需支付或兑换码，完成准备后可直接生成</text>
        </view>
        <text class="report-hero-icon">报告</text>
      </view>
      <view class="report-hero-cta">立即生成报告 →</view>
    </view>

    <!-- 院校与专业深度报告快捷入口 -->
    <view class="deep-report-section">
      <view class="section-heading">
        <text class="section-title">深度报告库</text>
        <text class="section-subtitle">先研究清楚，再做志愿选择</text>
      </view>
      <view class="deep-report-grid">
        <view class="deep-report-card university" @click="goDeepReport('university')">
          <view class="deep-report-icon">校</view>
          <text class="deep-report-title">院校深度报告</text>
          <text class="deep-report-desc">看清学校定位、王牌专业与毕业出路</text>
          <view class="deep-report-link">
            <text>查院校</text>
            <text class="deep-report-arrow">›</text>
          </view>
        </view>
        <view class="deep-report-card major" @click="goDeepReport('major')">
          <view class="deep-report-icon">专</view>
          <text class="deep-report-title">专业深度报告</text>
          <text class="deep-report-desc">判断专业前景、适合人群与报考风险</text>
          <view class="deep-report-link">
            <text>查专业</text>
            <text class="deep-report-arrow">›</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="showProfileSheet" class="profile-sheet-mask" @click="closeProfileSheet">
      <view class="profile-sheet" @click.stop>
        <view class="profile-sheet-head">
          <text class="profile-sheet-title">填写基础信息</text>
          <text class="profile-sheet-close" @click="closeProfileSheet">×</text>
        </view>
        <text class="profile-sheet-desc">先确定省份和科类；正式分数未出时，也可以用预估分或先做专业规划。</text>

        <view class="field-block">
          <text class="field-label">当前阶段</text>
          <view class="mode-cards">
            <view
              class="mode-card"
              :class="{ active: draft.planning_mode === 'score' }"
              @click="selectPlanningMode('score')"
            >
              <text class="mode-title">成绩/预估成绩</text>
              <text class="mode-desc">已有正式分或大致预估分</text>
            </view>
            <view
              class="mode-card"
              :class="{ active: draft.planning_mode === 'early' }"
              @click="selectPlanningMode('early')"
            >
              <text class="mode-title">提前规划</text>
              <text class="mode-desc">高一高二可先不填分数</text>
            </view>
          </view>
        </view>

        <view class="field-block">
          <text class="field-label">省份</text>
          <picker
            mode="selector"
            :range="PROVINCE_OPTIONS"
            :value="provincePickerValue"
            @change="selectProvince"
          >
            <view class="province-picker" :class="{ placeholder: !draft.province }">
              <text class="province-picker-text">{{ draft.province || '请选择省份' }}</text>
              <text class="province-picker-arrow">⌄</text>
            </view>
          </picker>
        </view>

        <view class="field-block">
          <text class="field-label">科类</text>
          <view class="segment">
            <view
              class="segment-option"
              :class="{ active: draft.category === '物理类' }"
              @click="selectCategory('物理类')"
            >
              <text class="segment-text">物理类</text>
            </view>
            <view
              class="segment-option"
              :class="{ active: draft.category === '历史类' }"
              @click="selectCategory('历史类')"
            >
              <text class="segment-text">历史类</text>
            </view>
          </view>
        </view>

        <view v-if="draft.planning_mode === 'score'" class="field-block">
          <text class="field-label">分数类型</text>
          <view class="segment">
            <view
              class="segment-option"
              :class="{ active: draft.score_type !== 'estimated' }"
              @click="selectScoreType('official')"
            >
              <text class="segment-text">正式分数</text>
            </view>
            <view
              class="segment-option"
              :class="{ active: draft.score_type === 'estimated' }"
              @click="selectScoreType('estimated')"
            >
              <text class="segment-text">预估分数</text>
            </view>
          </view>
        </view>

        <view v-if="draft.planning_mode === 'score'" class="field-row">
          <view class="field-block half">
            <text class="field-label">{{ scoreFieldLabel }}</text>
            <input v-model.trim="draft.score" class="field-input" type="number" :placeholder="scorePlaceholder" />
          </view>
          <view class="field-block half">
            <text class="field-label">位次</text>
            <input v-model.trim="draft.rank" class="field-input" type="number" placeholder="选填" />
          </view>
        </view>

        <view v-if="draft.planning_mode === 'score' && draft.score_type === 'estimated'" class="field-block">
          <text class="field-label">预估分数区间</text>
          <input v-model.trim="draft.score_range" class="field-input" placeholder="选填，例如：540-570" />
        </view>

        <view v-if="draft.planning_mode === 'early'" class="field-row">
          <view class="field-block half">
            <text class="field-label">年级</text>
            <input v-model.trim="draft.grade" class="field-input" placeholder="例如：高二" />
          </view>
          <view class="field-block half">
            <text class="field-label">身份</text>
            <input v-model.trim="draft.identity" class="field-input" placeholder="例如：家长" />
          </view>
        </view>

        <view v-if="draft.planning_mode === 'early'" class="field-row">
          <view class="field-block half">
            <text class="field-label">预估分数</text>
            <input v-model.trim="draft.score" class="field-input" type="number" placeholder="选填，例如：550" />
          </view>
          <view class="field-block half">
            <text class="field-label">预估分数区间</text>
            <input v-model.trim="draft.score_range" class="field-input" placeholder="选填，例如：520-560" />
          </view>
        </view>

        <button class="profile-save-btn" @click="saveProfileDraft">保存信息</button>
      </view>
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">
      <text class="disclaimer-text">结果仅供志愿填报参考，请以各省教育考试院和高校官方信息为准。</text>
      <text class="privacy-link" @click="goPrivacy">《隐私保护指引》</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow, onUnload, onShareAppMessage } from '@dcloudio/uni-app'
import { useHomeProgress, StepStatus } from '../../composables/useHomeProgress.js'
import { useMembershipStore } from '../../stores/membership.js'
import {
  getProfileReportMode,
  isProfileComplete,
  saveUserProfile,
} from '../../utils/storage.js'

const PROVINCE_OPTIONS = [
  '北京',
  '天津',
  '河北',
  '山西',
  '内蒙古',
  '辽宁',
  '吉林',
  '黑龙江',
  '上海',
  '江苏',
  '浙江',
  '安徽',
  '福建',
  '江西',
  '山东',
  '河南',
  '湖北',
  '湖南',
  '广东',
  '广西',
  '海南',
  '重庆',
  '四川',
  '贵州',
  '云南',
  '西藏',
  '陕西',
  '甘肃',
  '青海',
  '宁夏',
  '新疆',
]

const membershipStore = useMembershipStore()
const {
  profile,
  refresh,
  statusFor,
  step1Done,
  step2Done,
  step3Done,
  reportDone,
  step3Count,
  completedSteps,
  mbtiDone,
  hollandDone,
  chatRounds,
  nextAssessment,
} = useHomeProgress()

function createDraft(source = {}) {
  const hasSourceScore = source.score !== '' && source.score !== undefined && source.score !== null
  return {
    province: source.province || '',
    category: source.category || '',
    planning_mode: source.planning_mode || 'score',
    score_type: source.score_type || (hasSourceScore ? 'official' : ''),
    score_range: source.score_range || '',
    grade: source.grade || '',
    identity: source.identity || '',
    score: source.score === '' || source.score === undefined || source.score === null ? '' : String(source.score),
    rank: source.rank === '' || source.rank === undefined || source.rank === null ? '' : String(source.rank),
    family_resources: '',
    interest_subjects: source.interest_subjects || '',
    region_preference: source.region_preference || '',
    career_goal: source.career_goal || '',
  }
}

const showProfileSheet = ref(false)
const draft = ref(createDraft(profile.value))

// === 进度卡 ===
const progressPercent = computed(() => Math.round((completedSteps.value / 4) * 100))
const nextActionText = computed(() => {
  if (completedSteps.value === 0) return '从第 1 步开始'
  if (reportDone.value) return '已生成报告'
  if (step3Done.value) return '准备就绪'
  return `还差 ${4 - completedSteps.value} 步`
})
const scoreFieldLabel = computed(() => (draft.value.score_type === 'estimated' ? '预估分数' : '分数'))
const scorePlaceholder = computed(() => (draft.value.score_type === 'estimated' ? '例如：560' : '例如：580'))
const provincePickerIndex = computed(() => PROVINCE_OPTIONS.indexOf(draft.value.province))
const provincePickerValue = computed(() => (provincePickerIndex.value >= 0 ? provincePickerIndex.value : 0))
// === 招呼语 ===
const greetingText = computed(() => {
  if (!step1Done.value) return '你好，先花 30 秒了解一下吧'
  const tail = step3Done.value ? '已就绪' : `已完成 ${completedSteps.value}/4`
  const cat = profile.value.category ? profile.value.category.replace('类', '') : ''
  const scoreText = buildProfileBrief(profile.value)
  return `${profile.value.province} · ${cat} · ${scoreText} · ${tail}`
})

// === 每个步骤的状态 / class / icon / desc ===
const step1Status = computed(() => statusFor(1))
const step2Status = computed(() => statusFor(2))
const step3Status = computed(() => statusFor(3))
const step4Status = computed(() => statusFor(4))

function classObj(status) {
  return {
    'step-done': status === StepStatus.DONE,
    'step-active': status === StepStatus.ACTIVE,
    'step-locked': status === StepStatus.LOCKED,
  }
}
const step1ClassObj = computed(() => classObj(step1Status.value))
const step2ClassObj = computed(() => classObj(step2Status.value))
const step3ClassObj = computed(() => classObj(step3Status.value))
const step4ClassObj = computed(() => classObj(step4Status.value))

const step1IconText = computed(() => (step1Status.value === StepStatus.DONE ? '✓' : '1'))
const step2IconText = computed(() =>
  step2Status.value === StepStatus.DONE ? '✓' : step2Status.value === StepStatus.LOCKED ? '🔒' : '2'
)
const step3IconText = computed(() =>
  step3Status.value === StepStatus.DONE ? '✓' : step3Status.value === StepStatus.LOCKED ? '🔒' : '3'
)
const step4IconText = computed(() =>
  step4Status.value === StepStatus.DONE ? '✓' : step4Status.value === StepStatus.LOCKED ? '🔒' : '4'
)

const step1DescText = computed(() => {
  if (step1Done.value) {
    const cat = profile.value.category ? profile.value.category : ''
    return `${profile.value.province} · ${cat} · ${buildProfileBrief(profile.value)}`
  }
  return '省份和科类先定边界，分数可后补'
})

const step2DescText = computed(() => {
  if (step2Status.value === StepStatus.LOCKED) return '完成上一步后开始'
  if (step2Done.value) return `已聊 ${chatRounds.value} 轮 · 点击继续`
  return '先补充孩子画像、城市和家庭约束'
})

const step3DescText = computed(() => {
  if (step3Status.value === StepStatus.LOCKED) return '完成上一步后开始'
  if (step3Done.value) {
    const tags = []
    if (mbtiDone.value) tags.push('MBTI')
    if (hollandDone.value) tags.push('霍兰德')
    return `${tags.join(' / ')} 已记录`
  }
  return `补充分数之外的专业匹配依据 · 已完成 ${step3Count.value}/2`
})

const step4DescText = computed(() => {
  if (step4Status.value === StepStatus.LOCKED) return '完成测评后解锁'
  if (reportDone.value) return '报告已生成 · 点击查看'
  if (membershipStore.canUseDeepReports) return '深度报告已开放，一键生成'
  return '报告权益暂未开放'
})

function chipStatus(key) {
  if (key === 'mbti') return mbtiDone.value ? '✓' : nextAssessment.value === 'mbti' ? '→' : '—'
  if (key === 'holland') return hollandDone.value ? '✓' : nextAssessment.value === 'holland' ? '→' : '—'
  return '—'
}

const nextAssessmentCtaText = computed(() => {
  switch (nextAssessment.value) {
    case 'mbti':
      return '继续 性格类型定位 →'
    case 'holland':
      return '继续 霍兰德测评 →'
    default:
      return '查看测评结果 →'
  }
})

// === 跳转处理 ===
function onClickStep1() {
  openProfileSheet()
}
function onClickStep2() {
  if (step2Status.value === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成第 1 步', icon: 'none' })
    return
  }
  uni.switchTab({ url: '/pages/chat/chat' })
}
function onClickStep3() {
  if (step3Status.value === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成第 2 步', icon: 'none' })
    return
  }
  // done 状态点开看测评结果
  uni.navigateTo({ url: '/pages/assessments/assessments' })
}
function onContinueAssessment() {
  switch (nextAssessment.value) {
    case 'mbti':
      uni.navigateTo({ url: '/pages/mbti/mbti' })
      break
    case 'holland':
      uni.navigateTo({ url: '/pages/holland/holland' })
      break
    default:
      uni.navigateTo({ url: '/pages/assessments/assessments' })
  }
}
function onClickStep4() {
  if (step4Status.value === StepStatus.LOCKED) {
    uni.showToast({ title: '请先完成测评', icon: 'none' })
    return
  }
  uni.switchTab({ url: '/pages/report/report' })
}
function goReport() {
  uni.switchTab({ url: '/pages/report/report' })
}
function goDeepReport(mode) {
  uni.navigateTo({
    url: `/pages/deep-report-download/deep-report-download?mode=${encodeURIComponent(mode)}`,
  })
}
function goPrivacy() {
  uni.navigateTo({ url: '/pages/privacy/privacy' })
}

function openProfileSheet() {
  draft.value = createDraft(profile.value)
  showProfileSheet.value = true
}

function closeProfileSheet() {
  showProfileSheet.value = false
}

function selectProvince(event) {
  const index = Number(event?.detail?.value)
  draft.value.province = PROVINCE_OPTIONS[index] || ''
}

function selectCategory(category) {
  draft.value.category = category
}

function selectPlanningMode(mode) {
  draft.value.planning_mode = mode === 'early' ? 'early' : 'score'
  if (draft.value.planning_mode === 'early') {
    draft.value.score_type = ''
    draft.value.score = ''
    draft.value.rank = ''
    return
  }
  if (!draft.value.score_type) {
    draft.value.score_type = 'official'
  }
}

function selectScoreType(type) {
  draft.value.score_type = type === 'estimated' ? 'estimated' : 'official'
}

function buildProfileBrief(data = {}) {
  const mode = getProfileReportMode(data)
  if (mode === 'planning') {
    const estimate = data.score ? `预估${data.score}分` : data.score_range
    return [data.grade, estimate].filter(Boolean).join(' · ') || '提前规划'
  }
  if (mode === 'estimated') return data.score ? `预估${data.score}分` : (data.score_range || '预估分')
  return data.score ? `${data.score}分` : '待补分数'
}

async function saveProfileDraft() {
  if (!isProfileComplete(draft.value)) {
    uni.showToast({ title: '请先补充省份和科类', icon: 'none' })
    return
  }
  saveUserProfile(draft.value)
  refresh()
  membershipStore.syncProfile(profile.value).catch(() => {})
  membershipStore.markProfileCompleted().catch(() => {})
  closeProfileSheet()
  uni.showToast({ title: '基础信息已保存', icon: 'success' })
}

onLoad((options = {}) => {
  if (options.inviterId) membershipStore.setInviterId(options.inviterId)
  membershipStore.login().catch(() => {})
  uni.$on('open-profile-sheet', openProfileSheet)
})
onShow(() => {
  refresh()
  membershipStore.loadStatus().catch(() => {})
})
onUnload(() => {
  uni.$off('open-profile-sheet', openProfileSheet)
})

onShareAppMessage(() => ({
  title: '邀请你一起生成高考志愿参考报告',
  path: `/pages/index/index?inviterId=${membershipStore.userId || ''}`,
}))
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 25%, #f9fafb 100%);
  padding: calc(92rpx + env(safe-area-inset-top)) 28rpx 72rpx;
  position: relative;
  box-sizing: border-box;
}
.bg-glow-soft {
  position: absolute; top: 0; left: 0; right: 0; height: 320rpx;
  background: radial-gradient(circle at 50% 0%, rgba(249,115,22,0.12), transparent 60%);
  pointer-events: none;
}

/* === 顶部品牌 === */
.brand { text-align: center; padding: 14rpx 0 38rpx; position: relative; z-index: 1; }
.logo {
  width: 104rpx; height: 104rpx; margin: 0 auto 16rpx;
  border-radius: 26rpx; overflow: hidden;
  background: transparent;
  box-shadow: 0 10rpx 24rpx rgba(194, 65, 12, 0.16);
  display: flex; align-items: center; justify-content: center;
}
.logo-img { width: 104rpx; height: 104rpx; }
.brand-name { display: block; font-size: 40rpx; font-weight: 800; color: #111827; }
.brand-greet { display: block; font-size: 26rpx; color: #64748b; margin-top: 10rpx; }

/* === 进度卡 === */
.progress-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1rpx solid #eef2f7;
  border-radius: 20rpx;
  padding: 26rpx 26rpx;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.03);
  margin-bottom: 26rpx;
}
.progress-top { display: flex; justify-content: space-between; align-items: center; }
.progress-label { font-size: 27rpx; color: #6b7280; font-weight: 600; }
.progress-hint { font-size: 25rpx; color: #0f766e; font-weight: 700; }
.progress-stat { margin-top: 8rpx; }
.progress-frac { font-size: 44rpx; font-weight: 800; color: #111827; }
.progress-total { font-size: 27rpx; font-weight: 500; color: #9ca3af; }
.progress-bar { height: 9rpx; background: #f3f4f6; border-radius: 99rpx; margin-top: 14rpx; overflow: hidden; }
.progress-fill {
  height: 100%; border-radius: 99rpx;
  background: linear-gradient(90deg, #14b8a6, #f59e0b);
  transition: width 0.4s ease;
}
.progress-guide { display: block; font-size: 24rpx; color: #7c8794; margin-top: 14rpx; line-height: 1.5; }

/* === 步骤卡 === */
.step {
  background: white; border-radius: 20rpx;
  padding: 26rpx 24rpx; margin-bottom: 16rpx;
  display: flex; align-items: center; gap: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(17, 24, 39, 0.04);
}
.step-icon {
  width: 62rpx; height: 62rpx; border-radius: 16rpx;
  background: #f3f4f6; color: #9ca3af;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 29rpx; flex-shrink: 0;
}
.step-body { flex: 1; min-width: 0; }
.step-title { display: block; font-size: 31rpx; font-weight: 700; color: #111827; }
.step-desc { display: block; font-size: 25rpx; color: #9ca3af; margin-top: 6rpx; line-height: 1.4; }
.step-arrow { color: #d1d5db; font-size: 36rpx; }

.step-done .step-icon { background: #d1fae5; color: #059669; }
.step-done .step-desc { color: #059669; }
.step-active .step-icon {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: white;
  box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.35);
}
.step-active .step-desc { color: #f97316; }
.step-active .step-arrow { color: #f97316; }
.step-locked { opacity: 0.65; }
.step-locked .step-arrow { color: #d1d5db; }

/* === 展开形态 === */
.step-expanded {
  flex-direction: column; align-items: stretch;
  padding: 28rpx 26rpx; gap: 0;
}
.step-expanded .step-top-row { display: flex; align-items: center; gap: 20rpx; }
.chips { display: flex; gap: 14rpx; margin-top: 20rpx; }
.chip {
  flex: 1; background: #f9fafb; border-radius: 10rpx;
  padding: 14rpx 6rpx; text-align: center;
  border: 1rpx solid #e5e7eb;
}
.chip-label { display: block; font-size: 25rpx; color: #6b7280; }
.chip-status { display: block; font-size: 24rpx; color: #9ca3af; margin-top: 4rpx; }
.chip.done { background: #ecfdf5; border-color: #a7f3d0; }
.chip.done .chip-status { color: #059669; font-weight: 700; }
.chip.next { background: #fff7ed; border-color: #fdba74; }
.chip.next .chip-status { color: #ea580c; font-weight: 700; }
.step-cta {
  margin-top: 18rpx; padding: 22rpx;
  background: linear-gradient(90deg, #f97316, #ea580c);
  color: white; text-align: center;
  font-size: 28rpx; font-weight: 600;
  border-radius: 14rpx;
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
}
.step-cta-text { color: white; }

/* === 报告 hero === */
.report-hero {
  margin-top: 28rpx; padding: 28rpx;
  background: linear-gradient(135deg, #f97316 0%, #ea580c 60%);
  border-radius: 22rpx; color: white; position: relative; overflow: hidden;
  box-shadow: 0 10rpx 28rpx rgba(249, 115, 22, 0.35);
}
.report-hero-glow { position: absolute; top: -40rpx; right: -40rpx; width: 200rpx; height: 200rpx; background: radial-gradient(circle, rgba(255,255,255,0.3), transparent 70%); }
.report-hero-content { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }
.report-hero-text { flex: 1; }
.report-hero-title { display: block; font-size: 26rpx; font-weight: 600; opacity: 0.92; }
.report-hero-price { display: block; font-size: 52rpx; font-weight: 800; margin: 4rpx 0; }
.report-hero-currency { font-size: 28rpx; font-weight: 600; opacity: 0.85; margin-right: 4rpx; }
.report-hero-sub { display: block; font-size: 20rpx; opacity: 0.88; line-height: 1.5; }
.report-hero-icon {
  font-size: 24rpx; opacity: 0.95; font-weight: 800;
  border: 2rpx solid rgba(255,255,255,0.55);
  border-radius: 12rpx; padding: 10rpx 12rpx;
}
.report-hero-cta {
  margin-top: 18rpx; background: white; color: #c2410c;
  text-align: center; padding: 18rpx; border-radius: 14rpx;
  font-weight: 700; font-size: 28rpx;
}

/* === 深度报告快捷入口 === */
.deep-report-section { margin-top: 34rpx; }
.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 18rpx;
  padding: 0 4rpx;
}
.section-title { color: #111827; font-size: 32rpx; font-weight: 800; }
.section-subtitle { color: #94a3b8; font-size: 23rpx; text-align: right; }
.deep-report-grid { display: flex; gap: 16rpx; }
.deep-report-card {
  flex: 1;
  min-width: 0;
  min-height: 264rpx;
  border-radius: 22rpx;
  padding: 24rpx 22rpx 20rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border: 1rpx solid transparent;
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.06);
}
.deep-report-card.university {
  background: linear-gradient(145deg, #eff6ff 0%, #ffffff 100%);
  border-color: #dbeafe;
}
.deep-report-card.major {
  background: linear-gradient(145deg, #fff7ed 0%, #ffffff 100%);
  border-color: #ffedd5;
}
.deep-report-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 17rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 800;
  box-shadow: 0 6rpx 16rpx rgba(15, 23, 42, 0.12);
}
.university .deep-report-icon { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.major .deep-report-icon { background: linear-gradient(135deg, #fb923c, #ea580c); }
.deep-report-title {
  display: block;
  color: #111827;
  font-size: 29rpx;
  font-weight: 800;
  margin-top: 20rpx;
  line-height: 1.3;
}
.deep-report-desc {
  display: block;
  color: #64748b;
  font-size: 23rpx;
  line-height: 1.55;
  margin-top: 10rpx;
  flex: 1;
}
.deep-report-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid rgba(148, 163, 184, 0.18);
  font-size: 24rpx;
  font-weight: 700;
}
.university .deep-report-link { color: #2563eb; }
.major .deep-report-link { color: #ea580c; }
.deep-report-arrow { font-size: 32rpx; line-height: 1; }

/* === 基础信息弹窗 === */
.profile-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.42);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.profile-sheet {
  width: 100%;
  background: #ffffff;
  border-top-left-radius: 24rpx;
  border-top-right-radius: 24rpx;
  padding: 32rpx 32rpx calc(34rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}
.profile-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10rpx;
}
.profile-sheet-title { font-size: 34rpx; font-weight: 800; color: #111827; }
.profile-sheet-close { font-size: 44rpx; color: #9ca3af; line-height: 1; }
.profile-sheet-desc {
  display: block;
  font-size: 24rpx;
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 24rpx;
}
.field-row { display: flex; gap: 18rpx; }
.field-block { margin-bottom: 20rpx; }
.field-block.half { flex: 1; min-width: 0; }
.field-label {
  display: block;
  font-size: 24rpx;
  color: #374151;
  font-weight: 700;
  margin-bottom: 10rpx;
}
.field-input {
  height: 78rpx;
  background: #f9fafb;
  border: 1rpx solid #e5e7eb;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  color: #111827;
  box-sizing: border-box;
}
.province-picker {
  height: 78rpx;
  background: #f9fafb;
  border: 1rpx solid #e5e7eb;
  border-radius: 12rpx;
  padding: 0 20rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}
.province-picker-text {
  flex: 1;
  min-width: 0;
  color: #111827;
  font-size: 28rpx;
}
.province-picker.placeholder .province-picker-text {
  color: #9ca3af;
}
.province-picker-arrow {
  color: #9ca3af;
  font-size: 24rpx;
  line-height: 1;
}
.mode-cards {
  display: flex;
  gap: 14rpx;
}
.mode-card {
  flex: 1;
  min-height: 116rpx;
  border-radius: 12rpx;
  background: #f9fafb;
  border: 1rpx solid #e5e7eb;
  padding: 18rpx 16rpx;
  box-sizing: border-box;
}
.mode-card.active {
  background: #f0fdfa;
  border-color: #14b8a6;
}
.mode-title {
  display: block;
  color: #111827;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1.25;
}
.mode-desc {
  display: block;
  color: #6b7280;
  font-size: 21rpx;
  line-height: 1.35;
  margin-top: 8rpx;
}
.mode-card.active .mode-title { color: #0f766e; }
.segment {
  display: flex;
  gap: 14rpx;
}
.segment-option {
  flex: 1;
  height: 76rpx;
  border-radius: 12rpx;
  background: #f9fafb;
  border: 1rpx solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
}
.segment-option.active {
  background: #fff7ed;
  border-color: #f97316;
}
.segment-text {
  color: #6b7280;
  font-size: 28rpx;
  font-weight: 700;
}
.segment-option.active .segment-text { color: #ea580c; }
.profile-save-btn {
  height: 86rpx;
  line-height: 86rpx;
  border-radius: 14rpx;
  background: linear-gradient(90deg, #f97316, #ea580c);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
  margin-top: 10rpx;
}
.profile-save-btn::after { border: none; }

/* === 免责声明 === */
.disclaimer { margin-top: 44rpx; text-align: center; }
.disclaimer-text { display: block; font-size: 22rpx; color: #9ca3af; line-height: 1.65; }
.privacy-link { display: inline-block; font-size: 24rpx; color: #f97316; margin-top: 10rpx; }
</style>
