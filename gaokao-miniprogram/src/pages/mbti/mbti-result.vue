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
      <text class="empty-desc">请先完成 MBTI 性格测试</text>
      <button class="primary-btn" @click="goBack">前往测试</button>
    </view>

    <!-- 结果内容 -->
    <view v-else class="result-content">
      <!-- 结果头部 - 渐变背景 -->
      <view class="result-header">
        <view class="header-glow" />
        <view v-if="resultVersion" class="version-label" :class="resultVersion">
          <text class="version-label-text">{{ resultVersion === 'basic' ? '⚡ 精简版测评' : '🔬 完整版测评' }}</text>
        </view>
        <view class="type-badge-wrap">
          <view class="type-badge">{{ result.type }}</view>
        </view>
        <text class="type-name">{{ typeInfo?.name || '' }}</text>
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
      </view>

      <!-- 性格特征 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" />
            <text class="section-title">性格特征</text>
          </view>
        </view>
        <view class="traits-list">
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
            <text class="section-title">适合关注的职业方向</text>
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
            <text class="section-title">可优先了解的专业</text>
          </view>
        </view>
        <view class="majors-list">
          <view v-for="(major, index) in majorCards" :key="major.name" class="major-card" @click="viewMajorDetail(major.name)">
            <view class="major-header">
              <text class="major-name">{{ major.name }}</text>
              <view class="major-stars">
                <text v-for="s in 5" :key="s" class="star-char" :class="{ filled: s <= (5 - Math.floor(index / 2)) }">★</text>
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

      <!-- 底部操作区域 -->
      <view class="footer-bar">
        <view class="footer-blur" />
        <view class="footer-btns">
          <button v-if="resultVersion === 'basic'" class="upgrade-btn" @click="handleUpgrade">🔬 升级到完整版 (48题)</button>
          <button class="retry-btn" @click="handleRetry">重新测试</button>
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
        <text class="modal-title">重新进行 MBTI 测试？</text>
        <text class="modal-desc">重新测试会清除当前 MBTI 结果和答题进度，确认后需要重新作答。</text>
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
import { onShow } from '@dcloudio/uni-app'
import { loadAssessments, saveAssessments } from '../../utils/storage.js'
import { MBTI_TYPE_DESCRIPTIONS } from '../../data/mbti-questions.js'
import { fetchMajorInsights } from '../../api/majorInsights.js'

const result = ref(null)
const resultVersion = ref('')
const showConfirmModal = ref(false)
const majorInsights = ref({})

// 维度配置
const dimensions = {
  EI: { left: 'E', right: 'I', leftLabel: '外向 (E)', rightLabel: '内向 (I)' },
  SN: { left: 'S', right: 'N', leftLabel: '实感 (S)', rightLabel: '直觉 (N)' },
  TF: { left: 'T', right: 'F', leftLabel: '思考 (T)', rightLabel: '情感 (F)' },
  JP: { left: 'J', right: 'P', leftLabel: '判断 (J)', rightLabel: '感知 (P)' }
}

// 类型信息
const typeInfo = computed(() => {
  if (!result.value?.type) return null
  return MBTI_TYPE_DESCRIPTIONS[result.value.type] || null
})

const majorCards = computed(() => {
  return (typeInfo.value?.majors || []).map((name) => ({
    name,
    insight: majorInsights.value[name] || null,
  }))
})

// 加载结果
function loadResult() {
  const assessments = loadAssessments()
  if (assessments.mbti?.completed) {
    result.value = {
      type: assessments.mbti.type,
      scores: assessments.mbti.scores
    }
    resultVersion.value = assessments.mbti.version || 'full'
  } else {
    result.value = null
    resultVersion.value = ''
  }
}

