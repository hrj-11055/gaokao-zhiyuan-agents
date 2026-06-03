<template>
  <view class="holland-result-page">
    <view class="page-bg" />

    <view class="result-content">
      <!-- 头部：核心结果卡片 -->
      <view class="header-card">
        <view class="brand-line" />
        <view class="header-inner">
          <view v-if="resultVersion" class="version-label" :class="resultVersion">
            <text class="version-label-text">{{ resultVersion === 'basic' ? '⚡ 精简版测评' : '🔬 完整版测评' }}</text>
          </view>
          
          <view class="code-title-wrap">
            <text class="code-title">{{ result.code }}</text>
          </view>
          <text class="type-name">{{ typeInfo.name }}</text>
          
          <view class="type-tags">
            <text v-for="(tag, idx) in typeInfo.tags" :key="idx" class="tag">{{ tag }}</text>
          </view>
        </view>
      </view>

      <!-- 综合表现：雷达图与表格 -->
      <view class="section">
        <view class="section-header-center">
          <text class="section-title">综合表现</text>
        </view>
        
        <!-- 雷达图 -->
        <view class="score-scale-tip">
          <text class="scale-tip-text">{{ scoreScaleTip }}</text>
        </view>
        <view class="radar-container">
          <image class="radar-chart" :src="radarChartUrl" mode="aspectFit" />
        </view>

        <!-- 数据表格 -->
        <view class="data-table">
          <view class="table-header">
            <text class="th">兴趣维度</text>
            <text class="th">原始得分</text>
            <text class="th">本版满分</text>
          </view>
          <view class="table-row" v-for="dim in sortedDimensions" :key="dim.type">
            <text class="td font-medium">{{ dim.label }}({{ dim.type }})</text>
            <text class="td score-text">{{ dim.score }}</text>
            <text class="td text-light">{{ dim.maxScoreText }}</text>
          </view>
        </view>
      </view>

      <!-- 多维特质分析 -->
      <view class="section">
        <view class="section-header-center">
          <text class="section-title">特质分析</text>
        </view>
        
        <!-- 单维度解析 -->
        <view class="trait-group" v-for="dim in topDimensions" :key="dim.name">
          <view class="trait-group-title">
            <text class="trait-title-text">{{ dim.name }}</text>
          </view>
          <view class="trait-list">
            <view class="trait-row" v-for="(t, idx) in dim.traits" :key="idx">
              <view class="trait-bullet" />
              <text class="trait-text">{{ t }}</text>
            </view>
          </view>
        </view>
        
        <view class="trait-divider" />
        
        <!-- 综合解析 -->
        <view class="trait-group">
          <view class="trait-group-title">
            <text class="trait-title-text highlight">整体综合特质</text>
          </view>
          <view class="trait-list">
            <view class="trait-row" v-for="(t, idx) in typeInfo.traits" :key="idx">
              <view class="trait-bullet highlight" />
              <text class="trait-text">{{ t }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 职业方向推荐 -->
      <view class="section">
        <view class="section-header-center">
          <text class="section-title">职业方向推荐</text>
        </view>
        <view class="career-list">
          <view class="career-item" v-for="(career, idx) in typeInfo.careers" :key="idx">
            <view class="career-dot" />
            <text class="career-text">{{ career }}</text>
          </view>
        </view>
      </view>

      <!-- 专业推荐 -->
      <view class="section">
        <view class="section-header-center">
          <text class="section-title">专业推荐</text>
        </view>
        <view class="majors-list">
          <view v-for="(major, idx) in majorCards" :key="major.name" class="major-card" @click="viewMajorDetail(major.name)">
            <view class="major-header">
              <text class="major-name">{{ major.name }}</text>
              <view class="major-stars">
                <text v-for="s in 5" :key="s" class="star-char" :class="{ filled: s <= (5 - Math.floor(idx / 2)) }">★</text>
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
          </view>
        </view>
      </view>

      <!-- 底部悬浮按钮 -->
      <view class="footer-bar">
        <view class="footer-blur" />
        <view class="footer-btns">
          <button v-if="resultVersion === 'basic'" class="upgrade-btn" @click="handleUpgrade">🔬 升级到完整版 (60题)</button>
          <button class="retry-btn" @click="retry">重新测试</button>
        </view>
      </view>
    </view>

    <!-- 确认弹窗 -->
    <view v-if="showConfirm" class="modal-overlay" @click="showConfirm = false">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <view class="modal-icon">⚠️</view>
        </view>
        <text class="modal-title">重新进行职业兴趣测试？</text>
        <text class="modal-desc">重新测试会清除当前霍兰德结果和答题进度，确认后需要重新作答。</text>
        <view class="modal-actions">
          <button class="modal-btn cancel" @click="showConfirm = false">取消返回</button>
          <button class="modal-btn confirm" @click="confirmRetry">确认重设</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadAssessments, saveAssessments } from '../../utils/storage.js'
