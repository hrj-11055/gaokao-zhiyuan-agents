<template>
  <view class="holland-page">
    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-info">
        <text class="progress-text">{{ currentIndex + 1 }}/{{ HOLLAND_QUESTIONS.length }}</text>
        <text class="progress-pct">{{ Math.round((currentIndex + 1) / HOLLAND_QUESTIONS.length * 100) }}%</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: ((currentIndex + 1) / HOLLAND_QUESTIONS.length * 100) + '%' }" />
      </view>
    </view>

    <!-- 题目卡片 -->
    <view class="question-card">
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
            <text v-if="answers[currentQuestion.id] === index" class="radio-dot">●</text>
          </view>
          <text class="option-text">{{ option }}</text>
        </view>
      </view>
    </view>

    <!-- 底部导航按钮 -->
    <view class="footer">
      <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">上一题</view>
      <view v-if="currentIndex < HOLLAND_QUESTIONS.length - 1" class="nav-btn next-btn" :class="{ disabled: answers[currentQuestion.id] === undefined }" @click="next">下一题</view>
      <view v-else class="nav-btn finish-btn" :class="{ disabled: answers[currentQuestion.id] === undefined }" @click="finish">查看结果</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { HOLLAND_QUESTIONS, calculateHollandCode } from '../../data/holland-questions.js'
import { loadAssessments, saveHollandProgress, saveHollandResult } from '../../utils/storage.js'

const currentIndex = ref(0)
const answers = ref({})

const currentQuestion = computed(() => HOLLAND_QUESTIONS[currentIndex.value])

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

function selectOption(optionIndex) {
  answers.value[currentQuestion.value.id] = optionIndex

  // 保存进度 - 转换为数组格式
  const answersArray = Object.entries(answers.value).map(([questionId, optionIndex]) => ({
    questionId: parseInt(questionId),
    optionIndex
  }))
  saveHollandProgress(currentIndex.value, answersArray)
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function next() {
  if (answers.value[currentQuestion.value.id] === undefined) {
    uni.showToast({
      title: '请先选择一个选项',
      icon: 'none'
    })
    return
  }

  if (currentIndex.value < HOLLAND_QUESTIONS.length - 1) {
    currentIndex.value++
  }
}

function finish() {
  if (answers.value[currentQuestion.value.id] === undefined) {
    uni.showToast({
      title: '请先选择一个选项',
      icon: 'none'
    })
    return
  }

  // 检查是否所有题目都已回答
  const answeredCount = Object.keys(answers.value).length
  if (answeredCount < HOLLAND_QUESTIONS.length) {
    uni.showModal({
      title: '提示',
      content: `还有 ${HOLLAND_QUESTIONS.length - answeredCount} 道题未回答，确定要提交吗？`,
      success: (res) => {
        if (res.confirm) {
          submitResult()
        }
      }
    })
  } else {
    submitResult()
  }
}

function submitResult() {
  // 计算霍兰德代码
  const result = calculateHollandCode(answers.value)

  // 保存结果
  const answersArray = Object.entries(answers.value).map(([questionId, optionIndex]) => ({
    questionId: parseInt(questionId),
    optionIndex
  }))
  saveHollandResult({
    code: result.code,
    scores: result.scores,
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
  background: $bg-page;
  padding: 32rpx;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

.progress-bar-wrap {
  margin-bottom: 40rpx;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.progress-text {
  font-size: 28rpx;
  color: $text-secondary;
  font-weight: 500;
}

.progress-pct {
  font-size: 28rpx;
  color: $brand-primary;
  font-weight: 600;
}

.progress-track {
  height: 12rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, $brand-primary, $brand-primary-dark);
  border-radius: $radius-full;
  transition: width 0.3s ease;
}

.question-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  margin-bottom: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.question-text {
  font-size: 32rpx;
  font-weight: 500;
  color: $text-primary;
  line-height: 1.6;
  margin-bottom: 40rpx;
  display: block;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 28rpx 24rpx;
  background: $bg-input;
  border-radius: $radius-lg;
  border: 2rpx solid transparent;
  transition: all 0.2s ease;
}

.option-item.option-selected {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.08), rgba(249, 115, 22, 0.12));
  border-color: $brand-primary;
}

.option-radio {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 2rpx solid $border-light;
  margin-right: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.option-item.option-selected .option-radio {
  border-color: $brand-primary;
  background: rgba(249, 115, 22, 0.1);
}

.radio-dot {
  font-size: 24rpx;
  color: $brand-primary;
}

.option-text {
  font-size: 30rpx;
  color: $text-primary;
  flex: 1;
}

.option-item.option-selected .option-text {
  color: $brand-primary;
  font-weight: 500;
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: $bg-white;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.06);
  display: flex;
  gap: 20rpx;
}

.nav-btn {
  flex: 1;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-lg;
  font-size: 30rpx;
  font-weight: 500;
  transition: all 0.2s ease;
}

.prev-btn {
  background: $bg-input;
  color: $text-secondary;
}

.prev-btn.disabled {
  opacity: 0.5;
}

.next-btn {
  background: linear-gradient(135deg, $brand-primary, $brand-primary-dark);
  color: #fff;
}

.next-btn.disabled {
  opacity: 0.5;
}

.finish-btn {
  background: linear-gradient(135deg, #10B981, #059669);
  color: #fff;
}

.finish-btn.disabled {
  opacity: 0.5;
}
</style>
