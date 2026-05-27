import { requestBackendData } from './backend.js'

export async function fetchMajorInsights(names = []) {
  const uniqueNames = [...new Set(names.map((name) => String(name || '').trim()).filter(Boolean))]
  if (uniqueNames.length === 0) return []

  const params = encodeURIComponent(uniqueNames.join(','))
  const data = await requestBackendData({
    path: `/api/reports/major-insights?names=${params}`,
    method: 'GET',
  })
  return Array.isArray(data?.data) ? data.data : []
}
