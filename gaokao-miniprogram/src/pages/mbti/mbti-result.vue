<template>
  <view class="mbti-result-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 未完成提示 -->
    <view v-if="!result" class="empty-state">
      <view class="empty-icon-outer">
        <view class="empty-icon-glow" />
        <view class="empty-icon">📋</view>
      </view>
      <text class="empty-title">尚未完成测评</text>
      <text class="empty-desc">请先完成性格测试</text>
      <button class="primary-btn" @click="goBack">前往测试</button>
    </view>

    <!-- 结果内容 -->
    <view v-else class="result-content">
      <view class="report-meta-card">
        <view class="student-avatar">
          <text class="student-avatar-text">峰</text>
        </view>
        <view class="student-meta">
          <text class="student-id">{{ studentLabel }}</text>
          <text class="student-date">{{ resultDate }}</text>
        </view>
        <view class="student-stats">
          <text class="student-stat-label">用时</text>
          <text class="student-stat-value">{{ durationLabel }}</text>
        </view>
      </view>

      <!-- 结果头部 - 渐变背景 -->
      <view class="result-header">
        <view class="header-glow" />
        <view v-if="resultVersion" class="version-label" :class="resultVersion">
          <text class="version-label-text">{{ resultVersion === 'basic' ? '⚡ 精简版测评' : '🔬 完整版测评' }}</text>
        </view>
        <text class="result-kicker">您的性格类型是：</text>
        <view class="type-identity">
          <view class="type-badge-wrap">
            <view class="type-badge">{{ result.type }}</view>
          </view>
          <view class="type-copy">
            <text class="type-name">{{ typeInfo?.name || '' }}</text>
            <text class="type-subtitle">{{ typeSubtitle }}</text>
          </view>
        </view>
        <text class="type-summary">{{ typeSummary }}</text>
        <view class="type-tags">
          <text v-for="(tag, index) in typeInfo?.tags" :key="index" class="tag">{{ tag }}</text>
        </view>
      </view>

      <!-- 维度得分 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">性格维度结果</text>
          </view>
        </view>
        <view class="dimensions-list">
          <view v-for="(dim, key) in dimensions" :key="key" class="dimension-item">
            <view class="dimension-labels">
              <text class="dim-label left" :class="{ active: result.scores[dim.left] >= result.scores[dim.right] }">
                {{ dim.leftLabel }}
              </text>
              <text class="dim-label right" :class="{ active: result.scores[dim.right] > result.scores[dim.left] }">
                {{ dim.rightLabel }}
              </text>
            </view>
            <view class="score-bar-wrap">
              <view class="score-bar">
                <view class="bar-fill left" :style="{ width: getLeftPercent(dim.left, dim.right) + '%' }">
                  <view class="bar-glow-dot left" />
                </view>
                <view class="bar-fill right" :style="{ width: getRightPercent(dim.left, dim.right) + '%' }">
                  <view class="bar-glow-dot right" />
                </view>
              </view>
            </view>
            <view class="score-values">
              <text class="score-value left" :class="{ active: result.scores[dim.left] >= result.scores[dim.right] }">
                {{ getLeftPercent(dim.left, dim.right) }}%
              </text>
              <text class="score-value right" :class="{ active: result.scores[dim.right] > result.scores[dim.left] }">
                {{ getRightPercent(dim.left, dim.right) }}%
              </text>
            </view>
          </view>
        </view>
        <view class="axis-notes">
          <view v-for="item in dimensionInterpretations" :key="item.key" class="axis-note">
            <view class="axis-dot" />
            <text class="axis-note-text">{{ item.label }}：{{ item.text }}</text>
          </view>
        </view>
      </view>

      <!-- 性格特征 -->
      <view class="section feature-section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">具体性格特征</text>
          </view>
        </view>
        <view class="feature-blocks">
          <view v-for="section in featureSections" :key="section.title" class="feature-block">
            <view class="feature-icon">{{ section.icon }}</view>
            <view class="feature-copy">
              <text class="feature-title">{{ section.title }}</text>
              <text v-for="(item, index) in section.items" :key="index" class="feature-text">{{ index + 1 }}. {{ item }}</text>
            </view>
          </view>
        </view>
        <view class="traits-list compact">
          <view v-for="(trait, index) in typeInfo?.traits" :key="index" class="trait-item">
            <view class="trait-bullet-outer">
              <view class="trait-bullet" />
            </view>
            <text class="trait-text">{{ trait }}</text>
          </view>
        </view>
      </view>

      <!-- 适合职业方向 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">典型职业方向</text>
          </view>
        </view>
        <view class="careers-grid">
          <text v-for="(career, index) in typeInfo?.careers" :key="index" class="career-tag">
            {{ career }}
          </text>
        </view>
      </view>

      <!-- 专业推荐 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">专业推荐</text>
          </view>
          <text class="section-subtitle">先看课程内容是否喜欢，再看院校和就业路径。</text>
        </view>
        <view class="majors-list">
          <view v-for="(major, index) in majorCards" :key="major.name" class="major-card" @click="viewMajorDetail(major.name)">
            <view class="major-header">
              <text class="major-name">{{ major.name }}</text>
              <view class="major-stars">
                <text v-for="s in 5" :key="s" class="star-char" :class="{ filled: s <= (5 - Math.floor(index / 2)) }">★</text>
              </view>
            </view>
            <text class="major-desc">{{ major.insight.summary }}</text>
            <view v-if="major.insight" class="major-insights">
              <view class="major-insight-row">
                <text class="major-insight-label">核心课程</text>
                <text class="major-insight-text">{{ formatList(major.insight.courses) }}</text>
              </view>
              <view class="major-insight-row">
                <text class="major-insight-label">能力要求</text>
                <text class="major-insight-text">{{ formatList(major.insight.abilities) }}</text>
              </view>
              <view class="major-insight-row">
                <text class="major-insight-label">薪资参考</text>
                <text class="major-insight-text">{{ major.insight.salarySummary }}</text>
              </view>
            </view>
            <view class="major-footer">
              <text class="major-link">查看专业详情</text>
              <view class="arrow-icon">➔</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部操作区域 -->
      <view class="footer-bar">
        <view class="footer-blur" />
        <view class="footer-inner">
          <text class="footer-progress">已完成 {{ resultVersion === 'basic' ? '精简版' : '完整版' }}性格测试 · {{ questionCount }}题</text>
          <button v-if="resultVersion === 'basic' && !isSharedResult" class="upgrade-btn" @click="handleUpgrade">🔬 升级到完整版 (48题)</button>
          <view class="footer-btns">
            <button class="share-report-btn" open-type="share" data-share-kind="report">分享报告</button>
            <button class="share-test-btn" open-type="share" data-share-kind="test">分享测试</button>
          </view>
          <button v-if="!isSharedResult" class="retry-link" @click="handleRetry">重新测试</button>
        </view>
      </view>
    </view>

    <!-- 确认弹窗 -->
    <view v-if="showConfirmModal" class="modal-overlay" @click="closeModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <view class="modal-warning-glow" />
          <view class="modal-icon">⚠️</view>
        </view>
        <text class="modal-title">重新进行性格测试？</text>
        <text class="modal-desc">重新测试会清除当前性格测试结果和答题进度，确认后需要重新作答。</text>
        <view class="modal-actions">
          <button class="modal-btn cancel" @click="closeModal">取消返回</button>
          <button class="modal-btn confirm" @click="confirmRetry">确认重置</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad, onShow, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getUserId, loadAssessments, saveAssessments } from '../../utils/storage.js'
