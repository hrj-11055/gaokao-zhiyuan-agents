'use strict'

const REPORT_TYPES = {
  major: {
    collection: 'majors',
    idField: 'code',
  },
  university: {
    collection: 'universities',
    idField: 'name',
  },
}

function normalizeType(type) {
  const normalized = String(type || '').trim()
  if (normalized === 'major' || normalized === 'majors') return 'major'
  if (normalized === 'university' || normalized === 'universities' || normalized === 'school') {
    return 'university'
  }
  throw new Error('报告类型无效')
}

function reportDataApiBase() {
  return (process.env.REPORT_DATA_API_URL || '').replace(/\/+$/, '')
}

function hasReportDataApi() {
  return Boolean(reportDataApiBase())
}

function buildReportDataApiUrl(apiPath, params = {}) {
  const base = reportDataApiBase()
  if (!base) {
    throw new Error('REPORT_DATA_API_URL 未配置')
  }

  const url = new URL(`${base}/${apiPath.replace(/^\/+/, '')}`)
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value))
    }
  })
  return url.toString()
}

function buildHeaders() {
  const headers = {
    Accept: 'application/json',
  }
  const token = process.env.REPORT_DATA_API_TOKEN || ''
  if (token) {
    headers['X-Report-Token'] = token
  }
  return headers
}

async function fetchReportJson(apiPath, params = {}) {
  const url = buildReportDataApiUrl(apiPath, params)
  const res = await fetch(url, {
    headers: buildHeaders(),
    signal: AbortSignal.timeout(Number(process.env.REPORT_DATA_API_TIMEOUT_MS || 10000)),
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    const error = new Error(`报告数据 API 请求失败 ${res.status}: ${text.slice(0, 160)}`)
    error.status = res.status
    throw error
  }

  return res.json()
}

function collectionFor(type) {
  return REPORT_TYPES[normalizeType(type)].collection
}

async function listReports(type, params = {}) {
  const collection = collectionFor(type)
  return fetchReportJson(`/api/reports/${collection}`, params)
}

async function fetchReportDetail(type, id, options = {}) {
  const collection = collectionFor(type)
  const params = options.full ? { full: 1 } : {}
  return fetchReportJson(`/api/reports/${collection}/${encodeURIComponent(id)}`, params)
}

async function fetchReportStats() {
  return fetchReportJson('/api/reports/stats')
}

async function fetchReportHealth() {
  return fetchReportJson('/api/reports/health')
}

module.exports = {
  buildReportDataApiUrl,
  fetchReportDetail,
  fetchReportHealth,
  fetchReportStats,
  hasReportDataApi,
  listReports,
  normalizeType,
}
