const RECOMMENDATION_PATTERNS = [
  /推荐|冲稳保|冲|稳|保|能上|能报|报什么|报哪些|报考/u,
  /适合.*(?:学校|院校|大学|层次|志愿)/u,
  /志愿.*(?:怎么|如何|推荐|方案|填|报|冲|稳|保)/u,
  /(?:怎么|如何).*志愿/u,
  /填报.*(?:志愿|怎么|如何|推荐|方案|冲|稳|保)/u,
]

const SCORE_CONTEXT_PATTERNS = [
  /推荐|冲稳保|能上|能报|报考|学校|院校|大学|录取|分数线|投档线|最低分|位次/u,
  /志愿.*(?:填报|推荐|方案|冲|稳|保|风险|学校|院校)|填报志愿/u,
  /专业方向|专业选择|工科|理科|医学|计算机|财经|法学|师范|就业|风险|避坑|体面|性价比/u,
]

const STARTER_GUIDANCE_PATTERNS = [
  /不知道.*(?:问什么|怎么问|从哪|如何开始)/u,
  /(?:想|要|来).*咨询.*(?:高考|志愿|填报)/u,
  /(?:高考|志愿|填报).*咨询/u,
  /帮我看看|给点建议|怎么开始/u,
]

const CORE_FOLLOWUP_STEPS = [
  { field: 'province', question: '你是哪个省份的考生？' },
  { field: 'category', question: '你现在是物理类还是历史类？' },
  { field: 'score', question: '你的高考分数是多少？如果已经知道全省位次，也可以一起发我。' },
]

const PROVINCE_NAMES = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆',
]

const THREE_PLUS_THREE_PROVINCES = new Set(['北京', '天津', '上海', '浙江', '山东', '海南'])

const PERSONAL_FOLLOWUP_STEPS = [
  {
    field: 'rank',
    question: '如果你已经查到全省位次，也发我一下；同分段录取判断看位次会更准。',
  },
  {
    field: 'family_resources',
    question: '要做靠谱推荐，我先问一个关键问题：家里预算和资源大概是什么情况？比如能不能接受民办或中外合作，父母行业有没有能帮你实习就业的方向。',
  },
  {
    field: 'interest_subjects',
    question: '你自己更喜欢哪类学科？比如数学、物理、计算机、医学、生化、财经、法学、师范，或者有没有明确不想碰的方向。',
  },
  {
    field: 'region_preference',
    question: '城市有没有硬要求？是优先省内，还是可以去外省，北方、西南、东北这些地方能不能接受？',
  },
  {
    field: 'career_goal',
    question: '你未来更看重什么？求稳、想高薪、准备考研、想考公，还是本科毕业直接就业？',
  },
]

const RECOMMENDATION_PROFILE_STEPS = PERSONAL_FOLLOWUP_STEPS.filter((step) => step.field !== 'rank')

const EARLY_PLANNING_PROFILE_STEPS = [
  {
    field: 'family_resources',
    question: '做提前升学规划，我先了解一个现实条件：家里预算和资源大概是什么情况？比如是否考虑民办或中外合作，父母行业能提供哪些认知或实践机会。',
  },
  {
    field: 'interest_subjects',
    question: '孩子目前更喜欢或更擅长哪些学科？有没有明确抗拒、学起来很吃力，或者愿意长期投入探索的方向？',
  },
  {
    field: 'region_preference',
    question: '家庭对未来城市和地域有什么倾向？比如优先省内、接受外省，或者更看重产业机会和生活成本。',
  },
  {
    field: 'career_goal',
    question: '家庭目前更看重哪类长期方向？比如稳定、高薪、深造、考公，还是希望先广泛探索再逐步收敛。',
  },
]

function hasValue(value) {
  return value !== undefined && value !== null && String(value).trim() !== ''
}

function isEarlyPlanningInputs(inputs = {}) {
  return inputs.planning_mode === 'early' || inputs.report_mode === 'planning'
}

