<template>
  <view class="page">
    <!-- 介绍页 -->
    <view v-if="showIntro" class="intro-container">
      <view class="intro-card">
        <view class="intro-icon">📋</view>
        <text class="intro-title">五环问卷测评</text>
        <text class="intro-desc">通过 22 道题目的深度评估，全方位了解你的学习风格、学业现状、家庭背景、能力特质和职业期望。</text>
        
        <view class="intro-tips">
          <text class="tips-title">💡 答题建议：</text>
          <text class="tips-text">1. 请根据你目前的真实情况作答，不要有所顾虑。</text>
          <text class="tips-text">2. 部分题目可以多选，请仔细阅读题目要求。</text>
          <text class="tips-text">3. 答题过程中尽量顺从第一直觉，完成所有题目后继续完成其余测评。</text>
        </view>
        
        <button class="start-btn" @click="startTest">开始测试</button>
      </view>
    </view>

    <!-- 测试内容 -->
    <block v-else>
    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-info">
        <text class="progress-text">已完成 {{ completedCount }}/{{ QUESTIONS.length }} 题</text>
        <text class="progress-pct">{{ Math.round(completedCount / QUESTIONS.length * 100) }}%</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: (completedCount / 22 * 100) + '%' }" />
      </view>
    </view>

    <!-- 环选项卡 -->
    <scroll-view class="ring-tabs" scroll-x>
      <view
        v-for="ring in rings"
        :key="ring.id"
        class="ring-tab"
        :class="{ 'ring-tab-active': currentRing === ring.id }"
        @click="goToRing(ring.id)"
      >
        第{{ ring.label }}环
      </view>
    </scroll-view>

    <!-- 当前题目 -->
    <view class="question-card">
      <text class="ring-label">第{{ currentQ.ringName }}环 · {{ currentQ.ringDisplayName }}</text>
      <text class="question-text">{{ currentQ.text }}</text>
      <text v-if="currentQ.maxSelect" class="max-select-hint">最多选 {{ currentQ.maxSelect }} 个</text>

      <!-- 选项列表 -->
      <view class="options-list">
        <view
          v-for="opt in currentQ.options"
          :key="opt"
          class="option-item"
          :class="isSelected(currentQ.id, opt) ? 'option-selected' : ''"
          @click="toggleOption(currentQ.id, opt, currentQ.type, currentQ.maxSelect)"
        >
          <view class="option-check">
            <text v-if="isSelected(currentQ.id, opt)" class="check-icon">✓</text>
          </view>
          <text class="option-text">{{ opt }}</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">上一题</view>
      <view v-if="currentIndex < QUESTIONS.length - 1" class="nav-btn next-btn" @click="next">下一题</view>
      <view v-else class="nav-btn next-btn" @click="next">完成</view>
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
  { id: 'q9', ring: 2, ringName: '第二', ringDisplayName: '学业现状', type: 'single',
    text: '你的成绩在班级大概位置？',
    options: ['前 10%', '前 30%', '中等水平', '偏后'] },
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

const currentQ = computed(() => QUESTIONS[currentIndex.value])
const currentRing = computed(() => currentQ.value.ring)
const completedCount = computed(() =>
  Object.entries(answers.value).filter(([, v]) => v !== '' && !(Array.isArray(v) && v.length === 0)).length
)

onShow(() => {
  const saved = loadQuestionnaire()
  answers.value = saved.answers || {}
})

function startTest() {
  showIntro.value = false
}

function isSelected(id, opt) {
  const val = answers.value[id]
  if (!val) return false
  return Array.isArray(val) ? val.includes(opt) : val === opt
}

function toggleOption(id, opt, type, maxSelect) {
  if (type === 'single') {
    answers.value = { ...answers.value, [id]: opt }
    saveQuestionnaire(answers.value)
    if (currentIndex.value < QUESTIONS.length - 1) {
      setTimeout(() => { currentIndex.value++ }, 200)
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
  if (currentIndex.value < QUESTIONS.length - 1) {
    currentIndex.value++
  } else {
    finishQuestionnaire()
  }
}

function goToRing(ringId) {
  currentIndex.value = RING_START_INDEX[ringId]
}

function finishQuestionnaire() {
  if (completedCount.value < QUESTIONS.length) {
    uni.showToast({
      title: `还有 ${QUESTIONS.length - completedCount.value} 题未完成`,
      icon: 'none'
    })
    return
  }

  uni.showModal({
    title: '五环问卷已完成',
    content: '请继续完成 MBTI 和霍兰德测评。三项测评全部完成后，可在首页或我的页面生成综合报告。',
    confirmText: '去测评中心',
    cancelText: '返回首页',
    success: (res) => {
      if (res.confirm) {
        uni.switchTab({ url: '/pages/assessments/assessments' })
      } else {
        uni.switchTab({ url: '/pages/index/index' })
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 24rpx 32rpx 200rpx;
  box-sizing: border-box;
}

.intro-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 48rpx - 200rpx);
}

.intro-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 60rpx 40rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

.intro-icon {
  font-size: 96rpx;
  margin-bottom: 32rpx;
}

.intro-title {
  font-size: 40rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 24rpx;
  text-align: center;
}

.intro-desc {
  font-size: 28rpx;
  color: $text-secondary;
  line-height: 1.6;
  text-align: center;
  margin-bottom: 48rpx;
}

.intro-tips {
  background: $bg-input;
  border-radius: $radius-lg;
  padding: 32rpx;
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 60rpx;
}

.tips-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 16rpx;
  display: block;
}

.tips-text {
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.8;
  display: block;
  margin-bottom: 8rpx;
}

.start-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
  border-radius: $radius-full;
  font-size: 32rpx;
  font-weight: 600;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
}
.start-btn::after {
  border: none;
}
.start-btn:active {
  opacity: 0.9;
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
  background: #7c3aed;
  border-radius: $radius-full;
  height: 8rpx;
  transition: width 0.3s;
}

.ring-tabs {
  white-space: nowrap;
  margin-bottom: 24rpx;
}

.ring-tab {
  display: inline-block;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  font-size: 24rpx;
  color: $text-muted;
  background: $bg-white;
  margin-right: 12rpx;
  border: 2rpx solid $border-light;
}

.ring-tab-active {
  background: #7c3aed;
  color: #fff;
  border-color: #7c3aed;
}

.question-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.ring-label {
  font-size: 22rpx;
  color: #7c3aed;
  font-weight: 600;
  display: block;
  margin-bottom: 12rpx;
}

.question-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
  margin-bottom: 8rpx;
  line-height: 1.5;
}

.max-select-hint {
  font-size: 22rpx;
  color: $text-muted;
  display: block;
  margin-bottom: 24rpx;
}

.options-list {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  border-radius: $radius-lg;
  border: 2rpx solid $border-light;
  background: $bg-page;
}

.option-selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}

.option-check {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 2rpx solid $border-light;
  background: $bg-white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .option-selected & {
    background: #7c3aed;
    border-color: #7c3aed;
  }
}

.check-icon {
  color: #fff;
  font-size: 20rpx;
}

.option-text {
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.4;
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
  height: 80rpx;
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
}

.next-btn {
  background: #7c3aed;
  color: #fff;
}

.disabled {
  opacity: 0.4;
}

</style>