import {
  HOLLAND_RESULT_REPORTS,
  HOLLAND_TYPE_LABELS,
  HOLLAND_DIMENSION_TRAITS,
  getHollandDimensionMaxScores,
  getHollandMaxScore
} from '../../data/holland-questions.js'
import { fetchMajorInsights } from '../../api/majorInsights.js'
import { buildMajorCards, normalizeMajorName } from '../../data/major-learning-profiles.js'
import { useReportPregen } from '../../composables/useReportPregen.js'

const { tryTriggerPregenerate } = useReportPregen()

const result = ref({
  code: '',
  scores: { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 }
})
const resultVersion = ref('')
const majorInsights = ref({})

const showConfirm = ref(false)

// 维度标签映射
const dimensionLabels = HOLLAND_TYPE_LABELS

const hollandDimensionMaxScores = computed(() => getHollandDimensionMaxScores(resultVersion.value))
const hollandMaxScore = computed(() => getHollandMaxScore(resultVersion.value))
const resultModeName = computed(() => resultVersion.value === 'basic' ? '精简版' : '完整版')
const scoreScaleTip = computed(() => `${resultModeName.value}雷达图按本版满分 ${hollandMaxScore.value} 分绘制`)

// 排序后的维度（按分数降序）
const sortedDimensions = computed(() => {
  return Object.entries(result.value.scores)
    .map(([type, score]) => ({
      type,
      label: dimensionLabels[type],
      score,
      maxScore: hollandDimensionMaxScores.value[type] || hollandMaxScore.value,
      maxScoreText: String(hollandDimensionMaxScores.value[type] || hollandMaxScore.value)
    }))
    .sort((a, b) => b.score - a.score)
})

// 获取前三个维度的单项解析
const topDimensions = computed(() => {
  const code = result.value.code || ''
  const dims = []
  for (let i = 0; i < code.length; i++) {
    const letter = code[i]
    if (HOLLAND_DIMENSION_TRAITS[letter]) {
      dims.push(HOLLAND_DIMENSION_TRAITS[letter])
    }
  }
  return dims
})

