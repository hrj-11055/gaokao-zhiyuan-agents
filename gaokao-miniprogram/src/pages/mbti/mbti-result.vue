<template>
  <view class="mbti-result-page">
    <!-- 未完成提示 -->
    <view v-if="!result" class="empty-state">
      <text class="empty-icon">📋</text>
      <text class="empty-title">尚未完成测评</text>
      <text class="empty-desc">请先完成 MBTI 性格测试</text>
      <button class="primary-btn" @click="goBack">返回测评</button>
    </view>

    <!-- 结果内容 -->
    <view v-else class="result-content">
      <!-- 结果头部 - 渐变背景 -->
      <view class="result-header">
        <view class="type-badge">{{ result.type }}</view>
        <text class="type-name">{{ typeInfo?.name || '' }}</text>
        <view class="type-tags">
          <text v-for="(tag, index) in typeInfo?.tags" :key="index" class="tag">{{ tag }}</text>
        </view>
      </view>

      <!-- 维度得分 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">维度得分</text>
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
            <view class="score-bar">
              <view class="bar-fill left" :style="{ width: getLeftPercent(dim.left, dim.right) + '%' }"></view>
              <view class="bar-fill right" :style="{ width: getRightPercent(dim.left, dim.right) + '%' }"></view>
            </view>
            <view class="score-values">
              <text class="score-value left">{{ result.scores[dim.left] }}</text>
              <text class="score-value right">{{ result.scores[dim.right] }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 性格特征 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">性格特征</text>
        </view>
        <view class="traits-list">
          <view v-for="(trait, index) in typeInfo?.traits" :key="index" class="trait-item">
            <text class="trait-bullet">•</text>
            <text class="trait-text">{{ trait }}</text>
          </view>
        </view>
      </view>

      <!-- 适合职业方向 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">适合职业方向</text>
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
          <text class="section-title">专业推荐</text>
        </view>
        <view class="majors-list">
          <view v-for="(major, index) in typeInfo?.majors" :key="index" class="major-card" @click="viewMajorDetail(major)">
            <view class="major-header">
              <text class="major-name">{{ major }}</text>
              <text class="major-stars">{{ getStars(index) }}</text>
            </view>
            <text class="major-desc">{{ getMajorDesc(major) }}</text>
            <text class="major-link">查看详情 ›</text>
          </view>
        </view>
      </view>

      <!-- 底部按钮 -->
      <view class="footer-actions">
        <button class="retry-btn" @click="handleRetry">重新测试</button>
      </view>
    </view>

    <!-- 确认弹窗 -->
    <view v-if="showConfirmModal" class="modal-overlay" @click="closeModal">
      <view class="modal-content" @click.stop>
        <text class="modal-title">确认重新测试？</text>
        <text class="modal-desc">重新测试将覆盖当前结果，确定要开始吗？</text>
        <view class="modal-actions">
          <button class="modal-btn cancel" @click="closeModal">取消</button>
          <button class="modal-btn confirm" @click="confirmRetry">确认</button>
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

const result = ref(null)
const showConfirmModal = ref(false)

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

// 加载结果
function loadResult() {
  const assessments = loadAssessments()
  if (assessments.mbti?.completed) {
    result.value = {
      type: assessments.mbti.type,
      scores: assessments.mbti.scores
    }
  } else {
    result.value = null
  }
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
  uni.showToast({
    title: '即将跳转至专业详情',
    icon: 'none'
  })
  // TODO: 跳转到专业详情页
  // uni.navigateTo({ url: `/pages/major/detail?name=${major}` })
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

// 确认重新测试
function confirmRetry() {
  // 清除 MBTI 结果
  const assessments = loadAssessments()
  assessments.mbti = {
    completed: false,
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
  uni.setNavigationBarTitle({
    title: 'MBTI 测评结果'
  })
})

onShow(() => {
  loadResult()
})
</script>

<style lang="scss" scoped>
.mbti-result-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: 120rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 40rpx;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 24rpx;
}

.empty-title {
  font-size: 36rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.empty-desc {
  font-size: 28rpx;
  color: $text-secondary;
  margin-bottom: 40rpx;
}

.primary-btn {
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
  border: none;
  border-radius: $radius-full;
  padding: 24rpx 64rpx;
  font-size: 28rpx;
  font-weight: 600;
}

.result-content {
  padding: 32rpx;
}

// 结果头部
.result-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: $radius-xl;
  padding: 48rpx 32rpx;
  text-align: center;
  margin-bottom: 32rpx;
}

.type-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.25);
  border: 2rpx solid rgba(255, 255, 255, 0.4);
  border-radius: $radius-lg;
  padding: 12rpx 32rpx;
  font-size: 48rpx;
  font-weight: 700;
  color: #fff;
  letter-spacing: 4rpx;
  margin-bottom: 16rpx;
}

