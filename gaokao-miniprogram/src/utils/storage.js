// gaokao-miniprogram/src/utils/storage.js

const STORAGE_KEY = 'chat_history'
const USER_ID_KEY = 'user_id'

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
