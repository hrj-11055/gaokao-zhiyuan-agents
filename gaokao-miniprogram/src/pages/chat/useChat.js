import { ref, onMounted } from 'vue'
import { sendMessageStream } from '../../api/dify.js'
import { useChatStore } from '../../stores/chat.js'
import { useMembershipStore } from '../../stores/membership.js'
import { useUserStore } from '../../stores/user.js'
import {
  buildProfileInputs,
  isProfileComplete,
  loadUserProfile,
  saveUserProfile
} from '../../utils/storage.js'
import {
  containsProfileFollowupQuestion,
  getNextCoreProfileFollowup,
  getNextPersonalProfileFollowup,
  isCoreProfileField,
  isRecommendationIntent,
  mergeFollowupAnswer,
  mergeProfileFactsFromText
} from './profileFollowup.js'

function getProfileInputsKey(inputs) {
  return JSON.stringify({
    province: inputs.province || '',
    category: inputs.category || '',
    score: inputs.score || '',
    rank: inputs.rank || '',
    family_resources: inputs.family_resources || '',
    interest_subjects: inputs.interest_subjects || '',
    region_preference: inputs.region_preference || '',
    career_goal: inputs.career_goal || ''
  })
}

export function useChat() {
  const chatStore = useChatStore()
  const membershipStore = useMembershipStore()
  const userStore = useUserStore()

  const isStreaming = ref(false)
  const inputText = ref('')
  let currentAbort = null
  let lastQuery = ''

  onMounted(() => {
    chatStore.loadHistory()
    userStore.loadProfile()
    if (!userStore.userId) {
      userStore.initUserId()
    }
  })

  function scroll(callbacks = {}) {
    if (callbacks.onScrollToBottom) callbacks.onScrollToBottom()
  }

  function syncProfileWhenReady(profile) {
    if (!isProfileComplete(profile)) return
    membershipStore.syncProfile(profile).catch(() => {})
  }

  function prepareProfile() {
    const freshProfile = loadUserProfile()
    const profileInputs = buildProfileInputs(freshProfile)
    const profileInputsKey = getProfileInputsKey(profileInputs)
    userStore.profile = freshProfile

    if (chatStore.conversationId && chatStore.profileInputsKey !== profileInputsKey) {
      chatStore.conversationId = ''
    }
    if (chatStore.profileInputsKey !== profileInputsKey) {
      chatStore.setProfileInputsKey(profileInputsKey)
    }
    return { freshProfile, profileInputs }
  }

  function applyProfileFactsFromText(text, callbacks = {}) {
    const { profile, fields } = mergeProfileFactsFromText(loadUserProfile(), text)
    if (!fields.length) return loadUserProfile()

    const updatedProfile = saveUserProfile(profile)
    userStore.profile = updatedProfile
    syncProfileWhenReady(updatedProfile)
    if (callbacks.onProfileUpdated) callbacks.onProfileUpdated(updatedProfile)
    return updatedProfile
  }

  function appendUserMessage(text, callbacks = {}) {
    const lastMsg = chatStore.messages[chatStore.messages.length - 1]
    let messageIndex = chatStore.messages.length - 1
    if (!lastMsg || lastMsg.role !== 'user' || lastMsg.content !== text) {
      chatStore.appendMessage({ role: 'user', content: text })
      messageIndex = chatStore.messages.length - 1
      inputText.value = ''
    }
    if (callbacks.onUserMessageAppended) {
      callbacks.onUserMessageAppended(messageIndex)
    } else {
      scroll(callbacks)
    }
  }

  function appendFollowupQuestion(followup, recommendationQuery, callbacks = {}) {
    const last = chatStore.messages[chatStore.messages.length - 1]
    if (last && last.role === 'ai' && containsProfileFollowupQuestion(last.content, followup)) {
      // AI 正文已经问过同一个画像问题，只记录待填写字段，避免再追加一条重复气泡。
      chatStore.setProfileFollowup(followup.field, recommendationQuery)
      return
    }
    chatStore.appendMessage({ role: 'ai', content: followup.question })
    chatStore.setProfileFollowup(followup.field, recommendationQuery)
    scroll(callbacks)
  }

  function appendPostAnswerFollowup(callbacks = {}) {
    const followup = getNextPersonalProfileFollowup(buildProfileInputs(loadUserProfile()))
    if (!followup) return
    appendFollowupQuestion(followup, '', callbacks)
  }

  function appendProfileAck(callbacks = {}) {
    chatStore.appendMessage({
      role: 'ai',
      content: '收到，我后面会把这个条件纳入学校和专业判断。你继续问具体院校或专业时，我会结合它来给建议。'
    })
    scroll(callbacks)
  }

  function sendToDify(text, callbacks = {}, profileInputs = buildProfileInputs(loadUserProfile()), options = {}) {
    const { onAiResponseStarted, onScrollToBottom } = callbacks
    const { askPostAnswerFollowup = false } = options

    chatStore.appendMessage({ role: 'ai', content: '' })
    isStreaming.value = true
    if (onAiResponseStarted) {
      onAiResponseStarted()
    } else if (onScrollToBottom) {
      onScrollToBottom()
    }

    currentAbort = sendMessageStream({
      query: text,
      conversationId: chatStore.conversationId,
      user: userStore.userId,
      inputs: profileInputs,
      onChunk(answerChunk, convId, msgId) {
        // 更新最后一条 AI 消息的内容
        const last = chatStore.messages[chatStore.messages.length - 1]
        if (last && last.role === 'ai') {
          // 这里为了触发响应式更新，可能需要替换整个对象或者利用 Vue 响应式特性
          // 在 Pinia 中直接修改数组元素的属性是可以的
          last.content += answerChunk
          if (msgId) last.messageId = msgId
        }
        
        if (convId && !chatStore.conversationId) {
          chatStore.setConversationId(convId)
        }
      },
      onEnd(data = {}) {
        isStreaming.value = false
        if (data.conversationId && !chatStore.conversationId) {
           chatStore.setConversationId(data.conversationId)
        }
        const last = chatStore.messages[chatStore.messages.length - 1]
        if (last && last.role === 'ai') {
          if (data.truncated) {
            last.truncated = true
            const content = String(last.content || '').trim()
            if (content && !content.includes('本次回复中途断开')) {
              last.content = `${content}\n\n（本次回复中途断开，请点“重新生成”获取完整建议。）`
            }
          }
          if (!String(last.content || '').trim()) {
            last.content = data.truncated ? '这次回复中途断开了，请点重新生成获取完整建议。' : '这次没有收到有效回复，请稍后重试。'
            last.truncated = true
          }
        }
        chatStore.saveHistory()
        if (askPostAnswerFollowup && !data.truncated) {
          appendPostAnswerFollowup(callbacks)
        }
      },
      onError(err) {
        isStreaming.value = false
        const last = chatStore.messages[chatStore.messages.length - 1]
        if (last && last.role === 'ai') {
           last.truncated = true // 标记失败/截断，方便 UI 渲染重试按钮
           const content = String(last.content || '').trim()
           if (!content) {
             last.content = err || '生成失败，请重试'
           } else if (!content.includes('本次回复中途断开')) {
             last.content = `${content}\n\n（本次回复中途断开，请点“重新生成”获取完整建议。）`
           }
        }
        chatStore.saveHistory()
        uni.showToast({
          title: err || '生成失败',
          icon: 'none'
        })
      }
    })
  }

  function sendQuery(text, callbacks = {}) {
    lastQuery = text

    if (chatStore.pendingProfileField) {
      appendUserMessage(text, callbacks)
      const mergedProfile = mergeProfileFactsFromText(
        mergeFollowupAnswer(loadUserProfile(), chatStore.pendingProfileField, text),
        text
      ).profile
      const updatedProfile = saveUserProfile(mergedProfile)
      userStore.profile = updatedProfile
      syncProfileWhenReady(updatedProfile)
      if (callbacks.onProfileUpdated) callbacks.onProfileUpdated(updatedProfile)

      const profileInputs = buildProfileInputs(updatedProfile)
      const pendingField = chatStore.pendingProfileField
      const pendingQuery = chatStore.pendingRecommendationQuery || text
      chatStore.clearProfileFollowup()

      if (!isCoreProfileField(pendingField)) {
        prepareProfile()
        appendProfileAck(callbacks)
        return
      }

      const followup = getNextCoreProfileFollowup(profileInputs)
      if (followup) {
        appendFollowupQuestion(followup, pendingQuery, callbacks)
        prepareProfile()
        return
      }

      const prepared = prepareProfile()
      sendToDify(pendingQuery, callbacks, prepared.profileInputs, {
        askPostAnswerFollowup: isRecommendationIntent(pendingQuery)
      })
      return
    }

    appendUserMessage(text, callbacks)
    applyProfileFactsFromText(text, callbacks)
    const { profileInputs } = prepareProfile()

    if (isRecommendationIntent(text)) {
      const followup = getNextCoreProfileFollowup(profileInputs)
      if (followup) {
        appendFollowupQuestion(followup, text, callbacks)
        return
      }
    }

    sendToDify(text, callbacks, profileInputs, {
      askPostAnswerFollowup: isRecommendationIntent(text)
    })
  }

  function onSend(callbacks) {
    const text = inputText.value.trim()
    if (!text || isStreaming.value) return
    if (!isProfileComplete(loadUserProfile())) {
      uni.showToast({ title: '请先补全省份、科类和分数', icon: 'none' })
      return
    }
    sendQuery(text, callbacks)
  }

  function onRetry(callbacks) {
    if (!lastQuery || isStreaming.value) return
    
    // 移除最后一条 AI 消息（失败的截断消息）
    const msgs = chatStore.messages
    if (msgs.length > 0 && msgs[msgs.length - 1].role === 'ai') {
      chatStore.messages.pop()
      chatStore.saveHistory()
    }
    
    sendQuery(lastQuery, callbacks)
  }

  return {
    chatStore,
    inputText,
    isStreaming,
    onSend,
    onRetry,
    sendQuery // 暴露给快捷问题调用
  }
}
