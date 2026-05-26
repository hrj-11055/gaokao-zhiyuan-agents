// gaokao-miniprogram/src/api/report.js
import { API_BASE } from '../config.js'

/**
 * Call the report generation endpoint on gaokao-proxy.
 * Returns { url, generatedAt } on success.
 */
export function generateReport({ profile, questionnaire, assessments, conversationId, userId }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}/api/report/generate`,
      method: 'POST',
      data: {
        userId,
        profile,
        questionnaire: questionnaire || {},
        assessments: assessments || {},
        conversationId: conversationId || '',
      },
      timeout: 180000,
      success: (res) => {
        if (res.statusCode === 200 && res.data?.url) {
          resolve(res.data)
        } else if (res.statusCode === 402 || res.data?.code === 'MEMBERSHIP_REQUIRED') {
          reject(new Error(res.data?.error || '请先解锁会员后生成报告'))
        } else {
          reject(new Error(res.data?.error || res.data?.message || '生成失败'))
        }
      },
      fail: () => reject(new Error('网络异常')),
    })
  })
}
