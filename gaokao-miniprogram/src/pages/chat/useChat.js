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
  getNextCoreProfileFollowup,
  getNextPersonalProfileFollowup,
  isCoreProfileField,
  isRecommendationIntent,
  mergeFollowupAnswer
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

  function appendUserMessage(text, callbacks = {}) {
    const lastMsg = chatStore.messages[chatStore.messages.length - 1]
    if (!lastMsg || lastMsg.role !== 'user' || lastMsg.content !== text) {
      chatStore.appendMessage({ role: 'user', content: text })
      inputText.value = ''
    }
    scroll(callbacks)
  }

  function appendFollowupQuestion(followup, recommendationQuery, callbacks = {}) {
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
    const { onScrollToBottom } = callbacks
    const { askPostAnswerFollowup = false } = options

    chatStore.appendMessage({ role: 'ai', content: '' })
    isStreaming.value = true
    if (onScrollToBottom) onScrollToBottom()

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
      onEnd(data) {
        isStreaming.value = false
        if (data.conversationId && !chatStore.conversationId) {
           chatStore.setConversationId(data.conversationId)
        }
        const last = chatStore.messages[chatStore.messages.length - 1]
        if (last && last.role === 'ai' && !String(last.content || '').trim()) {
          last.content = '这次没有收到有效回复，请稍后重试。'
          last.truncated = true
        }
        chatStore.saveHistory()
        if (askPostAnswerFollowup) {
          appendPostAnswerFollowup(callbacks)
        }
      },
      onError(err) {
        isStreaming.value = false
        const last = chatStore.messages[chatStore.messages.length - 1]
        if (last && last.role === 'ai') {
           last.truncated = true // 标记失败/截断，方便 UI 渲染重试按钮
           if (!String(last.content || '').trim()) {
             last.content = err || '生成失败，请重试'
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
      const updatedProfile = saveUserProfile(
        mergeFollowupAnswer(loadUserProfile(), chatStore.pendingProfileField, text)
      )
      userStore.profile = updatedProfile
      syncProfileWhenReady(updatedProfile)

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

    const { profileInputs } = prepareProfile()
    appendUserMessage(text, callbacks)

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