import { MBTI_RESULT_REPORTS } from '../../data/mbti-questions.js'
import { fetchMajorInsights } from '../../api/majorInsights.js'
import { buildMajorCards, normalizeMajorName } from '../../data/major-learning-profiles.js'
import { useReportPregen } from '../../composables/useReportPregen.js'

const { tryTriggerPregenerate } = useReportPregen()

const result = ref(null)
const resultVersion = ref('')
const showConfirmModal = ref(false)
const majorInsights = ref({})
const localUserId = ref('')
const isSharedResult = ref(false)

// 维度配置
const dimensions = {
  EI: { left: 'E', right: 'I', leftLabel: '外向 (E)', rightLabel: '内向 (I)' },
  SN: { left: 'S', right: 'N', leftLabel: '实感 (S)', rightLabel: '直觉 (N)' },
  TF: { left: 'T', right: 'F', leftLabel: '思考 (T)', rightLabel: '情感 (F)' },
  JP: { left: 'J', right: 'P', leftLabel: '判断 (J)', rightLabel: '感知 (P)' }
}

const AXIS_LABELS = {
  E: '外向',
  I: '内向',
  S: '实感',
  N: '直觉',
  T: '思考',
  F: '情感',
  J: '判断',
  P: '感知',
}

const DIMENSION_EXPLANATIONS = {
  E: { key: 'E', label: '外向-E（精力来源）', text: '更容易在交流、讨论和真实互动中被激活，适合有反馈的学习环境。' },
  I: { key: 'I', label: '内向-I（精力来源）', text: '更喜欢独处整理思路，在安静、可控的环境中更容易进入深度学习。' },
  S: { key: 'S', label: '实感-S（信息搜集）', text: '偏好具体事实、现实案例和可操作步骤，课程越落地越容易有成就感。' },
  N: { key: 'N', label: '直觉-N（信息搜集）', text: '偏好概念框架、趋势判断和可能性探索，适合有想象空间的学科。' },
  T: { key: 'T', label: '思考-T（决策方式）', text: '做决定时更看重逻辑、公平和客观标准，适合规则清晰、推理密集的训练。' },
  F: { key: 'F', label: '情感-F（决策方式）', text: '做决定时会纳入价值感、关系和他人感受，适合人与服务场景更强的方向。' },
  J: { key: 'J', label: '判断-J（生活态度）', text: '偏好计划、确定性和阶段目标，适合路径清晰、进度可控的学习方式。' },
  P: { key: 'P', label: '感知-P（生活态度）', text: '偏好弹性、探索和临场调整，适合项目制、实践型和变化更快的场景。' },
}

