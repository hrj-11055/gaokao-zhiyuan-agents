'use strict'
const fs = require('fs').promises
const path = require('path')

const buildPrompt = require('./prompts/report-template')
const { fetchMajorReports, fetchUnivReports, fetchDifyMessages } = require('./data-api')

const REPORTS_DIR = process.env.REPORTS_DIR || path.join(__dirname, '../reports')
const REPORT_DRAFTS_DIR = process.env.REPORT_DRAFTS_DIR || path.join(REPORTS_DIR, 'drafts')
const REPORT_DEEPSEEK_MODEL = process.env.REPORT_DEEPSEEK_MODEL || 'deepseek-v4-flash'
const REPORT_MAX_TOKENS = Number(process.env.REPORT_MAX_TOKENS || 16384)
const REPORT_GENERATION_TIMEOUT_MS = Number(process.env.REPORT_GENERATION_TIMEOUT_MS || 600000)
const REPORT_PRIMARY_TIMEOUT_MS = Number(process.env.REPORT_PRIMARY_TIMEOUT_MS || Math.min(REPORT_GENERATION_TIMEOUT_MS, 180000))
const REPORT_RETRY_TIMEOUT_MS = Number(process.env.REPORT_RETRY_TIMEOUT_MS || Math.max(1000, REPORT_GENERATION_TIMEOUT_MS - REPORT_PRIMARY_TIMEOUT_MS))
const MIN_MODULE_CONTENT_CHARS = Number(process.env.REPORT_MIN_MODULE_CONTENT_CHARS || 1000)
const REPORT_AUTO_EXPAND_SHORT_MODULES = process.env.REPORT_AUTO_EXPAND_SHORT_MODULES === 'true'
const REPORT_ENFORCE_MODULE_LENGTH = process.env.REPORT_ENFORCE_MODULE_LENGTH === 'true'

async function generateReport({
  profile,
  assessments,
  conversationId,
  difyApiUrl,
  difyApiKey,
  skipExpansion = false,
}) {
  if (!process.env.DEEPSEEK_API_KEY) {
    throw new Error('DEEPSEEK_API_KEY 环境变量未配置')
  }

  const [majorReports, univData, messages] = await Promise.all([
    fetchMajorReports({}),
    fetchUnivReports(profile),
    fetchDifyMessages(conversationId, difyApiUrl, difyApiKey),
  ])

  const prompt = buildPrompt(profile, messages, majorReports, univData, assessments)

  try {
    const content = await requestDeepSeekJson(prompt)
    let reportData = extractJsonFromContent(content)
    let qualityIssues = getReportQualityIssues(reportData)

    if (qualityIssues.length > 0) {
      console.warn('Report content below length target:', formatReportQualityIssues(qualityIssues))
    }

    if (qualityIssues.length > 0 && REPORT_AUTO_EXPAND_SHORT_MODULES && !skipExpansion) {
      console.warn('Requesting report module expansion')
      const expandedContent = await requestDeepSeekJson(buildReportExpansionPrompt(reportData, qualityIssues))
      reportData = extractJsonFromContent(expandedContent)
      qualityIssues = getReportQualityIssues(reportData)
    }

    if (qualityIssues.length > 0 && REPORT_ENFORCE_MODULE_LENGTH) {
      const err = new Error(`报告内容未达到质量标准：${formatReportQualityIssues(qualityIssues)}`)
      err.code = 'REPORT_CONTENT_TOO_SHORT'
      throw err
    }

    return buildFinalHtml(reportData, profile, assessments)
  } catch (err) {
    console.error('DeepSeek generation failed:', err.message)
    if (err.code === 'REPORT_CONTENT_TOO_SHORT') {
      throw new Error('报告内容未达到质量标准，已保留草稿，请稍后重试')
    }
    throw new Error('AI 报告生成失败，请稍后重试')
  }
}

async function requestDeepSeekJson(prompt) {
  try {
    return await requestDeepSeekJsonFromModel(prompt, {
      model: REPORT_DEEPSEEK_MODEL,
      timeoutMs: REPORT_PRIMARY_TIMEOUT_MS,
      attempt: 'primary',
    })
  } catch (err) {
    if (!shouldRetryDeepSeekModel(err)) {
      throw err
    }
    console.warn('DeepSeek report generation retrying:', JSON.stringify({
      model: REPORT_DEEPSEEK_MODEL,
      reason: err.message,
      elapsedMs: err.elapsedMs,
    }))
    return requestDeepSeekJsonFromModel(prompt, {
      model: REPORT_DEEPSEEK_MODEL,
      timeoutMs: REPORT_RETRY_TIMEOUT_MS,
      attempt: 'retry',
    })
  }
}

