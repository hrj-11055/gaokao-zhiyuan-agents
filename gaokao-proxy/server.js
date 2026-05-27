require('dotenv').config()
const express = require('express')
const cors = require('cors')
const { generateReport, saveReport, saveReportDraft, REPORTS_DIR } = require('./lib/report-builder')
const { generatePdfFromHtml, isGeneratedPdfFresh } = require('./lib/pdf-generator')
const { createReportRoutes } = require('./lib/report-routes')
const { fetchReportDetail, normalizeType } = require('./lib/report-data-client')
const { buildDeepReportHtml, buildDeepReportReaderHtml, generateDeepReportPdf } = require('./lib/deep-report-pdf')
const { createDeepReportViewToken, verifyDeepReportViewToken } = require('./lib/deep-report-view-token')
const { getMajorInsights, parseNames } = require('./lib/major-insights')
const redis = require('./lib/redis')
const { textToSpeech } = require('./lib/tts')
const { createCommerceStore } = require('./lib/commerce-store')
const { signSessionToken, verifySessionToken } = require('./lib/session-token')
const { exchangeCodeForSession } = require('./lib/wechat-auth')
const { createJsapiPayment, parseWechatPayNotify } = require('./lib/wechat-pay')
const { msgSecCheck } = require('./lib/content-security')
const { buildProfileGateAnswer, buildRecommendationGuidedQuery } = require('./lib/profile-followup-gate')
const fs = require('fs').promises
const path = require('path')

const app = express()
const DIFY_API_URL = process.env.DIFY_API_URL || 'http://127.0.0.1:8080'
const DIFY_API_KEY = process.env.DIFY_API_KEY
const PORT = process.env.PORT || 3001
const JSON_BODY_LIMIT = process.env.JSON_BODY_LIMIT || '32kb'
const REQUEST_TIMEOUT_MS = Number(process.env.REQUEST_TIMEOUT_MS || 120000)
const STREAM_TIMEOUT_MS = Number(process.env.STREAM_TIMEOUT_MS || 180000)
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 60000)
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 30)
const MAX_QUERY_LENGTH = Number(process.env.MAX_QUERY_LENGTH || 2000)
const PROXY_API_TOKEN = process.env.PROXY_API_TOKEN || ''
const COMMERCE_SESSION_SECRET = process.env.COMMERCE_SESSION_SECRET || process.env.JWT_SECRET || 'local-commerce-session-secret'
const LIMITED_FREE_UNLOCK_ENABLED = process.env.LIMITED_FREE_UNLOCK_ENABLED !== 'false'
const DEEP_REPORT_VIEW_TOKEN_TTL_MS = Number(process.env.DEEP_REPORT_VIEW_TOKEN_TTL_MS || 10 * 60 * 1000)
const QUESTIONNAIRE_REQUIRED_COUNT = 21
const QUESTIONNAIRE_ACTIVE_IDS = [
  'q1', 'q2', 'q3', 'q4', 'q5',
  'q6', 'q7', 'q8',
  'q10', 'q11', 'q12', 'q13',
  'q14', 'q15', 'q16',
  'q17', 'q18', 'q19', 'q20', 'q21', 'q22'
]
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean)

const rateLimitBuckets = new Map()
const reportCooldowns = new Map()
const REPORT_COOLDOWN_MS = 10 * 60 * 1000
const THINK_OPEN = '<think>'
const THINK_CLOSE = '</think>'
const commerceStore = createCommerceStore()
const reportRoutes = createReportRoutes(false)

if (!DIFY_API_KEY) {
  console.error('ERROR: DIFY_API_KEY is not set in .env')
  process.exit(1)
}

app.use(cors({
  origin(origin, callback) {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true)
      return
    }
    if (ALLOWED_ORIGINS.length === 0) {
      callback(new Error('Origin not configured'))
      return
    }
    callback(new Error('Origin not allowed'))
  }
}))
app.use(express.json({
  limit: JSON_BODY_LIMIT,
  verify: (req, res, buf) => {
    req.rawBody = buf.toString('utf8')
  },
}))

