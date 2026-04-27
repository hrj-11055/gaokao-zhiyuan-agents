require('dotenv').config()
const express = require('express')
const cors = require('cors')

const app = express()
app.use(cors())
app.use(express.json())

const DIFY_API_URL = process.env.DIFY_API_URL || 'http://127.0.0.1:8080'
const DIFY_API_KEY = process.env.DIFY_API_KEY
const PORT = process.env.PORT || 3001

if (!DIFY_API_KEY) {
  console.error('ERROR: DIFY_API_KEY is not set in .env')
  process.exit(1)
}

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
})

// Blocking mode
app.post('/api/chat', async (req, res) => {
  try {
    const { query, conversation_id = '', user } = req.body

    if (!query || !user) {
      return res.status(400).json({ error: 'query and user are required' })
    }

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 30000)

    const response = await fetch(`${DIFY_API_URL}/v1/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: {},
        query,
        response_mode: 'blocking',
        conversation_id,
        user
      }),
      signal: controller.signal
    })
    clearTimeout(timeout)

    if (!response.ok) {
      const errText = await response.text()
      console.error('Dify blocking error:', response.status, errText)
      return res.status(502).json({ error: '服务暂时不可用，请稍后再试' })
    }

    const data = await response.json()
    res.json(data)
  } catch (err) {
    console.error('Proxy error:', err.message)
    res.status(500).json({ error: 'AI 思考时间有点长，请稍后再试' })
  }
})

// Streaming mode — pipe SSE
app.post('/api/chat/stream', async (req, res) => {
  try {
    const { query, conversation_id = '', user } = req.body

    if (!query || !user) {
      return res.status(400).json({ error: 'query and user are required' })
    }

    const response = await fetch(`${DIFY_API_URL}/v1/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: {},
        query,
        response_mode: 'streaming',
        conversation_id,
        user
      })
    })

    if (!response.ok) {
      const errText = await response.text()
      console.error('Dify streaming error:', response.status, errText)
      return res.status(502).json({ error: '服务暂时不可用，请稍后再试' })
    }

    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.setHeader('Connection', 'keep-alive')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    const pump = async () => {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          res.end()
          return
        }
        res.write(decoder.decode(value, { stream: true }))
      }
    }

    pump().catch((err) => {
      console.error('Stream pipe error:', err.message)
      if (!res.headersSent) {
        res.status(500).json({ error: 'AI 思考时间有点长，请稍后再试' })
      } else {
        res.end()
      }
    })
  } catch (err) {
    console.error('Proxy error:', err.message)
    if (!res.headersSent) {
      res.status(500).json({ error: 'AI 思考时间有点长，请稍后再试' })
    }
  }
})

app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`)
  console.log(`Dify API: ${DIFY_API_URL}`)
})