function isRecommendationIntent(text = '') {
  const query = String(text || '')
  return RECOMMENDATION_PATTERNS.some((pattern) => pattern.test(query))
}

function shouldUseScoreContext(text = '') {
  const query = String(text || '')
  return SCORE_CONTEXT_PATTERNS.some((pattern) => pattern.test(query))
}

function isStarterGuidanceIntent(text = '') {
  const query = String(text || '')
  if (isRecommendationIntent(query) || isSchoolScoreLookupIntent(query)) return false
  return STARTER_GUIDANCE_PATTERNS.some((pattern) => pattern.test(query))
}

function isSchoolScoreLookupIntent(text = '') {
  return /录取线|分数线|最低分|投档线|多少分|多少位次/u.test(String(text || ''))
}

function classifyScoreQuestion(text = '') {
  if (isSchoolScoreLookupIntent(text)) return 'direct_score_lookup'
  if (shouldUseScoreContext(text)) return 'score_context'
  return 'general_advice'
}

function normalizeProvince(value = '') {
  return String(value || '').replace(/壮族自治区$|回族自治区$|维吾尔自治区$|自治区$|省$|市$/u, '').trim()
}

function normalizeScoreApiCategory(province = '', category = '') {
  const normalizedProvince = normalizeProvince(province)
  const normalizedCategory = String(category || '').trim()
  if (
    THREE_PLUS_THREE_PROVINCES.has(normalizedProvince) &&
    /^(物理类|历史类|理科|文科)$/u.test(normalizedCategory)
  ) {
    return '综合'
  }
  if (normalizedCategory === '理科') return '物理类'
  if (normalizedCategory === '文科') return '历史类'
  return normalizedCategory
}

function extractProvinceFromQuery(query = '', inputs = {}) {
  const text = String(query || '')
  for (const province of PROVINCE_NAMES) {
    const targetPattern = new RegExp(`(?:在|面向|对)${province}(?:省|市|自治区)?`, 'u')
    if (targetPattern.test(text)) {
      return normalizeProvince(province)
    }
  }
  const fromQuery = PROVINCE_NAMES.find((province) => text.includes(province))
  return normalizeProvince(fromQuery || inputs.province || '')
}

function extractProfileInputsFromText(query = '') {
  const text = String(query || '')
  const inputs = {}
  const province = extractProvinceFromQuery(text, {})
  if (province) {
    inputs.province = province
  }

  if (/物理类|理科/u.test(text)) {
    inputs.category = '物理类'
  } else if (/历史类|文科/u.test(text)) {
    inputs.category = '历史类'
  }

  const scoreMatch = text.match(/(?<!\d)([1-7]\d{2})\s*分/u)
  if (scoreMatch) {
    inputs.score = scoreMatch[1]
  }

  const rankMatch = text.match(/(?:位次|排名|排位)\D{0,6}(\d{3,8})/u)
  if (rankMatch) {
    inputs.rank = rankMatch[1]
  }

  return inputs
}

function cleanSchoolName(value = '') {
  return String(value || '')
    .replace(/^(请问|帮我查一下|帮我查|查一下|想问|问一下)/u, '')
    .replace(/^(20\d{2}年?|近几年|去年|今年)/u, '')
    .replace(/[，。？！?；;：:\s]/g, '')
    .replace(/的$/u, '')
    .trim()
}

function extractSchoolScoreLookup(query = '', inputs = {}) {
  const text = String(query || '').trim()
  if (!isSchoolScoreLookupIntent(text)) return null

  const province = extractProvinceFromQuery(text, inputs)
  if (!province) return null

  const provincePattern = `${province}(?:省|市|自治区)?`
  const patterns = [
    new RegExp(`^(.+?)(?:在|面向|对)${provincePattern}.*(?:录取线|分数线|最低分|投档线|多少分|多少位次)`, 'u'),
    /^(.*?大学).*?(?:录取线|分数线|最低分|投档线|多少分|多少位次)/u,
    /^(.+?)(?:录取线|分数线|最低分|投档线|多少分|多少位次)/u,
  ]

  for (const pattern of patterns) {
    const match = text.match(pattern)
    const schoolName = cleanSchoolName(match && match[1])
    if (schoolName && schoolName.length >= 2) {
      return { schoolName, province }
    }
  }

  return null
}

