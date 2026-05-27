'use strict'

const { query } = require('./pg')
const {
  fetchReportDetail,
  hasReportDataApi,
  listReports,
} = require('./report-data-client')

const MAX_MAJOR_NAMES = 12

const FALLBACK_INSIGHTS = {
  计算机科学与技术: {
    courses: ['程序设计', '数据结构', '操作系统', '计算机网络'],
    abilities: ['数学和逻辑基础', '持续自学能力', '工程实践和调试能力'],
    salarySummary: '一线城市起薪常见 8K-15K/月，算法、后端、云计算等方向分化明显。',
  },
  数学: {
    courses: ['数学分析', '高等代数', '概率论', '常微分方程'],
    abilities: ['抽象推理', '严谨证明', '耐心钻研复杂问题'],
    salarySummary: '本科直接就业分化大，转数据/金融/算法后薪资上限更高。',
  },
  统计学: {
    courses: ['数学分析', '高等代数', '概率论', '数理统计'],
    abilities: ['量化分析思维', '数据建模能力', '概率判断', '编程基础'],
    salarySummary: '一线/新一线起薪约 7K-9K/月，5 年数据/量化方向约 15K-25K/月。',
  },
  物理学: {
    courses: ['力学', '电磁学', '量子力学', '热力学与统计物理'],
    abilities: ['数学建模', '实验分析', '长期科研训练耐受度'],
    salarySummary: '本科直接对口岗位有限，深造后进入科研、半导体、材料方向更有竞争力。',
  },
  经济学: {
    courses: ['微观经济学', '宏观经济学', '计量经济学', '统计学'],
    abilities: ['数据分析', '政策和市场理解', '数学建模'],
    salarySummary: '金融、咨询、数据分析方向差异大，头部城市和名校背景影响明显。',
  },
  建筑学: {
    courses: ['建筑设计基础', '建筑构造', '城市规划原理', '建筑历史'],
    abilities: ['空间想象', '审美表达', '长期方案打磨能力'],
    salarySummary: '起薪通常不算高，后期取决于作品集、平台和注册建筑师路径。',
  },
  心理学: {
    courses: ['普通心理学', '发展心理学', '实验心理学', '心理统计'],
    abilities: ['观察和访谈', '统计分析', '共情和伦理意识'],
    salarySummary: '本科直接就业一般，咨询、教育、用户研究等方向通常需要继续深造或项目经验。',
  },
  工商管理: {
    courses: ['管理学', '市场营销', '财务管理', '组织行为学'],
    abilities: ['沟通协调', '商业分析', '项目推进'],
    salarySummary: '岗位口径很宽，薪资更多取决于行业、实习经历和具体职能。',
  },
}

function parseNames(raw) {
  return String(raw || '')
    .split(',')
    .map((name) => {
      try {
        return decodeURIComponent(name).trim()
      } catch {
        return String(name || '').trim()
      }
    })
    .filter(Boolean)
    .slice(0, MAX_MAJOR_NAMES)
}

function compact(values) {
  return [...new Set((values || [])
    .map((value) => String(value || '').replace(/\s+/g, ' ').trim())
    .filter(Boolean))]
}