async function rateLimit(req, res, next) {
  const key = (req.body && req.body.user) || req.ip || 'unknown'
  
  // Redis 模式优先
  if (redis) {
    const redisKey = `ratelimit:${key}`
    try {
      const current = await redis.incr(redisKey)
      if (current === 1) {
        await redis.expire(redisKey, Math.floor(RATE_LIMIT_WINDOW_MS / 1000))
      }
      if (current > RATE_LIMIT_MAX) {
        return res.status(429).json({ error: '请求太频繁，请稍后再试' })
      }
      return next()
    } catch (err) {
      console.error('Redis RateLimit Error:', err.message)
      // 报错则降级到内存模式继续执行
    }
  }

  // 内存降级模式
  const now = Date.now()
  const bucket = rateLimitBuckets.get(key) || { count: 0, resetAt: now + RATE_LIMIT_WINDOW_MS }

  if (now > bucket.resetAt) {
    bucket.count = 0
    bucket.resetAt = now + RATE_LIMIT_WINDOW_MS
  }

  bucket.count += 1
  rateLimitBuckets.set(key, bucket)

  if (bucket.count > RATE_LIMIT_MAX) {
    return res.status(429).json({ error: '请求太频繁，请稍后再试' })
  }

  next()
}

function requireProxyToken(req, res, next) {
  if (!PROXY_API_TOKEN) {
    next()
    return
  }

  if (req.get('x-proxy-token') !== PROXY_API_TOKEN) {
    return res.status(401).json({ error: '未授权请求' })
  }

  next()
}

function getBearerToken(req) {
  const auth = req.get('authorization') || ''
  if (!auth.startsWith('Bearer ')) return ''
  return auth.slice('Bearer '.length).trim()
}

function requireCommerceAuth(req, res, next) {
  try {
    const token = getBearerToken(req)
    const payload = verifySessionToken(token, COMMERCE_SESSION_SECRET)
    if (!payload.userId || !payload.openid) {
      return res.status(401).json({ error: '请先登录微信身份' })
    }
    req.commerceAuth = payload
    next()
  } catch {
    res.status(401).json({ error: '请先登录微信身份' })
  }
}

function getOptionalCommerceAuth(req) {
  try {
    const token = getBearerToken(req)
    return verifySessionToken(token, COMMERCE_SESSION_SECRET)
  } catch {
    return null
  }
}

function requireMembershipForReports(req, res, next) {
  const membership = commerceStore.getMembershipStatus(req.commerceAuth.userId)
  if (membership.status !== 'active') {
    return res.status(402).json({
      error: '请先解锁深度填报会员',
      code: 'MEMBERSHIP_REQUIRED',
      priceCents: Number(process.env.MEMBERSHIP_PRICE_CENTS || 2900),
      invite: membership.invite,
      downloadQuota: membership.downloadQuota,
    })
  }
  req.membership = membership
  next()
}

function validateChatRequest(req, res, next) {
  const { query, user } = req.body || {}
  if (!query || !user) {
    return res.status(400).json({ error: 'query and user are required' })
  }
  if (typeof query !== 'string' || query.length > MAX_QUERY_LENGTH) {
    return res.status(400).json({ error: '问题内容过长，请精简后再试' })
  }
  if (typeof user !== 'string' || user.length > 128) {
    return res.status(400).json({ error: 'user is invalid' })
  }
  next()
}

async function checkContentSecurity(req, res, next) {
  const { query } = req.body || {}

  const token = getBearerToken(req)
  let openid = ''

  if (token) {
    try {
      const payload = verifySessionToken(token, COMMERCE_SESSION_SECRET)
      openid = payload.openid || ''
    } catch {
      // Not authenticated, skip content check
    }
  }

  if (!openid || !query) {
    return next()
  }

  try {
    const result = await msgSecCheck({ openid, content: query, scene: 5 })
    if (!result.pass) {
      return res.status(400).json({
        error: '消息内容不符合规范，请修改后重新发送',
        code: 'CONTENT_REJECTED',
        label: result.label,
      })
    }
    next()
  } catch (err) {
    console.error('Content security check failed:', err.message)
    next()
  }
}

function sanitizeProfileInputs(inputs = {}) {
  const clean = {}
  if (typeof inputs.province === 'string' && inputs.province.trim()) {
    clean.province = inputs.province.trim()
  }
  if (typeof inputs.category === 'string' && inputs.category.trim()) {
    clean.category = inputs.category.trim()
  }
  if (inputs.score !== undefined && inputs.score !== '') {
    const score = Number(inputs.score)
    if (Number.isFinite(score)) {
      clean.score = String(Math.trunc(score))
    }
  }
  if (inputs.rank !== undefined && inputs.rank !== '') {
    const rank = Number(inputs.rank)
    if (Number.isFinite(rank) && rank > 0) {
      clean.rank = String(Math.trunc(rank))
    }
  }
  ;['family_resources', 'interest_subjects', 'region_preference', 'career_goal'].forEach((key) => {
    if (typeof inputs[key] === 'string' && inputs[key].trim()) {
      clean[key] = inputs[key].trim()
    }
  })
  return clean
}

