// gaokao-miniprogram/src/api/dify.js

// 后端代理地址：本地开发默认 localhost，正式构建用 VITE_API_BASE 注入备案 HTTPS 域名。
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001'

/**
 * 持久 UTF-8 解码器
 * 微信 chunk 边界可能切在中文字符中间，必须复用同一个 TextDecoder。
 */
export class Utf8StreamDecoder {
  constructor() {
    this.decoder = new TextDecoder('utf-8')
  }

  decode(buffer) {
    return this.decoder.decode(buffer, { stream: true })
  }

  flush() {
    return this.decoder.decode()
  }
}

/**
 * SSE 流式解析器
 * 将 onChunkReceived 收到的文本片段解析为 Dify 事件
 */
export class SSEParser {
  constructor(onMessage, onEnd, onError) {
    this.buffer = ''
    this.onMessage = onMessage
    this.onEnd = onEnd
    this.onError = onError
  }

  feed(chunkText) {
    this.buffer += chunkText

    // SSE 事件以空行分隔；兼容 \n 和 \r\n 两种换行。
    const blocks = this.buffer.replace(/\r\n/g, '\n').split('\n\n')
    this.buffer = blocks.pop() // 最后一个可能不完整，保留

    for (const block of blocks) {
      this.processBlock(block)
    }
  }

  flush() {
    const block = this.buffer.replace(/\r\n/g, '\n').trim()
    this.buffer = ''
    if (block) {
      this.processBlock(block)
    }
  }

  processBlock(block) {
    const dataLines = []
    const lines = block.split('\n')

    for (const line of lines) {
      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart())
      }
    }

    if (dataLines.length === 0) return

    const dataText = dataLines.join('\n')
    if (dataText === '[DONE]') return

    try {
      const data = JSON.parse(dataText)
      if (data.event === 'message') {
        this.onMessage(data)
      } else if (data.event === 'message_end') {
        this.onEnd(data)
      } else if (data.event === 'error') {
        this.onError(data)
      }
    } catch {
      // 忽略解析失败的块
    }
  }
}

/**
 * 发送消息并接收 SSE 流式响应
 *
 * @param {Object} params
 * @param {string} params.query - 用户消息
 * @param {string} params.conversationId - 会话 ID（首轮为空）
 * @param {string} params.user - 用户标识
 * @param {Object} params.inputs - Dify 输入变量（考生省份、科目、分数、位次）
 * @param {Function} params.onChunk - 每收到一段文本时回调(answerChunk, conversationId)
 * @param {Function} params.onEnd - 流结束时回调({ conversationId, messageId })
 * @param {Function} params.onError - 错误回调(errorMessage)
 * @returns {{ abort: Function }} 可调用 abort() 取消请求
 */
export function sendMessageStream({ query, conversationId, user, inputs = {}, onChunk, onEnd, onError }) {
  const chunkDecoder = new Utf8StreamDecoder()
  const parser = new SSEParser(
    (data) => {
      if (data.answer) {
        onChunk(data.answer, data.conversation_id)
      }
    },
    (data) => {
      onEnd({
        conversationId: data.conversation_id,
        messageId: data.message_id
      })
    },
    (data) => {
      onError(data.message || 'AI 回复出错')
    }
  )

  // #ifdef MP-WEIXIN
  const requestTask = uni.request({
    url: `${API_BASE}/api/chat/stream`,
    method: 'POST',
    data: {
      query,
      conversation_id: conversationId || '',
      user,
      inputs
    },
    header: { 'Content-Type': 'application/json' },
    enableChunked: true,
    success(res) {
      if (res.statusCode && res.statusCode !== 200) {
        onError(res.data?.error || '服务暂时不可用，请稍后再试')
        return
      }
      const tail = chunkDecoder.flush()
      if (tail) parser.feed(tail)
      parser.flush()
    },
    fail(err) {
      onError('网络请求失败，请检查网络后重试')
    }
  })

  requestTask.onChunkReceived((res) => {
    const text = chunkDecoder.decode(res.data)
    parser.feed(text)
  })

  return {
    abort: () => requestTask.abort()
  }
  // #endif
}

/**
 * 发送消息并等待完整响应（blocking 模式）
 *
 * @param {Object} params
 * @returns {Promise<{ answer: string, conversationId: string, messageId: string }>}
 */
export async function sendMessageBlocking({ query, conversationId, user, inputs = {} }) {
  const response = await uni.request({
    url: `${API_BASE}/api/chat`,
    method: 'POST',
    data: {
      query,
      conversation_id: conversationId || '',
      user,
      inputs
    },
    header: { 'Content-Type': 'application/json' }
  })

  if (response.statusCode !== 200) {
    throw new Error(response.data?.error || '请求失败')
  }

  return {
    answer: response.data.answer,
    conversationId: response.data.conversation_id,
    messageId: response.data.message_id
  }
}
