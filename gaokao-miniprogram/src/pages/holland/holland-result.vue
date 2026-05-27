<template>
  <view class="holland-result-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-orange" />
    <view class="cyber-glow-bg-violet" />

    <!-- 结果内容 -->
    <view class="result-content">
      <!-- 结果头部 - 玻璃面板与炫金渐变 -->
      <view class="result-header">
        <view class="header-glow" />
        <view v-if="resultVersion" class="version-label" :class="resultVersion">
          <text class="version-label-text">{{ resultVersion === 'basic' ? '⚡ 精简版测评' : '🔬 完整版测评' }}</text>
        </view>
        <view class="code-badge-wrap">
          <view class="code-badge">{{ result.code }}</view>
        </view>
        <text class="type-name">{{ typeInfo.name }}</text>
        <view class="type-tags">
          <text v-for="(tag, idx) in typeInfo.tags" :key="idx" class="tag">{{ tag }}</text>
        </view>
      </view>

      <!-- 维度得分 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">RIASEC 六维兴趣结果</text>
          </view>
        </view>
        <view class="dimensions-list">
          <view v-for="dim in sortedDimensions" :key="dim.type" class="dimension-item" :class="'dim-' + dim.type.toLowerCase()">
            <view class="dimension-header">
              <view class="dim-label-wrap">
                <view class="dim-bullet" />
                <text class="dimension-label">{{ dim.label }} ({{ dim.type }})</text>
              </view>
              <text class="dimension-score">{{ dim.score }} 分</text>
            </view>
            <view class="score-bar-wrap">
              <view class="score-bar">
                <view class="score-fill" :style="{ width: getPercent(dim.score) }">
                  <view class="score-glow-dot" />
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 性格特征 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">主要兴趣特征</text>
          </view>
        </view>
        <view class="traits-list">
          <view v-for="(trait, idx) in typeInfo.traits" :key="idx" class="trait-item">
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
            <text class="section-title">适合关注的职业方向</text>
          </view>
        </view>
        <view class="careers-grid">
          <text v-for="(career, idx) in typeInfo.careers" :key="idx" class="career-tag">
            {{ career }}
          </text>
        </view>
      </view>

      <!-- 专业推荐 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">可优先了解的专业</text>
          </view>
        </view>
        <view class="majors-list">
          <view v-for="(major, idx) in majorCards" :key="major.name" class="major-card" @click="viewMajorDetail(major.name)">
            <view class="major-header">
              <text class="major-name">{{ major.name }}</text>
              <view class="major-stars">
                <text v-for="s in 5" :key="s" class="star-char" :class="{ filled: s <= (5 - Math.floor(idx / 2)) }">★</text>
              </view>
            </view>
            <text class="major-desc">{{ major.insight?.summary || getMajorDesc(major.name) }}</text>
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

      <!-- 底部按钮 -->
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
          <view class="modal-warning-glow" />
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
import { HOLLAND_TYPE_DESCRIPTIONS, HOLLAND_TYPE_LABELS } from '../../data/holland-questions.js'
import { fetchMajorInsights } from '../../api/majorInsights.js'

const result = ref({
  code: '',
  scores: { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 }
})
const resultVersion = ref('')
const majorInsights = ref({})

const showConfirm = ref(false)

// 维度标签映射
const dimensionLabels = HOLLAND_TYPE_LABELS

// 排序后的维度（按分数降序）
const sortedDimensions = computed(() => {
  return Object.entries(result.value.scores)
    .map(([type, score]) => ({
      type,
      label: dimensionLabels[type],
      score
    }))
    .sort((a, b) => b.score - a.score)
})

// 类型信息
const typeInfo = computed(() => {
  const code = result.value.code
  if (HOLLAND_TYPE_DESCRIPTIONS[code]) {
    return HOLLAND_TYPE_DESCRIPTIONS[code]
  }
  // 如果没有精确匹配，使用前两个字母匹配
  const twoLetterCode = code.substring(0, 2)
  for (const [key, value] of Object.entries(HOLLAND_TYPE_DESCRIPTIONS)) {
    if (key.startsWith(twoLetterCode)) {
      return value
    }
  }
  // 默认返回
  return {
    name: '职业兴趣类型',
    tags: ['职业', '兴趣', '探索'],
    traits: ['请完成完整测试获取详细分析'],
    careers: ['请完成完整测试获取详细推荐'],
    majors: ['请完成完整测试获取详细推荐']
  }
})

