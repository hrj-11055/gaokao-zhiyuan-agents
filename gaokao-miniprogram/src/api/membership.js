const API_BASE = import.meta.env.VITE_API_BASE || 'http://47.113.125.147'

const SESSION_KEY = 'membership_session'

function request({ url, method = 'GET', data, token }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        const err = new Error(res.data?.error || '请求失败')
        err.statusCode = res.statusCode
        err.code = res.data?.code || ''
        err.data = res.data
        reject(err)
      },
      fail(err) {
        reject(new Error(err.errMsg || '网络请求失败'))
      },
    })
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
