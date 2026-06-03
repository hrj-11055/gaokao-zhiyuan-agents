<template>
  <view class="major-detail-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-violet" />
    <view class="cyber-glow-bg-orange" />

    <!-- 结果内容 -->
    <view class="detail-content">
      <!-- 专业头部 -->
      <view class="major-header" :class="source">
        <view class="header-glow" />
        <text class="major-name">{{ majorName }}</text>
        <text class="major-desc">{{ majorDesc }}</text>
        <view class="source-tag-wrap">
          <view class="source-tag" :class="source">
            {{ source === 'mbti' ? '性格测试参考' : '霍兰德兴趣参考' }}
          </view>
        </view>
      </view>

      <!-- 推荐理由 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" :class="source" />
            <text class="section-title">推荐理由</text>
          </view>
        </view>
        <view class="match-info">
          <text class="match-type">契合维度：{{ typeName }} ({{ typeLabel }})</text>
        </view>
        <view class="reason-list">
          <view v-for="(trait, idx) in typeTraits" :key="idx" class="reason-item">
            <view class="reason-bullet-outer">
              <view class="reason-bullet" :class="source" />
            </view>
            <text class="reason-text">{{ trait }}</text>
          </view>
        </view>
      </view>

      <!-- 专业结构化信息 -->
      <view v-if="majorInsight" class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" :class="source" />
            <text class="section-title">专业学习重点</text>
          </view>
        </view>
        <view class="insight-block">
          <text class="insight-label">核心课程</text>
          <text class="insight-text">{{ formatList(majorInsight.courses) }}</text>
        </view>
        <view class="insight-block">
          <text class="insight-label">能力要求</text>
          <text class="insight-text">{{ formatList(majorInsight.abilities) }}</text>
        </view>
        <view class="insight-block">
          <text class="insight-label">薪资参考</text>
          <text class="insight-text">{{ majorInsight.salarySummary }}</text>
        </view>
      </view>

      <!-- 相关职业方向 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" :class="source" />
            <text class="section-title">适合关注的职业方向</text>
          </view>
        </view>
        <view class="careers-grid">
          <view v-for="(career, idx) in typeCareers" :key="idx" class="career-tag">
            {{ career }}
          </view>
        </view>
      </view>

      <!-- 性格标签 -->
      <view class="section">
        <view class="section-header">
          <view class="section-title-wrap">
            <view class="title-dot" :class="source" />
            <text class="section-title">相关特质</text>
          </view>
        </view>
        <view class="tags-list">
          <view v-for="(tag, idx) in typeTags" :key="idx" class="trait-tag" :class="source">
            {{ tag }}
          </view>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer-bar">
      <view class="footer-blur" />
      <view class="footer-btns">
        <button class="back-btn" :class="source" @click="goBack">返回测评结果</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { MBTI_RESULT_REPORTS } from '../../data/mbti-questions.js'
import { HOLLAND_RESULT_REPORTS } from '../../data/holland-questions.js'
import { fetchMajorInsights } from '../../api/majorInsights.js'
import { getMajorLearningProfile, normalizeMajorName } from '../../data/major-learning-profiles.js'

const majorName = ref('')
const source = ref('mbti')
const typeCode = ref('')
const majorInsight = ref(null)

const majorDesc = computed(() => (
  majorInsight.value?.summary ||
  getMajorLearningProfile(majorName.value).summary
))

// 获取类型信息
const typeInfo = computed(() => {
  if (source.value === 'mbti') {
    return MBTI_RESULT_REPORTS[typeCode.value] || null
  }
  // Holland: 先精确匹配，再前缀匹配
  if (HOLLAND_RESULT_REPORTS[typeCode.value]) {
    return HOLLAND_RESULT_REPORTS[typeCode.value]
  }
  const prefix = typeCode.value.substring(0, 2)
  for (const [key, value] of Object.entries(HOLLAND_RESULT_REPORTS)) {
    if (key.startsWith(prefix)) return value
  }
  return null
})

const typeName = computed(() => {
  if (source.value === 'mbti') return typeCode.value
  return typeCode.value
})

const typeLabel = computed(() => typeInfo.value?.name || '')

const typeTraits = computed(() => typeInfo.value?.traits || [])

const typeCareers = computed(() => typeInfo.value?.careers || [])

const typeTags = computed(() => typeInfo.value?.tags || [])

function goBack() {
  uni.navigateBack()
}

function formatList(items = []) {
  return items.slice(0, 4).join('、')
}

