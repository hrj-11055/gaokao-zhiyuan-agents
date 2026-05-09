require('dotenv').config()
const express = require('express')
const cors = require('cors')

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
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean)

const rateLimitBuckets = new Map()
const THINK_OPEN = '<think>'
const THINK_CLOSE = '</think>'

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
app.use(express.json({ limit: JSON_BODY_LIMIT }))

function rateLimit(req, res, next) {
  const key = req.ip || req.headers['x-forwarded-for'] || 'unknown'
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

app.use('/api/chat', rateLimit, requireProxyToken, validateChatRequest)

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
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

app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`)
  console.log(`Dify API: ${DIFY_API_URL}`)
})
