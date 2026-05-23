<template>
  <view class="page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 介绍页 -->
    <view v-if="showIntro" class="intro-container">
      <view class="intro-card">
        <view class="intro-icon-outer">
          <view class="intro-icon-glow" />
          <view class="intro-icon">🧠</view>
        </view>
        <text class="intro-title">MBTI 性格测试</text>
        <text class="intro-desc">了解你在沟通、信息处理、判断方式和生活节奏上的偏好，作为专业选择时的参考。</text>

        <!-- 版本选择器 -->
        <view class="version-selector">
          <text class="version-selector-title">选择测评模式</text>
          <view class="version-cards">
            <view
              class="version-card"
              :class="{ active: selectedVersion === 'basic' }"
              @click="selectedVersion = 'basic'"
            >
              <view class="version-check" v-if="selectedVersion === 'basic'">✓</view>
              <text class="version-icon">⚡</text>
              <text class="version-name">精简版</text>
              <text class="version-count">16 道题</text>
              <text class="version-time">约 3 分钟</text>
              <text class="version-hint">快速了解性格轮廓</text>
            </view>
            <view
              class="version-card"
              :class="{ active: selectedVersion === 'full' }"
              @click="selectedVersion = 'full'"
            >
              <view class="version-check" v-if="selectedVersion === 'full'">✓</view>
              <text class="version-icon">🔬</text>
              <text class="version-name">完整版</text>
              <text class="version-count">48 道题</text>
              <text class="version-time">约 10 分钟</text>
              <text class="version-hint">深度解析心智模型</text>
            </view>
          </view>
        </view>

        <view class="intro-tips">
          <text class="tips-title">答题建议：</text>
          <text class="tips-text">1. 请凭第一直觉作答，不需要反复比较。</text>
          <text class="tips-text">2. 选择无对错好坏之分，面对不同场景，选择你最自然流露的状态。</text>
          <text class="tips-text">3. 答题进度会自动保存，完成后可查看性格结果。</text>
        </view>

        <button class="start-btn" @click="startTest">开启心智测试</button>
      </view>
    </view>

    <!-- 测试内容 -->
    <block v-else>
      <!-- 头部进度条 -->
      <view class="progress-bar-wrap">
        <view class="progress-info">
          <text class="progress-text">MBTI 测试 {{ currentIndex + 1 }} / {{ activeQuestions.length }} 题</text>
          <text class="progress-pct">{{ Math.round((currentIndex + 1) / activeQuestions.length * 100) }}%</text>
        </view>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: ((currentIndex + 1) / activeQuestions.length * 100) + '%' }">
            <view class="progress-fill-glow" />
          </view>
        </view>
      </view>

      <!-- 维度指示器 -->
      <view class="dimension-indicator">
        <view class="dimension-badge">
          <view class="dimension-dot" />
          <text class="dimension-text">当前维度：{{ getDimensionText(currentQuestion.dimension) }}</text>
        </view>
        <view v-if="selectedVersion === 'basic'" class="version-tag-inline">⚡ 精简版</view>
      </view>

      <!-- 题目卡片 -->
      <view class="question-card">
        <view class="question-header">
          <text class="question-num">Q{{ currentIndex + 1 }}</text>
          <view class="header-divider" />
        </view>
        <text class="question-text">{{ currentQuestion.text }}</text>

        <!-- 选项列表 -->
        <view class="options-list">
          <view
            class="option-item"
            :class="{ 'option-selected': answers[currentQuestion.id] === 'A' }"
            @click="selectOption('A')"
          >
            <view class="option-radio">
              <view v-if="answers[currentQuestion.id] === 'A'" class="radio-dot" />
            </view>
            <text class="option-text">{{ currentQuestion.optionA }}</text>
          </view>

          <view
            class="option-item"
            :class="{ 'option-selected': answers[currentQuestion.id] === 'B' }"
            @click="selectOption('B')"
          >
            <view class="option-radio">
              <view v-if="answers[currentQuestion.id] === 'B'" class="radio-dot" />
            </view>
            <text class="option-text">{{ currentQuestion.optionB }}</text>
          </view>
        </view>
      </view>

      <!-- 悬浮底部控制条 -->
      <view class="footer-bar">
        <view class="footer-blur" />
        <view class="footer-btns">
          <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">
            <text class="btn-text">上一题</text>
          </view>
          <view v-if="currentIndex < activeQuestions.length - 1" class="nav-btn next-btn" :class="{ disabled: !isCurrentAnswered }" @click="next">
            <text class="btn-text">下一题</text>
          </view>
          <view v-else class="nav-btn finish-btn" :class="{ disabled: !isCurrentAnswered }" @click="finish">
            <text class="btn-text">查看测试结果</text>
          </view>
        </view>
      </view>
    </block>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { MBTI_QUESTIONS, MBTI_QUESTIONS_BASIC, calculateMbtiTypeFromQuestions } from '../../utils/mbti-questions.js'
