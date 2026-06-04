const crypto = require('crypto')

const DEFAULT_MODE = 'short_series_goods'
const DEFAULT_PRODUCT_ID = 'vip_report_1990'

function createVirtualPayError(message, code) {
  const err = new Error(message)
  err.code = code
  return err
}

function decodeXmlEntity(value = '') {
  return String(value)
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, '&')
}

function readXmlTag(xml, tag) {
  const pattern = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`)
  const match = String(xml || '').match(pattern)
  if (!match) return ''
  const rawValue = String(match[1] || '').trim()
  const cdata = rawValue.match(/^<!\[CDATA\[([\s\S]*?)\]\]>$/)
  return decodeXmlEntity(cdata ? cdata[1] : rawValue).trim()
}

function parseWechatXmlMessage(xml = '') {
  const goodsXml = readXmlTag(xml, 'GoodsInfo')
  const payXml = readXmlTag(xml, 'WeChatPayInfo')
  return {
    ToUserName: readXmlTag(xml, 'ToUserName'),
    FromUserName: readXmlTag(xml, 'FromUserName'),
    CreateTime: Number(readXmlTag(xml, 'CreateTime') || 0),
    MsgType: readXmlTag(xml, 'MsgType'),
    Event: readXmlTag(xml, 'Event'),
    OpenId: readXmlTag(xml, 'OpenId'),
    OutTradeNo: readXmlTag(xml, 'OutTradeNo'),
    Env: Number(readXmlTag(xml, 'Env') || 0),
    WeChatPayInfo: {
      MchOrderNo: readXmlTag(payXml, 'MchOrderNo'),
      TransactionId: readXmlTag(payXml, 'TransactionId'),
      PaidTime: Number(readXmlTag(payXml, 'PaidTime') || 0),
    },
    GoodsInfo: {
      ProductId: readXmlTag(goodsXml, 'ProductId'),
      Quantity: Number(readXmlTag(goodsXml, 'Quantity') || 1),
      OrigPrice: Number(readXmlTag(goodsXml, 'OrigPrice') || 0),
      ActualPrice: Number(readXmlTag(goodsXml, 'ActualPrice') || 0),
      Attach: readXmlTag(goodsXml, 'Attach'),
    },
  }
}

function getVirtualPayEnv(env = process.env) {
  const value = Number(env.WECHAT_VIRTUAL_PAY_ENV ?? env.WECHAT_XPAY_ENV ?? 0)
  return value === 1 ? 1 : 0
}

function getVirtualPayAppKey(payEnv, env = process.env) {
  if (payEnv === 1) {
    return env.WECHAT_VIRTUAL_PAY_SANDBOX_APP_KEY || env.WECHAT_VIRTUAL_PAY_APP_KEY || ''
  }
  return env.WECHAT_VIRTUAL_PAY_APP_KEY || env.WECHAT_VIRTUAL_PAY_PROD_APP_KEY || ''
}

function assertWechatVirtualPayConfig(payEnv = getVirtualPayEnv(), env = process.env) {
  const required = [
    'WECHAT_VIRTUAL_PAY_OFFER_ID',
    'WECHAT_VIRTUAL_PAY_PRODUCT_ID',
  ]
  const missing = required.filter((key) => !env[key])
  if (!getVirtualPayAppKey(payEnv, env)) {
    missing.push(payEnv === 1 ? 'WECHAT_VIRTUAL_PAY_SANDBOX_APP_KEY' : 'WECHAT_VIRTUAL_PAY_APP_KEY')
  }
  if (missing.length > 0) {
    throw createVirtualPayError(`微信虚拟支付未配置：${missing.join(', ')}`, 'WECHAT_VIRTUAL_PAY_NOT_CONFIGURED')
  }
}

function calcPaySig(uri, signData, appKey) {
  return crypto
    .createHmac('sha256', String(appKey || ''))
    .update(`${uri}&${signData}`)
    .digest('hex')
}

function calcUserSignature(signData, sessionKey) {
  if (!sessionKey) {
    throw createVirtualPayError('微信登录态已过期，请重新登录后支付', 'WECHAT_SESSION_KEY_REQUIRED')
  }
  return crypto
    .createHmac('sha256', String(sessionKey))
    .update(signData)
    .digest('hex')
}

function buildVirtualPaymentSignData({ order, payEnv = getVirtualPayEnv(), env = process.env }) {
  if (!order?.outTradeNo) throw new Error('outTradeNo is required')
  return {
    offerId: String(env.WECHAT_VIRTUAL_PAY_OFFER_ID || ''),
    buyQuantity: 1,
    currencyType: 'CNY',
    outTradeNo: order.outTradeNo,
    attach: JSON.stringify({
      orderId: order.orderId || '',
      userId: order.userId || '',
      source: 'membership',
    }),
    env: payEnv,
    productId: String(env.WECHAT_VIRTUAL_PAY_PRODUCT_ID || DEFAULT_PRODUCT_ID),
    goodsPrice: Number(order.amountCents || env.MEMBERSHIP_PRICE_CENTS || 1990),
  }
}

function createVirtualPayment({ order, sessionKey, env = process.env } = {}) {
  const payEnv = getVirtualPayEnv(env)
  assertWechatVirtualPayConfig(payEnv, env)

  const signData = JSON.stringify(buildVirtualPaymentSignData({ order, payEnv, env }))
  return {
    mode: env.WECHAT_VIRTUAL_PAY_MODE || DEFAULT_MODE,
    signData,
    paySig: calcPaySig('requestVirtualPayment', signData, getVirtualPayAppKey(payEnv, env)),
    signature: calcUserSignature(signData, sessionKey),
  }
}

function parseVirtualPayGoodsNotify(body = {}) {
  const normalizedBody = typeof body === 'string' ? parseWechatXmlMessage(body) : body
  if (!normalizedBody || typeof normalizedBody !== 'object') {
    throw createVirtualPayError('invalid virtual payment notify body', 'WECHAT_VIRTUAL_PAY_NOTIFY_INVALID')
  }
  if (normalizedBody.Event && normalizedBody.Event !== 'xpay_goods_deliver_notify') {
    throw createVirtualPayError(`unsupported virtual payment event: ${normalizedBody.Event}`, 'WECHAT_VIRTUAL_PAY_EVENT_UNSUPPORTED')
  }

  const goods = normalizedBody.GoodsInfo || normalizedBody.goodsInfo || {}
  const payInfo = normalizedBody.WeChatPayInfo || normalizedBody.weChatPayInfo || {}
  const outTradeNo = normalizedBody.OutTradeNo || normalizedBody.outTradeNo || ''
  if (!outTradeNo) {
    throw createVirtualPayError('OutTradeNo is required', 'WECHAT_VIRTUAL_PAY_NOTIFY_INVALID')
  }

  return {
    outTradeNo,
    openid: normalizedBody.OpenId || normalizedBody.openid || '',
    env: Number(normalizedBody.Env ?? normalizedBody.env ?? 0),
    transactionId: payInfo.TransactionId || payInfo.transactionId || payInfo.MchOrderNo || payInfo.mchOrderNo || '',
    productId: goods.ProductId || goods.productId || '',
    quantity: Number(goods.Quantity ?? goods.quantity ?? 1),
    amountCents: Number(goods.ActualPrice ?? goods.actualPrice ?? goods.OrigPrice ?? goods.origPrice ?? 0),
    attach: goods.Attach || goods.attach || '',
    raw: normalizedBody,
  }
}

module.exports = {
  assertWechatVirtualPayConfig,
  buildVirtualPaymentSignData,
  calcPaySig,
  calcUserSignature,
  createVirtualPayment,
  parseWechatXmlMessage,
  parseVirtualPayGoodsNotify,
}
