export const PERSONALITY_GUIDE_LONG_ANSWER_MIN_LENGTH = 500
export const PERSONALITY_GUIDE_LONG_ANSWER_MIN_ROUND = 3
export const PERSONALITY_GUIDE_FALLBACK_ROUND = 6

export function getVisibleAnswerLength(content = '') {
  return String(content)
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/https?:\/\/\S+/g, '')
    .replace(/<[^>]+>/g, '')
    .replace(/^\s{0,3}(#{1,6}|>|[-+*]|\d+\.)\s+/gm, '')
    .replace(/[*_~`]/g, '')
    .replace(/\s+/g, '')
    .length
}

function isCompleteAiReply(message = {}) {
  return Boolean(
    message.role === 'ai' &&
    !message.truncated &&
    !message.error &&
    String(message.content || '').trim()
  )
}

export function findPersonalityGuideMessageIndex(messages = []) {
  let completedRound = 0
  let hasPendingUserQuestion = false

  for (let index = 0; index < messages.length; index++) {
    const message = messages[index] || {}
    if (message.role === 'user') {
      hasPendingUserQuestion = true
      continue
    }
    if (!hasPendingUserQuestion || !isCompleteAiReply(message)) continue

    completedRound++
    hasPendingUserQuestion = false

    const isLongAnswerMoment = (
      completedRound >= PERSONALITY_GUIDE_LONG_ANSWER_MIN_ROUND &&
      getVisibleAnswerLength(message.content) >= PERSONALITY_GUIDE_LONG_ANSWER_MIN_LENGTH
    )
    if (isLongAnswerMoment || completedRound >= PERSONALITY_GUIDE_FALLBACK_ROUND) {
      return index
    }
  }

  return -1
}
