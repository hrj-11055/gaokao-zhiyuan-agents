// gaokao-miniprogram/src/api/dify.js
import { API_BASE } from '../config.js'
import { requestBackend } from './backend.js'
import { getStoredSession } from './membership.js'

const CHAT_RESPONSE_TIMEOUT_MS = 180000

export function isTruncatedSseEvent(data = {}) {
  const finishReason =
    data.finish_reason ||
    data.metadata?.finish_reason ||
    data.metadata?.usage?.finish_reason ||
    data.data?.process_data?.finish_reason ||
    data.data?.outputs?.usage?.finish_reason ||
    data.data?.outputs?.finish_reason

  return Boolean(
    data.truncated ||
    data.metadata?.proxy_truncated ||
    data.data?.truncated ||
    String(finishReason || '').toLowerCase() === 'length'
  )
}

/**
 * 持久 UTF-8 解码器
 * 微信 chunk 边界可能切在中文字符中间，必须保留未完成的 UTF-8 字节。
 */
export class Utf8StreamDecoder {
  constructor() {
    this.decoder = typeof TextDecoder !== 'undefined' ? new TextDecoder('utf-8') : null
    this.pendingBytes = []
  }

  normalizeBytes(buffer) {
    if (!buffer) return []
    if (buffer instanceof ArrayBuffer) return Array.from(new Uint8Array(buffer))
    if (ArrayBuffer.isView(buffer)) {
      return Array.from(new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.byteLength))
    }
    return Array.from(buffer)
  }

  decodeCodePoint(codePoint) {
    if (codePoint <= 0xFFFF) return String.fromCharCode(codePoint)
    const offset = codePoint - 0x10000
    return String.fromCharCode(0xD800 + (offset >> 10), 0xDC00 + (offset & 0x3FF))
  }

  isContinuation(byte) {
    return byte >= 0x80 && byte <= 0xBF
  }

  decodeWithFallback(buffer, flush = false) {
    const bytes = this.pendingBytes.concat(this.normalizeBytes(buffer))
    this.pendingBytes = []

    let output = ''
    let index = 0

    while (index < bytes.length) {
      const first = bytes[index]

      if (first <= 0x7F) {
        output += String.fromCharCode(first)
        index += 1
        continue
      }

      let needed = 0
      if (first >= 0xC2 && first <= 0xDF) {
        needed = 2
      } else if (first >= 0xE0 && first <= 0xEF) {
        needed = 3
      } else if (first >= 0xF0 && first <= 0xF4) {
        needed = 4
      } else {
        output += '\uFFFD'
        index += 1
        continue
      }

      if (index + needed > bytes.length) {
        if (!flush) {
          this.pendingBytes = bytes.slice(index)
          break
        }
        output += '\uFFFD'
        index += 1
        continue
      }

      const second = bytes[index + 1]
      const third = bytes[index + 2]
      const fourth = bytes[index + 3]
      let valid = this.isContinuation(second)

      if (needed === 3) {
        valid = valid && this.isContinuation(third)
        if (first === 0xE0) valid = valid && second >= 0xA0
        if (first === 0xED) valid = valid && second <= 0x9F
      }

      if (needed === 4) {
        valid = valid && this.isContinuation(third) && this.isContinuation(fourth)
        if (first === 0xF0) valid = valid && second >= 0x90
        if (first === 0xF4) valid = valid && second <= 0x8F
      }

      if (!valid) {
        output += '\uFFFD'
        index += 1
        continue
      }

      if (needed === 2) {
        output += String.fromCharCode(((first & 0x1F) << 6) | (second & 0x3F))
      } else if (needed === 3) {
        output += String.fromCharCode(
          ((first & 0x0F) << 12) | ((second & 0x3F) << 6) | (third & 0x3F)
        )
      } else {
        output += this.decodeCodePoint(
          ((first & 0x07) << 18) | ((second & 0x3F) << 12) | ((third & 0x3F) << 6) | (fourth & 0x3F)
        )
      }
      index += needed
    }

    return output
  }

  decode(buffer) {
    if (this.decoder) {
      return this.decoder.decode(buffer, { stream: true })
    }
    return this.decodeWithFallback(buffer, false)
  }

  flush() {
    if (this.decoder) {
      return this.decoder.decode()
    }
    return this.decodeWithFallback([], true)
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
    this.seenMessage = false
    this.seenEnd = false
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

  flush(options = {}) {
    const block = this.buffer.replace(/\r\n/g, '\n').trim()
    this.buffer = ''
    if (block) {
      this.processBlock(block)
    }
    if (options.markIncomplete && this.seenMessage && !this.seenEnd) {
      this.seenEnd = true
      this.onEnd({ truncated: true })
    }
  }

  processBlock(block) {
    const lines = block.split('\n')
    let dataText = ''

    for (const line of lines) {
      if (line.startsWith('data:')) {
        const content = line.slice(5).trimStart()
        if (content === '[DONE]') continue
        dataText += (dataText ? '\n' : '') + content
      }
    }

    if (!dataText) return

    try {
      const data = JSON.parse(dataText)
      if (data.event === 'message' || data.event === 'agent_message') {
        this.seenMessage = true
        this.onMessage(data)
      } else if (data.event === 'message_end' || data.event === 'workflow_finished') {
        this.seenEnd = true
        this.onEnd(data)
      } else if (data.event === 'error') {
        this.onError(data)
      }
    } catch (e) {
      console.error('SSE JSON Parse Error:', e, 'Data:', dataText)
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
 * @param {Function} params.onChunk - 每收到一段文本时回调(answerChunk, conversationId, messageId)
 * @param {Function} params.onEnd - 流结束时回调({ conversationId, messageId })
 * @param {Function} params.onError - 错误回调(errorMessage)
 * @returns {{ abort: Function }} 可调用 abort() 取消请求
 */
export function sendMessageStream({ query, conversationId, user, inputs = {}, onChunk, onEnd, onError }) {
  const chunkDecoder = new Utf8StreamDecoder()
  const parser = new SSEParser(
    (data) => {
      if (data.answer) {
        onChunk(data.answer, data.conversation_id, data.message_id)
      }
    },
    (data) => {
      onEnd({
        conversationId: data.conversation_id,
        messageId: data.message_id,
        truncated: isTruncatedSseEvent(data)
      })
    },
    (data) => {
      onError(data.message || 'AI 回复出错')
    }
  )

  // #ifdef MP-WEIXIN
  const session = getStoredSession()
  const requestTask = uni.request({
    url: `${API_BASE}/api/chat/stream`,
    method: 'POST',
    timeout: CHAT_RESPONSE_TIMEOUT_MS,
    data: {
      query,
      conversation_id: conversationId || '',
      user,
      inputs
    },
    header: {
      'Content-Type': 'application/json',
      ...(session.sessionToken ? { Authorization: `Bearer ${session.sessionToken}` } : {}),
    },
    enableChunked: true,
    success(res) {
      if (res.statusCode && res.statusCode !== 200) {
        onError(res.data?.error || '服务暂时不可用，请稍后再试')
        return
      }
      const tail = chunkDecoder.flush()
      if (tail) parser.feed(tail)
      parser.flush({ markIncomplete: true })
    },
    fail(err) {
      onError(err.errMsg || '网络请求失败，请检查网络后重试')
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
  const session = getStoredSession()
  const response = await requestBackend({
    path: '/api/chat',
    method: 'POST',
    data: {
      query,
      conversation_id: conversationId || '',
      user,
      inputs
    },
    timeout: CHAT_RESPONSE_TIMEOUT_MS,
    header: {
      'Content-Type': 'application/json',
      ...(session.sessionToken ? { Authorization: `Bearer ${session.sessionToken}` } : {}),
    }
  })

  if (response.statusCode !== 200) {
    throw new Error(response.data?.error || '请求失败')
  }

  return {
    answer: response.data.answer,
    conversationId: response.data.conversation_id,
    messageId: response.data.message_id,
    truncated: isTruncatedSseEvent(response.data),
  }
}

/**
 * 发送对话反馈（点赞/点踩）
 */
export async function sendFeedback({ messageId, rating, query, answer }) {
  const response = await requestBackend({
    path: '/api/chat/feedback',
    method: 'POST',
    data: { messageId, rating, query, answer },
    header: { 'Content-Type': 'application/json' }
  })
  return response.statusCode === 200
}

/**
 * 语音合成请求
 * 返回音频的 ArrayBuffer
 */
export async function fetchTTSAudio(text) {
  const response = await requestBackend({
    path: '/api/tts',
    method: 'POST',
    data: { text },
    responseType: 'arraybuffer',
    header: { 'Content-Type': 'application/json' }
  })
  
  if (response.statusCode !== 200) {
    throw new Error('语音合成失败')
  }
  return response.data
}
