// gaokao-miniprogram/src/utils/storage.js

const STORAGE_KEY = 'chat_history'
const USER_ID_KEY = 'user_id'
const USER_PROFILE_KEY = 'user_profile'
const PROFILE_IDENTITY_KEY = 'profile_identity'
const REPORT_KEY = 'user_report'
const PERSONALITY_GUIDE_DISMISSED_KEY = 'chat_personality_guide_dismissed'

/**
 * 获取或创建用户 ID（本地生成，无需微信登录）
 */
export function getUserId() {
  let userId = uni.getStorageSync(USER_ID_KEY)
  if (!userId) {
    userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11)
    uni.setStorageSync(USER_ID_KEY, userId)
  }
  return userId
}

/**
 * 加载对话历史
 * @returns {{ conversationId: string, messages: Array, updatedAt: number }}
 */
export function loadHistory() {
  const data = uni.getStorageSync(STORAGE_KEY)
  if (!data) {
    return { conversationId: '', messages: [], updatedAt: 0 }
  }
  try {
    return JSON.parse(data)
  } catch {
    return { conversationId: '', messages: [], updatedAt: 0 }
  }
}

/**
 * 保存对话历史
 * @param {string} conversationId
 * @param {Array} messages - [{ role: 'user'|'ai', content: string, timestamp: number }]
 */
export function saveHistory(conversationId, messages) {
  const data = JSON.stringify({
    conversationId,
    messages,
    updatedAt: Date.now()
  })
  uni.setStorageSync(STORAGE_KEY, data)
}

/**
 * 追加一条消息并保存
 * @param {string} conversationId
 * @param {{ role: string, content: string, timestamp: number }} message
 * @returns {Array} 更新后的 messages 数组
 */
export function appendMessage(conversationId, message) {
  const history = loadHistory()
  const messages = [...history.messages, { ...message, timestamp: Date.now() }]
  saveHistory(conversationId, messages)
  return messages
}

/**
 * 清空对话历史
 */
export function clearHistory() {
  uni.removeStorageSync(STORAGE_KEY)
}

export function isPersonalityGuideDismissed() {
  return uni.getStorageSync(PERSONALITY_GUIDE_DISMISSED_KEY) === true
}

export function dismissPersonalityGuide() {
  uni.setStorageSync(PERSONALITY_GUIDE_DISMISSED_KEY, true)
}

/**
 * 清空本地保存的用户数据。
 */
export function clearAllLocalData() {
  [
    STORAGE_KEY,
    USER_ID_KEY,
    USER_PROFILE_KEY,
    PROFILE_IDENTITY_KEY,
    QUESTIONNAIRE_KEY,
    ASSESSMENTS_KEY,
    REPORT_KEY,
    PERSONALITY_GUIDE_DISMISSED_KEY
  ].forEach((key) => uni.removeStorageSync(key))
}

function toIntOrEmpty(value) {
  if (value === '' || value === null || value === undefined) {
    return ''
  }
  const number = Number(value)
  return Number.isFinite(number) ? Math.trunc(number) : ''
}

function toTrimmedString(value) {
  return typeof value === 'string' ? value.trim() : ''
}

export const PROFILE_PLANNING_MODES = {
  SCORE: 'score',
  EARLY: 'early',
}

export const PROFILE_SCORE_TYPES = {
  OFFICIAL: 'official',
  ESTIMATED: 'estimated',
}

function normalizePlanningMode(value) {
  return value === PROFILE_PLANNING_MODES.EARLY
    ? PROFILE_PLANNING_MODES.EARLY
    : PROFILE_PLANNING_MODES.SCORE
}

function isValidScore(value) {
  return typeof value === 'number' && value >= 0 && value <= 750
}

function normalizeScoreType(value, planningMode, hasScore) {
  if (planningMode === PROFILE_PLANNING_MODES.EARLY) return ''
  if (value === PROFILE_SCORE_TYPES.ESTIMATED) return PROFILE_SCORE_TYPES.ESTIMATED
  return hasScore ? PROFILE_SCORE_TYPES.OFFICIAL : ''
}

/**
 * 规范化考生信息，字段顺序固定为：省份、科目、分数、位次。
 */