const majorCards = computed(() => {
  return (typeInfo.value.majors || []).map((name) => ({
    name,
    insight: majorInsights.value[name] || null,
  }))
})

// 获取百分比
function getPercent(score) {
  const maxScore = 40 // 每个类型最高40分（10题×4分）
  return Math.min((score / maxScore) * 100, 100) + '%'
}

// 获取专业描述
function getMajorDesc(major) {
  const descs = {
    '工业设计': '结合技术与艺术的交叉学科',
    '建筑学': '空间设计与建筑艺术的融合',
    '服装设计与工程': '时尚创意与工程技术结合',
    '产品设计': '从创意到产品的完整设计流程',
    '康复治疗学': '通过技术手段帮助患者康复',
    '生物医学工程': '工程技术在医学领域的应用',
    '风景园林': '户外空间规划与景观设计',
    '环境设计': '创造宜居的生活与工作环境',
    '工商管理': '企业管理与商业运作综合学科',
    '项目管理': '高效达成目标的管理方法',
    '质量管理工程': '确保产品与服务质量的体系',
    '心理学': '探索人类心理与行为规律',
    '社会学': '研究社会结构与社会关系',
    '教育学': '教学理论与教育实践的结合'
  }
  return descs[major] || '相关专业课程，适合该兴趣类型发展'
}

async function loadMajorInsightsForResult() {
  const names = typeInfo.value.majors || []
  if (names.length === 0 || !result.value.code) {
    majorInsights.value = {}
    return
  }

  try {
    const insights = await fetchMajorInsights(names)
    majorInsights.value = Object.fromEntries(
      insights.map((item) => [item.requestedName || item.name, item])
    )
  } catch {
    majorInsights.value = {}
  }
}

function formatList(items = []) {
  return items.slice(0, 4).join('、')
}

// 查看专业详情
function viewMajorDetail(major) {
  const params = encodeURIComponent(major)
  uni.navigateTo({
    url: `/pages/major-detail/major-detail?name=${params}&source=holland&type=${result.value.code}`
  })
}

// 重新测试
function retry() {
  showConfirm.value = true
}

// 确认重测
function confirmRetry() {
  showConfirm.value = false
  uni.redirectTo({
    url: '/pages/holland/holland'
  })
}

// 升级到完整版
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

// 页面显示时检查并加载结果
onShow(() => {
  const assessments = loadAssessments()
  if (!assessments.holland.completed) {
    uni.showToast({
      title: '请先完成测评',
      icon: 'none'
    })
    setTimeout(() => {
      uni.redirectTo({
        url: '/pages/holland/holland'
      })
    }, 1500)
    return
  }
  result.value = {
    code: assessments.holland.code,
    scores: assessments.holland.scores
  }
  resultVersion.value = assessments.holland.version || 'full'
  loadMajorInsightsForResult()
  uni.setNavigationBarTitle({
    title: '霍兰德测评结果'
  })
})
</script>

<style lang="scss" scoped>
.holland-result-page {
  min-height: 100vh;
  background:
    radial-gradient(90% 45% at 20% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  padding: 32rpx;
  padding-bottom: calc(160rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

.cyber-glow-bg-orange {
  position: fixed;
  top: -10%;
  right: -20%;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.04) 0%, rgba(0, 0, 0, 0) 70%);
  z-index: 0;
  pointer-events: none;
}

.cyber-glow-bg-violet {
  position: fixed;
  bottom: -10%;
  left: -20%;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.05) 0%, rgba(0, 0, 0, 0) 70%);
  z-index: 0;
  pointer-events: none;
}

.result-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.result-header {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid $border-light;
  border-radius: $radius-xl;
  padding: 56rpx 32rpx;
  text-align: center;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;

  .header-glow {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 250rpx;
    height: 250rpx;
    background: radial-gradient(circle, rgba(249, 115, 22, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
    filter: blur(20px);
    z-index: 0;
  }
}

.code-badge-wrap {
  display: inline-block;
  padding: 6rpx;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.4) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: $radius-lg;
  box-shadow: 0 10rpx 24rpx rgba(249, 115, 22, 0.18);
  margin-bottom: 24rpx;
  z-index: 1;
}

.code-badge {
  background: linear-gradient(135deg, #FF6B00 0%, #EA580C 100%);
  color: #fff;
  font-size: 56rpx;
  font-weight: 800;
  padding: 16rpx 48rpx;
  border-radius: calc($radius-lg - 6rpx);
  letter-spacing: 0;
}

.type-name {
  display: block;
  font-size: 38rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 20rpx;
  z-index: 1;
}

.type-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12rpx;
  z-index: 1;
}

.tag {
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.2);
  color: $brand-primary-light;
  font-size: 24rpx;
  padding: 8rpx 20rpx;
  border-radius: $radius-full;
  font-weight: 600;
}