const FEATURE_COPY = {
  E: {
    life: '从人群互动中恢复能量，适合多表达、多讨论、多展示的成长方式。',
    work: '更容易在协作、沟通、销售、组织和公开表达场景里被看见。',
  },
  I: {
    life: '需要稳定的独处时间恢复能量，陌生环境里通常先观察再投入。',
    work: '适合需要专注、独立判断、深度研究或持续打磨的任务。',
  },
  S: {
    learning: '喜欢课程有明确案例、实操步骤和可验证结果，实验、工程、护理、运营类训练会更有抓手。',
    work: '擅长把抽象要求落到流程、细节和真实问题上。',
  },
  N: {
    learning: '喜欢先理解框架和意义，再去吸收细节；理论、创意、策略和研究型课程更容易激发兴趣。',
    work: '擅长发现趋势、提出新方案和连接不同领域的信息。',
  },
  T: {
    learning: '会自然追问“证据是什么、逻辑是否成立”，适合结构严密、评价标准清楚的学科。',
    work: '面对分歧时倾向先看规则和事实，适合分析、技术、法律、金融等需要客观判断的岗位。',
  },
  F: {
    learning: '学习时会重视价值感和人的体验，能从真实个案、服务对象和社会意义中获得动力。',
    work: '适合教育、咨询、传播、公共服务等需要同理心和关系经营的方向。',
  },
  J: {
    life: '喜欢提前规划、按阶段推进，考试、证书和长期培养路径越清楚越能坚持。',
    work: '适合目标明确、职责边界清晰、需要统筹和执行力的岗位。',
  },
  P: {
    life: '喜欢保留选择空间，面对变化不容易慌，适合边做边优化的学习节奏。',
    work: '适合现场问题处理、创意迭代、产品探索和需要快速应变的工作。',
  },
}

// 类型信息
const typeInfo = computed(() => {
  if (!result.value?.type) return null
  return MBTI_RESULT_REPORTS[result.value.type] || null
})

const dominantAxes = computed(() => ({
  energy: getDominantKey('E', 'I'),
  information: getDominantKey('S', 'N'),
  decision: getDominantKey('T', 'F'),
  lifestyle: getDominantKey('J', 'P'),
}))