import { loadAssessments, saveMbtiProgress, saveMbtiResult } from '../../utils/storage.js'

const showIntro = ref(true)
const currentIndex = ref(0)
const answers = ref({})
const selectedVersion = ref('basic')

// 根据选择的版本使用对应题库
const activeQuestions = computed(() =>
  selectedVersion.value === 'basic' ? MBTI_QUESTIONS_BASIC : MBTI_QUESTIONS
)

const currentQuestion = computed(() => activeQuestions.value[currentIndex.value])
const isCurrentAnswered = computed(() => answers.value[currentQuestion.value.id] !== undefined)

onMounted(() => {
  uni.setNavigationBarTitle({
    title: 'MBTI 性格测试'
  })
})

onShow(() => {
  // 检查是否已完成
  const assessments = loadAssessments()
  if (assessments.mbti.completed) {
    // 已完成，跳转到结果页
    uni.redirectTo({ url: '/pages/mbti/mbti-result' })
    return
  }

  // 恢复版本选择
  if (assessments.mbti.version === 'basic' || assessments.mbti.version === 'full') {
    selectedVersion.value = assessments.mbti.version
  }

  // 恢复进度
  if (assessments.mbti.questionIndex >= 0) {
    currentIndex.value = assessments.mbti.questionIndex
  }
  // 恢复答案
  if (assessments.mbti.answers && assessments.mbti.answers.length > 0) {
    const savedAnswers = {}
    assessments.mbti.answers.forEach(item => {
      savedAnswers[item.questionId] = item.answer
    })
    answers.value = savedAnswers
  }
})

function startTest() {
  showIntro.value = false
}

function getDimensionText(dimension) {
  const texts = {
    'EI': '外向 / 内向',
    'SN': '实感 / 直觉',
    'TF': '思考 / 情感',
    'JP': '判断 / 感知'
  }
  return texts[dimension] || ''
}

function selectOption(option) {
  // 保存答案
  answers.value = {
    ...answers.value,
    [currentQuestion.value.id]: option
  }

  // 保存进度
  const answersArray = Object.entries(answers.value).map(([questionId, answer]) => ({
    questionId: parseInt(questionId),
    answer
  }))
  saveMbtiProgress(currentIndex.value, answersArray, selectedVersion.value)

  // 自动跳转到下一题
  if (currentIndex.value < activeQuestions.value.length - 1) {
    setTimeout(() => {
      currentIndex.value++
    }, 300)
  }
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    // 保存进度
    const answersArray = Object.entries(answers.value).map(([questionId, answer]) => ({
      questionId: parseInt(questionId),
      answer
    }))
    saveMbtiProgress(currentIndex.value, answersArray, selectedVersion.value)
  }
}

function next() {
  if (!isCurrentAnswered.value) {
    uni.showToast({
      title: '请先选择本题答案',
      icon: 'none'
    })
    return
  }

  if (currentIndex.value < activeQuestions.value.length - 1) {
    currentIndex.value++
    // 保存进度
    const answersArray = Object.entries(answers.value).map(([questionId, answer]) => ({
      questionId: parseInt(questionId),
      answer
    }))
    saveMbtiProgress(currentIndex.value, answersArray, selectedVersion.value)
  }
}

