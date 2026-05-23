import { defineStore } from 'pinia'
import {
  activateLimitedFreeMembership,
  createMembershipPayment,
  fetchMembershipStatus,
  fetchPaymentOrder,
  fetchUserProfileFromServer,
  getStoredSession,
  loginWithWechat,
  markProfileComplete,
  saveUserProfileToServer,
} from '../api/membership.js'
import { PAYMENT_ENABLED } from '../config.js'

const INVITER_KEY = 'membership_inviter_id'

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function normalizeStatus(data = {}) {
  const invite = data.invite || {}
  return {
    status: data.status || data.membership?.status || 'inactive',
    source: data.source || data.membership?.source || '',
    unlockedAt: data.unlockedAt || data.membership?.unlockedAt || 0,
    effectiveInviteCount: Number(invite.effectiveCount ?? data.membership?.invite?.effectiveCount ?? 0),
    requiredInviteCount: Number(invite.requiredCount ?? data.membership?.invite?.requiredCount ?? 3),
    features: data.features || data.membership?.features || {
      universityResearch: false,
      comprehensiveReport: false,
      pdfDownload: false,
      familyShare: false,
    },
  }
}

export const useMembershipStore = defineStore('membership', {
  state: () => {
    const session = getStoredSession()
    return {
      userId: session.userId,
      sessionToken: session.sessionToken,
      status: 'inactive',
      source: '',
      unlockedAt: 0,
      effectiveInviteCount: 0,
      requiredInviteCount: 3,
      features: {
        universityResearch: false,
        comprehensiveReport: false,
        pdfDownload: false,
        familyShare: false,
      },
      lastOrderId: '',
      lastOrderStatus: '',
      inviterId: uni.getStorageSync(INVITER_KEY) || '',
      loading: false,
      error: '',
    }
  },

  getters: {
    isActive(state) {
      return state.status === 'active'
    },
    inviteProgressText(state) {
      return `${state.effectiveInviteCount}/${state.requiredInviteCount}`
    },
    isPaymentEnabled() {
      return PAYMENT_ENABLED
    },
    paymentUnavailableText() {
      return '支付功能正在备案配置中，请先邀请 3 位同学免费解锁。'
    },
  },

  actions: {
    applyStatus(data) {
      const status = normalizeStatus(data)
      this.status = status.status
      this.source = status.source
      this.unlockedAt = status.unlockedAt
      this.effectiveInviteCount = status.effectiveInviteCount
      this.requiredInviteCount = status.requiredInviteCount
      this.features = status.features
    },

    setInviterId(inviterId) {
      if (!inviterId || this.userId === inviterId) return
      this.inviterId = inviterId
      uni.setStorageSync(INVITER_KEY, inviterId)
    },

    async login() {
      this.loading = true
      this.error = ''
      try {
        const data = await loginWithWechat({ inviterId: this.inviterId })
        this.userId = data.userId || ''
        this.sessionToken = data.sessionToken || ''
        this.applyStatus(data.membership || data)
        return data
      } catch (err) {
        this.error = err.message || '微信登录失败'
        throw err
      } finally {
        this.loading = false
      }
    },

    async ensureLogin() {
      if (this.sessionToken) return
      await this.login()
    },

    async loadStatus() {
      await this.ensureLogin()
      const data = await fetchMembershipStatus(this.sessionToken)
      this.applyStatus(data)
      return data
    },

    async markProfileCompleted() {
      await this.ensureLogin()
      const data = await markProfileComplete(this.sessionToken)
      this.applyStatus(data.membership || data)
      return data
    },

    async activateLimitedFree() {
      await this.ensureLogin()
      const data = await activateLimitedFreeMembership(this.sessionToken)
      this.applyStatus(data.membership || data)
      return data
    },

    async syncProfile(profile) {
      await this.ensureLogin()
      const data = await saveUserProfileToServer(profile, this.sessionToken)
      this.applyStatus(data.membership || data)
      return data
    },

    async fetchProfile() {
      await this.ensureLogin()
      const data = await fetchUserProfileFromServer(this.sessionToken)
      this.applyStatus(data.membership || data)
      return data
    },

    async createPayment() {
      if (!PAYMENT_ENABLED) {
        throw new Error(this.paymentUnavailableText)
      }
      await this.ensureLogin()
      const data = await createMembershipPayment(this.sessionToken)
      if (data.alreadyUnlocked) {
        this.applyStatus(data.membership)
        return data
      }
      this.lastOrderId = data.orderId || ''
      await new Promise((resolve, reject) => {
        uni.requestPayment({
          ...data.payment,
          success: resolve,
          fail: reject,
        })
      })
      return this.pollOrderUntilSettled(this.lastOrderId)
    },

    async pollOrder(orderId = this.lastOrderId) {
      if (!orderId) return null
      const data = await fetchPaymentOrder(orderId, this.sessionToken)
      this.lastOrderStatus = data.order?.status || ''
      this.applyStatus(data.membership || data)
      return data
    },

    async pollOrderUntilSettled(orderId = this.lastOrderId, { attempts = 6, intervalMs = 1200 } = {}) {
      let last = null
      for (let index = 0; index < attempts; index += 1) {
        last = await this.pollOrder(orderId)
        if (this.isActive || this.lastOrderStatus === 'paid') return last
        if (index < attempts - 1) await wait(intervalMs)
      }
      return last
    },
  },
})