function buildProfileInputs(profile = {}) {
  const inputs = {}
  if (profile.province) inputs.province = profile.province
  if (profile.category) inputs.category = profile.category
  if (typeof profile.score === 'number') inputs.score = String(profile.score)
  if (typeof profile.rank === 'number' && profile.rank > 0) inputs.rank = String(profile.rank)
  ;['family_resources', 'interest_subjects', 'region_preference', 'career_goal'].forEach((key) => {
    if (profile[key]) inputs[key] = profile[key]
  })
  return inputs
}

function mergeProfileInputs(req, requestInputs = {}) {
  const auth = req.commerceAuth || getOptionalCommerceAuth(req)
  const serverProfile = auth?.userId ? commerceStore.getProfile(auth.userId) : {}
  return {
    ...buildProfileInputs(serverProfile),
    ...sanitizeProfileInputs(requestInputs),
  }
}

function removeThinkBlocks(text) {
  if (typeof text !== 'string' || !text.includes(THINK_OPEN)) {
    return text
  }

  return text
    .replace(/<think>[\s\S]*?<\/think>/g, '')
    .replace(/<think>[\s\S]*$/g, '')
    .trimStart()
}

function removeThinkBlocksDeep(value) {
  if (typeof value === 'string') {
    return removeThinkBlocks(value)
  }
  if (Array.isArray(value)) {
    return value.map((item) => removeThinkBlocksDeep(item))
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, removeThinkBlocksDeep(item)])
    )
  }
  return value
}

function hasLengthFinishReason(data = {}) {
  const finishReason =
    data.finish_reason ||
    data.metadata?.finish_reason ||
    data.metadata?.usage?.finish_reason ||
    data.data?.process_data?.finish_reason ||
    data.data?.outputs?.usage?.finish_reason ||
    data.data?.outputs?.finish_reason

  return String(finishReason || '').toLowerCase() === 'length'
}

function markProxyTruncated(data = {}) {
  data.truncated = true
  data.metadata = {
    ...(data.metadata || {}),
    proxy_truncated: true,
    finish_reason: 'length',
  }
  if (data.data && typeof data.data === 'object') {
    data.data.truncated = true
  }
  return data
}

function markerPrefixSuffixLength(text, marker) {
  const max = Math.min(text.length, marker.length - 1)
  for (let length = max; length > 0; length -= 1) {
    if (text.endsWith(marker.slice(0, length))) {
      return length
    }
  }
  return 0
}

function createThinkStripper() {
  let inThinkBlock = false
  let pending = ''

  return {
    strip(text) {
      let input = pending + text
      pending = ''
      let output = ''

      while (input) {
        if (inThinkBlock) {
          const closeIndex = input.indexOf(THINK_CLOSE)
          if (closeIndex === -1) {
            const keep = markerPrefixSuffixLength(input, THINK_CLOSE)
            pending = keep > 0 ? input.slice(-keep) : ''
            return output
          }
          input = input.slice(closeIndex + THINK_CLOSE.length)
          inThinkBlock = false
          continue
        }

        const openIndex = input.indexOf(THINK_OPEN)
        if (openIndex === -1) {
          const keep = markerPrefixSuffixLength(input, THINK_OPEN)
          if (keep > 0) {
            output += input.slice(0, -keep)
            pending = input.slice(-keep)
          } else {
            output += input
          }
          return output
        }

        output += input.slice(0, openIndex)
        input = input.slice(openIndex + THINK_OPEN.length)
        inThinkBlock = true
      }

      return output
    },
    flush() {
      const output = inThinkBlock ? '' : pending
      pending = ''
      return output
    }
  }
}

app.use('/api/chat', requireProxyToken, validateChatRequest, rateLimit, checkContentSecurity)

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
})

// Report query API
app.get('/api/reports/health', reportRoutes.healthCheck)
app.get('/api/reports/stats', reportRoutes.getStats)
app.get('/api/reports/majors', reportRoutes.listMajors)
app.get('/api/reports/majors/:code', reportRoutes.getMajor)
app.get('/api/reports/universities', reportRoutes.listUniversities)
app.get('/api/reports/universities/:name', reportRoutes.getUniversity)

app.get('/api/reports/major-insights', async (req, res) => {
  const names = parseNames(req.query.names)
  if (names.length === 0) {
    res.status(400).json({ error: 'names is required' })
    return
  }

  try {
    res.json({ data: await getMajorInsights(names) })
  } catch (err) {
    console.error('Major insights error:', err.message)
    res.status(500).json({ error: '专业结构化信息查询失败' })
  }
})