const typeSubtitle = computed(() => {
  const keys = Object.values(dominantAxes.value).filter(Boolean)
  return keys.map((key) => AXIS_LABELS[key]).join(' · ')
})

const typeSummary = computed(() => {
  const traits = typeInfo.value?.traits || []
  if (traits.length === 0) return '这份结果用于判断学习方式、专业课程和未来职业场景是否匹配。'
  return `${traits.slice(0, 2).join('，')}。建议把它作为选专业时的性格参考，而不是唯一结论。`
})

const dimensionInterpretations = computed(() => (
  Object.values(dominantAxes.value)
    .map((key) => DIMENSION_EXPLANATIONS[key])
    .filter(Boolean)
))

const featureSections = computed(() => {
  const axes = dominantAxes.value
  return [
    {
      icon: '学',
      title: '学习偏好上',
      items: [
        FEATURE_COPY[axes.information]?.learning,
        FEATURE_COPY[axes.decision]?.learning,
      ].filter(Boolean),
    },
    {
      icon: '生',
      title: '生活偏好上',
      items: [
        FEATURE_COPY[axes.energy]?.life,
        FEATURE_COPY[axes.lifestyle]?.life,
      ].filter(Boolean),
    },
    {
      icon: '职',
      title: '工作偏好上',
      items: [
        FEATURE_COPY[axes.decision]?.work,
        FEATURE_COPY[axes.information]?.work,
        FEATURE_COPY[axes.energy]?.work,
        FEATURE_COPY[axes.lifestyle]?.work,
      ].filter(Boolean).slice(0, 3),
    },
  ]
})

const shortUserId = computed(() => {
  const raw = localUserId.value || 'SHARED'
  return raw.replace(/^user_/, '').slice(0, 8).toUpperCase()
})

const studentLabel = computed(() => (isSharedResult.value ? '分享报告' : `学籍 ${shortUserId.value}`))

const resultDate = computed(() => formatDate(result.value?.completedAt || Date.now()))

const questionCount = computed(() => (resultVersion.value === 'basic' ? 16 : 48))

const durationLabel = computed(() => (resultVersion.value === 'basic' ? '约3分钟' : '约10分钟'))

const recommendedMajorNames = computed(() => (
  buildMajorCards(typeInfo.value?.majors || []).map((major) => major.name)
))

const majorCards = computed(() => {
  return buildMajorCards(typeInfo.value?.majors || [], majorInsights.value)
})

// 加载结果
function loadResult() {
  localUserId.value = getUserId()
  const assessments = loadAssessments()
  if (assessments.mbti?.completed) {
    result.value = {
      type: assessments.mbti.type,
      scores: assessments.mbti.scores,
      completedAt: assessments.mbti.completedAt || Date.now(),
    }
    resultVersion.value = assessments.mbti.version || 'full'
  } else {
    result.value = null
    resultVersion.value = ''
  }
}

async function loadMajorInsightsForResult() {
  const names = recommendedMajorNames.value
  if (names.length === 0) {
    majorInsights.value = {}
    return
  }

  try {
    const insights = await fetchMajorInsights(names)
    majorInsights.value = Object.fromEntries(
      insights.flatMap((item) => [
        [normalizeMajorName(item.requestedName || item.name), item],
        [normalizeMajorName(item.name), item],
      ])
    )
  } catch {
    majorInsights.value = {}
  }
}

function formatList(items = []) {
  return items.slice(0, 6).join('、')
}

function getDominantKey(leftKey, rightKey) {
  if (!result.value?.scores) return leftKey
  return (result.value.scores[leftKey] || 0) >= (result.value.scores[rightKey] || 0) ? leftKey : rightKey
}

