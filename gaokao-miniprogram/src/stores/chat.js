import { defineStore } from 'pinia'

const STORAGE_KEY = 'chat_history'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversationId: '',
    messages: [],
    updatedAt: 0,
    profileInputsKey: '',
    pendingProfileField: '',
    pendingRecommendationQuery: ''
  }),
  
  actions: {
    loadHistory() {
      const data = uni.getStorageSync(STORAGE_KEY)
      if (data) {
        try {
          const parsed = JSON.parse(data)
          this.conversationId = parsed.conversationId || ''
          this.messages = parsed.messages || []
          this.updatedAt = parsed.updatedAt || 0
          this.profileInputsKey = parsed.profileInputsKey || ''
          this.pendingProfileField = parsed.pendingProfileField || ''
          this.pendingRecommendationQuery = parsed.pendingRecommendationQuery || ''
        } catch {
          this.clearHistory()
        }
      }
    },

    saveHistory() {
      const data = JSON.stringify({
        conversationId: this.conversationId,
        messages: this.messages,
        updatedAt: Date.now(),
        profileInputsKey: this.profileInputsKey,
        pendingProfileField: this.pendingProfileField,
        pendingRecommendationQuery: this.pendingRecommendationQuery
      })
      uni.setStorageSync(STORAGE_KEY, data)
    },

    appendMessage(message) {
      this.messages.push({ ...message, timestamp: Date.now() })
      this.saveHistory()
    },

    setConversationId(id) {
      this.conversationId = id
      this.saveHistory()
    },

    setProfileInputsKey(key) {
      this.profileInputsKey = key
      this.saveHistory()
    },

    setProfileFollowup(field, recommendationQuery) {
      this.pendingProfileField = field || ''
      this.pendingRecommendationQuery = recommendationQuery || ''
      this.saveHistory()
    },

    clearProfileFollowup() {
      this.pendingProfileField = ''
      this.pendingRecommendationQuery = ''
      this.saveHistory()
    },

    clearHistory() {
      this.conversationId = ''
      this.messages = []
      this.updatedAt = 0
      this.profileInputsKey = ''
      this.pendingProfileField = ''
      this.pendingRecommendationQuery = ''
      uni.removeStorageSync(STORAGE_KEY)
    }
  }
})
