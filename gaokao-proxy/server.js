require('dotenv').config()
const express = require('express')
const cors = require('cors')
const { generateReport, saveReport, REPORTS_DIR } = require('./lib/report-builder')
const redis = require('./lib/redis')
const { textToSpeech } = require('./lib/tts')
const { createCommerceStore } = require('./lib/commerce-store')
const { signSessionToken, verifySessionToken } = require('./lib/session-token')
const { exchangeCodeForSession } = require('./lib/wechat-auth')
const { createJsapiPayment, parseWechatPayNotify } = require('./lib/wechat-pay')
const fs = require('fs').promises
const path = require('path')

const app = express()
const DIFY_API_URL = process.env.DIFY_API_URL || 'http://127.0.0.1:8080'
const DIFY_API_KEY = process.env.DIFY_API_KEY
const PORT = process.env.PORT || 3001
const JSON_BODY_LIMIT = process.env.JSON_BODY_LIMIT || '32kb'
const REQUEST_TIMEOUT_MS = Number(process.env.REQUEST_TIMEOUT_MS || 30000)
const STREAM_TIMEOUT_MS = Number(process.env.STREAM_TIMEOUT_MS || 120000)
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 60000)
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 30)
const MAX_QUERY_LENGTH = Number(process.env.MAX_QUERY_LENGTH || 2000)
const PROXY_API_TOKEN = process.env.PROXY_API_TOKEN || ''
const COMMERCE_SESSION_SECRET = process.env.COMMERCE_SESSION_SECRET || process.env.JWT_SECRET || 'local-commerce-session-secret'
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

function requireMembershipForReports(req, res, next) {
  const membership = commerceStore.getMembershipStatus(req.commerceAuth.userId)
  if (membership.status !== 'active') {
    return res.status(402).json({
      error: '请先解锁深度填报会员',
      code: 'MEMBERSHIP_REQUIRED',
      priceCents: Number(process.env.MEMBERSHIP_PRICE_CENTS || 2900),
      invite: membership.invite,
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

app.use('/api/chat', requireProxyToken, validateChatRequest, rateLimit)

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
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
  try {
    const notify = parseWechatPayNotify(req.body, {
      headers: req.headers,
      rawBody: req.rawBody || '',
    })
    const resource = notify.resource || notify
    const outTradeNo = resource.out_trade_no || notify.out_trade_no
    const transactionId = resource.transaction_id || notify.transaction_id || ''
    const tradeState = resource.trade_state || notify.trade_state || 'SUCCESS'

    if (!outTradeNo) {
      return res.status(400).json({ code: 'FAIL', message: 'out_trade_no is required' })
    }
    if (tradeState !== 'SUCCESS') {
      return res.json({ code: 'SUCCESS', message: 'ignored' })
    }

    commerceStore.markOrderPaid(outTradeNo, transactionId, notify)
    res.json({ code: 'SUCCESS', message: '成功' })
  } catch (err) {
    console.error('WeChat pay notify error:', err.message)
    res.status(500).json({ code: 'FAIL', message: err.message || '支付通知处理失败' })
  }
})

// Blocking mode
app.post('/api/chat', async (req, res) => {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const { query, conversation_id = '', user, inputs = {} } = req.body

    const response = await fetch(`${DIFY_API_URL}/v1/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs,
        query,
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

    const response = await fetch(`${DIFY_API_URL}/v1/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs,
        query,
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
        if (typeof data.answer === 'string') {
          data.answer = thinkStripper.strip(data.answer)
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
            res.write(transformSseBlock(block))
          }
        }
      }
    }

    await pump()
  } catch (err) {
    if (err.name === 'AbortError' || clientClosed) {
      if (!res.headersSent && !res.destroyed) {
        res.status(504).json({ error: 'AI 思考时间有点长，请稍后再试' })
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

// 引入 PDF 生成器
const { generatePdfFromHtml } = require('./lib/pdf-generator')

// 静态报告文件 (拦截 .pdf 并在需要时生成)
app.get('/reports/:filename', async (req, res, next) => {
  const { filename } = req.params
  if (filename.endsWith('.pdf')) {
    const pdfPath = path.join(REPORTS_DIR, filename)
    
    // 如果 PDF 已经存在，则放行给 express.static 处理
    try {
      await fs.access(pdfPath)
      return next()
    } catch {
      // PDF 不存在，查找对应的 HTML
    }
    
    const htmlFilename = filename.replace('.pdf', '.html')
    const htmlPath = path.join(REPORTS_DIR, htmlFilename)
    
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
      // 如果 HTML 也不存在或生成失败，也放行（会报 404）
      return next()
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

  const questionCount = Object.values(questionnaire || {})
    .filter(v => v !== '' && !(Array.isArray(v) && v.length === 0)).length
  const mbtiCompleted = Boolean(assessments?.mbti?.completed)
  const hollandCompleted = Boolean(assessments?.holland?.completed)
  if (questionCount < 22 || !mbtiCompleted || !hollandCompleted) {
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
    res.status(500).json({ error: err.message || '报告生成失败，请稍后重试' })
  }
})

app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`)
  console.log(`Dify API: ${DIFY_API_URL}`)
})
