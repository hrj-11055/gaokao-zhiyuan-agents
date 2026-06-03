'use strict'

const crypto = require('crypto')

const DEFAULT_TTL_MS = 10 * 60 * 1000

function encode(value) {
  return Buffer.from(JSON.stringify(value)).toString('base64url')
}

function decode(value) {
  return JSON.parse(Buffer.from(value, 'base64url').toString('utf8'))
}

function sign(body, secret) {
  return crypto.createHmac('sha256', secret).update(body).digest('base64url')
}

function timingSafeEqual(a, b) {
  const left = Buffer.from(String(a || ''))
  const right = Buffer.from(String(b || ''))
  if (left.length !== right.length) return false
  return crypto.timingSafeEqual(left, right)
}

function createDeepReportViewToken({ userId, type, id }, secret, {
  ttlMs = DEFAULT_TTL_MS,
  now = () => Date.now(),
} = {}) {
  if (!secret) throw new Error('view token secret is required')
  if (!type || !id) throw new Error('type and id are required')

  const payload = {
    type: String(type),
    id: String(id),
    exp: now() + ttlMs,
    iat: now(),
    nonce: crypto.randomBytes(8).toString('hex'),
  }
  if (userId) payload.userId = String(userId)
  const body = encode(payload)
  return `${body}.${sign(body, secret)}`
}

function verifyDeepReportViewToken(token, secret, {
  now = () => Date.now(),
} = {}) {
  if (!secret) throw new Error('view token secret is required')
  if (!token || typeof token !== 'string' || !token.includes('.')) {
    throw new Error('invalid view token')
  }

  const [body, signature] = token.split('.')
  if (!timingSafeEqual(signature, sign(body, secret))) {
    throw new Error('invalid view token signature')
  }

  const payload = decode(body)
  if (!payload.exp || Number(payload.exp) < now()) {
    throw new Error('view token expired')
  }
  if (!payload.type || !payload.id) {
    throw new Error('invalid view token payload')
  }
  return payload
}

module.exports = {
  DEFAULT_TTL_MS,
  createDeepReportViewToken,
  verifyDeepReportViewToken,
}