app.post('/api/reports/deep/view-token', requireCommerceAuth, requireMembershipForReports, (req, res) => {
  const { type = '', id = '' } = req.body || {}
  if (!type || !id) {
    res.status(400).json({ error: 'type and id are required' })
    return
  }

  try {
    const normalizedType = normalizeType(type)
    const token = createDeepReportViewToken({
      userId: req.commerceAuth.userId,
      type: normalizedType,
      id,
    }, COMMERCE_SESSION_SECRET, { ttlMs: DEEP_REPORT_VIEW_TOKEN_TTL_MS })
    const baseUrl = process.env.REPORT_BASE_URL || `http://localhost:${PORT}`
    res.json({
      url: `${baseUrl}/reports/deep/view/${encodeURIComponent(token)}`,
      expiresIn: Math.floor(DEEP_REPORT_VIEW_TOKEN_TTL_MS / 1000),
    })
  } catch (err) {
    res.status(400).json({ error: err.message || '生成阅读链接失败' })
  }
})

app.get('/api/reports/deep/pdf', requireCommerceAuth, requireMembershipForReports, async (req, res) => {
  const { type = '', id = '' } = req.query || {}
  if (!type || !id) {
    res.status(400).json({ error: 'type and id are required' })
    return
  }

  const quotaCheck = commerceStore.canDownloadDeepReport(req.commerceAuth.userId)
  if (!quotaCheck.allowed) {
    const statusCode = quotaCheck.code === 'DOWNLOAD_QUOTA_EXHAUSTED' ? 429 : 402
    res.status(statusCode).json({
      code: quotaCheck.code,
      error: quotaCheck.code === 'DOWNLOAD_QUOTA_EXHAUSTED'
        ? '深度报告下载次数已用完'
        : '请先解锁深度填报会员',
      membership: quotaCheck.membership,
      downloadQuota: quotaCheck.membership?.downloadQuota,
    })
    return
  }

  try {
    const report = await fetchReportDetail(type, id, { full: true })
    buildDeepReportHtml({ type, report })
    const { filename, pdfPath, title } = await generateDeepReportPdf({
      type,
      report,
      outputDir: path.join(REPORTS_DIR, 'deep-reports'),
    })

    res.setHeader('Content-Type', 'application/pdf')
    res.setHeader(
      'Content-Disposition',
      `attachment; filename*=UTF-8''${encodeURIComponent(`${title}-${filename}`)}`
    )
    const membership = commerceStore.recordDeepReportDownload({
      userId: req.commerceAuth.userId,
      reportType: type,
      reportId: id,
      filename,
    })
    res.setHeader('X-Deep-Report-Downloads-Remaining', String(membership.downloadQuota.remaining))
    res.sendFile(pdfPath)
  } catch (err) {
    console.error('Deep report PDF error:', err.message)
    if (err.code === 'DOWNLOAD_QUOTA_EXHAUSTED') {
      return res.status(429).json({
        code: 'DOWNLOAD_QUOTA_EXHAUSTED',
        error: '深度报告下载次数已用完',
        membership: err.membership,
        downloadQuota: err.membership?.downloadQuota,
      })
    }
    const status = err.status === 404 ? 404 : 500
    res.status(status).json({ error: err.status === 404 ? '报告不存在' : '深度报告 PDF 生成失败' })
  }
})

app.get('/reports/deep/view/:token', async (req, res) => {
  try {
    const payload = verifyDeepReportViewToken(req.params.token, COMMERCE_SESSION_SECRET)
    const membership = commerceStore.getMembershipStatus(payload.userId)
    if (membership.status !== 'active') {
      res.status(403).send('<!doctype html><meta charset="utf-8"><title>会员已失效</title><body style="font-family:sans-serif;padding:32px">请重新回到小程序开通会员后查看。</body>')
      return
    }

    const type = normalizeType(payload.type)
    const report = await fetchReportDetail(type, payload.id, { full: true })
    const html = buildDeepReportReaderHtml({ type, report })
    res.setHeader('Content-Type', 'text/html; charset=utf-8')
    res.setHeader('Cache-Control', 'no-store')
    res.setHeader('X-Robots-Tag', 'noindex, nofollow')
    res.send(html)
  } catch (err) {
    console.error('Deep report reader error:', err.message)
    res.status(401).send('<!doctype html><meta charset="utf-8"><title>阅读链接已失效</title><body style="font-family:sans-serif;padding:32px">阅读链接已失效，请回到小程序重新打开报告。</body>')
  }
})

