const RECOMMENDATION_KEYWORDS = [
  '推荐',
  '冲',
  '稳',
  '保',
  '学校',
  '院校',
  '大学',
  '专业',
  '志愿',
  '填报',
  '能上',
  '报考',
  '适合',
  '录取',
]

const CORE_FOLLOWUP_STEPS = [
  { field: 'province', question: '你是哪个省份的考生？' },
  { field: 'category', question: '你现在是物理类还是历史类？' },
  { field: 'score', question: '你的高考分数是多少？如果已经知道全省位次，也可以一起发我。' },
]

function hasValue(value) {
  return value !== undefined && value !== null && String(value).trim() !== ''
}

function isRecommendationIntent(text = '') {
  const query = String(text || '')
  return RECOMMENDATION_KEYWORDS.some((keyword) => query.includes(keyword))
}

function getNextCoreProfileFollowup(inputs = {}) {
  return CORE_FOLLOWUP_STEPS.find((step) => !hasValue(inputs[step.field])) || null
}

function buildProfileGateAnswer({ query = '', inputs = {}, conversationId = '' } = {}) {
  if (!isRecommendationIntent(query)) return null

  const followup = getNextCoreProfileFollowup(inputs)
  if (!followup) return null

  return {
    answer: followup.question,
    conversation_id: conversationId || '',
    message_id: `profile_gate_${Date.now()}`,
    metadata: {
      profile_gate: true,
      field: followup.field,
    },
  }
}

module.exports = {
  buildProfileGateAnswer,
  getNextCoreProfileFollowup,
  isRecommendationIntent,
}
