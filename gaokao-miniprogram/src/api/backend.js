import { API_BASE } from '../config.js'

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

export function requestBackend(options) {
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