app.post('/api/auth/wechat-login', async (req, res) => {
  const { code, inviterId = '' } = req.body || {}
  try {
    const session = await exchangeCodeForSession({ code })
    const user = commerceStore.upsertWechatUser({
      openid: session.openid,
      unionid: session.unionid || '',
      inviterId,
    })
    const membership = commerceStore.getMembershipStatus(user.userId)
    const sessionToken = signSessionToken({
      userId: user.userId,
      openid: user.openid,
    }, COMMERCE_SESSION_SECRET)

    res.json({
      userId: user.userId,
      sessionToken,
      membership,
      invite: membership.invite,
    })
  } catch (err) {
    console.error('WeChat login error:', err.message)
    res.status(502).json({ error: err.message || '微信登录失败' })
  }
})

app.get('/api/membership/status', requireCommerceAuth, (req, res) => {
  res.json(commerceStore.getMembershipStatus(req.commerceAuth.userId))
})

app.post('/api/membership/redeem-code', requireCommerceAuth, (req, res) => {
  try {
    const result = commerceStore.redeemVipCode(req.commerceAuth.userId, req.body?.code || '')
    res.json({
      code: 'VIP_CODE_REDEEMED',
      membership: result.membership,
    })
  } catch (err) {
    res.status(400).json({
      code: 'VIP_CODE_INVALID',
      error: err.message || '会员邀请码兑换失败',
    })
  }
})

app.post('/api/membership/limited-free-unlock', requireCommerceAuth, (req, res) => {
  if (!LIMITED_FREE_UNLOCK_ENABLED) {
    res.status(403).json({ error: '限时免费入口已关闭' })
    return
  }

  try {
    const membership = commerceStore.activateMembership(req.commerceAuth.userId, 'limited_free')
    res.json({
      status: 'ok',
      membership,
    })
  } catch (err) {
    res.status(400).json({ error: err.message || '限时免费解锁失败' })
  }
})

app.post('/api/profile/complete', requireCommerceAuth, (req, res) => {
  try {
    const result = commerceStore.completeProfile(req.commerceAuth.userId)
    res.json({
      status: 'ok',
      inviteCounted: result.inviteCounted,
      membership: result.membership,
    })
  } catch (err) {
    res.status(400).json({ error: err.message || '保存用户资料失败' })
  }
})

app.post('/api/profile', requireCommerceAuth, (req, res) => {
  try {
    const profile = commerceStore.saveProfile(req.commerceAuth.userId, req.body?.profile || {})
    const completion = commerceStore.completeProfile(req.commerceAuth.userId)
    res.json({
      status: 'ok',
      profile,
      inviteCounted: completion.inviteCounted,
      membership: completion.membership,
    })
  } catch (err) {
    res.status(400).json({ error: err.message || '保存用户资料失败' })
  }
})

app.get('/api/profile', requireCommerceAuth, (req, res) => {
  res.json({
    profile: commerceStore.getProfile(req.commerceAuth.userId),
    membership: commerceStore.getMembershipStatus(req.commerceAuth.userId),
  })
})

app.post('/api/payment/create', requireCommerceAuth, async (req, res) => {
  const membership = commerceStore.getMembershipStatus(req.commerceAuth.userId)
  if (membership.status === 'active') {
    return res.json({ alreadyUnlocked: true, membership })
  }

  try {
    const order = commerceStore.createPaymentOrder(req.commerceAuth.userId)
    const paymentResult = await createJsapiPayment({
      order,
      openid: req.commerceAuth.openid,
      description: '深度填报会员',
    })
    commerceStore.attachPrepayId(order.orderId, paymentResult.prepayId)
    res.json({
      orderId: order.orderId,
      payment: paymentResult.payment,
    })
  } catch (err) {
    const status = err.code === 'WECHAT_PAY_NOT_CONFIGURED' ? 503 : 502
    res.status(status).json({ error: err.message || '微信支付下单失败', code: err.code || 'WECHAT_PAY_FAILED' })
  }
})

app.get('/api/payment/order/:orderId', requireCommerceAuth, (req, res) => {
  const order = commerceStore.getOrder(req.params.orderId)
  if (!order || order.userId !== req.commerceAuth.userId) {
    return res.status(404).json({ error: '订单不存在' })
  }
  res.json({
    order,
    membership: commerceStore.getMembershipStatus(req.commerceAuth.userId),
  })
})

