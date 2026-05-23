<template>
  <view class="holland-page">
    <!-- 炫彩背景氛围粒子 -->
    <view class="cyber-glow-bg-indigo" />
    <view class="cyber-glow-bg-orange" />

    <!-- 介绍页 -->
    <view v-if="showIntro" class="intro-container">
      <view class="intro-card">
        <view class="intro-icon-outer">
          <view class="intro-icon-glow" />
          <view class="intro-icon">🎯</view>
        </view>
        <text class="intro-title">霍兰德职业兴趣测试</text>
        <text class="intro-desc">通过实际型、研究型、艺术型、社会型、企业型、常规型六类兴趣，了解你更适合的职业和专业方向。</text>

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
              <text class="version-count">12 道题</text>
              <text class="version-time">约 2 分钟</text>
              <text class="version-hint">快速了解兴趣轮廓</text>
            </view>
            <view
              class="version-card"
              :class="{ active: selectedVersion === 'full' }"
              @click="selectedVersion = 'full'"
            >
              <view class="version-check" v-if="selectedVersion === 'full'">✓</view>
              <text class="version-icon">🔬</text>
              <text class="version-name">完整版</text>
              <text class="version-count">60 道题</text>
              <text class="version-time">约 15 分钟</text>
              <text class="version-hint">更完整地分析兴趣分布</text>
            </view>
          </view>
        </view>

        <view class="intro-tips">
          <text class="tips-title">答题建议：</text>
          <text class="tips-text">1. 建议只考虑该活动是否能带给您纯粹的乐趣，排除高薪或地位干扰。</text>
          <text class="tips-text">2. 请凭本能直觉作答，若有犹豫，可直接选择中性倾向。</text>
          <text class="tips-text">3. 完成后会得到兴趣代码，并用于后续专业方向分析。</text>
        </view>

        <button class="start-btn" @click="startTest">开启兴趣探索</button>
      </view>
    </view>

    <!-- 测试内容 -->
    <block v-else>
      <!-- 头部进度条 -->
      <view class="progress-bar-wrap">
        <view class="progress-info">
          <text class="progress-text">职业兴趣测试 {{ currentIndex + 1 }} / {{ activeQuestions.length }} 题</text>
          <text class="progress-pct">{{ Math.round((currentIndex + 1) / activeQuestions.length * 100) }}%</text>
        </view>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: ((currentIndex + 1) / activeQuestions.length * 100) + '%' }">
            <view class="progress-fill-glow" />
          </view>
        </view>
      </view>

      <!-- 题目卡片 -->
      <view class="question-card">
        <view class="question-header">
          <text class="question-num">Q{{ currentIndex + 1 }}</text>
          <view class="header-divider" />
          <view v-if="selectedVersion === 'basic'" class="version-tag-inline">⚡ 精简版</view>
        </view>
        <text class="question-text">{{ currentQuestion.text }}</text>

        <!-- 选项列表 - 李克特量表 -->
        <view class="options-list">
          <view
            v-for="(option, index) in currentQuestion.options"
            :key="index"
            class="option-item"
            :class="{ 'option-selected': answers[currentQuestion.id] === index }"
            @click="selectOption(index)"
          >
            <view class="option-radio">
              <view v-if="answers[currentQuestion.id] === index" class="radio-dot" />
            </view>
            <text class="option-text">{{ option }}</text>
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
import { HOLLAND_QUESTIONS, HOLLAND_QUESTIONS_BASIC, calculateHollandCodeFromQuestions } from '../../data/holland-questions.js'
import { loadAssessments, saveHollandProgress, saveHollandResult } from '../../utils/storage.js'

const showIntro = ref(true)
const currentIndex = ref(0)
const answers = ref({})
const selectedVersion = ref('basic')

// 根据选择的版本使用对应题库
const activeQuestions = computed(() =>
  selectedVersion.value === 'basic' ? HOLLAND_QUESTIONS_BASIC : HOLLAND_QUESTIONS
)

const currentQuestion = computed(() => activeQuestions.value[currentIndex.value])
const isCurrentAnswered = computed(() => answers.value[currentQuestion.value.id] !== undefined)