function getNextCoreProfileFollowup(inputs = {}) {
  return CORE_FOLLOWUP_STEPS.find((step) => {
    if (step.field === 'score' && isEarlyPlanningInputs(inputs)) return false
    return !hasValue(inputs[step.field])
  }) || null
}

function getNextPersonalProfileFollowup(inputs = {}) {
  const steps = isEarlyPlanningInputs(inputs) ? EARLY_PLANNING_PROFILE_STEPS : PERSONAL_FOLLOWUP_STEPS
  return steps.find((step) => !hasValue(inputs[step.field])) || null
}

function getNextRecommendationProfileFollowup(inputs = {}) {
  const steps = isEarlyPlanningInputs(inputs) ? EARLY_PLANNING_PROFILE_STEPS : RECOMMENDATION_PROFILE_STEPS
  return steps.find((step) => !hasValue(inputs[step.field])) || null
}

function hasAnyPersonalProfileInput(inputs = {}) {
  return PERSONAL_FOLLOWUP_STEPS
    .filter((step) => step.field !== 'rank')
    .some((step) => hasValue(inputs[step.field]))
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

function buildDeepProfileGateAnswer({ query = '', inputs = {}, conversationId = '' } = {}) {
  if (!isRecommendationIntent(query)) return null
  if (getNextCoreProfileFollowup(inputs)) return null

  const followup = getNextRecommendationProfileFollowup(inputs)
  if (!followup) return null

  const introduction = isEarlyPlanningInputs(inputs)
    ? '当前是提前升学规划。先把孩子的兴趣、能力、家庭约束和未来方向说清楚，再安排可执行的探索任务。'
    : '先别急着直接排冲稳保。只按省份、科类和分数给学校名单，很容易把专业、城市和家庭成本这些关键约束漏掉。'

  return {
    answer: [
      introduction,
      followup.question,
    ].join('\n\n'),
    conversation_id: conversationId || '',
    message_id: `deep_profile_gate_${Date.now()}`,
    metadata: {
      deep_profile_gate: true,
      field: followup.field,
    },
  }
}

function formatProfileLine(inputs = {}) {
  const parts = []
  if (inputs.province) parts.push(inputs.province)
  if (inputs.category) parts.push(inputs.category)
  if (inputs.grade) parts.push(inputs.grade)
  if (inputs.identity) parts.push(inputs.identity)
  if (inputs.score_range) parts.push(`预估区间${inputs.score_range}`)
  if (inputs.score) parts.push(`${inputs.score}分`)
  if (inputs.rank) parts.push(`位次${inputs.rank}`)
  return parts.join(' · ')
}

function buildStarterGuidanceAnswer({ inputs = {}, conversationId = '' } = {}) {
  const coreFollowup = getNextCoreProfileFollowup(inputs)
  if (coreFollowup) {
    return {
      event: 'message',
      answer: `你不用先想好怎么问，我会一步一步带你拆。先别急着要学校名单，核心信息不齐时很容易误判。\n\n${coreFollowup.question}`,
      conversation_id: conversationId || '',
      message_id: `starter_guidance_${Date.now()}`,
      metadata: {
        starter_guidance: true,
        field: coreFollowup.field,
      },
    }
  }

  const profileLine = formatProfileLine(inputs)
  const next = getNextPersonalProfileFollowup(inputs)
  const followup = next ? `\n\n${next.question}` : ''

  if (isEarlyPlanningInputs(inputs)) {
    return {
      event: 'message',
      answer: [
        profileLine ? `我先按你的档案看：${profileLine}。` : '我先按你目前给的信息看。',
        '当前先做提前升学规划，把专业探索和未来一年的行动安排清楚。',
        '建议先按这个顺序来：识别孩子的学科优势和兴趣边界，筛专业方向，再规划能力补齐、选科与实践探索，最后建立未来院校层次的校准方法。',
        '我最建议你先问这一句：未来一年最值得优先验证哪些专业方向，家长和孩子分别要做什么。'
      ].join('\n') + followup,
      conversation_id: conversationId || '',
      message_id: `starter_guidance_${Date.now()}`,
      metadata: {
        starter_guidance: true,
        planning_mode: true,
      },
    }
  }

  return {
    event: 'message',
    answer: [
      profileLine ? `我先按你的档案看：${profileLine}。` : '我先按你目前给的信息看。',
      '你不用会提问，志愿咨询先按这个顺序来：先看分数和位次的真实落点，再排除明显不适合的专业，接着看城市和预算，最后才排冲稳保。',
      '我最建议你先问这一句：按我的分数和位次，哪些选择是务实的，哪些只是看起来体面但风险很高。',
      '如果你愿意，我可以先从冲稳保初筛开始，也可以先帮你做专业排雷。'
    ].join('\n') + followup,
    conversation_id: conversationId || '',
    message_id: `starter_guidance_${Date.now()}`,
    metadata: {
      starter_guidance: true,
    },
  }
}

function compactText(value, maxLength = 80) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text
}