app.post('/api/payment/wechat/notify', async (req, res) => {
  let notifyLogContext = {}
  try {
    const notify = parseWechatPayNotify(req.body, {
      headers: req.headers,
      rawBody: req.rawBody || '',
    })
    const resource = notify.resource || notify
    const outTradeNo = resource.out_trade_no || notify.out_trade_no
    const transactionId = resource.transaction_id || notify.transaction_id || ''
    const tradeState = resource.trade_state || notify.trade_state || 'SUCCESS'
    notifyLogContext = { outTradeNo, transactionId, tradeState }

    if (!outTradeNo) {
      return res.status(400).json({ code: 'FAIL', message: 'out_trade_no is required' })
    }
    if (tradeState !== 'SUCCESS') {
      return res.json({ code: 'SUCCESS', message: 'ignored' })
    }

    commerceStore.markOrderPaid(outTradeNo, transactionId, notify)
    res.json({ code: 'SUCCESS', message: '成功' })
  } catch (err) {
    console.error('WeChat pay notify error:', {
      ...notifyLogContext,
      errorCode: err.code || 'WECHAT_PAY_NOTIFY_FAILED',
      message: err.message,
    })
    res.status(500).json({
      code: 'FAIL',
      message: err.message || '支付通知处理失败',
      errorCode: err.code || 'WECHAT_PAY_NOTIFY_FAILED',
    })
  }
})

// Blocking mode
app.post('/api/chat', async (req, res) => {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const { query, conversation_id = '', user, inputs = {} } = req.body
    const finalInputs = mergeProfileInputs(req, inputs)
    const gateAnswer = buildProfileGateAnswer({
      query,
      inputs: finalInputs,
      conversationId: conversation_id,
    })
    if (gateAnswer) {
      return res.json(gateAnswer)
    }
    const guidedQuery = buildRecommendationGuidedQuery(query)

    const response = await fetch(`${DIFY_API_URL}/v1/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: finalInputs,
        query: guidedQuery,
        response_mode: 'blocking',
        conversation_id,
        user
      }),
      signal: controller.signal
    })

    if (!response.ok) {
      const errText = await response.text()
      console.error('Dify blocking error:', response.status, errText)
      return res.status(502).json({ error: '服务暂时不可用，请稍后再试' })
    }

    const data = await response.json()
    if (typeof data.answer === 'string') {
      data.answer = removeThinkBlocks(data.answer)
    }
    if (hasLengthFinishReason(data)) {
      markProxyTruncated(data)
    }
    res.json(data)
  } catch (err) {
    if (err.name === 'AbortError') {
      return res.status(504).json({ error: 'AI 思考时间有点长，请稍后再试' })
    }
    console.error('Proxy error:', err.message)
    res.status(500).json({ error: 'AI 思考时间有点长，请稍后再试' })
  } finally {
    clearTimeout(timeout)
  }
})

// Streaming mode — pipe SSE
app.post('/api/chat/stream', async (req, res) => {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS)
  let clientClosed = false

  res.on('close', () => {
    clientClosed = true
    controller.abort()
  })

  try {
    const { query, conversation_id = '', user, inputs = {} } = req.body
    const finalInputs = mergeProfileInputs(req, inputs)
    const gateAnswer = buildProfileGateAnswer({
      query,
      inputs: finalInputs,
      conversationId: conversation_id,
    })
    if (gateAnswer) {
      res.setHeader('Content-Type', 'text/event-stream')
      res.setHeader('Cache-Control', 'no-cache')
      res.setHeader('Connection', 'keep-alive')
      res.setHeader('X-Accel-Buffering', 'no')
      if (typeof res.flushHeaders === 'function') {
        res.flushHeaders()
      }
      res.write(`data: ${JSON.stringify({
        event: 'message',
        answer: gateAnswer.answer,
        conversation_id: gateAnswer.conversation_id,
        message_id: gateAnswer.message_id,
        metadata: gateAnswer.metadata,
      })}\n\n`)
      res.write(`data: ${JSON.stringify({
        event: 'message_end',
        conversation_id: gateAnswer.conversation_id,
        message_id: gateAnswer.message_id,
        metadata: gateAnswer.metadata,
      })}\n\n`)
      res.end()
      return
    }
    const guidedQuery = buildRecommendationGuidedQuery(query)

    const response = await fetch(`${DIFY_API_URL}/v1/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: finalInputs,
        query: guidedQuery,
        response_mode: 'streaming',
        conversation_id,
        user
      }),
      signal: controller.signal
    })

    if (!response.ok) {
      const errText = await response.text()
      console.error('Dify streaming error:', response.status, errText)
      return res.status(502).json({ error: '服务暂时不可用，请稍后再试' })
    }

    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.setHeader('Connection', 'keep-alive')
    res.setHeader('X-Accel-Buffering', 'no')
    if (typeof res.flushHeaders === 'function') {
      res.flushHeaders()
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    const thinkStripper = createThinkStripper()
    let sseBuffer = ''
    let upstreamLengthTruncated = false

    const transformSseBlock = (block) => {
      const lines = block.split('\n')
      const dataLines = lines.filter((line) => line.startsWith('data:'))
      if (dataLines.length === 0) {
        return `${block}\n\n`
      }

      const dataText = dataLines.map((line) => line.slice(5).trimStart()).join('\n')
      if (!dataText || dataText === '[DONE]') {
        return `${block}\n\n`
      }

      try {
        const data = JSON.parse(dataText)
        if (hasLengthFinishReason(data)) {
          upstreamLengthTruncated = true
        }
        if (typeof data.answer === 'string') {
          data.answer = thinkStripper.strip(data.answer)
          if ((data.event === 'message' || data.event === 'agent_message') && data.answer === '') {
            return ''
          }
        }
        if (upstreamLengthTruncated && (data.event === 'message_end' || data.event === 'workflow_finished')) {
          markProxyTruncated(data)
        }
        return `${lines.filter((line) => !line.startsWith('data:')).join('\n')}\ndata: ${JSON.stringify(removeThinkBlocksDeep(data))}\n\n`
      } catch {
        return `${block}\n\n`
      }
    }

    const pump = async () => {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          const flushed = thinkStripper.flush()
          if (flushed && !clientClosed) {
            res.write(`data: ${JSON.stringify({ event: 'message', answer: flushed })}\n\n`)
          }
          res.end()
          return
        }
        if (!clientClosed) {
          sseBuffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
          const blocks = sseBuffer.split('\n\n')
          sseBuffer = blocks.pop()
          for (const block of blocks) {
            const transformed = transformSseBlock(block)
            if (transformed) {
              res.write(transformed)
            }
          }
        }
      }
    }

    await pump()
  } catch (err) {
    if (err.name === 'AbortError' || clientClosed) {
      if (!res.headersSent && !res.destroyed) {
        res.status(504).json({ error: 'AI 思考时间有点长，请稍后再试' })
      } else if (!res.destroyed && !clientClosed) {
        res.write(`data: ${JSON.stringify({
          event: 'error',
          message: 'AI 回复时间超过 3 分钟，请点重新生成获取完整建议。',
        })}\n\n`)
        res.end()
      }
      return
    }
    console.error('Proxy error:', err.message)
    if (!res.headersSent) {
      res.status(500).json({ error: 'AI 思考时间有点长，请稍后再试' })
    }
  } finally {
    clearTimeout(timeout)
  }
})

