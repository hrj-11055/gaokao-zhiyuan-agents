import {
  API_BASE,
  USE_WECHAT_CLOUD_CONTAINER,
  WECHAT_CLOUD_ENV,
  WECHAT_CLOUD_SERVICE,
} from '../config.js'

export function isWechatCloudContainerEnabled() {
  // #ifdef MP-WEIXIN
  return Boolean(
    USE_WECHAT_CLOUD_CONTAINER &&
    WECHAT_CLOUD_ENV &&
    WECHAT_CLOUD_SERVICE &&
    typeof wx !== 'undefined' &&
    wx.cloud &&
    wx.cloud.callContainer
  )
  // #endif

  return false
}

function requestViaHttp({ path, method = 'GET', data, header = {}, timeout, responseType }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method,
      data,
      header,
      timeout,
      responseType,
      success: resolve,
      fail(err) {
        reject(new Error(err.errMsg || '网络请求失败'))
      },
    })
  })
}

async function requestViaCloudContainer({ path, method = 'GET', data, header = {}, timeout, responseType }) {
  // #ifdef MP-WEIXIN
  try {
    return await wx.cloud.callContainer({
      config: {
        env: WECHAT_CLOUD_ENV,
      },
      path,
      method,
      data,
      timeout,
      responseType,
      header: {
        ...header,
        'X-WX-SERVICE': WECHAT_CLOUD_SERVICE,
      },
    })
  } catch (err) {
    throw new Error(err.errMsg || err.message || '云托管请求失败')
  }
  // #endif

  return requestViaHttp({ path, method, data, header, timeout, responseType })
}

export function requestBackend(options) {
  if (isWechatCloudContainerEnabled()) {
    return requestViaCloudContainer(options)
  }
  return requestViaHttp(options)
}

export async function requestBackendData(options) {
  const res = await requestBackend(options)
  const statusCode = res.statusCode || 0
  if (statusCode >= 200 && statusCode < 300) {
    return res.data
  }

  const err = new Error(res.data?.error || '请求失败')
  err.statusCode = statusCode
  err.code = res.data?.code || ''
  err.data = res.data
  throw err
}