async function requestDeepSeekJsonFromModel(prompt, { model, timeoutMs, attempt }) {
  const startedAt = Date.now()
  console.log('DeepSeek report generation started:', JSON.stringify({
    attempt,
    model,
    promptChars: prompt.length,
    maxTokens: REPORT_MAX_TOKENS,
    timeoutMs,
  }))

  let res
  try {
    res = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: REPORT_MAX_TOKENS,
        temperature: 0.7,
        response_format: { type: 'json_object' }
      }),
      signal: AbortSignal.timeout(timeoutMs),
    })
  } catch (err) {
    err.elapsedMs = Date.now() - startedAt
    console.error('DeepSeek report generation attempt failed:', JSON.stringify({
      attempt,
      model,
      elapsedMs: err.elapsedMs,
      error: err.message,
    }))
    throw err
  }

  if (!res.ok) {
    const body = await res.text()
    const err = new Error(`DeepSeek API error ${res.status}: ${body.slice(0, 200)}`)
    err.statusCode = res.status
    err.elapsedMs = Date.now() - startedAt
    console.error('DeepSeek report generation attempt failed:', JSON.stringify({
      attempt,
      model,
      statusCode: res.status,
      elapsedMs: err.elapsedMs,
      error: err.message,
    }))
    throw err
  }

  const data = await res.json()
  const content = data?.choices?.[0]?.message?.content
  if (!content) {
    const reason = data?.choices?.[0]?.finish_reason || 'unknown'
    const err = new Error(`DeepSeek 返回空内容 (finish_reason: ${reason})`)
    err.elapsedMs = Date.now() - startedAt
    throw err
  }

  console.log('DeepSeek report generation completed:', JSON.stringify({
    attempt,
    model,
    elapsedMs: Date.now() - startedAt,
    outputChars: content.length,
    finishReason: data?.choices?.[0]?.finish_reason || 'unknown',
  }))
  return content
}

function shouldRetryDeepSeekModel(err) {
  if (!err) return false
  if (err.name === 'TimeoutError' || err.name === 'AbortError') return true
  if (err.statusCode === 429 || err.statusCode >= 500) return true
  return /timeout|timed out|aborted|fetch failed|network/i.test(err.message || '')
}

async function saveReport(userId, html) {
  await fs.mkdir(REPORTS_DIR, { recursive: true })
  const filename = `${safeReportUserId(userId)}-${Date.now()}.html`
  await fs.writeFile(path.join(REPORTS_DIR, filename), normalizeReportHtml(html), 'utf8')
  return filename
}

async function saveReportDraft(userId, draft = {}) {
  await fs.mkdir(REPORT_DRAFTS_DIR, { recursive: true })
  const draftId = `${safeReportUserId(userId)}-${Date.now()}`
  const payload = {
    draftId,
    userId: safeReportUserId(userId),
    savedAt: new Date().toISOString(),
    ...draft,
  }
  await fs.writeFile(path.join(REPORT_DRAFTS_DIR, `${draftId}.json`), JSON.stringify(payload, null, 2), 'utf8')
  return draftId
}

function safeReportUserId(userId) {
  return String(userId || 'anonymous')
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .slice(0, 80) || 'anonymous'
}

function normalizeReportHtml(rawHtml) {
  return humanizeReportCopy(String(rawHtml || ''))
}

function humanizeReportCopy(html) {
  return String(html || '')
    .replace(/AI\s*总评/g, '顾问结论')
    .replace(/AI\s*对话记录/g, '咨询对话记录')
    .replace(/大模型认为/g, '建议判断')
    .replace(/作为\s*AI[，,]?\s*/g, '')
    .replace(/作为一个?\s*AI[，,]?\s*/g, '')
}

function getHollandRadarMaxScore(version = '', scores = {}) {
  if (version === 'basic') return 8
  if (version === 'full') return 40
  const values = Object.values(scores).map((score) => Number(score) || 0)
  return values.length > 0 && Math.max(...values) <= 8 ? 8 : 40
}