// 深度报告的中间 HTML/PDF 文件不允许绕过会员鉴权直接访问。
app.use('/reports/deep-reports', (req, res) => {
  res.status(404).json({ error: '报告不存在或链接已失效' })
})

// 静态报告文件 (拦截 .pdf 并在需要时生成)
app.get('/reports/:filename', async (req, res, next) => {
  const { filename } = req.params
  if (filename.endsWith('.pdf')) {
    const pdfPath = path.join(REPORTS_DIR, filename)
    const htmlFilename = filename.replace('.pdf', '.html')
    const htmlPath = path.join(REPORTS_DIR, htmlFilename)

    // 如果 PDF 已经存在且由当前生成器版本生成，则放行给 express.static 处理。
    // 旧 PDF 没有字体元数据时会重新生成，避免继续给真机返回中文方块乱码文件。
    try {
      await fs.access(pdfPath)
      try {
        await fs.access(htmlPath)
        if (await isGeneratedPdfFresh(pdfPath, htmlPath)) {
          return next()
        }
        console.log(`PDF is stale, regenerating ${filename}...`)
      } catch (err) {
        if (err && err.code === 'ENOENT') {
          return next()
        }
        throw err
      }
    } catch (err) {
      if (err && err.code !== 'ENOENT') {
        console.error(`PDF freshness check failed for ${filename}:`, err.message)
      }
    }

    try {
      await fs.access(htmlPath)
      // HTML 存在，生成 PDF
      console.log(`Generating PDF for ${htmlFilename}...`)
      await generatePdfFromHtml(htmlPath, pdfPath)
      console.log(`PDF generated: ${pdfPath}`)
      // 生成完毕后放行给 express.static
      return next()
    } catch (err) {
      console.error(`HTML not found or PDF generation failed for ${filename}:`, err.message)
      return res.status(404).json({ error: 'PDF 未生成成功，请重新生成报告' })
    }
  }
  next()
})
app.use('/reports', express.static(REPORTS_DIR))