function stripMarkdown(text) {
  return String(text || '')
    .replace(/[*_`#>]/g, '')
    .replace(/\[[^\]]+\]\([^)]+\)/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function splitItems(text) {
  return compact(String(text || '')
    .replace(/[。；;]/g, '、')
    .split(/[、，,]/)
    .map(stripMarkdown))
    .filter((item) => item.length >= 2 && item.length <= 28)
    .slice(0, 4)
}

function firstMatch(text, patterns) {
  for (const pattern of patterns) {
    const match = String(text || '').match(pattern)
    if (match?.[1]) return stripMarkdown(match[1])
  }
  return ''
}

function normalizeReportRow(row) {
  if (!row) return null
  const data = row.data || {}
  return {
    code: row.code || data.layer1_overview?.code || '',
    name: row.name || data.layer1_overview?.name || '',
    category: row.category || data.layer1_overview?.category || '',
    summary: row.summary || row.overview?.summary || data.layer1_overview?.summary || data.layer2_core?.summary || '',
    data,
  }
}

async function findMajorReport(name) {
  if (hasReportDataApi()) {
    const listed = await listReports('major', { search: name, page_size: 1, full: 1 })
    const row = listed?.data?.[0]
    if (!row) return null
    if (row.data || !row.code) return normalizeReportRow(row)
    return normalizeReportRow(await fetchReportDetail('major', row.code, { full: true }))
  }

  const result = await query(
    `SELECT code, name, category, data
     FROM majors
     WHERE name = $1 OR name ILIKE $2
     ORDER BY
       CASE WHEN name = $1 THEN 0 ELSE 1 END,
       (data->'layer1_overview'->>'weighted_score')::float DESC NULLS LAST
     LIMIT 1`,
    [name, `%${name}%`]
  )
  return normalizeReportRow(result.rows[0])
}

function collectRawContent(value, chunks = []) {
  if (!value || typeof value !== 'object') return chunks
  for (const [key, item] of Object.entries(value)) {
    if (typeof item === 'string' && key.includes('raw_content')) {
      chunks.push(item)
    } else if (item && typeof item === 'object') {
      collectRawContent(item, chunks)
    }
  }
  return chunks
}

function allRawText(data) {
  return collectRawContent(data, []).join('\n')
}

function extractCourses(data, raw, requestedName) {
  const direct = [
    data.layer3_details?.curriculum,
    data.layer3_detail?.curriculum,
    data.layer3_detail?.module4_comparison?.curriculum,
  ].find(Array.isArray)
  if (direct) return compact(direct).slice(0, 4)

  const text = firstMatch(raw, [
    /核心课程[：:]\s*([^\n。]+)/,
    /主要课程[：:]\s*([^\n。]+)/,
    /课程表里排满了([^。\n]+)/,
    /共享大量([^，。\n]+课程)/,
  ])
  const parsed = splitItems(text)
  if (parsed.length > 1 || (parsed[0] && !parsed[0].includes('基础课程'))) return parsed

  return FALLBACK_INSIGHTS[requestedName]?.courses || ['通识基础课', '专业基础课', '专业核心课', '实践训练课']
}

function extractAbilities(data, raw, requestedName) {
  const tags = data.layer3_detail?.module7_personality_tags?.tags
  if (Array.isArray(tags) && tags.length) return compact(tags).slice(0, 4)

  const text = firstMatch(raw, [
    /核心可迁移能力[：:]\s*([^\n]+)/,
    /\|\s*最看重的核心能力\s*\|\s*([^|\n]+)/,
    /普遍要求以下能力认证[：:]\s*([^\n]+)/,
  ])
  const parsed = splitItems(text)
  if (parsed.length) return parsed

  return FALLBACK_INSIGHTS[requestedName]?.abilities || ['持续学习', '信息检索', '表达沟通', '解决复杂问题']
}

function extractSalarySummary(data, raw, requestedName) {
  const employment = data.layer2_core?.employment || {}
  const parts = []
  if (employment.starting_salary) parts.push(`起薪 ${employment.starting_salary}`)
  if (employment.salary_5yr) parts.push(`5 年 ${employment.salary_5yr}`)
  if (employment.salary_avg_3yr) parts.push(`3 年均薪 ${employment.salary_avg_3yr}`)
  if (parts.length) return parts.join('；')

  const text = firstMatch(raw, [
    /\|\s*薪酬曲线\s*\|\s*([^|\n]+)/,
    /典型薪酬范围[：:]\s*([^\n]+)/,
    /一线\/新一线起薪中位数\s*\|\s*([^|\n]+)/,
    /5 年薪酬\s*\|\s*([^|\n]+)/,
  ])
  if (text) return text.slice(0, 80)

  return FALLBACK_INSIGHTS[requestedName]?.salarySummary || '薪资受城市、院校层次、学历和岗位方向影响较大，建议结合目标城市核验。'
}

function buildMajorInsight(report, requestedName) {
  const normalized = normalizeReportRow(report)
  const fallback = FALLBACK_INSIGHTS[requestedName] || {}
  if (!normalized) {
    return {
      requestedName,
      name: requestedName,
      code: '',
      category: '',
      summary: fallback.summary || '数据库暂未匹配到该专业，以下为通用参考。',
      courses: fallback.courses || ['通识基础课', '专业基础课', '专业核心课', '实践训练课'],
      abilities: fallback.abilities || ['持续学习', '信息检索', '表达沟通', '解决复杂问题'],
      salarySummary: fallback.salarySummary || '薪资受城市、院校层次、学历和岗位方向影响较大，建议结合目标城市核验。',
      source: 'fallback',
    }
  }

  const raw = allRawText(normalized.data)
  return {
    requestedName,
    name: normalized.name || requestedName,
    code: normalized.code,
    category: normalized.category,
    summary: normalized.summary || fallback.summary || '',
    courses: extractCourses(normalized.data, raw, requestedName),
    abilities: extractAbilities(normalized.data, raw, requestedName),
    salarySummary: extractSalarySummary(normalized.data, raw, requestedName),
    source: 'database',
  }
}

async function getMajorInsights(names) {
  return Promise.all(names.map(async (name) => {
    try {
      return buildMajorInsight(await findMajorReport(name), name)
    } catch (err) {
      console.error(`Major insight lookup failed for ${name}:`, err.message)
      return buildMajorInsight(null, name)
    }
  }))
}

module.exports = {
  buildMajorInsight,
  getMajorInsights,
  parseNames,
}