function finish() {
  if (!isCurrentAnswered.value) {
    uni.showToast({
      title: '请先选择本题答案',
      icon: 'none'
    })
    return
  }

  // 检查是否所有题目都已回答
  const firstUnansweredIndex = activeQuestions.value.findIndex(q => answers.value[q.id] === undefined)

  if (firstUnansweredIndex !== -1) {
    currentIndex.value = firstUnansweredIndex
    uni.showToast({
      title: `已跳到第 ${firstUnansweredIndex + 1} 题`,
      icon: 'none'
    })
    return
  }

  // 计算结果（使用当前版本题库）
  const result = calculateMbtiTypeFromQuestions(answers.value, activeQuestions.value)

  // 保存结果
  saveMbtiResult({
    type: result.type,
    scores: result.scores,
    version: selectedVersion.value,
    answers: Object.entries(answers.value).map(([questionId, answer]) => ({
      questionId: parseInt(questionId),
      answer
    }))
  })

  // 跳转到结果页
  uni.redirectTo({ url: '/pages/mbti/mbti-result' })
}
</script>

<style lang="scss" scoped>
.page {
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
  width: 550rpx;
  height: 550rpx;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, rgba(0, 0, 0, 0) 70%);
  top: -150rpx;
  right: -150rpx;
  pointer-events: none;
}
.cyber-glow-bg-orange {
  position: absolute;
  width: 550rpx;
  height: 550rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.035) 0%, rgba(0, 0, 0, 0) 70%);
  bottom: 100rpx;
  left: -150rpx;
  pointer-events: none;
}

// 介绍页
.intro-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120rpx);
  z-index: 10;
}

.intro-card {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 64rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
  z-index: 10;
}

.intro-icon-outer {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 36rpx;
}

.intro-icon {
  font-size: 100rpx;
  z-index: 2;
}

.intro-icon-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(37, 99, 235, 0.12);
  border-radius: 50%;
  filter: blur(20rpx);
  z-index: 1;
}

.intro-title {
  font-size: 42rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 24rpx;
  letter-spacing: 0;
  text-align: center;
}

.intro-desc {
  font-size: 27rpx;
  color: $text-secondary;
  line-height: 1.6;
  text-align: center;
  margin-bottom: 48rpx;
}

.intro-tips {
  background: $bg-input;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  padding: 32rpx;
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 60rpx;
}

.tips-title {
  font-size: 27rpx;
  font-weight: 700;
  color: $brand-primary;
  margin-bottom: 16rpx;
  display: block;
}

.tips-text {
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.8;
  display: block;
  margin-bottom: 8rpx;
}

.start-btn {
  width: 100%;
  height: 96rpx;
  background: $grad-royal;
  color: #fff;
  border-radius: $radius-full;
  font-size: 32rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
  box-shadow: 0 8rpx 24rpx rgba(99, 102, 241, 0.35);
  transition: transform 0.1s;

  &:active {
    transform: scale(0.98);
  }
}
.start-btn::after {
  border: none;
}

.progress-bar-wrap {
  margin-bottom: 36rpx;
  z-index: 10;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.progress-text, .progress-pct {
  font-size: 23rpx;
  color: $text-secondary;
  font-weight: 500;
}

.progress-track {
  background: $bg-input;
  border: 1px solid rgba(255, 255, 255, 0.02);
  border-radius: $radius-full;
  height: 12rpx;
}

.progress-fill {
  background: $grad-royal;
  border-radius: $radius-full;
  height: 12rpx;
  transition: width 0.3s ease;
  position: relative;
}

.progress-fill-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 16rpx;
  height: 100%;
  background: #fff;
  filter: blur(2rpx);
  opacity: 0.8;
}

// 维度指示器
.dimension-indicator {
  display: flex;
  justify-content: center;
  margin-bottom: 36rpx;
  z-index: 10;
}

