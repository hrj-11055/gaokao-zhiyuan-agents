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
    field: 'family_resources',
    question: '我先问一个家庭资源问题：家里预算和资源大概是什么情况？比如能不能接受民办或中外合作，父母行业有没有能帮你实习就业的方向。',
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

const PERSONAL_FOLLOWUP_ANCHORS = {
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
  return RECOMMENDATION_KEYWORDS.some((keyword) => query.includes(keyword))
}

export function isCoreProfileField(field) {
  return CORE_FOLLOWUP_STEPS.some((step) => step.field === field)
}

export function getNextCoreProfileFollowup(inputs = {}) {
  return CORE_FOLLOWUP_STEPS.find((step) => !hasValue(inputs[step.field])) || null
}

export function getNextPersonalProfileFollowup(inputs = {}) {
  return PERSONAL_FOLLOWUP_STEPS.find((step) => !hasValue(inputs[step.field])) || null
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
