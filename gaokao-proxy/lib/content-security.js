const { getAccessToken, clearCache } = require('./access-token')

async function msgSecCheck({ openid, content, scene = 5 }) {
  if (!openid || !content) {
    return { pass: true, skipped: true }
  }

  const accessToken = await getAccessToken()

  const response = await fetch(
    `https://api.weixin.qq.com/wxa/msg_sec_check?access_token=${accessToken}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        openid,
        version: 2,
        scene,
        content: content.slice(0, 2500),
      }),
    }
  )

  const data = await response.json()

  if (data.errcode === 0) {
    const result = data.result || {}
    return {
      pass: result.suggest === 'pass',
      suggest: result.suggest,
      label: result.label || 0,
      detail: data.detail || [],
    }
  }

  if (data.errcode === 42001 || data.errcode === 40001) {
    clearCache()
    console.warn('access_token expired or invalid, cleared cache')
  }

  console.error('msgSecCheck error:', data.errcode, data.errmsg)
  return { pass: true, error: true, errcode: data.errcode, errmsg: data.errmsg }
}

module.exports = { msgSecCheck }
