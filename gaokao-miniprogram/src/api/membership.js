import { requestBackendData } from './backend.js'

const SESSION_KEY = 'membership_session'

function request({ url, method = 'GET', data, token }) {
  return requestBackendData({
    path: url,
    method,
    data,
    header: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
}

function getLoginCode() {
  return new Promise((resolve, reject) => {
    if (!uni.login) {
      resolve(`dev_${Date.now()}`)
      return
    }
    uni.login({
      provider: 'weixin',
      success(res) {
        resolve(res.code || `dev_${Date.now()}`)
      },
      fail(err) {
        reject(new Error(err.errMsg || '微信登录失败'))
      },
    })
  })
}

export function getStoredSession() {
  const raw = uni.getStorageSync(SESSION_KEY)
  if (!raw) return { userId: '', sessionToken: '' }
  try {
    const parsed = JSON.parse(raw)
    return {
      userId: parsed.userId || '',
      sessionToken: parsed.sessionToken || '',
    }
  } catch {
    return { userId: '', sessionToken: '' }
  }
}

export function saveStoredSession(session) {
  uni.setStorageSync(SESSION_KEY, JSON.stringify({
    userId: session.userId || '',
    sessionToken: session.sessionToken || '',
  }))
}

export function clearStoredSession() {
  uni.removeStorageSync(SESSION_KEY)
}

export function loginWithWechat({ inviterId = '' } = {}) {
  return getLoginCode()
    .then((code) => request({
      url: '/api/auth/wechat-login',
      method: 'POST',
      data: { code, inviterId },
    }))
    .then((data) => {
      saveStoredSession(data)
      return data
    })
}

export function fetchMembershipStatus(sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/membership/status',
    token: sessionToken,
  })
}

export function markProfileComplete(sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/profile/complete',
    method: 'POST',
    data: {},
    token: sessionToken,
  })
}

export function activateLimitedFreeMembership(sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/membership/limited-free-unlock',
    method: 'POST',
    data: {},
    token: sessionToken,
  })
}

export function saveUserProfileToServer(profile, sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/profile',
    method: 'POST',
    data: { profile },
    token: sessionToken,
  })
}

export function fetchUserProfileFromServer(sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/profile',
    token: sessionToken,
  })
}

export function createMembershipPayment(sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/payment/create',
    method: 'POST',
    data: {},
    token: sessionToken,
  })
}

export function fetchPaymentOrder(orderId, sessionToken = getStoredSession().sessionToken) {
  return request({
    url: `/api/payment/order/${orderId}`,
    token: sessionToken,
  })
}
