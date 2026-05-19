const redis = require('./redis')

let memoryCache = { token: '', expiresAt: 0 }

async function getAccessToken() {
  const appId = process.env.WECHAT_APPID
  const appSecret = process.env.WECHAT_SECRET
  if (!appId || !appSecret) {
    throw new Error('WECHAT_APPID and WECHAT_SECRET are required')
  }

  // 1. Redis cache
  if (redis) {
    try {
      const cached = await redis.get('wechat:access_token')
      if (cached) return cached
    } catch (err) {
      console.error('Redis access_token read error:', err.message)
    }
  }

  // 2. Memory cache
  if (memoryCache.token && Date.now() < memoryCache.expiresAt) {
    return memoryCache.token
  }

  // 3. Fetch from WeChat
  const params = new URLSearchParams({
    grant_type: 'client_credential',
    appid: appId,
    secret: appSecret,
  })
  const response = await fetch(`https://api.weixin.qq.com/cgi-bin/token?${params}`)
  const data = await response.json()

  if (!response.ok || data.errcode) {
    throw new Error(data.errmsg || '获取 access_token 失败')
  }

  const token = data.access_token
  const expiresIn = data.expires_in || 7200
  const cacheTtl = Math.max(expiresIn - 200, 3600)

  if (redis) {
    try {
      await redis.set('wechat:access_token', token, 'EX', cacheTtl)
    } catch (err) {
      console.error('Redis access_token write error:', err.message)
    }
  }

  memoryCache = { token, expiresAt: Date.now() + cacheTtl * 1000 }

  return token
}

function clearCache() {
  memoryCache = { token: '', expiresAt: 0 }
  if (redis) {
    redis.del('wechat:access_token').catch(() => {})
  }
}

module.exports = { getAccessToken, clearCache }
