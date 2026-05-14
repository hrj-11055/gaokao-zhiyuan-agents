const crypto = require('crypto')

function base64url(input) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
}

function fromBase64url(input) {
  const padded = input + '='.repeat((4 - (input.length % 4)) % 4)
  return Buffer.from(padded.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8')
}

function signSessionToken(payload, secret, now = () => Date.now()) {
  if (!secret) throw new Error('session secret is required')
  const body = base64url(JSON.stringify({ ...payload, iat: now() }))
  const signature = crypto.createHmac('sha256', secret).update(body).digest('base64url')
  return `${body}.${signature}`
}

function verifySessionToken(token, secret) {
  if (!secret) throw new Error('session secret is required')
  if (!token || typeof token !== 'string' || !token.includes('.')) {
    throw new Error('invalid session token')
  }

  const [body, signature] = token.split('.')
  const expected = crypto.createHmac('sha256', secret).update(body).digest('base64url')
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    throw new Error('invalid session signature')
  }

  return JSON.parse(fromBase64url(body))
}

module.exports = {
  signSessionToken,
  verifySessionToken,
}
