const RECOMMENDATION_PATTERNS = [
  /推荐|冲稳保|冲|稳|保|能上|能报|报什么|报哪些|报考/u,
  /适合.*(?:学校|院校|大学|层次|志愿)/u,
  /志愿.*(?:怎么|如何|推荐|方案|填|报|冲|稳|保)/u,
  /(?:怎么|如何).*志愿/u,
  /填报.*(?:志愿|怎么|如何|推荐|方案|冲|稳|保)/u,
]

const CORE_FOLLOWUP_STEPS = [
  {
    field: 'province',
    question: '你是哪个省份的考生？',
  },
  {
    field: 'category',
    question: '你现在是物理类还是历史类？',
  },
  {
    field: 'score',
    question: '你的高考分数是多少？如果已经知道全省位次，也可以一起发我。',
  },
]

const PERSONAL_FOLLOWUP_STEPS = [
  {
    field: 'rank',
    question: '如果你已经查到全省位次，也发我一下；同分段录取判断看位次会更准。',
  },
  {
    field: 'family_resources',
    question: '我再问一个关键问题：家里预算和资源大概是什么情况？比如能不能接受民办或中外合作，父母行业有没有能帮你实习就业的方向。',
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

const PERSONAL_FOLLOWUP_ANCHORS = {
  rank: ['全省位次', '同分段', '录取判断', '位次会更准'],
  family_resources: ['家庭资源', '家里预算', '民办', '中外合作', '父母行业', '实习就业'],
  interest_subjects: ['更喜欢哪类学科', '明确不想碰', '数学', '物理', '计算机', '医学'],
  region_preference: ['城市有没有硬要求', '优先省内', '可以去外省', '北方', '西南', '东北'],
  career_goal: ['未来更看重什么', '求稳', '想高薪', '准备考研', '想考公', '直接就业'],
}

const PROVINCE_NAMES = [
  '北京',
  '天津',
  '河北',
  '山西',
  '内蒙古',
  '辽宁',
  '吉林',
  '黑龙江',
  '上海',
  '江苏',
  '浙江',
  '安徽',
  '福建',
  '江西',
  '山东',
  '河南',
  '湖北',
  '湖南',
  '广东',
  '广西',
  '海南',
  '重庆',
  '四川',
  '贵州',
  '云南',
  '西藏',
  '陕西',
  '甘肃',
  '青海',
  '宁夏',
  '新疆',
]

function hasValue(value) {
  return value !== undefined && value !== null && String(value).trim() !== ''
}

function normalizeQuestionText(value) {
  return String(value || '')
    .replace(/\s+/g, '')
    .replace(/[，。？！：:；;、/（）()“”"']/g, '')
}

export function containsProfileFollowupQuestion(text = '', followupOrField = '') {
  const source = String(text || '')
  if (!source.trim()) return false

  const field = typeof followupOrField === 'string' ? followupOrField : followupOrField?.field
  const question = typeof followupOrField === 'object' ? followupOrField?.question : ''
  const normalizedSource = normalizeQuestionText(source)
  const normalizedQuestion = normalizeQuestionText(question)

  if (normalizedQuestion && normalizedSource.includes(normalizedQuestion)) {
    return true
  }

  const anchors = PERSONAL_FOLLOWUP_ANCHORS[field] || []
  if (!anchors.length || !/[?？]/.test(source)) return false

  const hitCount = anchors.filter((anchor) => normalizedSource.includes(normalizeQuestionText(anchor))).length
  return hitCount >= 2
}

function normalizeProvince(value) {
  return String(value || '')
    .trim()
    .replace(/壮族自治区$|回族自治区$|维吾尔自治区$|自治区$|省$|市$/u, '')
}

function normalizeCategory(value) {
  const text = String(value || '').trim()
  if (text.includes('物理')) return '物理类'
  if (text.includes('理科')) return '物理类'
  if (text.includes('历史') || text.includes('文科')) return '历史类'
  return text
}

function extractNumbers(text) {
  const matches = String(text || '').match(/\d+/g) || []
  return matches.map((item) => Number(item)).filter(Number.isFinite)
}

export function isRecommendationIntent(text) {
  const query = String(text || '')
  return RECOMMENDATION_PATTERNS.some((pattern) => pattern.test(query))
}

export function isCoreProfileField(field) {
  return CORE_FOLLOWUP_STEPS.some((step) => step.field === field)
}

function isEarlyPlanningInputs(inputs = {}) {
  return inputs.planning_mode === 'early' || inputs.report_mode === 'planning'
}

export function getNextCoreProfileFollowup(inputs = {}) {
  return CORE_FOLLOWUP_STEPS.find((step) => {
    if (step.field === 'score' && isEarlyPlanningInputs(inputs)) return false
    return !hasValue(inputs[step.field])
  }) || null
}

export function getNextPersonalProfileFollowup(inputs = {}) {
  return PERSONAL_FOLLOWUP_STEPS.find((step) => {
    if (step.field === 'rank' && isEarlyPlanningInputs(inputs)) return false
    return !hasValue(inputs[step.field])
  }) || null
}

export function getNextRecommendationProfileFollowup(inputs = {}) {
  return RECOMMENDATION_PROFILE_STEPS.find((step) => !hasValue(inputs[step.field])) || null
}

export function hasAnyPersonalProfileInput(inputs = {}) {
  return PERSONAL_FOLLOWUP_STEPS
    .filter((step) => step.field !== 'rank')
    .some((step) => hasValue(inputs[step.field]))
}

export function mergeFollowupAnswer(profile = {}, field, answer) {
  const text = String(answer || '').trim()
  if (!field || !text) return { ...profile }

  if (field === 'province') {
    return { ...profile, province: normalizeProvince(text) }
  }

  if (field === 'category') {
    return { ...profile, category: normalizeCategory(text) }
  }

  if (field === 'score') {
    const numbers = extractNumbers(text)
    return {
      ...profile,
      ...(numbers[0] !== undefined ? { score: numbers[0] } : {}),
      ...(numbers[1] !== undefined ? { rank: numbers[1] } : {}),
    }
  }

  if (field === 'rank') {
    const numbers = extractNumbers(text)
    return {
      ...profile,
      ...(numbers[0] !== undefined ? { rank: numbers[0] } : {}),
    }
  }

  return {
    ...profile,
    [field]: text,
  }
}

function extractProvince(text) {
  const query = String(text || '')
  return PROVINCE_NAMES.find((province) => query.includes(province)) || ''
}

function extractCategory(text) {
  const query = String(text || '')
  if (/物理类?|理科/u.test(query)) return '物理类'
  if (/历史类?|文科/u.test(query)) return '历史类'
  return ''
}

function extractScore(text) {
  const query = String(text || '')
  const scorePatterns = [
    /(?:考了|高考|分数|成绩|总分|分是|成绩是|考到)\D{0,6}(750|7[0-4]\d|[1-6]\d{2})/u,
    /(?:^|[^\d])(750|7[0-4]\d|[1-6]\d{2})\s*分/u,
  ]
  for (const pattern of scorePatterns) {
    const match = query.match(pattern)
    if (match) return Number(match[1])
  }
  return ''
}

function extractRank(text) {
  const query = String(text || '')
  const match = query.match(/(?:位次|排名|排位|名次)\D{0,6}(\d{3,8})/u)
  return match ? Number(match[1]) : ''
}

export function mergeProfileFactsFromText(profile = {}, text = '') {
  const updates = {}
  const province = extractProvince(text)
  const category = extractCategory(text)
  const score = extractScore(text)
  const rank = extractRank(text)

  if (province) updates.province = normalizeProvince(province)
  if (category) updates.category = category
  if (score !== '') updates.score = score
  if (rank !== '') updates.rank = rank

  return {
    profile: {
      ...profile,
      ...updates,
    },
    fields: Object.keys(updates),
  }
}

export function buildCandidateQuestions(profile = {}) {
  const province = normalizeProvince(profile.province)
  const category = normalizeCategory(profile.category)
  if (isEarlyPlanningInputs(profile)) {
    const stage = [profile.grade, profile.identity].filter(Boolean).join('') || '提前规划家庭'
    const base = [province, category, stage].filter(Boolean).join(' · ')
    return [
      `结合${base || '我的当前阶段'}，未来一年最值得优先验证的 3 个专业方向是什么？`,
      '我应该安排哪些真实体验，判断自己是否真的适合这些专业方向？',
      '哪些能力短板会限制我未来的专业选择？请给出具体补齐顺序。',
      '请给我一份从现在到填报前的阶段性行动清单，并标出每阶段的验证目标。',
    ]
  }

  const score = profile.score !== undefined && profile.score !== '' ? Number(profile.score) : ''
  const scoreText = Number.isFinite(score) ? `${score}分` : ''
  const profileText = [province, category, scoreText].filter(Boolean).join('')
  const base = profileText ? `按我${profileText}` : '结合我的当前情况'

  return [
    `${base}，哪些选择最值得争取，哪些最容易踩坑？请说明判断依据。`,
    `当学校层次、专业前景和城市机会冲突时，${base}应该怎么排序？`,
    `请结合${profileText || '我的情况'}规划 3 条报考路线，并说明每条路线的风险和退路。`,
    `结合${profileText || '我的情况'}，哪些热门专业对我并不划算？请按就业、考研和家庭成本分析。`,
  ]
}
