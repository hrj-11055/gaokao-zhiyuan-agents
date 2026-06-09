// gaokao-miniprogram/src/config.js

/**
 * 统一后端服务基准 API 地址
 * 当前 MVP 统一使用已备案 HTTPS 域名进入 47 服务器 gaokao-proxy。
 */
export const API_BASE = import.meta.env.VITE_API_BASE || 'https://gaokao.aicoming.cn'

/**
 * 上线能力开关
 * 1.3.0 默认免费开放深度报告；支付能力保留但默认关闭。
 * PDF 下载仍需要 HTTPS 合法域名和构建开关。
 */
export const FREE_DEEP_REPORTS_ENABLED = import.meta.env.VITE_FREE_DEEP_REPORTS_ENABLED !== 'false'
export const PAYMENT_ENABLED = import.meta.env.VITE_PAYMENT_ENABLED === 'true'
export const PDF_DOWNLOAD_ENABLED = import.meta.env.VITE_PDF_DOWNLOAD_ENABLED === 'true'
export const WECHAT_LOGIN_MOCK = import.meta.env.VITE_WECHAT_LOGIN_MOCK === 'true'
export const MEMBERSHIP_PRICE_LABEL = import.meta.env.VITE_MEMBERSHIP_PRICE_LABEL || '¥19.9'
export const CUSTOMER_WECHAT_ID = import.meta.env.VITE_CUSTOMER_WECHAT_ID || 'HRJ-11055'
export const CUSTOMER_WECHAT_QR_IMAGE = import.meta.env.VITE_CUSTOMER_WECHAT_QR_IMAGE || '/static/contact/wechat-qr.png'