function formatScoreMatchContext(matchData = {}, inputs = {}) {
  const tiers = ['冲', '稳', '保']
  const lines = []
  const contextTiers = matchData.tiers || matchData
  const isEstimated = matchData.query?.mode && matchData.query.mode !== 'official'
  const estimatedTierLabels = { '冲': '较高目标层', '稳': '匹配目标层', '保': '保守目标层' }
  const scoreLabel = inputs.score
    ? `${inputs.score}分`
    : (inputs.score_range ? `预估区间${inputs.score_range}` : `${matchData.query?.score || matchData.score || ''}分`)

  lines.push(`定位性质：${isEstimated ? '预估院校层次参考，不是正式志愿推荐' : '正式冲稳保参考'}`)
  lines.push(`查询条件：${inputs.province || matchData.query?.province || matchData.province || ''} ${inputs.category || matchData.query?.category || matchData.category || ''} ${scoreLabel}，年份 ${matchData.query?.year || matchData.year || inputs.year || '未标明'}`)

  for (const tier of tiers) {
    const rows = Array.isArray(contextTiers[tier]) ? contextTiers[tier] : []
    if (rows.length === 0) {
      lines.push(`${tier}：本次查询未返回可用学校`)
      continue
    }
    rows.slice(0, 5).forEach((row, index) => {
      const school = row.school_name || row.name || row.school || '未知学校'
      const scoreText = row.min_score
        ? `${row.min_score}${row.max_score && row.max_score !== row.min_score ? `-${row.max_score}` : ''}分`
        : '分数未返回'
      const rankText = row.min_rank ? `，最低位次 ${row.min_rank}` : ''
      const majors = row.majors ? `，专业：${compactText(row.majors, 120)}` : ''
      const reason = row.reason ? `，依据：${row.reason}` : ''
      const tierLabel = isEstimated ? estimatedTierLabels[tier] : tier
      lines.push(`${tierLabel}${index + 1}. ${school}：${scoreText}${rankText}${majors}${reason}`)
    })
  }

  return lines.join('\n')
}

