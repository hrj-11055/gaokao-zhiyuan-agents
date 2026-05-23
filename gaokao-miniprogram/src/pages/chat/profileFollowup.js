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

function hasValue(value) {
  return value !== undefined && value !== null && String(value).trim() !== ''
}

function normalizeProvince(value) {
  return String(value || '')
    .trim()
    .replace(/壮族自治区$|回族自治区$|维吾尔自治区$|自治区$|省$|市$/u, '')
}

function normalizeCategory(value) {
  const text = String(value || '').trim()
  if (text.includes('物理')) return '物理类'
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
