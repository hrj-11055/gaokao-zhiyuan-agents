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
            {{ source === 'mbti' ? 'MBTI 性格参考' : '霍兰德兴趣参考' }}
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
import { MBTI_TYPE_DESCRIPTIONS } from '../../data/mbti-questions.js'
import { HOLLAND_TYPE_DESCRIPTIONS } from '../../data/holland-questions.js'

const majorName = ref('')
const source = ref('mbti')
const typeCode = ref('')

// 专业描述映射（合并 MBTI 和 Holland 的 descMap）
const majorDescMap = {
  // MBTI 专业
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
  '金融学': '资音乐通与金融市场研究',
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
  '艺术设计': '视觉艺术与设计实践',
  '计算机科学': '计算机系统与软件研究',
  // Holland 专业
  '工业设计': '结合技术与艺术的交叉学科',
  '服装设计与工程': '时尚创意与工程技术结合',
  '产品设计': '从创意到产品的完整设计流程',
  '康复治疗学': '通过技术手段帮助患者康复',
  '生物医学工程': '工程技术在医学领域的应用',
  '风景园林': '户外空间规划与景观设计',
  '环境设计': '创造宜居的生活与工作环境',
  '质量管理工程': '确保产品与服务质量的体系',
}

const majorDesc = computed(() => majorDescMap[majorName.value] || '适合该性格类型的热门专业方向')

// 获取类型信息
const typeInfo = computed(() => {
  if (source.value === 'mbti') {
    return MBTI_TYPE_DESCRIPTIONS[typeCode.value] || null
  }
  // Holland: 先精确匹配，再前缀匹配
  if (HOLLAND_TYPE_DESCRIPTIONS[typeCode.value]) {
    return HOLLAND_TYPE_DESCRIPTIONS[typeCode.value]
  }
  const prefix = typeCode.value.substring(0, 2)
  for (const [key, value] of Object.entries(HOLLAND_TYPE_DESCRIPTIONS)) {
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

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  majorName.value = decodeURIComponent(options.name || '')
  source.value = options.source || 'mbti'
  typeCode.value = options.type || ''

  uni.setNavigationBarTitle({
    title: majorName.value || '专业详情'
  })
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
    background: linear-gradient(135deg, #FF6B00 0%, #EA580C 100%);
    box-shadow: 0 6rpx 16rpx rgba(249, 115, 22, 0.3);

    &:active {
      transform: scale(0.98);
      box-shadow: 0 3rpx 8rpx rgba(249, 115, 22, 0.2);
    }
  }
}
</style>