function formatSchoolScoreContext(scoreData = {}, lookup = {}) {
  const rows = Array.isArray(scoreData.majors) ? scoreData.majors : []
  const school = scoreData.school || lookup.schoolName || ''
  const province = scoreData.province || lookup.province || ''

  if (rows.length === 0) {
    return `${school}在${province}：本次查询未返回分数线数据`
  }

  const lines = [`${school}在${province}的专业分数线（查询返回 ${scoreData.total || rows.length} 条，以下为前 ${Math.min(rows.length, 10)} 条）：`]
  rows.slice(0, 10).forEach((row, index) => {
    const year = row.year || lookup.year || '未标明年份'
    const category = row.category ? `，${row.category}` : ''
    const batch = row.batch ? `，${row.batch}` : ''
    const rank = row.min_rank ? `，最低位次 ${row.min_rank}` : ''
    const avg = row.avg_score ? `，平均分 ${row.avg_score}` : ''
    lines.push(`${index + 1}. ${year}${category}${batch}，${row.major_name || '未标明专业'}：最低分 ${row.min_score || '未返回'}${rank}${avg}`)
  })
  return lines.join('\n')
}

function buildSchoolScoreGuidedQuery(query = '', scoreContext = '') {
  if (!scoreContext) return query

  return [
    buildCurrentAdvisoryContext(),
    '用户在问具体学校录取分数线。必须优先使用【后端学校分数线查询结果】里的年份、科类、专业、最低分、位次。',
    '不要编造未返回的年份、位次或专业；如果数据未覆盖，就明确说未返回。',
    `\n【后端学校分数线查询结果】\n${scoreContext}`,
    '',
    `用户原问题：${query}`,
  ].join('\n')
}

function buildCurrentAdvisoryContext(inputs = {}) {
  const profileParts = []
  if (inputs.province) profileParts.push(`省份：${inputs.province}`)
  if (inputs.category) profileParts.push(`科类：${inputs.category}`)
  if (inputs.grade) profileParts.push(`年级：${inputs.grade}`)
  if (inputs.identity) profileParts.push(`身份：${inputs.identity}`)
  if (inputs.score_range) profileParts.push(`预估区间：${inputs.score_range}`)
  if (inputs.score) profileParts.push(`分数：${inputs.score}`)
  if (inputs.rank) profileParts.push(`位次：${inputs.rank}`)
  if (inputs.family_resources) profileParts.push(`家庭资源：${inputs.family_resources}`)
  if (inputs.interest_subjects) profileParts.push(`兴趣学科：${inputs.interest_subjects}`)
  if (inputs.region_preference) profileParts.push(`地域偏好：${inputs.region_preference}`)
  if (inputs.career_goal) profileParts.push(`发展倾向：${inputs.career_goal}`)

  if (isEarlyPlanningInputs(inputs)) {
    return [
      '【当前咨询背景】',
      '当前用户是高一/高二家庭的提前升学规划场景，尚未掌握正式高考分数和位次。',
      '咨询重点是专业方向、学科能力、选科与学习路径、探索任务、家庭约束和未来校准方法；不能输出精确冲稳保或把院校名单当成最终志愿推荐。',
      '涉及历史录取数据时，只使用 2024-2025 年数据，优先使用 2025 年后端分数线或知识库结果；没有返回就明确说未覆盖。',
      profileParts.length ? `【已知考生档案】${profileParts.join('；')}` : '【已知考生档案】本轮未取得完整档案。',
    ].join('\n')
  }

  return [
    '【当前咨询背景】',
    '现在是 2026 年 6 月，你正在为 2026 年高考生做志愿填报规划。',
    'DeepSeek-V4 Pro 模型自身知识覆盖到 2025 年；但涉及录取分数线、投档线、位次和院校专业推荐时，必须优先使用系统提供的 2025 年后端分数线查询结果和 Dify 知识库，不要只按模型记忆回答。',
    '不要声称“我的知识截止到 2024 年”或“无法了解 2025 数据”；如果系统没有返回数据，只能说“本次后端/知识库未返回相关数据”。',
    profileParts.length ? `【已知考生档案】${profileParts.join('；')}` : '【已知考生档案】本轮未取得完整档案。',
  ].join('\n')
}

