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
          <view class="intro-icon">📋</view>
        </view>
        <text class="intro-title">五环学业特质测评</text>
        <text class="intro-desc">通过 21 道题了解学习方式、学业现状、家庭期待、能力特质和职业偏好，后续报告会参考这些信息。</text>
        
        <view class="intro-tips">
          <text class="tips-title">答题建议：</text>
          <text class="tips-text">1. 请按真实情况作答，不需要选择“看起来更好”的答案。</text>
          <text class="tips-text">2. 选项没有对错，只用于帮助报告理解你的实际处境。</text>
          <text class="tips-text">3. 答题进度会自动保存，退出后可继续完成。</text>
        </view>
        
        <button class="start-btn" @click="startTest">开始答题</button>
      </view>
    </view>

    <!-- 测试内容 -->
    <block v-else>
      <!-- 头部进度条 -->
      <view class="progress-bar-wrap">
        <view class="progress-info">
          <text class="progress-text">已完成 {{ completedCount }} / {{ QUESTIONS.length }} 题</text>
          <text class="progress-pct">{{ Math.round(completedCount / QUESTIONS.length * 100) }}%</text>
        </view>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: (completedCount / QUESTIONS.length * 100) + '%' }">
            <view class="progress-fill-glow" />
          </view>
        </view>
      </view>

      <!-- 五环雷达选项卡 -->
      <scroll-view class="ring-tabs" scroll-x>
        <view
          v-for="ring in rings"
          :key="ring.id"
          class="ring-tab"
          :class="{ 'ring-tab-active': currentRing === ring.id }"
          @click="goToRing(ring.id)"
        >
          第 {{ ring.label }} 环
        </view>
      </scroll-view>

      <!-- 题目卡片 -->
      <view class="question-card">
        <view class="ring-header">
          <text class="ring-label">第{{ currentQ.ringName }}环 · {{ currentQ.ringDisplayName }}维度</text>
          <view class="dimension-pulse-dot" />
        </view>
        <text class="question-text">{{ currentQ.text }}</text>
        <text v-if="currentQ.maxSelect" class="max-select-hint">💡 多选题：最多可选 {{ currentQ.maxSelect }} 项</text>

        <!-- 选项列表 -->
        <view class="options-list">
          <view
            v-for="opt in currentQ.options"
            :key="opt"
            class="option-item"
            :class="{ 'option-selected': isSelected(currentQ.id, opt) }"
            @click="toggleOption(currentQ.id, opt, currentQ.type, currentQ.maxSelect)"
          >
            <view class="option-check">
              <view v-if="isSelected(currentQ.id, opt)" class="check-dot" />
            </view>
            <text class="option-text">{{ opt }}</text>
          </view>
        </view>
      </view>

      <!-- 悬浮底部控制条 -->
      <view class="footer-bar">
        <view class="footer-blur" />
        <view class="footer-btns">
          <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">上一题</view>
          <view v-if="currentIndex < QUESTIONS.length - 1" class="nav-btn next-btn" :class="{ disabled: !isCurrentAnswered }" @click="next">下一题</view>
          <view v-else class="nav-btn finish-btn" :class="{ disabled: !isCurrentAnswered }" @click="next">完成测评</view>
        </view>
      </view>
    </block>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { saveQuestionnaire, loadQuestionnaire } from '../../utils/storage.js'