.section {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
}

.section-header {
  margin-bottom: 32rpx;
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.title-dot {
  width: 8rpx;
  height: 28rpx;
  background: $grad-accent;
  border-radius: $radius-full;
}

.section-title {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
}

// 维度得分
.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dim-label-wrap {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.dim-bullet {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
}

.dimension-label {
  font-size: 27rpx;
  font-weight: 700;
  color: $text-primary;
}

.dimension-score {
  font-size: 26rpx;
  font-weight: 800;
}

.score-bar-wrap {
  position: relative;
  width: 100%;
}

.score-bar {
  height: 16rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
  position: relative;
  border: 1px solid $border-light;
}

.score-fill {
  height: 100%;
  border-radius: $radius-full;
  transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
}

.score-glow-dot {
  position: absolute;
  right: 0;
  top: 0;
  width: 6rpx;
  height: 100%;
  background: #fff;
  filter: blur(2rpx);
  opacity: 0.9;
}

// R 实际型 - 橙色
.dim-r {
  .dim-bullet { background: #FF6B00; }
  .dimension-score { color: #FF8F3D; }
  .score-fill { background: linear-gradient(90deg, rgba(255, 107, 0, 0.2), #FF6B00); }
}

// I 研究型 - 蓝色
.dim-i {
  .dim-bullet { background: #3B82F6; }
  .dimension-score { color: #60A5FA; }
  .score-fill { background: linear-gradient(90deg, rgba(59, 130, 246, 0.2), #3B82F6); }
}

// A 艺术型 - 粉色
.dim-a {
  .dim-bullet { background: #EC4899; }
  .dimension-score { color: #F472B6; }
  .score-fill { background: linear-gradient(90deg, rgba(236, 72, 153, 0.2), #EC4899); }
}

// S 社会型 - 绿色
.dim-s {
  .dim-bullet { background: #10B981; }
  .dimension-score { color: #34D399; }
  .score-fill { background: linear-gradient(90deg, rgba(16, 185, 129, 0.2), #10B981); }
}

// E 企业型 - 金黄
.dim-e {
  .dim-bullet { background: #F59E0B; }
  .dimension-score { color: #FBBF24; }
  .score-fill { background: linear-gradient(90deg, rgba(245, 158, 11, 0.2), #F59E0B); }
}

// C 传统型 - 紫色
.dim-c {
  .dim-bullet { background: #8B5CF6; }
  .dimension-score { color: #A78BFA; }
  .score-fill { background: linear-gradient(90deg, rgba(139, 92, 246, 0.2), #8B5CF6); }
}

// 性格特征
.traits-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
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

// 适合职业方向
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
    background: $grad-accent;
    opacity: 0.8;
  }

  &:active {
    transform: scale(0.98);
    border-color: rgba(249, 115, 22, 0.3);
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
  color: $brand-primary-light;
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
  color: $brand-primary-light;
  font-weight: 700;
}

.arrow-icon {
  font-size: 20rpx;
  color: $brand-primary-light;
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
  border-top: 1px solid $border-light;
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
  background: #F8FAFC;
  color: $text-primary;
  border: 1px solid $border-light;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
    background: rgba(255, 255, 255, 0.08);
  }
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

.modal-content,
.confirm-content {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  margin: 32rpx;
  text-align: center;
}

.modal-icon,
.confirm-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}

.modal-title,
.confirm-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.modal-desc,
.confirm-desc {
  display: block;
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.6;
  margin-bottom: 32rpx;
}

.modal-actions,
.confirm-actions {
  display: flex;
  gap: 16rpx;
}

.modal-btn,
.confirm-btn {
  flex: 1;
  height: 80rpx;
  font-size: 28rpx;
  font-weight: 500;
  border: none;
  border-radius: $radius-md;
}

.modal-btn::after,
.confirm-btn::after {
  border: none;
}

.modal-btn.cancel,
.confirm-btn.cancel {
  background: $bg-input;
  color: $text-secondary;
}

.modal-btn.confirm,
.confirm-btn.confirm {
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
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
  height: 84rpx;
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
  margin-bottom: 16rpx;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
  }
}
.upgrade-btn::after {
  border: none;
}
</style>
