<template>
  <view class="guide-wrap">
    <view class="guide-head">
      <text class="guide-kicker">先把问题变小</text>
      <text class="guide-title">不知道怎么问，就按真实处境开始</text>
      <text class="guide-desc">{{ profileLine }}</text>
    </view>

    <view class="guide-grid">
      <view
        v-for="item in guideCards"
        :key="item.key"
        class="guide-card"
        :class="`guide-card-${item.tone}`"
        @click="$emit('select', item.prompt)"
      >
        <view class="guide-card-top">
          <text class="guide-badge">{{ item.badge }}</text>
          <text class="guide-label">{{ item.label }}</text>
        </view>
        <text class="guide-copy">{{ item.copy }}</text>
      </view>
    </view>

    <view class="guide-strip">
      <text class="guide-strip-title">真心话</text>
      <text class="guide-strip-copy">{{ guideStripCopy }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

defineEmits(['select'])

const props = defineProps({
  profile: {
    type: Object,
    default: () => ({})
  }
})

const isEarlyPlanning = computed(() => (
  props.profile?.planning_mode === 'early' || props.profile?.report_mode === 'planning'
))

const profileLine = computed(() => {
  const province = props.profile?.province || '你的省份'
  const category = props.profile?.category || '科类'
  if (isEarlyPlanning.value) {
    const stage = props.profile?.grade || '提前规划'
    return `${province} · ${category} · ${stage}`
  }
  const score = props.profile?.score ? `${props.profile.score}分` : '分数'
  const rank = props.profile?.rank ? `，位次${props.profile.rank}` : ''
  return `${province} · ${category} · ${score}${rank}`
})

const guideCards = computed(() => {
  const province = props.profile?.province || '广东'
  const category = props.profile?.category || '物理类'
  if (isEarlyPlanning.value) {
    const stage = props.profile?.grade || '高一/高二'
    const base = `${province}${category}${stage}`
    return [
      {
        key: 'planning-map',
        tone: 'blue',
        badge: '01',
        label: '升学规划',
        copy: '先明确未来一年最值得验证的方向和任务。',
        prompt: `我是${base}家长，请帮我做提前升学规划，告诉我现在最该验证什么。`
      },
      {
        key: 'major-explore',
        tone: 'amber',
        badge: '02',
        label: '专业探索',
        copy: '先找到值得深入了解和需要谨慎的专业方向。',
        prompt: `结合${category}，哪些专业方向值得优先探索，哪些方向要谨慎？`
      },
      {
        key: 'ability-path',
        tone: 'green',
        badge: '03',
        label: '能力路径',
        copy: '把学科能力、实践经历和探索任务排出优先级。',
        prompt: '未来一年应该重点补哪些学科能力、实践经历和信息搜集任务？'
      },
      {
        key: 'parent-actions',
        tone: 'slate',
        badge: '04',
        label: '家长行动',
        copy: '帮助孩子探索，但不替孩子做决定。',
        prompt: '家长现在应该怎样帮助孩子做专业探索，又避免替孩子做决定？'
      }
    ]
  }
  const score = props.profile?.score || '580'
  const rankPart = props.profile?.rank ? `，位次${props.profile.rank}` : ''
  const base = `${province}${category}${score}分${rankPart}`

  return [
    {
      key: 'score-range',
      tone: 'blue',
      badge: '01',
      label: '先看落点',
      copy: '这个分数到底能碰哪些学校，先别凭感觉猜。',
      prompt: `我是${base}，请先按后端分数线给我一个冲稳保初筛，必须带最低分和位次证据。`
    },
    {
      key: 'avoid-risk',
      tone: 'amber',
      badge: '02',
      label: '专业排雷',
      copy: '不确定专业时，先排除明显不适合自己的方向。',
      prompt: `我是${base}，普通家庭，请真诚地告诉我这个分数段哪些专业方向要谨慎，为什么。`
    },
    {
      key: 'major-choice',
      tone: 'green',
      badge: '03',
      label: '专业取舍',
      copy: '把热门、稳定、考研、就业放在一张桌子上比较。',
      prompt: `我是${base}，计算机、法学、师范、医学这些方向怎么取舍？请按就业、考研和风险说实话。`
    },
    {
      key: 'city-budget',
      tone: 'slate',
      badge: '04',
      label: '现实约束',
      copy: '城市、预算和家庭资源会改变最优解。',
      prompt: `我是${base}，如果优先省内、预算有限、想稳一点，学校和专业应该怎么排序？`
    }
  ]
})

const guideStripCopy = computed(() => (
  isEarlyPlanning.value
    ? '先认识孩子，再看专业方向；先做探索，再谈未来院校层次。'
    : '先问风险，再问学校；先看位次，再谈冲稳保。'
))
</script>

<style lang="scss" scoped>
.guide-wrap {
  margin: 0 32rpx 28rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.guide-head {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding: 4rpx 4rpx 2rpx;
}

.guide-kicker {
  font-size: 22rpx;
  color: #0F766E;
  font-weight: 800;
}

.guide-title {
  font-size: 32rpx;
  line-height: 1.25;
  color: $text-primary;
  font-weight: 900;
}

.guide-desc {
  font-size: 24rpx;
  line-height: 1.45;
  color: $text-secondary;
}

.guide-grid {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.guide-card {
  min-height: 150rpx;
  padding: 22rpx 24rpx;
  border-radius: $radius-md;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.06);
  box-sizing: border-box;
  transition: transform 0.18s ease, box-shadow 0.18s ease;

  &:active {
    transform: scale(0.985);
    box-shadow: 0 6rpx 18rpx rgba(15, 23, 42, 0.06);
  }
}

.guide-card-top {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 12rpx;
}

.guide-badge {
  width: 48rpx;
  height: 36rpx;
  border-radius: 6rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 21rpx;
  font-weight: 900;
}

.guide-label {
  font-size: 28rpx;
  color: $text-primary;
  font-weight: 900;
}

.guide-copy {
  display: block;
  font-size: 24rpx;
  line-height: 1.48;
  color: $text-secondary;
}

.guide-card-blue {
  border-left: 6rpx solid #2563EB;
  .guide-badge {
    color: #1D4ED8;
    background: #DBEAFE;
  }
}

.guide-card-amber {
  border-left: 6rpx solid #D97706;
  .guide-badge {
    color: #92400E;
    background: #FEF3C7;
  }
}

.guide-card-green {
  border-left: 6rpx solid #059669;
  .guide-badge {
    color: #047857;
    background: #D1FAE5;
  }
}

.guide-card-slate {
  border-left: 6rpx solid #475569;
  .guide-badge {
    color: #334155;
    background: #E2E8F0;
  }
}

.guide-strip {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  padding: 18rpx 20rpx;
  border-radius: $radius-md;
  background: rgba(15, 23, 42, 0.88);
}

.guide-strip-title {
  flex-shrink: 0;
  font-size: 23rpx;
  color: #FDE68A;
  font-weight: 900;
}

.guide-strip-copy {
  font-size: 23rpx;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.9);
}
</style>
