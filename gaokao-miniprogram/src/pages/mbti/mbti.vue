<template>
  <view class="page">
    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-info">
        <text class="progress-text">第 {{ currentIndex + 1 }}/{{ MBTI_QUESTIONS.length }} 题</text>
        <text class="progress-pct">{{ Math.round((currentIndex + 1) / MBTI_QUESTIONS.length * 100) }}%</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: ((currentIndex + 1) / MBTI_QUESTIONS.length * 100) + '%' }" />
      </view>
    </view>

    <!-- 维度指示器 -->
    <view class="dimension-indicator">
      <text class="dimension-text">{{ getDimensionText(currentQuestion.dimension) }}</text>
    </view>

    <!-- 题目卡片 -->
    <view class="question-card">
      <text class="question-text">{{ currentQuestion.text }}</text>

      <!-- 选项列表 -->
      <view class="options-list">
        <view
          class="option-item"
          :class="{ 'option-selected': answers[currentQuestion.id] === 'A' }"
          @click="selectOption('A')"
        >
          <view class="option-radio">
            <view v-if="answers[currentQuestion.id] === 'A'" class="radio-dot"></view>
          </view>
          <text class="option-text">{{ currentQuestion.optionA }}</text>
        </view>
        <view
          class="option-item"
          :class="{ 'option-selected': answers[currentQuestion.id] === 'B' }"
          @click="selectOption('B')"
        >
          <view class="option-radio">
            <view v-if="answers[currentQuestion.id] === 'B'" class="radio-dot"></view>
          </view>
          <text class="option-text">{{ currentQuestion.optionB }}</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">
        <text class="btn-text">上一题</text>
      </view>
      <view v-if="currentIndex < MBTI_QUESTIONS.length - 1" class="nav-btn next-btn" @click="next">
        <text class="btn-text">下一题</text>
      </view>
      <view v-else class="nav-btn finish-btn" @click="finish">
        <text class="btn-text">查看结果</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { MBTI_QUESTIONS, calculateMbtiType } from '../../utils/mbti-questions.js'
import { loadAssessments, saveMbtiProgress, saveMbtiResult } from '../../utils/storage.js'

const currentIndex = ref(0)
const answers = ref({})

const currentQuestion = computed(() => MBTI_QUESTIONS[currentIndex.value])

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
  saveMbtiProgress(currentIndex.value, answersArray)

  // 自动跳转到下一题
  if (currentIndex.value < MBTI_QUESTIONS.length - 1) {
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
    saveMbtiProgress(currentIndex.value, answersArray)
  }
}

function next() {
  if (currentIndex.value < MBTI_QUESTIONS.length - 1) {
    currentIndex.value++
    // 保存进度
    const answersArray = Object.entries(answers.value).map(([questionId, answer]) => ({
      questionId: parseInt(questionId),
      answer
    }))
    saveMbtiProgress(currentIndex.value, answersArray)
  }
}

function finish() {
  // 检查是否所有题目都已回答
  if (Object.keys(answers.value).length < MBTI_QUESTIONS.length) {
    uni.showToast({
      title: '请完成所有题目',
      icon: 'none'
    })
    return
  }

  // 计算结果
  const result = calculateMbtiType(answers.value)

  // 保存结果
  saveMbtiResult({
    type: result.type,
    scores: result.scores,
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
  background: $bg-page;
  padding: 24rpx 32rpx 200rpx;
  box-sizing: border-box;
}

.progress-bar-wrap {
  margin-bottom: 24rpx;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.progress-text, .progress-pct {
  font-size: 24rpx;
  color: $text-muted;
}

.progress-track {
  background: $border-light;
  border-radius: $radius-full;
  height: 8rpx;
}

.progress-fill {
  background: linear-gradient(90deg, #7c3aed, #6d28d9);
  border-radius: $radius-full;
  height: 8rpx;
  transition: width 0.3s;
}

.dimension-indicator {
  text-align: center;
  margin-bottom: 24rpx;
}

.dimension-text {
  font-size: 24rpx;
  color: #7c3aed;
  font-weight: 500;
  padding: 8rpx 24rpx;
  background: rgba(124, 58, 237, 0.1);
  border-radius: $radius-full;
}

.question-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
  min-height: 400rpx;
  display: flex;
  flex-direction: column;
}

.question-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
  margin-bottom: 32rpx;
  line-height: 1.6;
}

.options-list {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 28rpx;
  border-radius: $radius-lg;
  border: 2rpx solid $border-light;
  background: $bg-white;
  transition: all 0.2s;
}

.option-selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}

.option-radio {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 2rpx solid $border-light;
  background: $bg-white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;

  .option-selected & {
    border-color: #7c3aed;
  }
}

.radio-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: #7c3aed;
}

.option-text {
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.5;
  flex: 1;
}

.footer {
  position: fixed;
  bottom: calc(32rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
  display: flex;
  gap: 16rpx;
}

.nav-btn {
  flex: 1;
  height: 88rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
}

.prev-btn {
  background: $bg-white;
  color: $text-secondary;
  border: 2rpx solid $border-light;

  .btn-text {
    color: $text-secondary;
  }
}

.next-btn, .finish-btn {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);

  .btn-text {
    color: #fff;
  }
}

.disabled {
  opacity: 0.4;
}

.btn-text {
  font-size: 30rpx;
  font-weight: 600;
}
</style>
