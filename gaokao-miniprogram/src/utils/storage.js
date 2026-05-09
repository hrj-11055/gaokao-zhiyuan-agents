// gaokao-miniprogram/src/utils/storage.js

const STORAGE_KEY = 'chat_history'
const USER_ID_KEY = 'user_id'
const USER_PROFILE_KEY = 'user_profile'

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

function toIntOrEmpty(value) {
  if (value === '' || value === null || value === undefined) {
    return ''
  }
  const number = Number(value)
  return Number.isFinite(number) ? Math.trunc(number) : ''
}

/**
 * 规范化考生信息，字段顺序固定为：省份、科目、分数、位次。
 */
export function normalizeUserProfile(profile = {}) {
  return {
    province: typeof profile.province === 'string' ? profile.province : '',
    category: typeof profile.category === 'string' ? profile.category : '',
    score: toIntOrEmpty(profile.score),
    rank: toIntOrEmpty(profile.rank),
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

/**
 * 智能填报最低必填项：省份、科目、分数。
 */
export function isProfileComplete(profile) {
  const data = normalizeUserProfile(profile)
  return Boolean(
    data.province &&
    (data.category === '物理类' || data.category === '历史类') &&
    typeof data.score === 'number' &&
    data.score >= 0 &&
    data.score <= 750
  )
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
  if (typeof data.score === 'number') {
    inputs.score = String(data.score)
  }
  if (typeof data.rank === 'number' && data.rank > 0) {
    inputs.rank = String(data.rank)
  }
  return inputs
}
