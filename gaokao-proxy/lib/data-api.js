'use strict'

const SCORE_API_URL = process.env.SCORE_API_URL || 'http://159.75.110.157/score-api'
const pg = require('./pg')
const { extractFullContent } = require('./deep-report-pdf')
const {
  fetchRecommendationContext,
  flattenRecommendationContext,
  hasRecommendationPosition,
} = require('./recommendation-context-client')
const {
  fetchReportDetail,
  hasReportDataApi,
  listReports,
} = require('./report-data-client')

// 兴趣领域 → 专业门类代码前缀
const INTEREST_TO_CODES = {
  '理工技术': ['07', '08'],
  '医学健康': ['09', '10'],
  '人文社科': ['01', '05', '06'],
  '商科管理': ['02', '12'],
  '艺术传媒': ['05', '13'],
  '法律政治': ['03'],
}

// 目标行业 → 专业门类代码前缀
const INDUSTRY_TO_CODES = {
  '互联网/科技': ['08'],
  '金融': ['02', '12'],
  '医疗': ['10'],
  '教育': ['04'],
  '制造/工程': ['08'],
  '传媒/艺术': ['13'],
  '政府/公务': ['03', '12'],
  '法律': ['03'],
}

/**
 * 获取专业报告内容（从 PostgreSQL）
 */
async function fetchMajorReports(questionnaire) {
  const interests = Array.isArray(questionnaire.q15) ? questionnaire.q15 : []
  const industry = questionnaire.q20 || ''

  const codes = new Set()
  ;(INDUSTRY_TO_CODES[industry] || []).forEach(c => codes.add(c))
  interests.forEach(i => (INTEREST_TO_CODES[i] || []).forEach(c => codes.add(c)))

  if (codes.size === 0) return []

  if (hasReportDataApi()) {
    try {
      const rowsByCode = new Map()
      for (const prefix of codes) {
        const data = await listReports('major', {
          category: prefix,
          page_size: 20,
          full: 1,
        })
        ;(data.data || []).forEach((row) => {
          if (row.code && !rowsByCode.has(row.code)) {
            rowsByCode.set(row.code, row)
          }
        })
      }

      return Array.from(rowsByCode.values())
        .slice(0, 20)
        .map((row) => {
          const content = extractFullContent(row) || row.summary || ''
          return `### 专业：${row.name}（${row.code}）\n${content.slice(0, 3500)}`
        })
        .filter(Boolean)
    } catch (err) {
      console.warn('fetchMajorReports data API failed:', err.message)
    }
  }

  try {
    const codePrefixes = Array.from(codes)
    const placeholders = codePrefixes.map((_, i) => `$${i + 1}`).join(', ')
    const likeConditions = codePrefixes.map((_, i) => `code LIKE $${i + 1}`).join(' OR ')
    const values = codePrefixes.map(c => `${c}%`)

    const result = await pg.query(
      `SELECT code, name, data->'layer1_overview'->>'summary' AS summary,
              data->'layer3_detail'->'module1_image'->>'raw_content' AS module1
       FROM majors WHERE ${likeConditions}
       ORDER BY (data->'layer1_overview'->>'weighted_score')::float DESC NULLS LAST
       LIMIT 20`,
      values
    )

    return result.rows.map(r => {
      const content = r.module1 || r.summary || ''
      return `### 专业：${r.name}（${r.code}）\n${content.slice(0, 3000)}`
    })
  } catch (err) {
    console.warn('fetchMajorReports failed:', err.message)
    return []
  }
}

/**
 * 获取院校推荐和大学报告内容（从 PostgreSQL）
 */
async function fetchUnivReports(profile) {
  const { province, category } = profile || {}
  if (!province || !category || !hasRecommendationPosition(profile)) {
    return { recommendations: [], reports: [], recommendationContext: null }
  }

  let recommendations = []
  let recommendationContext = null
  try {
    recommendationContext = await fetchRecommendationContext(profile, {
      scoreApiUrl: SCORE_API_URL,
      year: 2025,
      limitPerTier: 10,
    })
    recommendations = flattenRecommendationContext(recommendationContext)
  } catch (err) {
    console.warn('Recommendation context API failed:', err.message)
  }

  if (recommendations.length === 0) {
    return { recommendations: [], reports: [], recommendationContext }
  }

  const univNames = recommendations.slice(0, 5).map(r => r.school_name || r.name || r.school).filter(Boolean)

  if (hasReportDataApi()) {
    const reports = []
    for (const name of univNames) {
      try {
        const row = await fetchReportDetail('university', name, { full: true })
        const content = extractFullContent(row) || row.summary || ''
        if (content) {
          reports.push(`### 院校深度研究资料：${row.name || name}\n${content.slice(0, 3500)}`)
        }
      } catch (err) {
        console.warn(`fetchUnivReports data API failed for ${name}:`, err.message)
      }
    }

    return {
      recommendations: recommendations.slice(0, 18),
      reports,
      recommendationContext,
    }
  }

  let reports = []
  try {
    const placeholders = univNames.map((_, i) => `$${i + 1}`).join(', ')
    const result = await pg.query(
      `SELECT name,
              data->'layer1_overview'->>'summary' AS summary,
              data->'layer3_detail'->'module1_academic_capital'->>'raw_content' AS module1
       FROM universities WHERE name IN (${placeholders})`,
      univNames
    )

    reports = result.rows.map(r => {
      const content = r.module1 || r.summary || ''
      return `### 院校深度研究资料：${r.name}\n${content.slice(0, 3000)}`
    })
  } catch (err) {
    console.warn('fetchUnivReports DB failed:', err.message)
  }

  return {
    recommendations: recommendations.slice(0, 18),
    reports: reports.filter(Boolean),
    recommendationContext,
  }
}

/**
 * 获取 Dify 历史对话
 */
async function fetchDifyMessages(conversationId, difyApiUrl, difyApiKey) {
  if (!conversationId || !difyApiUrl || !difyApiKey) return []
  try {
    const res = await fetch(
      `${difyApiUrl}/v1/messages?conversation_id=${conversationId}&limit=50&user=report-gen`,
      {
        headers: { 'Authorization': `Bearer ${difyApiKey}` },
        signal: AbortSignal.timeout(5000),
      }
    )
    if (!res.ok) return []
    const data = await res.json()
    return (data.data || []).map(m => ({
      role: m.role === 'user' ? '用户' : 'AI',
      content: m.query || m.answer || '',
    }))
  } catch {
    return []
  }
}

module.exports = {
  fetchMajorReports,
  fetchUnivReports,
  fetchDifyMessages
}