onMounted(() => {
  uni.setNavigationBarTitle({
    title: '霍兰德职业兴趣测试'
  })
})

onShow(() => {
  // 检查是否已完成
  const assessments = loadAssessments()
  if (assessments.holland.completed) {
    // 已完成，跳转到结果页
    uni.redirectTo({
      url: '/pages/holland/holland-result'
    })
    return
  }

  // 恢复版本选择
  if (assessments.holland.version === 'basic' || assessments.holland.version === 'full') {
    selectedVersion.value = assessments.holland.version
  }

  // 恢复进度
  if (assessments.holland.questionIndex > 0) {
    currentIndex.value = assessments.holland.questionIndex
  }
  if (assessments.holland.answers && assessments.holland.answers.length > 0) {
    // 将数组转换为对象格式 { questionId: optionIndex }
    const answersObj = {}
    assessments.holland.answers.forEach(item => {
      answersObj[item.questionId] = item.optionIndex
    })
    answers.value = answersObj
  }
})

function startTest() {
  showIntro.value = false
}

function selectOption(optionIndex) {
  answers.value[currentQuestion.value.id] = optionIndex

  // 保存进度 - 转换为数组格式
  const answersArray = Object.entries(answers.value).map(([questionId, optionIndex]) => ({
    questionId: parseInt(questionId),
    optionIndex
  }))
  saveHollandProgress(currentIndex.value, answersArray, selectedVersion.value)

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

  submitResult()
}

function submitResult() {
  // 计算霍兰德代码（使用当前版本题库）
  const result = calculateHollandCodeFromQuestions(answers.value, activeQuestions.value)

  // 保存结果
  const answersArray = Object.entries(answers.value).map(([questionId, optionIndex]) => ({
    questionId: parseInt(questionId),
    optionIndex
  }))
  saveHollandResult({
    code: result.code,
    scores: result.scores,
    version: selectedVersion.value,
    answers: answersArray
  })

  // 跳转到结果页
  uni.redirectTo({
    url: '/pages/holland/holland-result'
  })
}
</script>

<style lang="scss" scoped>
.holland-page {
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
  z-index: 1;
}
.cyber-glow-bg-orange {
  position: absolute;
  width: 550rpx;
  height: 550rpx;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.035) 0%, rgba(0, 0, 0, 0) 70%);
  bottom: 100rpx;
  left: -150rpx;
  pointer-events: none;
  z-index: 1;
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
  background: rgba(249, 115, 22, 0.12);
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
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
  border-radius: $radius-full;
  font-size: 32rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
  box-shadow: 0 8rpx 24rpx rgba(249, 115, 22, 0.35);
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

.progress-text {
  font-size: 23rpx;
  color: $text-secondary;
  font-weight: 500;
}

.progress-pct {
  font-size: 23rpx;
  color: $brand-primary;
  font-weight: 700;
}

.progress-track {
  background: $bg-input;
  border: 1px solid rgba(255, 255, 255, 0.02);
  border-radius: $radius-full;
  height: 12rpx;
}

.progress-fill {
  background: linear-gradient(90deg, $brand-primary, $brand-primary-dark);
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
  background: linear-gradient(90deg, rgba(249, 115, 22, 0.25) 0%, rgba(255, 255, 255, 0) 100%);
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
  border-color: rgba(249, 115, 22, 0.5);
  background: rgba(249, 115, 22, 0.08);
  box-shadow: inset 0 0 20rpx rgba(249, 115, 22, 0.15);
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
    background: $brand-primary;
    border-color: $brand-primary;
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

  .option-selected & {
    color: $brand-primary;
    font-weight: 600;
  }
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
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
}

.finish-btn {
  background: linear-gradient(135deg, #10B981, #059669);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(16, 185, 129, 0.3);
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
    border-color: rgba(249, 115, 22, 0.5);
    background: rgba(249, 115, 22, 0.08);
    box-shadow: 0 10rpx 24rpx rgba(249, 115, 22, 0.10);
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
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
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
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.2);
  border-radius: $radius-full;
  font-size: 21rpx;
  color: rgba(249, 115, 22, 0.9);
  font-weight: 600;
  margin-left: auto;
}
</style>