function buildPostAnswerFollowupInstruction(inputs = {}) {
  const followup = getNextPersonalProfileFollowup(inputs)
  if (!followup) return ''

  return [
    '回答完用户当前问题后，只能在最后追加下面这一句追问，不要提前反问，不要列待补充清单：',
    followup.question,
  ].join('\n')
}

function buildRecommendationGuidedQuery(query = '', options = {}) {
  if (isStarterGuidanceIntent(query)) return query

  const inputs = options.inputs || {}
  const scoreContext = String(options.scoreContext || '').trim()
  const questionClass = classifyScoreQuestion(query)
  const earlyPlanning = isEarlyPlanningInputs(inputs)
  if (questionClass === 'general_advice' && !scoreContext && !earlyPlanning) return query

  const needsScoreContext = shouldUseScoreContext(query)
  const postAnswerFollowup = buildPostAnswerFollowupInstruction(inputs)
  const recommendationIntent = isRecommendationIntent(query)
  const taskInstruction = earlyPlanning
    ? [
        '当前任务是提前升学规划，不是高三志愿填报推荐。',
        '即使用户说“推荐学校”或“冲稳保”，也要先解释当前不能输出精确冲稳保，并转为专业方向、能力差距、学习路径、探索任务、家长行动和未来院校层次校准方法。',
        '如果系统提供了【后端预估院校层次参考】，可以用其中学校帮助家庭理解目标层次，但必须称为预估参考，不能当作最终志愿推荐或录取承诺。',
      ].join('\n')
    : recommendationIntent
    ? [
        '若给出院校、专业或志愿推荐，每个关键推荐必须包含：年份、最低分/位次等分数线证据、为什么推荐、风险点、下一步。',
        '必须优先使用【后端分数线查询结果】里的学校和分数；没有出现在查询结果里的学校，不能说成“已查到”。',
        '信息仍偏泛时，也要先基于已知省份、科类、分数给方向判断。',
      ].join('\n')
    : [
        '用户当前问题不一定是在要最终冲稳保名单。先精准回答原问题，不要硬凑学校名单。',
        '如果是在问专业方向、工科/理科、避坑或就业风险，要结合已知档案和分数段层次回答，并说明哪些判断来自 2025 分数线/知识库，哪些只是一般策略。',
      ].join('\n')

  return [
    buildCurrentAdvisoryContext(inputs),
    '先回答用户原问题，不要先反问。',
    '不要为了压缩篇幅删减关键判断；需要展开时可以完整说明，但必须完整收尾，不能在句中结束。',
    taskInstruction,
    '整段回复里最多出现一个问句。',
    postAnswerFollowup,
    scoreContext
      ? `\n【${earlyPlanning ? '后端预估院校层次参考' : '后端分数线查询结果'}】\n${scoreContext}`
      : (needsScoreContext ? '\n【后端分数线查询结果】本次未取得可用分数线数据；涉及学校/分数/推荐时必须明确说明数据未返回，不能编造分数线。' : ''),
    '',
    `用户原问题：${query}`,
  ].join('\n')
}

module.exports = {
  buildProfileGateAnswer,
  buildDeepProfileGateAnswer,
  buildRecommendationGuidedQuery,
  buildSchoolScoreGuidedQuery,
  buildPostAnswerFollowupInstruction,
  buildStarterGuidanceAnswer,
  extractSchoolScoreLookup,
  extractProfileInputsFromText,
  formatScoreMatchContext,
  formatSchoolScoreContext,
  getNextCoreProfileFollowup,
  getNextPersonalProfileFollowup,
  getNextRecommendationProfileFollowup,
  hasAnyPersonalProfileInput,
  isSchoolScoreLookupIntent,
  isRecommendationIntent,
  normalizeScoreApiCategory,
  shouldUseScoreContext,
  classifyScoreQuestion,
  isStarterGuidanceIntent,
}