export function normalizeUserProfile(profile = {}) {
  const score = toIntOrEmpty(profile.score)
  const planningMode = normalizePlanningMode(profile.planning_mode)
  const hasScore = isValidScore(score)
  return {
    nickname: toTrimmedString(profile.nickname),
    province: toTrimmedString(profile.province),
    category: toTrimmedString(profile.category),
    planning_mode: planningMode,
    score_type: normalizeScoreType(profile.score_type, planningMode, hasScore),
    score_range: toTrimmedString(profile.score_range),
    grade: toTrimmedString(profile.grade),
    identity: toTrimmedString(profile.identity),
    score,
    rank: toIntOrEmpty(profile.rank),
    family_resources: toTrimmedString(profile.family_resources),
    interest_subjects: toTrimmedString(profile.interest_subjects),
    region_preference: toTrimmedString(profile.region_preference),
    career_goal: toTrimmedString(profile.career_goal),
    updatedAt: profile.updatedAt === undefined ? Date.now() : profile.updatedAt
  }
}

/**
 * 保存考生信息。允许保存草稿，完整性由 isProfileComplete 判断。
 */
export function saveUserProfile(profile) {
  const data = normalizeUserProfile({ ...profile, updatedAt: Date.now() })
  uni.setStorageSync(USER_PROFILE_KEY, JSON.stringify(data))
  return data
}

/**
 * 读取考生信息。
 */
export function loadUserProfile() {
  const data = uni.getStorageSync(USER_PROFILE_KEY)
  if (!data) {
    return normalizeUserProfile({ updatedAt: 0 })
  }
  try {
    return normalizeUserProfile(JSON.parse(data))
  } catch {
    return normalizeUserProfile({ updatedAt: 0 })
  }
}

export function hasProfileScore(profile = {}) {
  const data = normalizeUserProfile(profile)
  return isValidScore(data.score)
}

export function getProfileReportMode(profile = {}) {
  const data = normalizeUserProfile(profile)
  if (data.planning_mode === PROFILE_PLANNING_MODES.EARLY) {
    return 'planning'
  }
  if (data.score_type === PROFILE_SCORE_TYPES.ESTIMATED) {
    return 'estimated'
  }
  if (isValidScore(data.score)) {
    return 'official'
  }
  return 'planning'
}

/**
 * 智能填报最低必填项：省份、科目、分数。
 */
export function isProfileComplete(profile) {
  const data = normalizeUserProfile(profile)
  const hasBase = Boolean(
    data.province &&
    (data.category === '物理类' || data.category === '历史类')
  )
  if (!hasBase) return false
  if (data.planning_mode === PROFILE_PLANNING_MODES.EARLY) return true
  return isValidScore(data.score)
}

/**
 * 构造 Dify inputs；选填位次为空时不传 rank。
 */
export function buildProfileInputs(profile) {
  const data = normalizeUserProfile(profile)
  const inputs = {}
  if (data.province) {
    inputs.province = data.province
  }
  if (data.category) {
    inputs.category = data.category
  }
  inputs.planning_mode = data.planning_mode
  inputs.report_mode = getProfileReportMode(data)
  if (data.score_type) {
    inputs.score_type = data.score_type
  }
  if (data.score_range) {
    inputs.score_range = data.score_range
  }
  if (data.grade) {
    inputs.grade = data.grade
  }
  if (data.identity) {
    inputs.identity = data.identity
  }
  if (typeof data.score === 'number') {
    inputs.score = String(data.score)
  }
  if (typeof data.rank === 'number' && data.rank > 0) {
    inputs.rank = String(data.rank)
  }
  if (data.family_resources) {
    inputs.family_resources = data.family_resources
  }
  if (data.interest_subjects) {
    inputs.interest_subjects = data.interest_subjects
  }
  if (data.region_preference) {
    inputs.region_preference = data.region_preference
  }
  if (data.career_goal) {
    inputs.career_goal = data.career_goal
  }
  return inputs
}

const QUESTIONNAIRE_KEY = 'questionnaire'
const ASSESSMENTS_KEY = 'assessments'
export const QUESTIONNAIRE_REQUIRED_COUNT = 21
export const ASSESSMENT_REQUIRED_COUNT = 2
const QUESTIONNAIRE_ACTIVE_IDS = new Set([
  'q1', 'q2', 'q3', 'q4', 'q5',
  'q6', 'q7', 'q8',
  'q10', 'q11', 'q12', 'q13',
  'q14', 'q15', 'q16',
  'q17', 'q18', 'q19', 'q20', 'q21', 'q22'
])