// 生成 SVG 雷达图 Data URI
const radarChartUrl = computed(() => {
  const scores = result.value.scores || {}
  const cx = 120
  const cy = 120
  const radius = 82
  const order = ['R', 'I', 'A', 'S', 'E', 'C']
  const labels = ['实用型R', '研究型I', '艺术型A', '社会型S', '企业型E', '常规型C']
  const maxScores = hollandDimensionMaxScores.value
  const fallbackMaxScore = hollandMaxScore.value
  
  let dataPtsStr = ''
  let circlesSvg = ''
  let scoreLabelsSvg = ''
  
  order.forEach((key, i) => {
    const maxScore = maxScores[key] || fallbackMaxScore
    const score = Math.min(Number(scores[key]) || 0, maxScore)
    const r = (score / maxScore) * radius
    // 旋转-90度，让 R 在最上方
    const angle = (Math.PI / 180) * (i * 60 - 90)
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    dataPtsStr += `${x},${y} `
    circlesSvg += `<circle cx="${x}" cy="${y}" r="5.2" fill="#2563EB" stroke="#FFFFFF" stroke-width="2.4"/>`
  })

  // 背景网格
  let gridSvg = ''
  for(let step = 1; step <= 5; step++) {
    const r = (step / 5) * radius
    let pts = ''
    order.forEach((_, i) => {
      const angle = (Math.PI / 180) * (i * 60 - 90)
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      pts += `${x},${y} `
    })
    gridSvg += `<polygon points="${pts.trim()}" fill="${step === 5 ? '#F8FBFF' : 'none'}" stroke="#CBD5E1" stroke-width="${step === 5 ? 1.6 : 1.1}" stroke-dasharray="${step === 5 ? '0' : '4,4'}"/>`
  }

  // 辐射轴线
  let axesSvg = ''
  order.forEach((_, i) => {
    const angle = (Math.PI / 180) * (i * 60 - 90)
    const x = cx + radius * Math.cos(angle)
    const y = cy + radius * Math.sin(angle)
    axesSvg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#CBD5E1" stroke-width="1.2"/>`
  })

  // 标签
  let labelsSvg = ''
  order.forEach((key, i) => {
    const label = labels[i]
    const angle = (Math.PI / 180) * (i * 60 - 90)
    const x = cx + (radius + 30) * Math.cos(angle)
    const y = cy + (radius + 30) * Math.sin(angle)
    
    let anchor = "middle"
    if (x > cx + 5) anchor = "start"
    else if (x < cx - 5) anchor = "end"
    
    const isPrimary = result.value.code.includes(key)
    const fill = isPrimary ? '#2563EB' : '#64748B'
    const fontWeight = isPrimary ? 'bold' : 'normal'
    const score = Math.min(Number(scores[key]) || 0, maxScores[key] || fallbackMaxScore)
    const maxScore = maxScores[key] || fallbackMaxScore
    
    labelsSvg += `<text x="${x}" y="${y - 2}" font-size="12.5" font-weight="${fontWeight}" fill="${fill}" text-anchor="${anchor}">${label}</text>`
    scoreLabelsSvg += `<text x="${x}" y="${y + 13}" font-size="10.5" font-weight="700" fill="${isPrimary ? '#2563EB' : '#94A3B8'}" text-anchor="${anchor}">${score}/${maxScore}</text>`
  })

  const svg = `<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
    ${gridSvg}
    ${axesSvg}
    <polygon points="${dataPtsStr.trim()}" fill="rgba(37, 99, 235, 0.28)" stroke="#2563EB" stroke-width="4" stroke-linejoin="round"/>
    ${circlesSvg}
    ${labelsSvg}
    ${scoreLabelsSvg}
  </svg>`

  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
})

// 类型信息
const typeInfo = computed(() => {
  const code = result.value.code
  if (HOLLAND_RESULT_REPORTS[code]) {
    return HOLLAND_RESULT_REPORTS[code]
  }
  const twoLetterCode = code.substring(0, 2)
  for (const [key, value] of Object.entries(HOLLAND_RESULT_REPORTS)) {
    if (key.startsWith(twoLetterCode)) {
      return value
    }
  }
  return {
    name: '职业兴趣类型',
    tags: ['职业', '兴趣', '探索'],
    traits: ['请完成完整测试获取详细分析'],
    careers: ['请完成完整测试获取详细推荐'],
    majors: ['请完成完整测试获取详细推荐']
  }
})

const recommendedMajorNames = computed(() => (
  buildMajorCards(typeInfo.value.majors || []).map((major) => major.name)
))

const majorCards = computed(() => {
  return buildMajorCards(typeInfo.value.majors || [], majorInsights.value)
})

async function loadMajorInsightsForResult() {
  const names = recommendedMajorNames.value
  if (names.length === 0 || !result.value.code) {
    majorInsights.value = {}
    return
  }

  try {
    const insights = await fetchMajorInsights(names)
    majorInsights.value = Object.fromEntries(
      insights.map((item) => [normalizeMajorName(item.requestedName || item.name), item])
    )
  } catch {
    majorInsights.value = {}
  }
}

function formatList(items = []) {
  return items.slice(0, 4).join('、')
}

function viewMajorDetail(major) {
  const params = encodeURIComponent(major)
  uni.navigateTo({
    url: `/pages/major-detail/major-detail?name=${params}&source=holland&type=${result.value.code}`
  })
}

