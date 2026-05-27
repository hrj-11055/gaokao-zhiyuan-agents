import { requestBackendData } from './backend.js'

function normalizeReportError(err) {
  const message = err.data?.error || err.data?.message || err.message || '生成失败'
  const next = new Error(message)
  next.statusCode = err.statusCode || 0
  next.code = err.code || err.data?.code || ''
  next.data = err.data || null
  return next
}

/**
 * Call the report generation endpoint on gaokao-proxy.
 * Returns { url, generatedAt } on success.
 */
export async function generateReport({
  profile,
  questionnaire,
  assessments,
  conversationId,
  userId,
  sessionToken,
}) {
  try {
    const data = await requestBackendData({
      path: '/api/report/generate',
      method: 'POST',
      data: {
        userId,
        profile,
        questionnaire: questionnaire || {},
        assessments: assessments || {},
        conversationId: conversationId || '',
      },
      header: {
        'Content-Type': 'application/json',
        ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
      },
      timeout: 180000,
    })
    return data
  } catch (err) {
    throw normalizeReportError(err)
  }
}
