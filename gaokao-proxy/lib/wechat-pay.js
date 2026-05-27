const crypto = require('crypto')
const fs = require('fs')

function assertWechatPayConfig(env = process.env) {
  const required = [
    'WECHAT_APPID',
    'WECHAT_MCH_ID',
    'WECHAT_PAY_SERIAL_NO',
    'WECHAT_PAY_PRIVATE_KEY_PATH',
    'WECHAT_PAY_NOTIFY_URL',
  ]
  const missing = required.filter((key) => !env[key])
  if (missing.length > 0) {
    const err = new Error(`微信支付未配置：${missing.join(', ')}`)
    err.code = 'WECHAT_PAY_NOT_CONFIGURED'
    throw err
  }
}

function assertApiV3Key(env = process.env) {
  if (!env.WECHAT_PAY_API_V3_KEY) {
    const err = new Error('WECHAT_PAY_API_V3_KEY is required')
    err.code = 'WECHAT_PAY_NOT_CONFIGURED'
    throw err
  }
}

function readPrivateKey(env = process.env) {
  return fs.readFileSync(env.WECHAT_PAY_PRIVATE_KEY_PATH, 'utf8')
}

function readNotifyPublicKey(env = process.env) {
  if (!env.WECHAT_PAY_PUBLIC_KEY_PATH) return ''
  return fs.readFileSync(env.WECHAT_PAY_PUBLIC_KEY_PATH, 'utf8')
}

function randomNonce() {
  return crypto.randomBytes(16).toString('hex')
}

function signWithPrivateKey(message, privateKey) {
  return crypto.createSign('RSA-SHA256').update(message).sign(privateKey, 'base64')
}

function buildAuthorization({ method, urlPath, body, timestamp, nonce, env = process.env }) {
  const privateKey = readPrivateKey(env)
  const message = `${method}\n${urlPath}\n${timestamp}\n${nonce}\n${body}\n`
  const signature = signWithPrivateKey(message, privateKey)
  const params = [
    `mchid="${env.WECHAT_MCH_ID}"`,
    `nonce_str="${nonce}"`,
    `signature="${signature}"`,
    `timestamp="${timestamp}"`,
    `serial_no="${env.WECHAT_PAY_SERIAL_NO}"`,
  ].join(',')
  return `WECHATPAY2-SHA256-RSA2048 ${params}`
}

function buildFrontendPayParams({ appId = process.env.WECHAT_APPID, prepayId, privateKey = readPrivateKey() }) {
  const timeStamp = String(Math.floor(Date.now() / 1000))
  const nonceStr = randomNonce()
  const packageValue = `prepay_id=${prepayId}`
  const message = `${appId}\n${timeStamp}\n${nonceStr}\n${packageValue}\n`
  return {
    timeStamp,
    nonceStr,
    package: packageValue,
    signType: 'RSA',
    paySign: signWithPrivateKey(message, privateKey),
  }
}

function verifyWechatPayNotifySignature({ headers = {}, rawBody = '', env = process.env }) {
  const publicKey = readNotifyPublicKey(env)
  if (!publicKey) return true

  const timestamp = headers['wechatpay-timestamp']
  const nonce = headers['wechatpay-nonce']
  const signature = headers['wechatpay-signature']
  if (!timestamp || !nonce || !signature || !rawBody) {
    throw new Error('微信支付回调签名参数缺失')
  }

  const message = `${timestamp}\n${nonce}\n${rawBody}\n`
  const ok = crypto
    .createVerify('RSA-SHA256')
    .update(message)
    .verify(publicKey, signature, 'base64')
  if (!ok) throw new Error('微信支付回调签名校验失败')
  return true
}

function decryptWechatPayResource(resource, env = process.env) {
  if (!resource?.ciphertext) return resource
  assertApiV3Key(env)

  const ciphertext = Buffer.from(resource.ciphertext, 'base64')
  const authTag = ciphertext.subarray(ciphertext.length - 16)
  const encrypted = ciphertext.subarray(0, ciphertext.length - 16)
  const decipher = crypto.createDecipheriv(
    'aes-256-gcm',
    Buffer.from(env.WECHAT_PAY_API_V3_KEY, 'utf8'),
    Buffer.from(resource.nonce || '', 'utf8')
  )
  decipher.setAuthTag(authTag)
  if (resource.associated_data) {
    decipher.setAAD(Buffer.from(resource.associated_data, 'utf8'))
  }
  const plaintext = Buffer.concat([decipher.update(encrypted), decipher.final()]).toString('utf8')
  return JSON.parse(plaintext)
}

async function createJsapiPayment({ order, openid, description = '深度填报会员', env = process.env }) {
  assertWechatPayConfig(env)
  if (!openid) throw new Error('openid is required')

  const urlPath = '/v3/pay/transactions/jsapi'
  const body = JSON.stringify({
    appid: env.WECHAT_APPID,
    mchid: env.WECHAT_MCH_ID,
    description,
    out_trade_no: order.outTradeNo,
    notify_url: env.WECHAT_PAY_NOTIFY_URL,
    amount: {
      total: order.amountCents,
      currency: 'CNY',
    },
    payer: {
      openid,
    },
  })
  const timestamp = String(Math.floor(Date.now() / 1000))
  const nonce = randomNonce()
  const response = await fetch(`https://api.mch.weixin.qq.com${urlPath}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(env.WECHAT_PAY_PUBLIC_KEY_ID ? { 'Wechatpay-Serial': env.WECHAT_PAY_PUBLIC_KEY_ID } : {}),
      Authorization: buildAuthorization({ method: 'POST', urlPath, body, timestamp, nonce, env }),
    },
    body,
  })
  const data = await response.json()
  if (!response.ok || !data.prepay_id) {
    throw new Error(data.message || data.code || '微信支付下单失败')
  }
  return {
    prepayId: data.prepay_id,
    payment: buildFrontendPayParams({
      appId: env.WECHAT_APPID,
      prepayId: data.prepay_id,
      privateKey: readPrivateKey(env),
    }),
  }
}

function parseWechatPayNotify(body, { headers = {}, rawBody = '', env = process.env } = {}) {
  if (!body || typeof body !== 'object') {
    throw new Error('invalid wechat pay notify body')
  }
  verifyWechatPayNotifySignature({ headers, rawBody, env })
  return {
    ...body,
    resource: decryptWechatPayResource(body.resource, env),
  }
}

module.exports = {
  assertWechatPayConfig,
  buildAuthorization,
  buildFrontendPayParams,
  createJsapiPayment,
  decryptWechatPayResource,
  parseWechatPayNotify,
  verifyWechatPayNotifySignature,
}
