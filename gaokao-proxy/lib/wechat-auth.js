async function exchangeCodeForSession({
  code,
  appId = process.env.WECHAT_APPID,
  appSecret = process.env.WECHAT_SECRET,
  mock = process.env.WECHAT_LOGIN_MOCK === '1',
} = {}) {
  if (!code || typeof code !== 'string') {
    throw new Error('code is required')
  }

  if (mock || code.startsWith('dev_')) {
    return {
      openid: `mock_openid_${code}`,
      unionid: '',
      sessionKey: '',
    }
  }

  if (!appId || !appSecret) {
    throw new Error('WECHAT_APPID and WECHAT_SECRET are required')
  }

  const params = new URLSearchParams({
    appid: appId,
    secret: appSecret,
    js_code: code,
    grant_type: 'authorization_code',
  })
  const response = await fetch(`https://api.weixin.qq.com/sns/jscode2session?${params}`)
  const data = await response.json()

  if (!response.ok || data.errcode) {
    throw new Error(data.errmsg || '微信登录失败')
  }

  return {
    openid: data.openid,
    unionid: data.unionid || '',
    sessionKey: data.session_key || '',
  }
}

module.exports = {
  exchangeCodeForSession,
}