function isFilledAnswer(value) {
  return value !== '' && value !== undefined && value !== null && !(Array.isArray(value) && value.length === 0)
}

function sanitizeQuestionnaireAnswers(answers = {}) {
  if (typeof answers !== 'object' || answers === null) {
    return {}
  }
  return Object.fromEntries(
    Object.entries(answers).filter(([id, value]) => QUESTIONNAIRE_ACTIVE_IDS.has(id) && isFilledAnswer(value))
  )
}

function countQuestionnaireAnswers(answers = {}) {
  return Object.keys(sanitizeQuestionnaireAnswers(answers)).length
}

function normalizeQuestionnaire(questionnaire = {}) {
  const answers = sanitizeQuestionnaireAnswers(questionnaire.answers)
  return {
    answers,
    completedCount: countQuestionnaireAnswers(answers),
    updatedAt: questionnaire.updatedAt || 0
  }
}

/**
 * 保存问卷草稿（随时调用，允许部分填写）
 * @param {{ [id: string]: string | string[] }} answers
 */
export function saveQuestionnaire(answers) {
  const normalizedAnswers = sanitizeQuestionnaireAnswers(answers)
  const questionnaire = {
    answers: normalizedAnswers,
    completedCount: countQuestionnaireAnswers(normalizedAnswers),
    updatedAt: Date.now()
  }
  uni.setStorageSync(QUESTIONNAIRE_KEY, JSON.stringify(questionnaire))

  const assessments = loadAssessments()
  saveAssessments({
    ...assessments,
    questionnaire
  })
}

/**
 * 读取问卷草稿
 * @returns {{ answers: object, completedCount: number, updatedAt: number }}
 */
export function loadQuestionnaire() {
  const data = uni.getStorageSync(QUESTIONNAIRE_KEY)
  if (!data) return { answers: {}, completedCount: 0, updatedAt: 0 }
  try {
    return normalizeQuestionnaire(JSON.parse(data))
  } catch {
    return { answers: {}, completedCount: 0, updatedAt: 0 }
  }
}

// ==================== 报告存储 ====================

/**
 * 保存报告数据到本地
 * @param {object} data - { url, generatedAt, ... }
 */
export function saveReport(data) {
  try { uni.setStorageSync(REPORT_KEY, JSON.stringify(data)) } catch { /* ignore */ }
}

/**
 * 读取本地报告数据
 * @returns {object|null}
 */
export function loadReport() {
  try {
    const raw = uni.getStorageSync(REPORT_KEY)
    if (!raw) return null
    return typeof raw === 'string' ? JSON.parse(raw) : raw
  } catch { return null }
}

// ==================== 测评模块存储 ====================

/**
 * 规范化 MBTI 测评数据
 */
function normalizeMbti(mbti = {}) {
  return {
    completed: Boolean(mbti.completed),
    version: mbti.version === 'basic' ? 'basic' : (mbti.completed ? 'full' : (mbti.version || '')),
    type: typeof mbti.type === 'string' ? mbti.type : '',
    scores: {
      E: Number(mbti.scores?.E) || 0,
      I: Number(mbti.scores?.I) || 0,
      S: Number(mbti.scores?.S) || 0,
      N: Number(mbti.scores?.N) || 0,
      T: Number(mbti.scores?.T) || 0,
      F: Number(mbti.scores?.F) || 0,
      J: Number(mbti.scores?.J) || 0,
      P: Number(mbti.scores?.P) || 0
    },
    answers: Array.isArray(mbti.answers) ? mbti.answers : [],
    questionIndex: typeof mbti.questionIndex === 'number' ? mbti.questionIndex : 0,
    completedAt: mbti.completedAt || 0
  }
}

/**
 * 规范化霍兰德测评数据
 */
