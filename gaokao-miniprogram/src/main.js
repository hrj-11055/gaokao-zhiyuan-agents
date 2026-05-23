import { createSSRApp } from 'vue'
import App from './App.vue'
import pinia from './stores'
import { USE_WECHAT_CLOUD_CONTAINER, WECHAT_CLOUD_ENV } from './config.js'

function initWechatCloud() {
  // #ifdef MP-WEIXIN
  if (
    USE_WECHAT_CLOUD_CONTAINER &&
    typeof wx !== 'undefined' &&
    wx.cloud &&
    WECHAT_CLOUD_ENV
  ) {
    try {
      // callContainer 的目标环境在每次请求的 config.env 中指定。
      // 这里按微信云托管示例只做全局初始化，避免真机初始化失败阻断 App 挂载。
      wx.cloud.init({
        traceUser: true,
      })
    } catch (err) {
      console.warn('wx.cloud.init failed:', err)
    }
  }
  // #endif
}

export function createApp() {
  initWechatCloud()
  const app = createSSRApp(App)
  app.use(pinia)
  return { app, pinia }
}