function retry() {
  showConfirm.value = true
}

function confirmRetry() {
  const assessments = loadAssessments()
  assessments.holland = {
    completed: false,
    version: '',
    code: '',
    scores: { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 },
    answers: [],
    questionIndex: 0,
    completedAt: 0
  }
  saveAssessments(assessments)
  showConfirm.value = false
  uni.redirectTo({
    url: '/pages/holland/holland'
  })
}

function handleUpgrade() {
  const assessments = loadAssessments()
  assessments.holland = {
    completed: false,
    version: 'full',
    code: '',
    scores: { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 },
    answers: [],
    questionIndex: 0,
    completedAt: 0
  }
  saveAssessments(assessments)
  uni.redirectTo({
    url: '/pages/holland/holland'
  })
}

onShow(() => {
  const assessments = loadAssessments()
  if (!assessments.holland.completed) {
    uni.showToast({ title: '请先完成测评', icon: 'none' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/holland/holland' })
    }, 1500)
    return
  }
  result.value = {
    code: assessments.holland.code,
    scores: assessments.holland.scores
  }
  resultVersion.value = assessments.holland.version || 'full'
  loadMajorInsightsForResult()
  uni.setNavigationBarTitle({ title: '霍兰德测评结果' })
  tryTriggerPregenerate()
})
</script>

<style lang="scss" scoped>
.holland-result-page {
  min-height: 100vh;
  background: #F4F7FA; // 参考图极简冷灰蓝背景
  padding: 32rpx;
  padding-bottom: calc(160rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
}

.page-bg {
  position: fixed;
  top: 0; left: 0; right: 0; height: 50vh;
  background: linear-gradient(180deg, #EBF3FF 0%, #F4F7FA 100%);
  z-index: 0;
}

.result-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

// 头部主卡片
.header-card {
  background: #FFFFFF;
  border-radius: $radius-xl;
  box-shadow: 0 4rpx 20rpx rgba(37, 99, 235, 0.04);
  position: relative;
  overflow: hidden;
  padding: 50rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;

  .brand-line {
    position: absolute;
    left: 0;
    top: 40rpx;
    bottom: 40rpx;
    width: 8rpx;
    background: $brand-primary;
    border-radius: 0 8rpx 8rpx 0;
  }
  
  .header-inner {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
}

.code-title-wrap {
  margin-bottom: 12rpx;
}

.code-title {
  font-size: 72rpx;
  font-weight: 900;
  color: $brand-primary;
  letter-spacing: 2rpx;
  font-family: 'SF Pro Display', -apple-system, sans-serif;
}

.type-name {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 24rpx;
}

.type-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16rpx;
}

.tag {
  background: rgba(37, 99, 235, 0.06);
  color: $brand-primary;
  font-size: 24rpx;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  font-weight: 600;
}

// 通用版块
.section {
  background: #FFFFFF;
  border-radius: $radius-xl;
  box-shadow: 0 4rpx 20rpx rgba(37, 99, 235, 0.04);
  padding: 40rpx 32rpx;
}

.section-header-center {
  display: flex;
  justify-content: center;
  margin-bottom: 40rpx;
  position: relative;
  
  &::before, &::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 80rpx;
    height: 1px;
    background: #E2E8F0;
  }
  &::before { left: 80rpx; }
  &::after { right: 80rpx; }
}

.section-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #FFFFFF;
  background: $brand-primary;
  padding: 8rpx 40rpx;
  border-radius: $radius-full;
  position: relative;
  z-index: 2;
  box-shadow: 0 4rpx 12rpx rgba(37, 99, 235, 0.2);
}

// 雷达图与表格
.score-scale-tip {
  display: flex;
  justify-content: center;
  margin: -8rpx 0 18rpx;
}

.scale-tip-text {
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  background: #EFF6FF;
  color: #2563EB;
  font-size: 22rpx;
  font-weight: 700;
  border: 1px solid #DBEAFE;
}

.radar-container {
  width: 100%;
  height: 470rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 32rpx;
}

.radar-chart {
  width: 100%;
  height: 100%;
}

