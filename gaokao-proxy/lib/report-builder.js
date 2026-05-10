'use strict'
const fs = require('fs').promises
const path = require('path')
const { GoogleGenerativeAI } = require('@google/generative-ai')

const MAJOR_REPORTS_DIR = process.env.MAJOR_REPORTS_DIR ||
  path.join(__dirname, '../../data/专业评估报告')
const UNIV_REPORTS_DIR = process.env.UNIV_REPORTS_DIR ||
  path.join(__dirname, '../../data/大学评估报告')
const REPORTS_DIR = process.env.REPORTS_DIR ||
  path.join(__dirname, '../reports')
const SCORE_API_URL = process.env.SCORE_API_URL || 'http://159.75.110.157:5000'
const GEMINI_MODEL = process.env.GEMINI_MODEL || 'gemini-2.0-flash'

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

async function matchMajorReports(questionnaire) {
  const interests = Array.isArray(questionnaire.q15) ? questionnaire.q15 : []
  const industry = questionnaire.q20 || ''

  const codes = new Set()
  ;(INDUSTRY_TO_CODES[industry] || []).forEach(c => codes.add(c))
  interests.forEach(i => (INTEREST_TO_CODES[i] || []).forEach(c => codes.add(c)))

  if (codes.size === 0) return []

  let files
  try {
    files = await fs.readdir(MAJOR_REPORTS_DIR)
  } catch {
    return []
  }

  const matched = files
    .filter(f => f.endsWith('.md') && Array.from(codes).some(code => f.startsWith(code)))
    .slice(0, 3)

  return Promise.all(
    matched.map(async f => {
      const content = await fs.readFile(path.join(MAJOR_REPORTS_DIR, f), 'utf8')
      return `### 专业：${f.replace('.md', '')}\n${content.slice(0, 3000)}`
    })
  )
}

async function matchUnivReports(profile) {
  const { province, score, category } = profile || {}
  if (!province || !score) return []

  let univNames = []
  try {
    const url = `${SCORE_API_URL}/api/recommend?province=${encodeURIComponent(province)}&score=${score}&category=${encodeURIComponent(category || '')}&year=2024&limit=10`
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      univNames = (data.recommendations || [])
        .map(r => r.school_name || r.name)
        .filter(Boolean)
    }
  } catch {
    // Flask API 不可用时跳过
  }

  if (univNames.length === 0) return []

  let files
  try {
    files = await fs.readdir(UNIV_REPORTS_DIR)
  } catch {
    return []
  }

  const fileSet = new Set(files.map(f => f.replace('.md', '')))
  const matched = univNames.filter(name => fileSet.has(name)).slice(0, 5)

  return Promise.all(
    matched.map(async name => {
      const content = await fs.readFile(path.join(UNIV_REPORTS_DIR, `${name}.md`), 'utf8')
      return `### 院校：${name}\n${content.slice(0, 3000)}`
    })
  )
}

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

function buildPrompt(profile, questionnaire, messages, majorReports, univReports) {
  const q = questionnaire || {}
  const arr = v => (Array.isArray(v) ? v.join('、') : v || '未作答')

  const msgText = messages.length > 0
    ? messages.slice(-20).map(m => `${m.role}：${m.content}`).join('\n')
    : '（暂无对话记录）'

  const majorText = majorReports.length > 0
    ? majorReports.join('\n\n')
    : '（暂无专业研究资料，请根据考生兴趣自行分析）'

  const univText = univReports.length > 0
    ? univReports.join('\n\n')
    : '（暂无院校研究资料，请根据考生分数自行推荐）'

  return `你是一位专业的高考志愿填报顾问，风格参考张雪峰：直接、有态度、给具体可操作的建议。根据以下考生完整信息，生成一份个人化的综合志愿分析 HTML 报告。

【考生基本信息】
省份：${profile.province || '未填写'} | 科目：${profile.category || '未填写'} | 分数：${profile.score || '未填写'} | 位次：${profile.rank || '未填写'}

【问卷答案（五环框架）】
第一环-学习风格：Q1=${q.q1 || '未作答'} | Q2=${q.q2 || '未作答'} | Q3=${q.q3 || '未作答'} | Q4=${q.q4 || '未作答'} | Q5=${q.q5 || '未作答'}
第二环-学业现状：优势科目=${arr(q.q6)} | 薄弱科目=${arr(q.q7)} | 压力来源=${q.q8 || '未作答'} | 班级位置=${q.q9 || '未作答'}
第三环-家庭背景：父母职业=${q.q10 || '未作答'} | 家庭期望=${arr(q.q11)} | 城市偏好=${q.q12 || '未作答'} | 经济状况=${q.q13 || '未作答'}
第四环-能力特质：突出能力=${arr(q.q14)} | 兴趣领域=${arr(q.q15)} | 排斥方向=${arr(q.q16)}
第五环-职业期望：成就感=${q.q17 || '未作答'} | 价值观=${q.q18 || '未作答'} | 工作方式=${q.q19 || '未作答'} | 目标行业=${q.q20 || '未作答'} | 毕业方向=${q.q21 || '未作答'} | 城市偏好=${q.q22 || '未作答'}

【AI 对话记录（最近 20 条）】
${msgText}

【专业深度研究资料（Tab 4 直接引用，不得编造数据）】
${majorText}

【院校深度研究资料（Tab 5 直接引用，不得编造数据）】
${univText}

输出要求：
- 直接输出完整 HTML 文本，不要任何代码块标记
- 包含 6 个 Tab：自我评估总结、个人特质分析、专业匹配分析、专业深度研究、大学深度研究、综合决策报告
- Tab 4 专业深度研究和 Tab 5 大学深度研究必须基于上方提供的预生成资料，内容具体
- 使用 ECharts（CDN: https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js）绘制六维能力雷达图
- 顶部深色渐变背景（#0f1419 → #1a2332），内容区白色圆角卡片
- Tab 切换用纯 JavaScript 实现`
}

async function generateReport({ profile, questionnaire, conversationId, difyApiUrl, difyApiKey }) {
  const [majorReports, univReports, messages] = await Promise.all([
    matchMajorReports(questionnaire),
    matchUnivReports(profile),
    fetchDifyMessages(conversationId, difyApiUrl, difyApiKey),
  ])

  const prompt = buildPrompt(profile, questionnaire, messages, majorReports, univReports)

  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)
  const model = genAI.getGenerativeModel({
    model: GEMINI_MODEL,
    generationConfig: { maxOutputTokens: 8192, temperature: 0.7 },
  })

  const result = await model.generateContent(prompt)
  return result.response.text()
}

async function saveReport(userId, html) {
  await fs.mkdir(REPORTS_DIR, { recursive: true })
  const filename = `${userId}-${Date.now()}.html`
  await fs.writeFile(path.join(REPORTS_DIR, filename), html, 'utf8')
  return filename
}

module.exports = { generateReport, saveReport, REPORTS_DIR }