.dimension-badge {
  display: flex;
  align-items: center;
  padding: 10rpx 32rpx;
  background: rgba(124, 58, 237, 0.12);
  border: 1px solid rgba(124, 58, 237, 0.25);
  border-radius: $radius-full;
}

.dimension-dot {
  width: 8rpx;
  height: 8rpx;
  background: $brand-violet;
  border-radius: 50%;
  margin-right: 12rpx;
}

.dimension-text {
  font-size: 23rpx;
  color: $brand-violet;
  font-weight: 700;
  letter-spacing: 0;
}

// 题目卡片
.question-card {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 48rpx 36rpx;
  z-index: 10;
  min-height: 420rpx;
  display: flex;
  flex-direction: column;
}

.question-header {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.question-num {
  font-size: 32rpx;
  font-weight: 900;
  color: $brand-primary;
  letter-spacing: 0;
}

.header-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.25) 0%, rgba(255, 255, 255, 0) 100%);
  margin-left: 20rpx;
}

.question-text {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  display: block;
  margin-bottom: 48rpx;
  line-height: 1.5;
}

.options-list {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 28rpx;
  border-radius: $radius-lg;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.01);
  transition: all 0.25s;

  &:active {
    transform: scale(0.98);
  }
}

.option-selected {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.08);
  box-shadow: inset 0 0 20rpx rgba(99, 102, 241, 0.15);
}

.option-radio {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;

  .option-selected & {
    background: $brand-violet;
    border-color: $brand-violet;
  }
}

.radio-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #fff;
}

.option-text {
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.5;
  font-weight: 500;
  flex: 1;
}

// 底部悬浮控制条
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
  display: flex;
  gap: 20rpx;
  padding: 0 32rpx;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 2;
}

.nav-btn {
  flex: 1;
  height: 84rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:active:not(.disabled) {
    transform: scale(0.97);
  }
}

.prev-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.next-btn {
  background: $grad-royal;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(99, 102, 241, 0.3);
}

.finish-btn {
  background: $grad-accent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
}

.btn-text {
  font-size: 28rpx;
  font-weight: 700;
  color: #fff;

  .prev-btn & {
    color: $text-primary;
  }
}

.disabled {
  opacity: 0.3;
}

// 版本选择器
.version-selector {
  width: 100%;
  margin-bottom: 36rpx;
}

.version-selector-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $text-secondary;
  margin-bottom: 20rpx;
  text-align: center;
  letter-spacing: 0;
}

.version-cards {
  display: flex;
  gap: 20rpx;
}

.version-card {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28rpx 16rpx 24rpx;
  border-radius: $radius-lg;
  border: 1.5px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
  overflow: hidden;

  &.active {
    border-color: rgba(99, 102, 241, 0.5);
    background: rgba(99, 102, 241, 0.08);
    box-shadow: 0 10rpx 24rpx rgba(37, 99, 235, 0.10);
  }

  &:active {
    transform: scale(0.97);
  }
}

.version-check {
  position: absolute;
  top: 12rpx;
  right: 12rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: $grad-royal;
  color: #fff;
  font-size: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.version-icon {
  font-size: 52rpx;
  margin-bottom: 12rpx;
}

.version-name {
  font-size: 28rpx;
  font-weight: 800;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.version-count {
  font-size: 24rpx;
  font-weight: 700;
  color: $brand-primary;
  margin-bottom: 4rpx;
}

.version-time {
  font-size: 22rpx;
  color: $text-secondary;
  margin-bottom: 8rpx;
}

.version-hint {
  font-size: 21rpx;
  color: $text-muted;
  text-align: center;
  line-height: 1.4;
}

// 答题中的版本标签
.version-tag-inline {
  padding: 6rpx 18rpx;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: $radius-full;
  font-size: 21rpx;
  color: rgba(99, 102, 241, 0.9);
  font-weight: 600;
  margin-left: 16rpx;
}
</style>