.data-table {
  width: 100%;
  border: 1px solid #E2E8F0;
  border-radius: $radius-lg;
  overflow: hidden;
}

.table-header {
  display: flex;
  background: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;
}

.th {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 24rpx;
  color: $text-secondary;
  font-weight: 700;
}

.table-row {
  display: flex;
  border-bottom: 1px solid #F1F5F9;
  &:last-child { border-bottom: none; }
}

.td {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 26rpx;
  color: $text-primary;
}

.font-medium { font-weight: 600; }
.text-light { color: #94A3B8; }
.score-text { color: $brand-primary; font-weight: 700; }

// 特质分析
.trait-group {
  margin-bottom: 32rpx;
  &:last-child { margin-bottom: 0; }
}

.trait-group-title {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
}

.trait-title-text {
  font-size: 30rpx;
  font-weight: 800;
  color: $brand-primary;
  position: relative;
  padding-left: 20rpx;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 6rpx;
    height: 24rpx;
    background: $brand-primary;
    border-radius: 4rpx;
  }

  &.highlight { color: #F59E0B; }
  &.highlight::before { background: #F59E0B; }
}

.trait-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding-left: 20rpx;
}

.trait-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.trait-bullet {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #94A3B8;
  margin-top: 14rpx;
  flex-shrink: 0;
  &.highlight { background: #F59E0B; }
}

.trait-text {
  font-size: 26rpx;
  color: $text-primary;
  line-height: 1.6;
}

.trait-divider {
  height: 1px;
  background: #E2E8F0;
  margin: 32rpx 0;
}

// 职业推荐列表
.career-list {
  background: #F8FAFC;
  border-radius: $radius-lg;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.career-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.career-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: $brand-primary;
  opacity: 0.8;
}

.career-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

// 专业推荐
.majors-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.major-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
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
    background: #F59E0B;
  }

  &:active {
    transform: scale(0.98);
    background: #F8FAFC;
  }
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.major-name {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
}

.major-stars {
  display: flex;
  gap: 4rpx;
}

.star-char {
  font-size: 24rpx;
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
  border: 1px solid #E2E8F0;
  border-radius: $radius-md;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
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
  line-height: 1.5;
}

// 底部悬浮按钮与弹窗
.footer-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(120rpx + env(safe-area-inset-bottom));
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
  border-top: 1px solid #E2E8F0;
  z-index: 1;
}

.footer-btns {
  position: relative;
  padding: 0 32rpx;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 2;
}

.retry-btn {
  width: 100%;
  height: 84rpx;
  background: #FFFFFF;
  color: $text-primary;
  border: 1px solid #E2E8F0;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;

  &:active {
    background: #F1F5F9;
  }
}

.retry-btn::after {
  border: none;
}

.upgrade-btn {
  width: 100%;
  height: 84rpx;
  background: $brand-primary;
  color: #fff;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16rpx;
}
.upgrade-btn::after { border: none; }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  margin: 32rpx;
  text-align: center;
  width: 80%;
}

.modal-icon { font-size: 80rpx; margin-bottom: 16rpx; }
.modal-title { display: block; font-size: 32rpx; font-weight: 600; color: $text-primary; margin-bottom: 12rpx; }
.modal-desc { display: block; font-size: 26rpx; color: $text-secondary; line-height: 1.6; margin-bottom: 32rpx; }
.modal-actions { display: flex; gap: 16rpx; }
.modal-btn { flex: 1; height: 80rpx; font-size: 28rpx; border-radius: $radius-md; border: none; }
.modal-btn::after { border: none; }
.modal-btn.cancel { background: #F1F5F9; color: $text-secondary; }
.modal-btn.confirm { background: $brand-primary; color: #fff; }

.version-label {
  display: inline-flex;
  padding: 6rpx 20rpx;
  border-radius: $radius-full;
  margin-bottom: 16rpx;
  &.basic { background: rgba(249, 115, 22, 0.1); border: 1px solid rgba(249, 115, 22, 0.2); }
  &.full { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); }
}
.version-label-text {
  font-size: 22rpx; font-weight: 700;
  .basic & { color: #EA580C; }
  .full & { color: #059669; }
}
</style>