async function loadMajorInsight() {
  if (!majorName.value) return
  try {
    const officialName = normalizeMajorName(majorName.value)
    const insights = await fetchMajorInsights([officialName])
    majorInsight.value = getMajorLearningProfile(officialName, insights[0] || null)
  } catch {
    majorInsight.value = getMajorLearningProfile(majorName.value)
  }
}

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  majorName.value = normalizeMajorName(decodeURIComponent(options.name || ''))
  source.value = options.source || 'mbti'
  typeCode.value = options.type || ''

  uni.setNavigationBarTitle({
    title: majorName.value || '专业详情'
  })
  loadMajorInsight()
})
</script>

<style lang="scss" scoped>
.major-detail-page {
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

.cyber-glow-bg-violet {
  position: fixed;
  top: -10%;
  left: -20%;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.05) 0%, rgba(0, 0, 0, 0) 70%);
  z-index: 0;
  pointer-events: none;
}

.cyber-glow-bg-orange {
  position: fixed;
  bottom: -10%;
  right: -20%;
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.04) 0%, rgba(0, 0, 0, 0) 70%);
  z-index: 0;
  pointer-events: none;
}

.detail-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

// 专业头部
.major-header {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid $border-light;
  border-radius: $radius-xl;
  padding: 56rpx 40rpx;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: flex-start;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 8rpx;
  }

  &.mbti::after {
    background: $grad-royal;
  }

  &.holland::after {
    background: $grad-accent;
  }

  .header-glow {
    position: absolute;
    top: 50%;
    right: 10%;
    transform: translateY(-50%);
    width: 250rpx;
    height: 250rpx;
    filter: blur(24px);
    z-index: 0;
  }

  &.mbti .header-glow {
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
  }

  &.holland .header-glow {
    background: radial-gradient(circle, rgba(249, 115, 22, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
  }
}

.major-name {
  display: block;
  font-size: 46rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 20rpx;
  z-index: 1;
  letter-spacing: 0;
}

.major-desc {
  display: block;
  font-size: 28rpx;
  color: $text-secondary;
  line-height: 1.6;
  margin-bottom: 28rpx;
  z-index: 1;
}

.source-tag-wrap {
  display: inline-block;
  padding: 2px;
  border-radius: $radius-full;
  z-index: 1;
}

.source-tag {
  font-size: 24rpx;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0;

  &.mbti {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.45) 0%, rgba(79, 70, 229, 0.45) 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
  }

  &.holland {
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.45) 0%, rgba(234, 88, 12, 0.45) 100%);
    border: 1px solid rgba(249, 115, 22, 0.3);
  }
}

.section {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
}

.section-header {
  margin-bottom: 28rpx;
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.title-dot {
  width: 8rpx;
  height: 28rpx;
  border-radius: $radius-full;

  &.mbti {
    background: $grad-royal;
  }

  &.holland {
    background: $grad-accent;
  }
}

.section-title {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
}

.match-info {
  margin-bottom: 28rpx;
}

.match-type {
  font-size: 26rpx;
  font-weight: 700;
  color: $text-primary;
  background: $bg-input;
  padding: 14rpx 24rpx;
  border-radius: $radius-md;
  border: 1px solid $border-light;
}

.reason-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.reason-item {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
}

.reason-bullet-outer {
  margin-top: 14rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.reason-bullet {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;

  &.mbti {
    background: $brand-violet;
  }

  &.holland {
    background: $brand-primary;
  }
}

.reason-text {
  flex: 1;
  font-size: 27rpx;
  color: $text-primary;
  line-height: 1.6;
  font-weight: 500;
}

.insight-block {
  background: #F8FAFC;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  padding: 22rpx 24rpx;
  margin-bottom: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.insight-label {
  font-size: 24rpx;
  font-weight: 800;
  color: $text-primary;
}

.insight-text {
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.55;
}

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

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.trait-tag {
  font-size: 24rpx;
  padding: 10rpx 24rpx;
  border-radius: $radius-full;
  font-weight: 600;

  &.mbti {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #818CF8;
  }

  &.holland {
    background: rgba(249, 115, 22, 0.1);
    border: 1px solid rgba(249, 115, 22, 0.2);
    color: $brand-primary-light;
  }
}

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

.back-btn {
  width: 100%;
  height: 84rpx;
  color: #fff;
  border: none;
  border-radius: $radius-full;
  font-size: 28rpx;
  font-weight: 800;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;

  &::after {
    border: none;
  }

  &.mbti {
    background: linear-gradient(135deg, $brand-violet 0%, #4F46E5 100%);
    box-shadow: 0 6rpx 16rpx rgba(99, 102, 241, 0.3);

    &:active {
      transform: scale(0.98);
      box-shadow: 0 3rpx 8rpx rgba(99, 102, 241, 0.2);
    }
  }

  &.holland {
    background: $grad-primary;
    box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);

    &:active {
      transform: scale(0.98);
      box-shadow: 0 3rpx 8rpx rgba(249, 115, 22, 0.2);
    }
  }
}
</style>
