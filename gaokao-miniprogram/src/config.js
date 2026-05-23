// gaokao-miniprogram/src/config.js

/**
 * 统一后端服务基准 API 地址
 * 非微信小程序环境或关闭云托管调用时，使用公网代理 IP 兜底。
 */
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://47.113.125.147'

/**
 * 微信云开发/云托管配置
 * 当前真机测试默认走 47 gaokao-proxy。只有显式配置为 true 时才走云托管。
 */
export const WECHAT_CLOUD_ENV = import.meta.env.VITE_WECHAT_CLOUD_ENV || 'cloud1-d9gnnxnx79feadfae'
export const WECHAT_CLOUD_SERVICE = import.meta.env.VITE_WECHAT_CLOUD_SERVICE || 'flask-xsun'
export const USE_WECHAT_CLOUD_CONTAINER = import.meta.env.VITE_USE_WECHAT_CLOUD_CONTAINER === 'true'

/**
 * 上线能力开关
 * 支付和小程序 PDF 下载依赖微信支付、HTTPS 合法域名和备案配置，默认关闭。
 */
export const PAYMENT_ENABLED = import.meta.env.VITE_PAYMENT_ENABLED === 'true'
export const PDF_DOWNLOAD_ENABLED = import.meta.env.VITE_PDF_DOWNLOAD_ENABLED === 'true'