function formatDate(timestamp) {
  const date = new Date(timestamp || Date.now())
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}.${month}.${day}`
}

function encodeScores(scores = {}) {
  return ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']
    .map((key) => `${key}${Number(scores[key]) || 0}`)
    .join('-')
}

function decodeScores(raw = '') {
  const scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 }
  String(raw || '').split('-').forEach((item) => {
    const match = item.match(/^([EISNTFJP])(\d+)$/)
    if (match) scores[match[1]] = Number(match[2]) || 0
  })
  return scores
}

function safeDecode(value = '') {
  try {
    return decodeURIComponent(value)
  } catch {
    return String(value || '')
  }
}

function loadSharedResult(options = {}) {
  const type = String(options.type || '').toUpperCase()
  if (!MBTI_RESULT_REPORTS[type]) return false
  result.value = {
    type,
    scores: decodeScores(safeDecode(options.scores || '')),
    completedAt: Number(options.at) || Date.now(),
  }
  resultVersion.value = options.version === 'basic' ? 'basic' : 'full'
  localUserId.value = 'shared'
  isSharedResult.value = true
  loadMajorInsightsForResult()
  return true
}

function buildSharedReportPath() {
  if (!result.value?.type) return '/pages/mbti/mbti'
  const params = [
    'shared=1',
    `type=${encodeURIComponent(result.value.type)}`,
    `version=${encodeURIComponent(resultVersion.value || 'full')}`,
    `scores=${encodeURIComponent(encodeScores(result.value.scores))}`,
    `at=${encodeURIComponent(String(result.value.completedAt || Date.now()))}`,
  ].join('&')
  return `/pages/mbti/mbti-result?${params}`
}

// 计算左侧百分比
function getLeftPercent(leftKey, rightKey) {
  if (!result.value) return 50
  const left = result.value.scores[leftKey] || 0
  const right = result.value.scores[rightKey] || 0
  const total = left + right
  return total > 0 ? Math.round((left / total) * 100) : 50
}

// 计算右侧百分比
function getRightPercent(leftKey, rightKey) {
  if (!result.value) return 50
  const left = result.value.scores[leftKey] || 0
  const right = result.value.scores[rightKey] || 0
  const total = left + right
  return total > 0 ? Math.round((right / total) * 100) : 50
}

// 星级评分（根据索引递减）
function getStars(index) {
  const count = Math.max(1, 5 - Math.floor(index / 2))
  return '★'.repeat(count) + '☆'.repeat(5 - count)
}

// 查看专业详情
function viewMajorDetail(major) {
  const params = encodeURIComponent(major)
  uni.navigateTo({
    url: `/pages/major-detail/major-detail?name=${params}&source=mbti&type=${result.value.type}`
  })
}

// 返回测评页
function goBack() {
  uni.navigateBack()
}

// 重新测试
function handleRetry() {
  showConfirmModal.value = true
}

// 关闭弹窗
function closeModal() {
  showConfirmModal.value = false
}

// 升级到完整版
function handleUpgrade() {
  // 清除结果，保留版本为 full
  const assessments = loadAssessments()
  assessments.mbti = {
    completed: false,
    version: 'full',
    type: '',
    scores: { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 },
    answers: [],
    questionIndex: 0,
    completedAt: 0
  }
  saveAssessments(assessments)
  uni.redirectTo({
    url: '/pages/mbti/mbti'
  })
}

// 确认重新测试
function confirmRetry() {
  // 清除 MBTI 结果
  const assessments = loadAssessments()
  assessments.mbti = {
    completed: false,
    version: '',
    type: '',
    scores: { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 },
    answers: [],
    questionIndex: 0,
    completedAt: 0
  }
  saveAssessments(assessments)

  closeModal()
  uni.redirectTo({
    url: '/pages/mbti/mbti'
  })
}

onLoad((options = {}) => {
  loadSharedResult(options)
})

onMounted(() => {
  if (!isSharedResult.value) {
    loadResult()
    loadMajorInsightsForResult()
    tryTriggerPregenerate()
  }
  uni.setNavigationBarTitle({
    title: '性格测试结果'
  })
})

onShow(() => {
  if (isSharedResult.value) return
  loadResult()
  loadMajorInsightsForResult()
})

onShareAppMessage((res = {}) => {
  const shareKind = res.target?.dataset?.shareKind
  if (shareKind === 'test') {
    return {
      title: '做个性格测试，看看哪些专业更适合你',
      path: '/pages/mbti/mbti',
    }
  }
  return {
    title: `我的性格测试报告：${result.value?.type || ''} ${typeInfo.value?.name || ''}`,
    path: buildSharedReportPath(),
  }
})

onShareTimeline(() => ({
  title: `我的性格测试报告：${result.value?.type || ''} ${typeInfo.value?.name || ''}`,
  query: buildSharedReportPath().split('?')[1] || '',
}))
</script>

<style lang="scss" scoped>
.mbti-result-page {
  min-height: 100vh;
  background:
    radial-gradient(90% 45% at 20% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  padding: 32rpx;
  padding-top: calc(32rpx + env(safe-area-inset-top));
  padding-bottom: calc(260rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.cyber-glow-bg-indigo {
  position: absolute;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, rgba(0, 0, 0, 0) 70%);
  top: -100rpx;
  right: -100rpx;
  pointer-events: none;
  z-index: 1;
}
.cyber-glow-bg-orange {
  position: absolute;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.035) 0%, rgba(0, 0, 0, 0) 70%);
  bottom: 200rpx;
  left: -200rpx;
  pointer-events: none;
  z-index: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 40rpx;
  z-index: 10;
}

.empty-icon-outer {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
}

.empty-icon {
  font-size: 110rpx;
  z-index: 2;
}

.empty-icon-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(99, 102, 241, 0.25);
  border-radius: 50%;
  filter: blur(24rpx);
  z-index: 1;
}

.empty-title {
  font-size: 38rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 16rpx;
}

.empty-desc {
  font-size: 26rpx;
  color: $text-secondary;
  margin-bottom: 64rpx;
}

.primary-btn {
  width: 320rpx;
  height: 88rpx;
  background: $grad-royal;
  color: #fff;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8rpx 24rpx rgba(99, 102, 241, 0.3);
  border: none;
}

.result-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.report-meta-card {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.98);
  border-radius: $radius-lg;
  padding: 24rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.student-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #EFF6FF;
  border: 1px solid rgba(37, 99, 235, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.student-avatar-text {
  font-size: 28rpx;
  font-weight: 900;
  color: $brand-primary;
}

.student-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.student-id {
  font-size: 27rpx;
  font-weight: 800;
  color: $text-primary;
}

.student-date {
  font-size: 22rpx;
  color: $text-muted;
}

.student-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6rpx;
  flex-shrink: 0;
}

.student-stat-label {
  font-size: 21rpx;
  color: $text-muted;
}

.student-stat-value {
  font-size: 25rpx;
  font-weight: 800;
  color: $text-primary;
}

// 结果头部
.result-header {
  @include glass-panel;
  position: relative;
  border-radius: $radius-xl;
  padding: 52rpx 40rpx 44rpx;
  text-align: left;
  overflow: hidden;
}

.header-glow {
  position: absolute;
  top: -150rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 350rpx;
  height: 350rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.14) 0%, rgba(0, 0, 0, 0) 70%);
  filter: blur(20rpx);
  pointer-events: none;
  z-index: 1;
}

.type-badge-wrap {
  position: relative;
  z-index: 2;
  flex-shrink: 0;
}

.type-badge {
  background: $grad-royal;
  border: none;
  border-radius: $radius-lg;
  padding: 18rpx 36rpx;
  font-size: 58rpx;
  font-weight: 900;
  color: #fff;
  letter-spacing: 0;
  box-shadow: 0 10rpx 24rpx rgba(37, 99, 235, 0.20);
}

.result-kicker {
  position: relative;
  z-index: 2;
  display: block;
  font-size: 28rpx;
  color: $text-secondary;
  font-weight: 700;
  margin-bottom: 22rpx;
}

.type-identity {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.type-copy {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}

.type-name {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: $text-primary;
  z-index: 2;
  position: relative;
}

.type-subtitle {
  font-size: 23rpx;
  font-weight: 700;
  color: $brand-primary;
}

.type-summary {
  position: relative;
  z-index: 2;
  display: block;
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.65;
  margin-bottom: 28rpx;
}

.type-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  z-index: 2;
  position: relative;
}

.tag {
  background: #EFF6FF;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: $radius-full;
  padding: 8rpx 24rpx;
  font-size: 23rpx;
  color: $text-secondary;
}

// 通用区块
.section {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border-radius: $radius-xl;
  padding: 40rpx 36rpx;
}

.section-header {
  margin-bottom: 36rpx;
}

.section-title-wrap {
  display: flex;
  align-items: center;
}

.title-dot {
  width: 8rpx;
  height: 24rpx;
  background: $brand-primary;
  border-radius: $radius-full;
  margin-right: 16rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 800;
  color: $text-primary;
  letter-spacing: 0;
}

.section-subtitle {
  display: block;
  font-size: 23rpx;
  color: $text-muted;
  line-height: 1.5;
  margin-top: 12rpx;
}

// 维度得分
.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 36rpx;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.dimension-labels {
  display: flex;
  justify-content: space-between;
}

.dim-label {
  font-size: 26rpx;
  color: $text-secondary;
  font-weight: 600;
  transition: all 0.3s;
}

.dim-label.active {
  color: $brand-primary;
}

.score-bar-wrap {
  position: relative;
}

.score-bar {
  height: 20rpx;
  background: $bg-input;
  border: 1px solid $border-light;
  border-radius: $radius-full;
  overflow: hidden;
  display: flex;
  position: relative;
}

.bar-fill {
  height: 100%;
  transition: width 0.6s ease;
  position: relative;
}

.bar-fill.left {
  background: $grad-royal;
  border-radius: $radius-full 0 0 $radius-full;
}

.bar-fill.right {
  background: $grad-accent;
  border-radius: 0 $radius-full $radius-full 0;
}

.bar-glow-dot {
  position: absolute;
  top: 0;
  width: 6rpx;
  height: 100%;
  background: #fff;
  filter: blur(2rpx);
  opacity: 0.9;
}

.bar-glow-dot.left {
  right: 0;
}

.bar-glow-dot.right {
  left: 0;
}

.score-values {
  display: flex;
  justify-content: space-between;
}

.score-value {
  font-size: 23rpx;
  color: $text-muted;
  font-weight: 500;
}

.score-value.active {
  color: $text-primary;
  font-weight: 700;
}

.axis-notes {
  margin-top: 36rpx;
  padding: 24rpx 24rpx;
  background: #F8FAFC;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.axis-note {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.axis-dot {
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: $brand-primary;
  margin-top: 14rpx;
  flex-shrink: 0;
}

.axis-note-text {
  flex: 1;
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.65;
}

// 性格特征
.feature-blocks {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
  margin-bottom: 34rpx;
}

.feature-block {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
}

.feature-icon {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #EFF6FF;
  border: 1px solid rgba(37, 99, 235, 0.16);
  color: $brand-primary;
  font-size: 23rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 4rpx;
}

.feature-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.feature-title {
  font-size: 27rpx;
  font-weight: 800;
  color: $text-primary;
}

.feature-text {
  font-size: 25rpx;
  color: $text-secondary;
  line-height: 1.7;
}

.traits-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.traits-list.compact {
  padding-top: 26rpx;
  border-top: 1px solid $border-light;
}

.trait-item {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
}

.trait-bullet-outer {
  margin-top: 14rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.trait-bullet {
  width: 10rpx;
  height: 10rpx;
  background: $brand-primary;
  border-radius: 50%;
}

.trait-text {
  flex: 1;
  font-size: 27rpx;
  color: $text-primary;
  line-height: 1.6;
  font-weight: 500;
}

// 职业方向
.careers-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.career-tag {
  background: #F8FAFC;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  padding: 14rpx 28rpx;
  font-size: 26rpx;
  color: $text-primary;
  font-weight: 600;
}

// 专业推荐
.majors-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.major-card {
  @include glass-panel;
  background: #FFFFFF;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  padding: 32rpx;
  position: relative;
  overflow: hidden;
  transition: all 0.25s;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 6rpx;
    background: $grad-royal;
    opacity: 0.8;
  }

  &:active {
    transform: scale(0.98);
    border-color: rgba(99, 102, 241, 0.3);
  }
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.major-name {
  font-size: 29rpx;
  font-weight: 800;
  color: $text-primary;
}

.major-stars {
  display: flex;
  gap: 4rpx;
}

.star-char {
  font-size: 23rpx;
  color: #CBD5E1;
}

.star-char.filled {
  color: #FBBF24;
}

.major-desc {
  display: block;
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.6;
  margin-bottom: 24rpx;
}

.major-insights {
  background: #F8FAFC;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  padding: 18rpx 20rpx;
  margin-bottom: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.major-insight-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.major-insight-label {
  width: 104rpx;
  flex-shrink: 0;
  font-size: 22rpx;
  font-weight: 800;
  color: $brand-primary;
}

.major-insight-text {
  flex: 1;
  font-size: 22rpx;
  color: $text-secondary;
  line-height: 1.45;
}

.major-footer {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.major-link {
  font-size: 23rpx;
  color: $brand-primary;
  font-weight: 700;
}

.arrow-icon {
  font-size: 20rpx;
  color: $brand-primary;
  transition: transform 0.2s;

  .major-card:active & {
    transform: translateX(6rpx);
  }
}

// 底部悬浮按钮
.footer-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  min-height: calc(190rpx + env(safe-area-inset-bottom));
  z-index: 50;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.footer-blur {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid $border-light;
  z-index: 1;
}

.footer-inner {
  position: relative;
  padding: 20rpx 32rpx 12rpx;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 2;
}

.footer-progress {
  display: block;
  text-align: center;
  font-size: 23rpx;
  color: $text-muted;
  margin-bottom: 14rpx;
}

.footer-btns {
  display: flex;
  gap: 18rpx;
}

.share-report-btn,
.share-test-btn {
  flex: 1;
  height: 84rpx;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.share-report-btn {
  background: #FFFFFF;
  color: #EF4444;
  border: 1px solid rgba(239, 68, 68, 0.28);
}

.share-test-btn {
  background: $grad-primary;
  color: #fff;
  box-shadow: 0 8rpx 18rpx rgba(239, 68, 68, 0.24);
}

.share-report-btn::after,
.share-test-btn::after,
.retry-link::after,
.upgrade-btn::after {
  border: none;
}

.retry-link {
  width: 100%;
  height: 48rpx;
  margin-top: 8rpx;
  background: transparent;
  color: $text-muted;
  border: none;
  font-size: 23rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

// 弹出确认窗
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(5, 7, 16, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid $border-light;
  border-radius: $radius-xl;
  padding: 56rpx 40rpx;
  width: 580rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-sizing: border-box;
}

.modal-header {
  position: relative;
  width: 120rpx;
  height: 120rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28rpx;
}

.modal-icon {
  font-size: 64rpx;
  z-index: 2;
}

.modal-warning-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(249, 115, 22, 0.25);
  border-radius: 50%;
  filter: blur(16rpx);
  z-index: 1;
}

.modal-title {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 20rpx;
  text-align: center;
}

.modal-desc {
  font-size: 25rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.7;
  margin-bottom: 48rpx;
}

.modal-actions {
  display: flex;
  gap: 20rpx;
  width: 100%;
}

.modal-btn {
  flex: 1;
  height: 84rpx;
  border-radius: $radius-full;
  font-size: 27rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
  transition: all 0.2s;

  &:active {
    transform: scale(0.97);
  }
}

.modal-btn.cancel {
  background: #F8FAFC;
  color: $text-primary;
  border: 1px solid $border-light;
}

.modal-btn.confirm {
  background: $grad-accent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.35);
}

// 版本标签
.version-label {
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  margin-bottom: 20rpx;

  &.basic {
    background: rgba(249, 115, 22, 0.12);
    border: 1px solid rgba(249, 115, 22, 0.3);
  }

  &.full {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
}

.version-label-text {
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 0;

  .basic & {
    color: #FB923C;
  }

  .full & {
    color: #34D399;
  }
}

// 升级按钮
.upgrade-btn {
  width: 100%;
  height: 72rpx;
  background: $grad-royal;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: $radius-full;
  font-size: 26rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 6rpx 16rpx rgba(99, 102, 241, 0.3);
  margin-bottom: 14rpx;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
  }
}
.upgrade-btn::after {
  border: none;
}
</style>
