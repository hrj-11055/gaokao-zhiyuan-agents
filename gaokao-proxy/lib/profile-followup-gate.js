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

function buildRecommendationGuidedQuery(query = '') {
  if (!isRecommendationIntent(query)) return query

  return [
    '先回答用户原问题，不要先反问。',
    '最多 3 个学校/专业组合，总字数控制在 600 字以内；宁可少列，也必须完整收尾，不能在句中结束。',
    '若给出院校、专业或志愿推荐，每个关键推荐必须包含：为什么推荐、风险点、下一步。',
    '信息仍偏泛时，也要先基于已知省份、科类、分数给方向判断，再只追问一个最关键缺口。',
    '',
    `用户原问题：${query}`,
  ].join('\n')
}

module.exports = {
  buildProfileGateAnswer,
  buildRecommendationGuidedQuery,
  getNextCoreProfileFollowup,
  isRecommendationIntent,
}
