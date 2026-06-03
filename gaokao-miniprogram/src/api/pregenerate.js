import { requestBackendData } from './backend.js'

/**
 * Trigger background report pre-generation on the server.
 * Call this when the user completes the required assessments.
 * Returns { taskId, status } — does NOT block on generation.
 */
export async function triggerPregenerate({
  profile,
  assessments,
  conversationId,
  userId,
  sessionToken,
}) {
  return requestBackendData({
    path: '/api/report/pre-generate',
    method: 'POST',
    data: {
      userId,
      profile: profile || {},
      assessments: assessments || {},
      conversationId: conversationId || '',
    },
    header: {
      'Content-Type': 'application/json',
      ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    },
    timeout: 15000,
  })
}

/**
 * Check the status of a pre-generated report.
 * Returns { status, taskId?, url?, error? }
 * status: 'pending' | 'ready' | 'failed' | 'not_found'
 */
export async function checkPregenerateStatus({ sessionToken }) {
  return requestBackendData({
    path: '/api/report/pre-generate/status',
    method: 'GET',
    header: {
      ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    },
    timeout: 10000,
  })
}
