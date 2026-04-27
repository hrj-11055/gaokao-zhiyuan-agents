// gaokao-miniprogram/src/api/dify.js

// 后端代理地址（部署后替换为真实域名）
const API_BASE = 'http://localhost:3001'

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

    // 按 \n\n 分割完整的 SSE 事件块
    const blocks = this.buffer.split('\n\n')
    this.buffer = blocks.pop() // 最后一个可能不完整，保留

    for (const block of blocks) {
      const lines = block.split('\n')
      let dataLine = ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          dataLine = line.slice(6)
        }
      }

      if (!dataLine) continue

      try {
        const data = JSON.parse(dataLine)
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
}

/**
 * 发送消息并接收 SSE 流式响应
 *
 * @param {Object} params
 * @param {string} params.query - 用户消息
 * @param {string} params.conversationId - 会话 ID（首轮为空）
 * @param {string} params.user - 用户标识
 * @param {Function} params.onChunk - 每收到一段文本时回调(answerChunk, conversationId)
 * @param {Function} params.onEnd - 流结束时回调({ conversationId, messageId })
 * @param {Function} params.onError - 错误回调(errorMessage)
 * @returns {{ abort: Function }} 可调用 abort() 取消请求
 */
export function sendMessageStream({ query, conversationId, user, onChunk, onEnd, onError }) {
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
      user
    },
    header: { 'Content-Type': 'application/json' },
    enableChunked: true,
    success() {},
    fail(err) {
      onError('网络请求失败，请检查网络后重试')
    }
  })

  requestTask.onChunkReceived((res) => {
    const text = new TextDecoder('utf-8').decode(res.data)
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
export async function sendMessageBlocking({ query, conversationId, user }) {
  const response = await uni.request({
    url: `${API_BASE}/api/chat`,
    method: 'POST',
    data: {
      query,
      conversation_id: conversationId || '',
      user
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
