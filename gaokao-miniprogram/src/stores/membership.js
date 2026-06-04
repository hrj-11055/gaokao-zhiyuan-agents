import { defineStore } from 'pinia'
import {
  activateLimitedFreeMembership,
  createMembershipPayment,
  fetchMembershipStatus,
  fetchPaymentOrder,
  fetchUserProfileFromServer,
  getStoredSession,
  isTestMiniProgramEnv,
  loginWithWechat,
  markProfileComplete,
  redeemMembershipCode,
  saveUserProfileToServer,
} from '../api/membership.js'
import { PAYMENT_ENABLED } from '../config.js'

const INVITER_KEY = 'membership_inviter_id'

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function normalizeStatus(data = {}) {
  const invite = data.invite || {}
  const quota = data.downloadQuota || data.membership?.downloadQuota || {}
  return {
    status: data.status || data.membership?.status || 'inactive',
    source: data.source || data.membership?.source || '',
    unlockedAt: data.unlockedAt || data.membership?.unlockedAt || 0,
    effectiveInviteCount: Number(invite.effectiveCount ?? data.membership?.invite?.effectiveCount ?? 0),
    requiredInviteCount: Number(invite.requiredCount ?? data.membership?.invite?.requiredCount ?? 5),
    downloadQuota: {
      used: Number(quota.used ?? 0),
      limit: Number(quota.limit ?? 10),
      remaining: Number(quota.remaining ?? quota.limit ?? 10),
    },
    features: data.features || data.membership?.features || {
      universityResearch: false,
      comprehensiveReport: false,
      pdfDownload: false,
      familyShare: false,
    },
  }
}

function createPaymentFlowError(message, code, details = {}) {
  const err = new Error(message)
  err.code = code
  Object.assign(err, details)
  return err
}

export function normalizeRequestPaymentError(err = {}) {
  const message = String(err.errMsg || err.message || '')
  if (err.errCode === -2 || /cancel|取消/i.test(message)) {
    return createPaymentFlowError('支付已取消', 'PAYMENT_CANCELLED', { originalError: err })
  }
  return createPaymentFlowError('支付失败，请稍后重试', 'PAYMENT_FAILED', { originalError: err })
}

function requestVirtualPayment(params = {}) {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    if (typeof wx !== 'undefined' && wx.requestVirtualPayment) {
      wx.requestVirtualPayment({
        mode: params.mode,
        signData: params.signData,
        paySig: params.paySig,
        signature: params.signature,
        success: resolve,
        fail: reject,
      })
      return
    }
    // #endif

    reject(createPaymentFlowError('当前微信版本不支持虚拟支付，请升级微信后重试', 'VIRTUAL_PAYMENT_UNSUPPORTED'))
  })
}

export function createPendingPaymentError(orderId = '', orderStatus = '') {
  if (orderStatus === 'expired') {
    return createPaymentFlowError('支付超时，请重新发起支付', 'PAYMENT_EXPIRED', { orderId, orderStatus })
  }
  return createPaymentFlowError('支付结果确认中，请稍后刷新会员状态', 'PAYMENT_PENDING', {
    orderId,
    orderStatus,
  })
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
      requiredInviteCount: 5,
      downloadQuota: {
        used: 0,
        limit: 10,
        remaining: 10,
      },
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
    inviteUnlockText(state) {
      if (state.requiredInviteCount === 5) return '请先邀请 5 位同学免费解锁'
      return `请先邀请 ${state.requiredInviteCount} 位同学免费解锁`
    },
    isPaymentEnabled() {
      return PAYMENT_ENABLED
    },
    canUseTrialUnlock() {
      return isTestMiniProgramEnv() && !PAYMENT_ENABLED
    },
    paymentUnavailableText() {
      return '当前构建未启用微信支付，请重新上传支付测试版。'
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
      this.downloadQuota = status.downloadQuota
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

    async redeemCode(code) {
      await this.ensureLogin()
      const data = await redeemMembershipCode(code, this.sessionToken)
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
      try {
        await requestVirtualPayment(data.virtualPayment)
      } catch (err) {
        throw normalizeRequestPaymentError(err)
      }
      const settled = await this.pollOrderUntilSettled(this.lastOrderId)
      if (!this.isActive && this.lastOrderStatus !== 'paid') {
        throw createPendingPaymentError(this.lastOrderId, this.lastOrderStatus)
      }
      return settled
    },

    async openMembership() {
      return this.createPayment()
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
