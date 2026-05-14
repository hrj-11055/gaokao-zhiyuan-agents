import { ref, onMounted } from 'vue'
import { sendMessageStream } from '../../api/dify.js'
import { useChatStore } from '../../stores/chat.js'
import { useUserStore } from '../../stores/user.js'
import { buildProfileInputs, loadUserProfile } from '../../utils/storage.js'

function getProfileInputsKey(inputs) {
  return JSON.stringify({
    province: inputs.province || '',
    category: inputs.category || '',
    score: inputs.score || '',
    rank: inputs.rank || ''
  })
}

export function useChat() {
  const chatStore = useChatStore()
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

  function sendQuery(text, callbacks = {}) {
    lastQuery = text
    const { onScrollToBottom } = callbacks
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

    // 添加用户消息
    const lastMsg = chatStore.messages[chatStore.messages.length - 1]
    if (!lastMsg || lastMsg.role !== 'user' || lastMsg.content !== text) {
      chatStore.appendMessage({ role: 'user', content: text })
      inputText.value = ''
    }
    
    if (onScrollToBottom) onScrollToBottom()

    // 添加空的 AI 消息占位
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
        chatStore.saveHistory() // 流结束后完整保存一次
      },
      onError(err) {
        isStreaming.value = false
        const last = chatStore.messages[chatStore.messages.length - 1]
        if (last && last.role === 'ai') {
           last.truncated = true // 标记失败/截断，方便 UI 渲染重试按钮
        }
        chatStore.saveHistory()
        uni.showToast({
          title: err || '生成失败',
          icon: 'none'
        })
      }
    })
  }

  function onSend(callbacks) {
    const text = inputText.value.trim()
    if (!text || isStreaming.value) return
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
