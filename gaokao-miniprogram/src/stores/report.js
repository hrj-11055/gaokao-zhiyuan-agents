import { defineStore } from 'pinia'

const REPORT_KEY = 'user_report'

export const useReportStore = defineStore('report', {
  state: () => ({
    url: '',
    generatedAt: 0
  }),

  actions: {
    loadReport() {
      const data = uni.getStorageSync(REPORT_KEY)
      if (data) {
        try {
          const parsed = JSON.parse(data)
          this.url = parsed.url || ''
          this.generatedAt = parsed.generatedAt || 0
        } catch {
          this.url = ''
          this.generatedAt = 0
        }
      }
    },

    saveReport(url) {
      this.url = url
      this.generatedAt = Date.now()
      uni.setStorageSync(REPORT_KEY, JSON.stringify({
        url: this.url,
        generatedAt: this.generatedAt
      }))
    },

    clearReport() {
      this.url = ''
      this.generatedAt = 0
      uni.removeStorageSync(REPORT_KEY)
    }
  }
})