async function loadMajorInsightsForResult() {
  const names = typeInfo.value?.majors || []
  if (names.length === 0) {
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

// 专业描述（简化版）
function getMajorDesc(major) {
  const descMap = {
    '计算机科学与技术': '研究计算机系统、软件开发与人工智能',
    '数学': '研究数量、结构、空间等基础概念',
    '物理学': '研究物质、能量及其相互作用',
    '哲学': '探讨存在、知识、价值等根本问题',
    '经济学': '研究资源配置与经济运行规律',
    '建筑学': '结合艺术与技术的建筑设计与规划',
    '化学': '研究物质的组成、结构、性质与变化',
    '生物学': '研究生命现象与生命活动规律',
    '逻辑学': '研究思维形式与推理规律',
    '工商管理': '企业管理与运营的综合学科',
    '法学': '法律规范与法律制度的研究',
    '金融学': '资金融通与金融市场研究',
    '国际关系': '国家间政治、经济关系研究',
    '市场营销': '市场分析与营销策略研究',
    '心理学': '人类心理与行为规律研究',
    '社会学': '社会结构与社会变迁研究',
    '教育学': '教育理论与教学实践研究',
    '文学': '语言文学创作与鉴赏',
    '社会工作': '社会服务与社会福利研究',
    '公共管理': '公共事务与组织管理',
    '新闻传播': '新闻传播理论与实务',
    '设计学': '视觉传达与艺术设计',
    '人力资源管理': '人才选拔与组织发展',
    '公共关系': '组织形象与公众沟通',
    '播音主持': '广播电视语言传播艺术',
    '表演艺术': '舞台表演艺术研究',
    '广告学': '广告策划与创意设计',
    '会计学': '财务核算与审计监督',
    '医学': '疾病预防与临床治疗',
    '土木工程': '工程建设与结构设计',
    '项目管理': '项目规划与执行管理',
    '行政管理': '政府与公共组织管理',
    '物流管理': '供应链与物流系统优化',
    '军事学': '军事理论与国防建设',
    '护理学': '护理理论与临床实践',
    '图书馆学': '信息资源组织与管理',
    '医学技术': '医学检验与辅助技术',
    '酒店管理': '酒店运营与服务管理',
    '旅游管理': '旅游资源开发与规划',
    '机械工程': '机械系统设计与制造',
    '航空技术': '航空器运行与维护',
    '自动化': '自动控制系统研究',
    '体育教育': '体育教学与运动训练',
    '美术学': '美术创作与理论',
    '音乐学': '音乐理论与演奏',
    '服装设计': '服装艺术与工程设计',
    '园林设计': '景观规划与植物配置',
    '烹饪艺术': '烹饪技艺与餐饮管理',
    '国际贸易': '跨国贸易与商务',
    '艺术设计': '视觉艺术与设计实践'
  }
  return descMap[major] || '适合该性格类型的热门专业方向'
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

onMounted(() => {
  loadResult()
  loadMajorInsightsForResult()
  uni.setNavigationBarTitle({
    title: 'MBTI 测评结果'
  })
})

onShow(() => {
  loadResult()
  loadMajorInsightsForResult()
})
</script>

<style lang="scss" scoped>
.mbti-result-page {
  min-height: 100vh;
  background:
    radial-gradient(90% 45% at 20% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  padding: 32rpx;
  padding-top: calc(32rpx + env(safe-area-inset-top));
  padding-bottom: calc(180rpx + env(safe-area-inset-bottom));
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

// 结果头部
.result-header {
  @include glass-panel;
  position: relative;
  border-radius: $radius-xl;
  padding: 64rpx 40rpx;
  text-align: center;
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
  display: inline-block;
  margin-bottom: 24rpx;
  z-index: 2;
}

.type-badge {
  background: $grad-royal;
  border: none;
  border-radius: $radius-lg;
  padding: 16rpx 48rpx;
  font-size: 54rpx;
  font-weight: 900;
  color: #fff;
  letter-spacing: 0;
  box-shadow: 0 10rpx 24rpx rgba(37, 99, 235, 0.20);
}

.type-name {
  display: block;
  font-size: 38rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 28rpx;
  z-index: 2;
  position: relative;
}

.type-tags {
  display: flex;
  justify-content: center;
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
  background: rgba(255, 255, 255, 0.04);
  color: $text-primary;
  border: 1px solid rgba(255, 255, 255, 0.08);
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
  height: 84rpx;
  background: $grad-royal;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 6rpx 16rpx rgba(99, 102, 241, 0.3);
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
