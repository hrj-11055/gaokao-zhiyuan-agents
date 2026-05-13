<template>
  <view class="holland-result-page">
    <!-- 结果头部 -->
    <view class="result-header">
      <view class="code-badge">{{ result.code }}</view>
      <text class="type-name">{{ typeInfo.name }}</text>
      <view class="tag-list">
        <view v-for="(tag, idx) in typeInfo.tags" :key="idx" class="tag">
          {{ tag }}
        </view>
      </view>
    </view>

    <!-- 维度得分 -->
    <view class="section">
      <view class="section-title">维度得分</view>
      <view class="dimensions-list">
        <view v-for="dim in sortedDimensions" :key="dim.type" class="dimension-item">
          <view class="dimension-header">
            <text class="dimension-label">{{ dim.label }}</text>
            <text class="dimension-score">{{ dim.score }}分</text>
          </view>
          <view class="score-bar">
            <view class="score-fill" :style="{ width: getPercent(dim.score) }"></view>
          </view>
        </view>
      </view>
    </view>

    <!-- 性格特征 -->
    <view class="section">
      <view class="section-title">性格特征</view>
      <view class="traits-list">
        <view v-for="(trait, idx) in typeInfo.traits" :key="idx" class="trait-item">
          <view class="trait-bullet"></view>
          <text class="trait-text">{{ trait }}</text>
        </view>
      </view>
    </view>

    <!-- 适合职业方向 -->
    <view class="section">
      <view class="section-title">适合职业方向</view>
      <view class="careers-list">
        <view v-for="(career, idx) in typeInfo.careers" :key="idx" class="career-tag">
          {{ career }}
        </view>
      </view>
    </view>

    <!-- 专业推荐 -->
    <view class="section">
      <view class="section-title">专业推荐</view>
      <view class="majors-list">
        <view v-for="(major, idx) in typeInfo.majors" :key="idx" class="major-item" @click="viewMajorDetail(major)">
          <view class="major-header">
            <text class="major-name">{{ major }}</text>
            <view class="major-stars">{{ getStars(idx + 1) }}</view>
          </view>
          <text class="major-desc">{{ getMajorDesc(major) }}</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer-actions">
      <button class="retry-btn" @click="retry">重新测试</button>
    </view>

    <!-- 确认弹窗 -->
    <view v-if="showConfirm" class="confirm-modal" @click="showConfirm = false">
      <view class="confirm-content" @click.stop>
        <view class="confirm-icon">⚠️</view>
        <text class="confirm-title">确认重新测试？</text>
        <text class="confirm-desc">重新测试将清除当前结果，需要重新回答所有问题</text>
        <view class="confirm-actions">
          <button class="confirm-btn cancel" @click="showConfirm = false">取消</button>
          <button class="confirm-btn confirm" @click="confirmRetry">确认重测</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadAssessments } from '../../utils/storage.js'
import { HOLLAND_TYPE_DESCRIPTIONS, HOLLAND_TYPE_LABELS } from '../../data/holland-questions.js'

const result = ref({
  code: '',
  scores: { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 }
})

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

// 获取百分比
function getPercent(score) {
  const maxScore = 40 // 每个类型最高40分（10题×4分）
  return Math.min((score / maxScore) * 100, 100) + '%'
}

// 获取星级评价
function getStars(index) {
  if (index <= 2) return '★★★★★'
  if (index <= 4) return '★★★★☆'
  return '★★★☆☆'
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
    '风景园林': ' outdoor 空间规划与景观设计',
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

// 查看专业详情
function viewMajorDetail(major) {
  uni.showToast({
    title: `查看${major}详情`,
    icon: 'none'
  })
  // TODO: 跳转到专业详情页
  // uni.navigateTo({ url: `/pages/major/detail?name=${major}` })
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
  uni.setNavigationBarTitle({
    title: '霍兰德测评结果'
  })
})
</script>

<style lang="scss" scoped>
.holland-result-page {
  min-height: 100vh;
  background: $bg-page;
  padding: 32rpx;
  padding-bottom: 120rpx;
  box-sizing: border-box;
}

.result-header {
  background: linear-gradient(135deg, $brand-gradient-start, $brand-gradient-end);
  border-radius: $radius-xl;
  padding: 48rpx 32rpx;
  text-align: center;
  margin-bottom: 24rpx;
}

.code-badge {
  display: inline-block;
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
  font-size: 56rpx;
  font-weight: 700;
  padding: 16rpx 48rpx;
  border-radius: $radius-lg;
  margin-bottom: 16rpx;
  letter-spacing: 8rpx;
}

.type-name {
  display: block;
  font-size: 36rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 20rpx;
}

.tag-list {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12rpx;
}

.tag {
  background: rgba(249, 115, 22, 0.15);
  color: $brand-primary-dark;
  font-size: 24rpx;
  padding: 8rpx 20rpx;
  border-radius: $radius-full;
}

.section {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 16rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 24rpx;
}

// 维度得分
.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dimension-label {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-secondary;
}

.dimension-score {
  font-size: 26rpx;
  font-weight: 600;
  color: $brand-primary;
}

.score-bar {
  height: 16rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, $brand-primary-light, $brand-primary);
  border-radius: $radius-full;
  transition: width 0.3s ease;
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
  width: 12rpx;
  height: 12rpx;
  background: $brand-primary;
  border-radius: 50%;
  margin-top: 10rpx;
  flex-shrink: 0;
}

.trait-text {
  flex: 1;
  font-size: 28rpx;
  line-height: 1.6;
  color: $text-secondary;
}

// 职业方向
.careers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.career-tag {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.1), rgba(249, 115, 22, 0.05));
  border: 1rpx solid rgba(249, 115, 22, 0.2);
  color: $brand-primary-dark;
  font-size: 26rpx;
  padding: 12rpx 24rpx;
  border-radius: $radius-md;
}

// 专业推荐
.majors-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.major-item {
  background: $bg-page;
  border-radius: $radius-md;
  padding: 20rpx;
  border: 1rpx solid $border-light;
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8rpx;
}

.major-name {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-primary;
}

.major-stars {
  font-size: 24rpx;
  color: #FBBF24;
}

.major-desc {
  font-size: 24rpx;
  color: $text-muted;
  line-height: 1.5;
}

// 底部按钮
.footer-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: $bg-white;
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.retry-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
}

.retry-btn::after {
  border: none;
}

// 确认弹窗
.confirm-modal {
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

.confirm-content {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  margin: 32rpx;
  text-align: center;
}

.confirm-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}

.confirm-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 12rpx;
}

.confirm-desc {
  display: block;
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.6;
  margin-bottom: 32rpx;
}

.confirm-actions {
  display: flex;
  gap: 16rpx;
}

.confirm-btn {
  flex: 1;
  height: 80rpx;
  font-size: 28rpx;
  font-weight: 500;
  border: none;
  border-radius: $radius-md;
}

.confirm-btn::after {
  border: none;
}

.confirm-btn.cancel {
  background: $bg-input;
  color: $text-secondary;
}

.confirm-btn.confirm {
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
}
</style>