// TTS 语音合成接口
app.post('/api/tts', async (req, res) => {
  const { text } = req.body
  if (!text) {
    return res.status(400).json({ error: 'text is required' })
  }

  try {
    const audioBuffer = await textToSpeech(text.slice(0, 1000)) // 调整为 1000 字限制
    res.setHeader('Content-Type', 'audio/mpeg')
    res.send(audioBuffer)
  } catch (err) {
    console.error('TTS Error:', err.message)
    res.status(500).json({ error: '语音合成失败' })
  }
})

// 对话反馈接口
app.post('/api/chat/feedback', async (req, res) => {
  const { messageId, rating, query, answer } = req.body
  if (!rating) {
    return res.status(400).json({ error: 'rating is required' })
  }

  const logEntry = {
    timestamp: new Date().toISOString(),
    messageId,
    rating, // 1 为点赞, -1 为踩
    query,
    answer
  }

  try {
    const logPath = path.join(__dirname, 'logs', 'feedback.jsonl')
    await fs.mkdir(path.dirname(logPath), { recursive: true })
    await fs.appendFile(logPath, JSON.stringify(logEntry) + '\n')
    res.json({ status: 'ok' })
  } catch (err) {
    console.error('Feedback Log Error:', err.message)
    res.status(500).json({ error: '反馈提交失败' })
  }
})

// 报告生成端点
app.post('/api/report/generate', requireCommerceAuth, requireMembershipForReports, async (req, res) => {
  const { userId, profile, questionnaire, assessments, conversationId } = req.body || {}

  const reportUserId = req.commerceAuth.userId || userId

  const questionCount = QUESTIONNAIRE_ACTIVE_IDS.map(id => questionnaire?.[id])
    .filter(v => v !== '' && !(Array.isArray(v) && v.length === 0)).length
  const mbtiCompleted = Boolean(assessments?.mbti?.completed)
  const hollandCompleted = Boolean(assessments?.holland?.completed)
  if (questionCount < QUESTIONNAIRE_REQUIRED_COUNT || !mbtiCompleted || !hollandCompleted) {
    return res.status(400).json({ error: '请先完成全部 3 项测评后再生成综合报告' })
  }

  const cooldownKey = `cooldown:report:${reportUserId}`
  
  if (redis) {
    try {
      const ttl = await redis.ttl(cooldownKey)
      if (ttl > 0) {
        return res.status(429).json({ error: `请 ${ttl} 秒后再试` })
      }
    } catch (err) {
      console.error('Redis Cooldown Check Error:', err.message)
    }
  } else {
    const lastAt = reportCooldowns.get(reportUserId) || 0
    if (Date.now() - lastAt < REPORT_COOLDOWN_MS) {
      const waitSec = Math.ceil((REPORT_COOLDOWN_MS - (Date.now() - lastAt)) / 1000)
      return res.status(429).json({ error: `请 ${waitSec} 秒后再试` })
    }
  }

  try {
    const html = await generateReport({
      profile: profile || {},
      questionnaire: questionnaire || {},
      assessments: assessments || {},
      conversationId: conversationId || '',
      difyApiUrl: DIFY_API_URL,
      difyApiKey: DIFY_API_KEY,
    })

    const filename = await saveReport(reportUserId, html)
    
    // 设置冷却
    if (redis) {
      await redis.set(cooldownKey, '1', 'EX', Math.floor(REPORT_COOLDOWN_MS / 1000)).catch(e => {
        console.error('Redis Cooldown Set Error:', e.message)
      })
    } else {
      reportCooldowns.set(reportUserId, Date.now())
    }

    const baseUrl = process.env.REPORT_BASE_URL || `http://localhost:${PORT}`
    res.json({ url: `${baseUrl}/reports/${filename}` })
  } catch (err) {
    console.error('Report generation error:', err.message)
    if (!redis) reportCooldowns.delete(reportUserId)
    let draftId = ''
    try {
      draftId = await saveReportDraft(reportUserId, {
        profile: profile || {},
        questionnaire: questionnaire || {},
        assessments: assessments || {},
        conversationId: conversationId || '',
        error: err.message || '报告生成失败',
      })
    } catch (draftErr) {
      console.error('Report draft save error:', draftErr.message)
    }
    res.status(500).json({
      error: err.message || '报告生成失败，请稍后重试',
      draftId,
    })
  }
})

app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`)
  console.log(`Dify API: ${DIFY_API_URL}`)
})