function normalizeHolland(holland = {}) {
  return {
    completed: Boolean(holland.completed),
    version: holland.version === 'basic' ? 'basic' : (holland.completed ? 'full' : (holland.version || '')),
    code: typeof holland.code === 'string' ? holland.code : '',
    scores: {
      R: Number(holland.scores?.R) || 0,
      I: Number(holland.scores?.I) || 0,
      A: Number(holland.scores?.A) || 0,
      S: Number(holland.scores?.S) || 0,
      E: Number(holland.scores?.E) || 0,
      C: Number(holland.scores?.C) || 0
    },
    answers: Array.isArray(holland.answers) ? holland.answers : [],
    questionIndex: typeof holland.questionIndex === 'number' ? holland.questionIndex : 0,
    completedAt: holland.completedAt || 0
  }
}

/**
 * 规范化测评数据（内部使用）
 */
function normalizeAssessments(data = {}) {
  return {
    mbti: normalizeMbti(data.mbti),
    holland: normalizeHolland(data.holland),
    questionnaire: normalizeQuestionnaire(data.questionnaire),
    updatedAt: data.updatedAt || 0
  }
}

/**
 * 保存测评数据
 * @param {object} assessments - 包含 mbti, holland, questionnaire 的测评数据
 */
export function saveAssessments(assessments) {
  const data = normalizeAssessments({ ...assessments, updatedAt: Date.now() })
  uni.setStorageSync(ASSESSMENTS_KEY, JSON.stringify(data))
  return data
}

/**
 * 读取测评数据
 * @returns {object} 规范化后的测评数据
 */
export function loadAssessments() {
  const questionnaire = loadQuestionnaire()
  const data = uni.getStorageSync(ASSESSMENTS_KEY)
  if (!data) {
    return normalizeAssessments({ questionnaire, updatedAt: 0 })
  }
  try {
    const assessments = normalizeAssessments(JSON.parse(data))
    if (questionnaire.completedCount > assessments.questionnaire.completedCount) {
      assessments.questionnaire = questionnaire
    }
    return assessments
  } catch {
    return normalizeAssessments({ questionnaire, updatedAt: 0 })
  }
}

/**
 * 保存 MBTI 测评结果
 * @param {object} result - { type, scores, answers }
 */
export function saveMbtiResult(result) {
  const assessments = loadAssessments()
  assessments.mbti = normalizeMbti({
    ...result,
    completed: true,
    completedAt: Date.now()
  })
  const saved = saveAssessments(assessments)
  return saved.mbti
}

/**
 * 保存霍兰德测评结果
 * @param {object} result - { code, scores, answers }
 */
export function saveHollandResult(result) {
  const assessments = loadAssessments()
  assessments.holland = normalizeHolland({
    ...result,
    completed: true,
    completedAt: Date.now()
  })
  const saved = saveAssessments(assessments)
  return saved.holland
}

/**
 * 保存 MBTI 答题进度
 * @param {number} questionIndex - 当前题目索引
 * @param {Array} answers - 已保存的答案
 */
export function saveMbtiProgress(questionIndex, answers = [], version = '') {
  const assessments = loadAssessments()
  assessments.mbti = normalizeMbti({
    ...assessments.mbti,
    completed: false,
    questionIndex,
    answers,
    version: version || assessments.mbti.version
  })
  return saveAssessments(assessments)
}

/**
 * 保存霍兰德答题进度
 * @param {number} questionIndex - 当前题目索引
 * @param {Array} answers - 已保存的答案
 */
export function saveHollandProgress(questionIndex, answers = [], version = '') {
  const assessments = loadAssessments()
  assessments.holland = normalizeHolland({
    ...assessments.holland,
    completed: false,
    questionIndex,
    answers,
    version: version || assessments.holland.version
  })
  return saveAssessments(assessments)
}

/**
 * 计算已完成测评数量（0-2）。五环问卷数据保留但暂不参与报告生成。
 * @returns {number} 已完成的测评数量
 */
export function getCompletedAssessmentsCount() {
  const assessments = loadAssessments()
  let count = 0
  if (assessments.mbti.completed) count++
  if (assessments.holland.completed) count++
  return count
}

/**
 * 检查是否所有测评都完成
 * @returns {boolean}
 */
export function isAllAssessmentsCompleted() {
  const assessments = loadAssessments()
  return (
    assessments.mbti.completed &&
    assessments.holland.completed
  )
}