const QUESTIONS = [
  { id: 'q1', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '学习新内容时你更偏向？',
    options: ['先理解原理，再做题', '大量刷题，从中归纳规律', '跟着老师走，课后复习'] },
  { id: 'q2', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '遇到难题时你会？',
    options: ['反复拆解，直到搞懂', '先跳过，找会的做', '找同学或老师讨论'] },
  { id: 'q3', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '记公式和知识点时你更擅长？',
    options: ['用逻辑规律推导记忆', '反复抄写背诵', '做题时自然记住'] },
  { id: 'q4', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '上课时你通常？',
    options: ['紧跟老师思路认真记笔记', '自己推演，不喜欢抄', '听懂大意，课后再补'] },
  { id: 'q5', ring: 1, ringName: '第一', ringDisplayName: '学习风格', type: 'single',
    text: '你最高效的学习时段？',
    options: ['早晨', '下午', '深夜'] },
  { id: 'q6', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'multi',
    text: '你的优势学科（可多选）',
    options: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'] },
  { id: 'q7', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'multi',
    text: '你的薄弱学科（可多选）',
    options: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'] },
  { id: 'q8', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'single',
    text: '你当前的主要压力来源？',
    options: ['来自同学竞争', '来自父母期望', '来自自我高要求', '备考本身的压力'] },
  { id: 'q10', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'single',
    text: '父母的职业背景？',
    options: ['体制内（公务员/教师/医生）', '企业职员', '自营生意', '其他'] },
  { id: 'q11', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'multi',
    text: '家庭对专业选择的期望（可多选）',
    options: ['好就业', '收入高', '体面稳定', '尊重孩子兴趣', '没有明确要求'] },
  { id: 'q12', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'single',
    text: '家庭对就读城市的偏好？',
    options: ['本省优先', '北上广深', '不限制'] },
  { id: 'q13', ring: 3, ringName: '第三', ringDisplayName: '家庭背景', type: 'single',
    text: '家庭经济状况？',
    options: ['宽裕', '小康', '普通', '偏紧'] },
  { id: 'q14', ring: 4, ringName: '第四', ringDisplayName: '能力特质', type: 'multi', maxSelect: 3,
    text: '你最突出的能力（最多选 3 个）',
    options: ['逻辑推理', '动手实验', '语言表达', '创意设计', '记忆背诵', '数据分析'] },
  { id: 'q15', ring: 4, ringName: '第四', ringDisplayName: '能力特质', type: 'multi',
    text: '你最感兴趣的领域（可多选）',
    options: ['理工技术', '医学健康', '人文社科', '商科管理', '艺术传媒', '法律政治'] },
  { id: 'q16', ring: 4, ringName: '第四', ringDisplayName: '能力特质', type: 'multi',
    text: '你最排斥的方向（可多选）',
    options: ['纯理论研究', '大量背诵', '对人服务', '户外体力工作', '高风险行业'] },
  { id: 'q17', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '什么让你最有成就感？',
    options: ['解出一道难题', '帮助了他人', '作品被认可', '团队协调成功', '赚到钱'] },
  { id: 'q18', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '工作中你最看重什么？',
    options: ['收入高', '稳定安全', '有意义有价值', '自由灵活', '社会地位'] },
  { id: 'q19', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '你更倾向于哪种工作方式？',
    options: ['独立深度工作', '团队协作项目'] },
  { id: 'q20', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '你最感兴趣的行业？',
    options: ['互联网/科技', '金融', '医疗', '教育', '制造/工程', '传媒/艺术', '政府/公务', '法律'] },
  { id: 'q21', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '毕业后你的首选方向？',
    options: ['直接就业', '国内考研', '出国留学', '考公/考编', '还没想好'] },
  { id: 'q22', ring: 5, ringName: '第五', ringDisplayName: '职业期望', type: 'single',
    text: '你对工作城市的偏好？',
    options: ['回家乡', '留在读书城市', '去一线城市', '无所谓'] },
]

const rings = [
  { id: 1, label: '一' },
  { id: 2, label: '二' },
  { id: 3, label: '三' },
  { id: 4, label: '四' },
  { id: 5, label: '五' },
]

const RING_START_INDEX = (() => {
  const index = {}
  let cur = null
  QUESTIONS.forEach((q, i) => { if (q.ring !== cur) { cur = q.ring; index[cur] = i } })
  return index
})()

const showIntro = ref(true)
const currentIndex = ref(0)
const answers = ref({})
const QUESTION_IDS = new Set(QUESTIONS.map((question) => question.id))

const currentQ = computed(() => QUESTIONS[currentIndex.value])
const currentRing = computed(() => currentQ.value.ring)
const isCurrentAnswered = computed(() => isAnswered(currentQ.value))
const completedCount = computed(() =>
  QUESTIONS.filter(isAnswered).length
)

onShow(() => {
  const saved = loadQuestionnaire()
  answers.value = sanitizeAnswers(saved.answers)
  if (Object.keys(answers.value).length !== Object.keys(saved.answers || {}).length) {
    saveQuestionnaire(answers.value)
  }
})

function startTest() {
  showIntro.value = false
}

function isSelected(id, opt) {
  const val = answers.value[id]
  if (!val) return false
  return Array.isArray(val) ? val.includes(opt) : val === opt
}

function sanitizeAnswers(savedAnswers = {}) {
  if (typeof savedAnswers !== 'object' || savedAnswers === null) {
    return {}
  }
  return Object.fromEntries(
    Object.entries(savedAnswers).filter(([id]) => QUESTION_IDS.has(id))
  )
}

function toggleOption(id, opt, type, maxSelect) {
  if (type === 'single') {
    answers.value = { ...answers.value, [id]: opt }
    saveQuestionnaire(answers.value)
    // 如果所有题都已答完，直接完成
    if (getFirstUnansweredIndex() === -1) {
      setTimeout(completeAndReturn, 250)
      return
    }
    if (currentIndex.value < QUESTIONS.length - 1) {
      setTimeout(() => { currentIndex.value++ }, 250)
    }
    return
  }
  const current = Array.isArray(answers.value[id]) ? [...answers.value[id]] : []
  const idx = current.indexOf(opt)
  if (idx === -1 && maxSelect && current.length >= maxSelect) {
    uni.showToast({ title: `最多选 ${maxSelect} 个`, icon: 'none' })
    return
  }
  if (idx === -1) {
    current.push(opt)
  } else {
    current.splice(idx, 1)
  }
  answers.value = { ...answers.value, [id]: current }
  saveQuestionnaire(answers.value)
}

function prev() {
  if (currentIndex.value > 0) currentIndex.value--
}

function next() {
  if (!isCurrentAnswered.value) {
    uni.showToast({
      title: '请先选择本题答案',
      icon: 'none'
    })
    return
  }

  if (currentIndex.value < QUESTIONS.length - 1) {
    currentIndex.value++
  } else {
    finishQuestionnaire()
  }
}

function goToRing(ringId) {
  currentIndex.value = RING_START_INDEX[ringId]
}

function isAnswered(question) {
  const value = answers.value[question.id]
  return value !== '' && value !== undefined && value !== null && !(Array.isArray(value) && value.length === 0)
}

function getFirstUnansweredIndex() {
  return QUESTIONS.findIndex((question) => !isAnswered(question))
}

  function completeAndReturn() {
    uni.showToast({
      title: '五环测评已完成',
      icon: 'success',
      duration: 500
    })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/index/index' })
    }, 500)
  }

  function finishQuestionnaire() {
  const firstUnansweredIndex = getFirstUnansweredIndex()
  if (firstUnansweredIndex !== -1) {
    currentIndex.value = firstUnansweredIndex
    uni.showToast({
      title: `已跳到第 ${firstUnansweredIndex + 1} 题`,
      icon: 'none'
    })
    return
  }

  uni.showToast({
    title: '五环测评已完成',
    icon: 'success',
    duration: 500
  })
  setTimeout(() => {
    uni.switchTab({ url: '/pages/index/index' })
  }, 500)
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
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(79, 70, 229, 0.08);
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

// 头部进度条
.progress-bar-wrap {
  margin-bottom: 32rpx;
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
  background: rgba(226, 232, 240, 0.9);
  border: 1px solid rgba(79, 70, 229, 0.08);
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

// 五环选项卡
.ring-tabs {
  white-space: nowrap;
  margin-bottom: 32rpx;
  z-index: 10;
}

.ring-tab {
  display: inline-block;
  padding: 10rpx 32rpx;
  border-radius: $radius-full;
  font-size: 23rpx;
  font-weight: 600;
  color: $text-secondary;
  background: rgba(255, 255, 255, 0.82);
  margin-right: 16rpx;
  border: 1px solid rgba(79, 70, 229, 0.08);
  transition: all 0.2s;
}

.ring-tab-active {
  background: $grad-royal;
  color: #fff;
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 4rpx 16rpx rgba(99, 102, 241, 0.3);
}

// 题目卡片
.question-card {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(79, 70, 229, 0.10);
  border-radius: $radius-xl;
  padding: 48rpx 36rpx;
  z-index: 10;
}

.ring-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.ring-label {
  font-size: 23rpx;
  color: $brand-violet;
  font-weight: 700;
  letter-spacing: 0;
}

.dimension-pulse-dot {
  width: 8rpx;
  height: 8rpx;
  background-color: $brand-violet;
  border-radius: 50%;
  margin-left: 12rpx;
}

.question-text {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-primary;
  display: block;
  margin-bottom: 12rpx;
  line-height: 1.5;
}

.max-select-hint {
  font-size: 22rpx;
  color: #F59E0B;
  display: block;
  margin-bottom: 32rpx;
  font-weight: 500;
}

.options-list {
  margin-top: 32rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 28rpx 28rpx;
  border-radius: $radius-lg;
  border: 1px solid rgba(79, 70, 229, 0.10);
  background: rgba(248, 250, 252, 0.96);
  transition: all 0.25s;

  &:active {
    transform: scale(0.98);
  }
}

.option-selected {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(79, 70, 229, 0.10);
  box-shadow: inset 0 0 20rpx rgba(99, 102, 241, 0.10);
}

.option-check {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 1px solid rgba(79, 70, 229, 0.22);
  background: #fff;
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

.check-dot {
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
  background: rgba(248, 250, 252, 0.92);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-top: 1px solid rgba(79, 70, 229, 0.08);
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
  font-size: 28rpx;
  font-weight: 700;
  transition: all 0.2s;

  &:active:not(.disabled) {
    transform: scale(0.97);
  }
}

.prev-btn {
  background: rgba(255, 255, 255, 0.9);
  color: $text-primary;
  border: 1px solid rgba(79, 70, 229, 0.10);
}

.next-btn {
  background: $grad-royal;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(99, 102, 241, 0.3);
}

.finish-btn {
  background: $grad-accent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);
}

.disabled {
  opacity: 0.3;
}
</style>
