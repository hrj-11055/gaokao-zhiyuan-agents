// gaokao-miniprogram/src/config.js

/**
 * 统一后端服务基准 API 地址
 * 当前 MVP 统一使用已备案 HTTPS 域名进入 47 服务器 gaokao-proxy。
 */
export const API_BASE = import.meta.env.VITE_API_BASE || 'https://gaokao.aicoming.cn'

/**
 * 上线能力开关
 * 支付依赖微信支付配置；PDF 下载依赖 HTTPS 合法域名、会员状态和构建开关。
 */
export const PAYMENT_ENABLED = import.meta.env.VITE_PAYMENT_ENABLED !== 'false'
export const PDF_DOWNLOAD_ENABLED = import.meta.env.VITE_PDF_DOWNLOAD_ENABLED === 'true'
export const WECHAT_LOGIN_MOCK = import.meta.env.VITE_WECHAT_LOGIN_MOCK === 'true'
export const MEMBERSHIP_PRICE_LABEL = import.meta.env.VITE_MEMBERSHIP_PRICE_LABEL || '¥29'
