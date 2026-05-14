'use strict'

const SCORE_API_URL = process.env.SCORE_API_URL || 'http://159.75.110.157:5000'
const CONTENT_API_URL = process.env.CONTENT_API_URL || 'http://localhost:3002' // 模拟的内容服务地址

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
 * 获取专业报告内容
 */
async function fetchMajorReports(questionnaire) {
  const interests = Array.isArray(questionnaire.q15) ? questionnaire.q15 : []
  const industry = questionnaire.q20 || ''

  const codes = new Set()
  ;(INDUSTRY_TO_CODES[industry] || []).forEach(c => codes.add(c))
  interests.forEach(i => (INTEREST_TO_CODES[i] || []).forEach(c => codes.add(c)))

  if (codes.size === 0) return []

  const requestedCodes = Array.from(codes)
  
  try {
    // 假设未来有个内容接口，可以根据门类代码批量拉取专业报告
    const url = `${CONTENT_API_URL}/api/reports/majors?codes=${requestedCodes.join(',')}`
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      return (data.reports || []).map(r => `### 专业：${r.majorName}\n${r.content.slice(0, 3000)}`)
    }
    // 如果接口不可用，我们优雅兜底
    console.warn(`[Mock] Content API not ready: ${url}. Gracefully falling back.`)
    return [] 
  } catch (err) {
    console.warn('Content API failed or missing, gracefully degraded:', err.message)
    return []
  }
}

/**
 * 获取院校推荐和大学报告内容
 */
async function fetchUnivReports(profile) {
  const { province, score, category } = profile || {}
  if (!province || !score) return { recommendations: [], reports: [] }

  let recommendations = []
  try {
    const url = `${SCORE_API_URL}/api/recommend?province=${encodeURIComponent(province)}&score=${score}&category=${encodeURIComponent(category || '')}&year=2024&limit=15`
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      recommendations = data.recommendations || []
    }
  } catch (err) {
    console.warn('Score API failed:', err.message)
  }

  if (recommendations.length === 0) return { recommendations: [], reports: [] }

  const univNames = recommendations.slice(0, 5).map(r => r.school_name || r.name).filter(Boolean)

  let reports = []
  try {
    // 假设未来有个内容接口，可以根据学校名称批量拉取大学报告
    const url = `${CONTENT_API_URL}/api/reports/universities?names=${encodeURIComponent(univNames.join(','))}`
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      reports = (data.reports || []).map(r => `### 院校深度研究资料：${r.schoolName}\n${r.content.slice(0, 3000)}`)
    } else {
      console.warn(`[Mock] Content API not ready: ${url}. Gracefully falling back.`)
    }
  } catch (err) {
    console.warn('Content API failed or missing, gracefully degraded:', err.message)
  }

  return {
    recommendations: recommendations.slice(0, 10),
    reports: reports.filter(Boolean)
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