function buildHollandRadarSVG(scores = {}, version = '') {
  const maxScore = getHollandRadarMaxScore(version, scores)
  const cx = 100
  const cy = 100
  const radius = 65
  const order = ['R', 'I', 'A', 'S', 'E', 'C']
  const labels = ['实用型R', '研究型I', '艺术型A', '社会型S', '企业型E', '常规型C']

  let dataPtsStr = ''
  let circlesSvg = ''

  order.forEach((key, i) => {
    const score = Math.min(Number(scores[key]) || 0, maxScore)
    const r = (score / maxScore) * radius
    const angle = (Math.PI / 180) * (i * 60 - 90)
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    dataPtsStr += `${x},${y} `
    circlesSvg += `<circle cx="${x}" cy="${y}" r="3.5" fill="#2563EB" stroke="#FFFFFF" stroke-width="1.5"/>`
  })

  let gridSvg = ''
  for(let step = 1; step <= 4; step++) {
    const r = (step / 4) * radius
    let pts = ''
    order.forEach((_, i) => {
      const angle = (Math.PI / 180) * (i * 60 - 90)
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      pts += `${x},${y} `
    })
    gridSvg += `<polygon points="${pts.trim()}" fill="none" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="3,3"/>`
  }

  let axesSvg = ''
  order.forEach((_, i) => {
    const angle = (Math.PI / 180) * (i * 60 - 90)
    const x = cx + radius * Math.cos(angle)
    const y = cy + radius * Math.sin(angle)
    axesSvg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#E2E8F0" stroke-width="1"/>`
  })

  let labelsSvg = ''
  order.forEach((key, i) => {
    const label = labels[i]
    const angle = (Math.PI / 180) * (i * 60 - 90)
    const x = cx + (radius + 18) * Math.cos(angle)
    const y = cy + (radius + 18) * Math.sin(angle)
    let anchor = "middle"
    if (x > cx + 5) anchor = "start"
    else if (x < cx - 5) anchor = "end"

    labelsSvg += `<text x="${x}" y="${y + 4}" font-size="11" font-weight="bold" fill="#64748B" text-anchor="${anchor}">${label}</text>`
  })

  return `<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" style="width: 100%; max-width: 300px; display: block; margin: 0 auto;">
    ${gridSvg}
    ${axesSvg}
    <polygon points="${dataPtsStr.trim()}" fill="rgba(37, 99, 235, 0.15)" stroke="#2563EB" stroke-width="2"/>
    ${circlesSvg}
    ${labelsSvg}
  </svg>`
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function splitReadableParagraphs(value) {
  const text = String(value || '')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .trim()

  if (!text) return []

  const labeledText = text.replace(/([。！？!?；;])(?=[^。！？!?；;：:\n]{2,24}[：:])/g, '$1\n\n')
  const rawParts = labeledText
    .split(/\n{2,}/)
    .flatMap((part) => part.split(/\n/))
    .map((part) => part.trim())
    .filter(Boolean)

  const paragraphs = []
  for (const part of rawParts) {
    const sentences = part.match(/[^。！？!?；;]+[。！？!?；;]?/g) || [part]
    let current = ''
    for (const sentence of sentences) {
      const next = `${current}${sentence}`
      if (current && next.length > 130) {
        paragraphs.push(current.trim())
        current = sentence
      } else {
        current = next
      }
    }
    if (current.trim()) paragraphs.push(current.trim())
  }

  return paragraphs.length ? paragraphs : [text]
}

function renderInlineText(value) {
  return escapeHtml(value)
    .replace(/\*\*([^*]{1,80})\*\*/g, '<strong>$1</strong>')
    .replace(/^([^：:。！？!?；;，,\s<][^：:。！？!?；;]{1,30}[：:])/, '<strong>$1</strong>')
}

function renderReadableText(value, paragraphClass = '') {
  const classAttr = paragraphClass ? ` class="${escapeHtml(paragraphClass)}"` : ''
  return splitReadableParagraphs(value)
    .map((paragraph) => `<p${classAttr}>${renderInlineText(paragraph)}</p>`)
    .join('\n')
}

function renderPrintText(value) {
  return renderReadableText(value, 'print-readable-text')
}

function renderPrintBlock(block = {}) {
  const title = block.title ? `<h3>${escapeHtml(block.title)}</h3>` : ''
  if (block.type === 'list') {
    const items = Array.isArray(block.items) ? block.items : []
    return `<section class="print-block">
      ${title}
      <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
    </section>`
  }
  if (block.type === 'alert') {
    const items = Array.isArray(block.items) ? block.items : []
    return `<section class="print-block print-alert ${escapeHtml(block.level || 'info')}">
      ${title || `<h3>${escapeHtml(block.title || '提示')}</h3>`}
      ${renderPrintText(block.content)}
      ${items.length ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : ''}
    </section>`
  }
  if (block.type === 'quote') {
    return `<blockquote class="print-quote">
      ${block.author ? `<strong>${escapeHtml(block.author)}</strong>` : ''}
      ${renderPrintText(block.content)}
    </blockquote>`
  }
  if (block.type === 'table') {
    const headers = Array.isArray(block.headers) ? block.headers : []
    const rows = Array.isArray(block.rows) ? block.rows : []
    return `<section class="print-block">
      ${title}
      <table>
        ${headers.length ? `<thead><tr>${headers.map((cell) => `<th>${escapeHtml(cell)}</th>`).join('')}</tr></thead>` : ''}
        <tbody>${rows.map((row) => `<tr>${(Array.isArray(row) ? row : []).map((cell) => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody>
      </table>
    </section>`
  }
  return `<section class="print-block">
    ${title}
    ${renderPrintText(block.content || block.text || '')}
  </section>`
}

function buildStaticPrintReport(data = {}, profile = {}, radarSvg = '') {
  const modules = Array.isArray(data.modules) ? data.modules : []
  const conclusions = Array.isArray(data.conclusions) ? data.conclusions : []
  return `
    <header class="print-cover">
      <div class="print-kicker">专属升学规划方案</div>
      <h1>升学规划深度解析报告</h1>
      <div class="print-meta">
        <span>${escapeHtml(profile.province || '未填写')}</span>
        <span>${escapeHtml(profile.category || '未填写')}</span>
        <span>${escapeHtml(profile.score || '--')} 分</span>
        <span>${escapeHtml(profile.rank || '--')} 位</span>
      </div>
    </header>
    ${conclusions.length ? `<section class="print-conclusions">
      <h2>家长先看结论</h2>
      <ol>${conclusions.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ol>
    </section>` : ''}
    ${modules.map((mod) => `<section class="print-module">
      <h2>${escapeHtml(mod.title || '报告章节')}</h2>
      ${mod.summary ? renderReadableText(mod.summary, 'print-summary print-readable-text') : ''}
      ${mod.id === 'tab2' && radarSvg ? `<div class="print-radar">${radarSvg}</div>` : ''}
      ${(Array.isArray(mod.blocks) ? mod.blocks : []).map(renderPrintBlock).join('\n')}
    </section>`).join('\n')}
  `
}

function extractJsonFromContent(content) {
  try {
    return JSON.parse(content)
  } catch (e) {
    const match = content.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (match) {
      try {
        return JSON.parse(match[1])
      } catch (err) {}
    }
    throw new Error('无法解析大模型返回的 JSON')
  }
}

function countReportContentChars(value) {
  const text = String(value || '')
  const cjkChars = text.match(/[\u3400-\u9FFF\uF900-\uFAFF]/g) || []
  const latinWords = text
    .replace(/[\u3400-\u9FFF\uF900-\uFAFF]/g, ' ')
    .match(/[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*/g) || []
  return cjkChars.length + latinWords.length
}

function collectModuleContentText(mod = {}) {
  const parts = []
  if (mod.summary) parts.push(mod.summary)

  for (const block of Array.isArray(mod.blocks) ? mod.blocks : []) {
    if (block.type === 'text') {
      parts.push(block.content || block.text || '')
    } else if (block.type === 'list') {
      parts.push(...(Array.isArray(block.items) ? block.items : []))
    } else if (block.type === 'alert') {
      parts.push(block.content || '')
      parts.push(...(Array.isArray(block.items) ? block.items : []))
    } else if (block.type === 'quote') {
      parts.push(block.content || '')
    }
  }

  return parts.join('\n')
}

function getReportQualityIssues(data = {}, minModuleChars = MIN_MODULE_CONTENT_CHARS) {
  const modules = Array.isArray(data.modules) ? data.modules : []
  const requiredIds = ['tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'tab6']
  const issues = []

  for (const id of requiredIds) {
    const mod = modules.find((item) => item && item.id === id)
    if (!mod) {
      issues.push({ id, title: id, chars: 0, min: minModuleChars, reason: 'missing' })
      continue
    }
    const chars = countReportContentChars(collectModuleContentText(mod))
    if (chars < minModuleChars) {
      issues.push({
        id,
        title: mod.title || id,
        chars,
        min: minModuleChars,
        reason: 'too_short',
      })
    }
  }

  return issues
}

function formatReportQualityIssues(issues = []) {
  return issues
    .map((issue) => `${issue.title || issue.id} ${issue.chars}/${issue.min}`)
    .join('；')
}

function buildReportExpansionPrompt(reportData = {}, qualityIssues = []) {
  return `你正在补全一份固定 HTML 模板的数据 JSON。服务端只会读取 JSON 内容并渲染固定模板，所以不要输出 HTML、CSS、Markdown 或解释说明。

下面这些模块正文长度不足，需要扩写到每个模块不少于 ${MIN_MODULE_CONTENT_CHARS} 个中文正文字符。正文长度只计算 summary、text.content、list.items、alert.content、alert.items、quote.content，不计算标题、表头或短标签：
${qualityIssues.map((issue) => `- ${issue.id} ${issue.title || ''}：当前 ${issue.chars}，最低 ${issue.min}`).join('\n')}

扩写要求：
- 返回完整合法 JSON 对象，必须保留 conclusions 和全部 6 个 modules。
- 保留原来的 id、title、事实依据、分数线和风险判断，不要编造结构化院校推荐列表之外的学校。
- 只扩写过短模块；已达标模块可以保持原意，但输出时仍要放回完整 JSON。
- 每个过短模块至少补足 4 个实质分析 blocks，其中至少 2 个 text block 各不少于 250 字。
- Tab 4 和 Tab 5 也必须作为综合报告正文写足，不要只写 500-800 字摘要；最后仍保留“完整 5000 字以上 PDF 已入库，需要到小程序‘深度报告下载页’付费后选择对应专业/学校下载”的提示。
- 不要生成额外目录页、Table 页、独立表格页或模板代码。

当前 JSON：
${JSON.stringify(reportData)}`
}

function buildFinalHtml(content, profile, assessments) {
  let data
  if (typeof content === 'object' && content !== null) {
    data = content
  } else {
    try {
      data = extractJsonFromContent(String(content))
    } catch (e) {
      console.error('JSON Parse Failed. Fallback to raw string injection.', e.message)
      data = null
    }
  }
  if (!data || !Array.isArray(data.modules)) {
    data = {
      conclusions: ['大模型返回格式异常，分析可能未能正确结构化显示'],
      modules: [{ id: 'tab1', title: '系统提示', blocks: [{ type: 'text', content: '生成的报告格式异常，请稍后重试' }] }],
    }
  }

  const hollandScores = assessments?.holland?.scores || {}
  const radarSvg = buildHollandRadarSVG(hollandScores, assessments?.holland?.version)
  const staticPrintReport = buildStaticPrintReport(data, profile, radarSvg)

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>升学规划深度解析报告</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Vue 3 -->
  <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    :root {
      --gaokao-cjk-font: "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Color Emoji", Arial, sans-serif;
    }
    html, body {
      font-family: var(--gaokao-cjk-font);
      background: #F8FAFC;
      color: #0F172A;
      -webkit-font-smoothing: antialiased;
      -webkit-text-size-adjust: 100%;
    }
    .glass-card {
      background: rgba(255, 255, 255, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.4);
      box-shadow: 0 10px 40px -10px rgba(15, 23, 42, 0.08), 0 4px 10px -5px rgba(15, 23, 42, 0.04);
    }
    .text-gradient {
      background-clip: text;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-image: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
    }
    .bg-gradient-primary {
      background-image: linear-gradient(135deg, #2563EB 0%, #4F46E5 100%);
    }
    [v-cloak] { display: none; }
    .pdf-print-report {
      display: none;
    }
    @media print {
      @page {
        size: A4;
        margin: 14mm 13mm;
      }
      html,
      body {
        background: #fff !important;
      }
      #app,
      body > .fixed {
        display: none !important;
      }
      .pdf-print-report {
        display: block !important;
        color: #111827;
        font-size: 12px;
        line-height: 1.68;
      }
      .pdf-print-report h1 {
        margin: 8px 0 12px;
        font-size: 26px;
        line-height: 1.25;
      }
      .pdf-print-report h2 {
        margin: 0 0 10px;
        color: #1e3a8a;
        font-size: 18px;
        line-height: 1.35;
      }
      .pdf-print-report h3 {
        margin: 0 0 8px;
        color: #111827;
        font-size: 14px;
      }
      .pdf-print-report p {
        margin: 6px 0;
        text-align: justify;
        word-break: break-word;
      }
      .print-cover,
      .print-conclusions,
      .print-block,
      .print-quote {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px 14px;
        background: #fff;
      }
      .print-kicker {
        color: #2563eb;
        font-size: 12px;
        font-weight: 700;
      }
      .print-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        color: #475569;
      }
      .print-meta span {
        border: 1px solid #dbeafe;
        border-radius: 999px;
        padding: 3px 9px;
        background: #eff6ff;
      }
      .print-conclusions {
        margin-top: 14px;
        background: #f8fafc;
      }
      .print-conclusions li {
        margin: 6px 0;
        font-weight: 600;
      }
      .print-module {
        margin-top: 18px;
        padding-top: 18px;
        border-top: 2px solid #dbeafe;
        break-inside: auto;
        page-break-inside: auto;
      }
      .print-summary {
        color: #475569;
        font-weight: 600;
      }
      .print-block,
      .print-quote,
      .print-radar {
        margin: 10px 0;
        break-inside: auto;
      }
      .print-alert {
        border-color: #fed7aa;
        background: #fff7ed;
      }
      .print-quote {
        border-color: #cbd5e1;
        background: #f8fafc;
      }
      .print-radar svg {
        max-width: 220px !important;
      }
      .pdf-print-report ul,
      .pdf-print-report ol {
        margin: 6px 0;
        padding-left: 20px;
      }
      .pdf-print-report li {
        margin: 4px 0;
      }
      .pdf-print-report table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
      }
      .pdf-print-report th,
      .pdf-print-report td {
        padding: 6px 7px;
        border: 1px solid #e5e7eb;
        vertical-align: top;
        word-break: break-word;
      }
      .pdf-print-report th {
        background: #eff6ff;
        color: #1e3a8a;
      }
      .pdf-print-report tr {
        break-inside: avoid;
      }
    }
  </style>
</head>
<body class="relative min-h-screen pb-16 overflow-x-hidden">
  <!-- Dynamic Background Blurs -->
  <div class="fixed top-[-10%] left-[-10%] w-96 h-96 rounded-full bg-blue-400/20 blur-3xl pointer-events-none"></div>
  <div class="fixed top-[20%] right-[-10%] w-80 h-80 rounded-full bg-purple-400/20 blur-3xl pointer-events-none"></div>

  <main class="pdf-print-report">
    ${staticPrintReport}
  </main>

  <div id="app" v-cloak class="relative z-10 w-full max-w-4xl mx-auto px-4 sm:px-6 md:px-8 pt-8">

    <!-- Header -->
    <header class="mb-10 text-center">
      <div class="inline-flex items-center justify-center px-4 py-1.5 mb-4 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-sm font-semibold tracking-wide shadow-sm">
        <i data-lucide="sparkles" class="w-4 h-4 mr-2"></i>专属升学规划方案
      </div>
      <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight mb-4">升学规划深度解析报告</h1>
      <div class="flex flex-wrap items-center justify-center gap-3 text-slate-600 font-medium">
        <span class="flex items-center px-3 py-1.5 bg-white shadow-sm border border-slate-100 rounded-lg"><i data-lucide="map-pin" class="w-4 h-4 mr-1.5 text-slate-400"></i>{{ profile.province || '未填写' }}</span>
        <span class="flex items-center px-3 py-1.5 bg-white shadow-sm border border-slate-100 rounded-lg"><i data-lucide="book-open" class="w-4 h-4 mr-1.5 text-slate-400"></i>{{ profile.category || '未填写' }}</span>
        <span class="flex items-center px-3 py-1.5 bg-blue-50 shadow-sm border border-blue-100 rounded-lg text-blue-700 font-bold"><i data-lucide="award" class="w-4 h-4 mr-1.5 text-blue-500"></i>{{ profile.score || '--' }} 分</span>
        <span class="flex items-center px-3 py-1.5 bg-white shadow-sm border border-slate-100 rounded-lg"><i data-lucide="bar-chart-2" class="w-4 h-4 mr-1.5 text-slate-400"></i>{{ profile.rank || '--' }} 位</span>
      </div>
    </header>

    <!-- Conclusions Card -->
    <div v-if="report.conclusions && report.conclusions.length" class="glass-card rounded-2xl p-6 md:p-8 mb-8 relative overflow-hidden border-t-4 border-t-blue-600">
      <div class="absolute top-0 right-0 p-4 opacity-[0.03] pointer-events-none">
        <i data-lucide="lightbulb" class="w-32 h-32 text-blue-900"></i>
      </div>
      <h2 class="text-xl font-bold text-slate-900 mb-5 flex items-center relative z-10">
        <i data-lucide="target" class="w-6 h-6 mr-2 text-blue-600"></i> 家长先看结论
      </h2>
      <ul class="space-y-4 relative z-10">
        <li v-for="(conc, idx) in report.conclusions" :key="idx" class="flex items-start">
          <span class="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold text-sm mr-4 mt-0.5">{{ idx + 1 }}</span>
          <span class="text-slate-700 leading-relaxed text-[15px] md:text-base font-medium">{{ conc }}</span>
        </li>
      </ul>
    </div>

    <!-- Chapter navigation: mobile-first, no tab switching -->
    <div class="glass-card rounded-2xl p-5 md:p-6 mb-8">
      <div class="text-xs font-bold tracking-[0.2em] text-slate-400 mb-4">章节导航</div>
      <div class="grid gap-3">
        <div
          v-for="(mod, idx) in report.modules"
          :key="mod.id"
          class="flex items-center gap-3 rounded-xl bg-slate-50 border border-slate-100 px-4 py-3 cursor-pointer hover:bg-blue-50 hover:border-blue-100 transition-colors"
          role="button"
          @click="scrollToModule(mod.id)"
        >
          <span class="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">{{ idx + 1 }}</span>
          <span class="text-slate-700 font-semibold text-[15px] leading-snug">{{ mod.title }}</span>
        </div>
      </div>
    </div>

    <!-- Continuous Chapter Content -->
    <div class="space-y-8">
      <section v-for="mod in report.modules" :key="mod.id" :id="'section-' + mod.id" class="animate-fade-in">

        <!-- Module Header -->
        <div class="mb-8 pl-3 border-l-4 border-blue-600">
          <h2 class="text-2xl md:text-3xl font-extrabold text-slate-900 mb-3 tracking-tight">{{ mod.title }}</h2>
          <div v-if="mod.summary" class="readable-copy text-slate-600 text-[15px] md:text-base leading-relaxed">
            <p v-for="(paragraph, pIdx) in readableParagraphs(mod.summary)" :key="pIdx" v-html="formatInlineText(paragraph)"></p>
          </div>
        </div>

        <!-- Radar Chart for Tab 2 -->
        <div v-if="mod.id === 'tab2'" class="glass-card rounded-2xl p-6 md:p-8 mb-8 flex flex-col items-center justify-center relative overflow-hidden">
          <h3 class="text-lg font-bold text-slate-800 mb-4 flex items-center z-10"><i data-lucide="radar" class="w-5 h-5 mr-2 text-indigo-500"></i>霍兰德职业兴趣图谱</h3>
          <div v-html="radarSvg" class="w-full max-w-[320px] z-10 relative"></div>
          <div class="absolute inset-0 bg-gradient-to-b from-transparent to-slate-50/50 pointer-events-none"></div>
        </div>

        <!-- Blocks -->
        <div v-for="(block, bIdx) in mod.blocks" :key="bIdx" class="mb-8">

          <!-- Text Block -->
          <div v-if="block.type === 'text'" class="glass-card rounded-2xl p-6 md:p-8 transition-transform duration-300 hover:scale-[1.01]">
            <h3 v-if="block.title" class="text-lg font-bold text-slate-900 mb-4 flex items-center">
              <span class="w-1.5 h-4 bg-blue-500 rounded-full mr-2"></span>{{ block.title }}
            </h3>
            <div class="readable-copy text-slate-700 leading-relaxed text-[15px] md:text-base">
              <p v-for="(paragraph, pIdx) in readableParagraphs(block.content || block.text)" :key="pIdx" v-html="formatInlineText(paragraph)"></p>
            </div>
          </div>

          <!-- List Block -->
          <div v-else-if="block.type === 'list'" class="glass-card rounded-2xl p-6 md:p-8 transition-transform duration-300 hover:scale-[1.01]">
            <h3 v-if="block.title" class="text-lg font-bold text-slate-900 mb-5 flex items-center">
              <span class="w-1.5 h-4 bg-indigo-500 rounded-full mr-2"></span>{{ block.title }}
            </h3>
            <ul class="space-y-4">
              <li v-for="(item, iIdx) in block.items" :key="iIdx" class="flex items-start bg-slate-50/50 p-3 rounded-xl border border-slate-100">
                <i data-lucide="check-circle-2" class="w-5 h-5 mr-3 flex-shrink-0 text-indigo-500 mt-0.5"></i>
                <span class="text-slate-700 leading-relaxed text-[15px] md:text-base" v-html="formatInlineText(item)"></span>
              </li>
            </ul>
          </div>

          <!-- Alert Block -->
          <div v-else-if="block.type === 'alert'"
               class="rounded-2xl p-6 md:p-8 border shadow-sm transition-transform duration-300 hover:scale-[1.01]"
               :class="{
                 'bg-amber-50 border-amber-200': block.level === 'warning',
                 'bg-red-50 border-red-200': block.level === 'danger',
                 'bg-emerald-50 border-emerald-200': block.level === 'success',
                 'bg-blue-50 border-blue-200': !block.level || block.level === 'info',
               }">
            <div class="flex items-center mb-4">
               <div class="p-2 rounded-full mr-3"
                    :class="{
                      'bg-amber-100 text-amber-600': block.level === 'warning',
                      'bg-red-100 text-red-600': block.level === 'danger',
                      'bg-emerald-100 text-emerald-600': block.level === 'success',
                      'bg-blue-100 text-blue-600': !block.level || block.level === 'info'
                    }">
                 <i v-if="block.level === 'warning'" data-lucide="alert-triangle" class="w-5 h-5"></i>
                 <i v-else-if="block.level === 'danger'" data-lucide="alert-octagon" class="w-5 h-5"></i>
                 <i v-else-if="block.level === 'success'" data-lucide="check-square" class="w-5 h-5"></i>
                 <i v-else data-lucide="info" class="w-5 h-5"></i>
               </div>
               <h3 class="text-lg font-bold"
                   :class="{
                     'text-amber-900': block.level === 'warning',
                     'text-red-900': block.level === 'danger',
                     'text-emerald-900': block.level === 'success',
                     'text-blue-900': !block.level || block.level === 'info'
                   }">{{ block.title || '提示' }}</h3>
            </div>
            <div v-if="block.content" class="readable-copy leading-relaxed mb-5 text-[15px] md:text-base"
               :class="{
                 'text-amber-800': block.level === 'warning',
                 'text-red-800': block.level === 'danger',
                 'text-emerald-800': block.level === 'success',
                 'text-blue-800': !block.level || block.level === 'info'
               }">
              <p v-for="(paragraph, pIdx) in readableParagraphs(block.content)" :key="pIdx" v-html="formatInlineText(paragraph)"></p>
            </div>
            <ul v-if="block.items && block.items.length" class="space-y-3">
              <li v-for="(item, iIdx) in block.items" :key="iIdx" class="flex items-start">
                <div class="w-1.5 h-1.5 rounded-full mt-2 mr-3 flex-shrink-0"
                     :class="{
                       'bg-amber-500': block.level === 'warning',
                       'bg-red-500': block.level === 'danger',
                       'bg-emerald-500': block.level === 'success',
                       'bg-blue-500': !block.level || block.level === 'info'
                     }"></div>
                <span class="font-medium text-[15px] md:text-base leading-relaxed"
                      :class="{
                        'text-amber-900': block.level === 'warning',
                        'text-red-900': block.level === 'danger',
                        'text-emerald-900': block.level === 'success',
                        'text-blue-900': !block.level || block.level === 'info'
                      }" v-html="formatInlineText(item)"></span>
              </li>
            </ul>
          </div>

          <!-- Quote Block -->
          <div v-else-if="block.type === 'quote'" class="relative rounded-2xl p-6 md:p-8 bg-gradient-to-br from-slate-800 to-slate-900 text-white shadow-xl overflow-hidden transition-transform duration-300 hover:scale-[1.01]">
            <i data-lucide="quote" class="absolute -top-4 -right-4 w-32 h-32 text-white/5 rotate-12 pointer-events-none"></i>
            <div class="relative z-10 flex flex-col md:flex-row items-start md:items-center">
              <div class="w-12 h-12 md:w-14 md:h-14 rounded-full bg-orange-500/20 flex flex-shrink-0 items-center justify-center mb-4 md:mb-0 md:mr-5">
                <i data-lucide="mic" class="w-6 h-6 md:w-7 md:h-7 text-orange-400"></i>
              </div>
              <div>
                <h4 class="text-orange-400 font-bold mb-2 tracking-wide text-sm md:text-base uppercase">{{ block.author || '顾问直言' }}</h4>
                <div class="readable-copy text-slate-200 text-lg md:text-xl leading-relaxed italic font-medium">
                  <p v-for="(paragraph, pIdx) in readableParagraphs(block.content)" :key="pIdx">"<span v-html="formatInlineText(paragraph)"></span>"</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Table Block -->
          <div v-else-if="block.type === 'table'" class="glass-card rounded-2xl p-6 md:p-8 overflow-hidden transition-transform duration-300 hover:scale-[1.01]">
            <h3 v-if="block.title" class="text-lg font-bold text-slate-900 mb-5 flex items-center">
              <span class="w-1.5 h-4 bg-emerald-500 rounded-full mr-2"></span>{{ block.title }}
            </h3>
            <div class="overflow-x-auto pb-2 -mx-2 px-2 md:mx-0 md:px-0">
              <table class="w-full text-left border-collapse min-w-[500px]">
                <thead>
                  <tr class="bg-slate-100/50 border-b-2 border-slate-200">
                    <th v-for="(th, hIdx) in block.headers" :key="hIdx" class="py-3.5 px-4 font-bold text-slate-700 whitespace-nowrap">{{ th }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rIdx) in block.rows" :key="rIdx" class="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
                    <td v-for="(td, dIdx) in row" :key="dIdx" class="py-3.5 px-4 text-slate-600 leading-relaxed">{{ td }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </section>
    </div>

  </div>

  <style>
    .readable-copy p + p {
      margin-top: 0.9rem;
    }
    .readable-copy strong {
      color: #0f172a;
      font-weight: 800;
    }
    .readable-copy.text-slate-200 strong {
      color: #ffffff;
    }
    .animate-fade-in {
      animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  </style>

  <script>
    const rawData = ${JSON.stringify(JSON.stringify(data)).replace(/</g, '\\u003c')};
    const radarSvg = ${JSON.stringify(radarSvg || "")};
    const profile = ${JSON.stringify(JSON.stringify(profile || {})).replace(/</g, '\\u003c')};

    const { createApp, ref, onMounted } = Vue;

    function escapeHtmlClient(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function readableParagraphs(value) {
      const text = String(value || '')
        .replace(/\\r\\n/g, '\\n')
        .replace(/\\r/g, '\\n')
        .trim();
      if (!text) return [];

      const labeledText = text.replace(/([。！？!?；;])(?=[^。！？!?；;：:\\n]{2,24}[：:])/g, '$1\\n\\n');
      const rawParts = labeledText
        .split(/\\n{2,}/)
        .flatMap((part) => part.split(/\\n/))
        .map((part) => part.trim())
        .filter(Boolean);

      const paragraphs = [];
      rawParts.forEach((part) => {
        const sentences = part.match(/[^。！？!?；;]+[。！？!?；;]?/g) || [part];
        let current = '';
        sentences.forEach((sentence) => {
          const next = current + sentence;
          if (current && next.length > 130) {
            paragraphs.push(current.trim());
            current = sentence;
          } else {
            current = next;
          }
        });
        if (current.trim()) paragraphs.push(current.trim());
      });

      return paragraphs.length ? paragraphs : [text];
    }

    function formatInlineText(value) {
      return escapeHtmlClient(value)
        .replace(/\\*\\*([^*]{1,80})\\*\\*/g, '<strong>$1</strong>')
        .replace(/^([^：:。！？!?；;，,\\s<][^：:。！？!?；;]{1,30}[：:])/, '<strong>$1</strong>');
    }

    createApp({
      setup() {
        let parsedData = { modules: [] };
        try {
          parsedData = JSON.parse(rawData);
        } catch(e) {
          console.error("JSON parse error on rawData", e);
        }

        let parsedProfile = {};
        try {
          parsedProfile = JSON.parse(profile);
        } catch(e) {}

        const report = ref(parsedData);

        onMounted(() => {
          if (window.lucide) {
            window.lucide.createIcons();
          }
        });

        function scrollToModule(id) {
          const el = document.getElementById('section-' + id);
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        return {
          report,
          radarSvg,
          profile: parsedProfile,
          readableParagraphs,
          formatInlineText,
          scrollToModule
        }
      }
    }).mount('#app');
  </script>
</body>
</html>`
}

module.exports = {
  generateReport,
  saveReport,
  saveReportDraft,
  REPORTS_DIR,
  REPORT_DRAFTS_DIR,
  MIN_MODULE_CONTENT_CHARS,
  normalizeReportHtml,
  humanizeReportCopy,
  splitReadableParagraphs,
  renderInlineText,
  renderReadableText,
  buildHollandRadarSVG,
  countReportContentChars,
  collectModuleContentText,
  getReportQualityIssues,
  buildReportExpansionPrompt,
  buildFinalHtml,
  requestDeepSeekJson,
}