.type-name {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  color: #fff;
  margin-bottom: 24rpx;
}

.type-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12rpx;
}

.tag {
  background: rgba(255, 255, 255, 0.2);
  border-radius: $radius-full;
  padding: 8rpx 20rpx;
  font-size: 24rpx;
  color: #fff;
}

// 通用区块
.section {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.section-header {
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
}

// 维度得分
.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.dimension-labels {
  display: flex;
  justify-content: space-between;
}

.dim-label {
  font-size: 26rpx;
  color: $text-secondary;
  font-weight: 500;
  transition: color 0.3s;
}

.dim-label.active {
  color: $brand-primary;
  font-weight: 600;
}

.score-bar {
  height: 24rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
  display: flex;
  position: relative;
}

.bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.bar-fill.left {
  background: linear-gradient(90deg, $brand-primary, $brand-primary-light);
}

.bar-fill.right {
  background: linear-gradient(90deg, #F59E0B, #FBBF24);
}

.score-values {
  display: flex;
  justify-content: space-between;
}

.score-value {
  font-size: 24rpx;
  color: $text-muted;
}

.score-value.active {
  color: $text-primary;
  font-weight: 600;
}

// 性格特征
.traits-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.trait-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.trait-bullet {
  font-size: 32rpx;
  color: $brand-primary;
  line-height: 1.4;
}

.trait-text {
  flex: 1;
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.6;
}

// 职业方向
.careers-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.career-tag {
  background: $bg-input;
  border-radius: $radius-lg;
  padding: 12rpx 24rpx;
  font-size: 26rpx;
  color: $text-primary;
}

// 专业推荐
.majors-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.major-card {
  background: $bg-page;
  border-radius: $radius-lg;
  padding: 24rpx;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 6rpx;
    background: linear-gradient(180deg, $brand-primary, $brand-primary-dark);
  }
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.major-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.major-stars {
  font-size: 24rpx;
  color: #F59E0B;
}

.major-desc {
  display: block;
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.5;
  margin-bottom: 12rpx;
}

.major-link {
  font-size: 24rpx;
  color: $brand-primary;
}

// 底部按钮
.footer-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: $bg-white;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.05);
}

.retry-btn {
  width: 100%;
  background: $bg-input;
  color: $text-primary;
  border: none;
  border-radius: $radius-full;
  padding: 28rpx;
  font-size: 28rpx;
  font-weight: 600;
}

// 弹窗
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  width: 560rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 16rpx;
}

.modal-desc {
  font-size: 26rpx;
  color: $text-secondary;
  text-align: center;
  line-height: 1.6;
  margin-bottom: 32rpx;
}

.modal-actions {
  display: flex;
  gap: 16rpx;
  width: 100%;
}

.modal-btn {
  flex: 1;
  border: none;
  border-radius: $radius-full;
  padding: 24rpx;
  font-size: 28rpx;
  font-weight: 600;
}

.modal-btn.cancel {
  background: $bg-input;
  color: $text-primary;
}

.modal-btn.confirm {
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
}
</style>
