'use strict'

const crypto = require('crypto')
const fs = require('fs').promises
const path = require('path')

const { generatePdfFromHtml } = require('./pdf-generator')
const { normalizeType } = require('./report-data-client')

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function reportTitle(type, report) {
  const normalizedType = normalizeType(type)
  if (normalizedType === 'major') {
    return `${report.name || '专业'}${report.code ? `（${report.code}）` : ''}`
  }
  return report.name || '院校'
}

function extractRawSections(data = {}) {
  const sections = []
  const layer3 = data.layer3_detail || data.layer3_details || {}
  Object.entries(layer3).forEach(([key, value]) => {
    if (value && typeof value === 'object' && value.raw_content) {
      sections.push({
        title: value.title || key,
        content: value.raw_content,
      })
    }
  })

  const layer4 = data.layer4_supplement || {}
  if (layer4.full_raw_content) {
    sections.push({
      title: '完整原始研究',
      content: layer4.full_raw_content,
    })
  }

  return sections
}

function extractFullContent(report) {
  const data = report?.data || {}
  const sections = extractRawSections(data)
  if (sections.length > 0) {
    return sections.map((section) => section.content).join('\n\n')
  }

  const summary = data.layer2_core?.summary || report.summary || ''
  const overview = data.layer1_overview?.summary || report.overview?.summary || ''
  return [summary, overview].filter(Boolean).join('\n\n')
}

function renderMarkdownish(text) {
  const lines = String(text || '').replace(/\r\n/g, '\n').split('\n')
  const html = []
  let listOpen = false
  let tableLines = []

  const flushList = () => {
    if (listOpen) {
      html.push('</ul>')
      listOpen = false
    }
  }

  const flushTable = () => {
    if (tableLines.length > 0) {
      html.push(`<pre class="table-block">${escapeHtml(tableLines.join('\n'))}</pre>`)
      tableLines = []
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) {
      flushList()
      flushTable()
      continue
    }

    if (line.startsWith('|')) {
      flushList()
      tableLines.push(line)
      continue
    }

    flushTable()

    const heading = line.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      flushList()
      const level = Math.min(heading[1].length + 1, 4)
      html.push(`<h${level}>${escapeHtml(heading[2])}</h${level}>`)
      continue
    }

    const bullet = line.match(/^[-*]\s+(.+)$/)
    if (bullet) {
      if (!listOpen) {
        html.push('<ul>')
        listOpen = true
      }
      html.push(`<li>${escapeHtml(bullet[1])}</li>`)
      continue
    }

    flushList()
    html.push(`<p>${escapeHtml(line)}</p>`)
  }

  flushList()
  flushTable()
  return html.join('\n')
}

function buildDeepReportHtml({ type, report }) {
  const normalizedType = normalizeType(type)
  const title = reportTitle(normalizedType, report)
  const label = normalizedType === 'major' ? '专业深度评估' : '大学深度研究'
  const wordCount = Number(report.word_count || 0)
  const fullContent = extractFullContent(report)

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} - ${escapeHtml(label)}</title>
  <style>
    body {
      margin: 0;
      background: #f7f7f5;
      color: #1f2933;
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      line-height: 1.75;
    }
    .page {
      max-width: 860px;
      margin: 0 auto;
      padding: 42px 38px 64px;
      background: #fff;
    }
    .kicker {
      color: #b45309;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1 {
      margin: 10px 0 12px;
      color: #111827;
      font-size: 30px;
      line-height: 1.25;
    }
    .meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 30px;
      color: #52616f;
      font-size: 14px;
    }
    .pill {
      border: 1px solid #e5e7eb;
      border-radius: 999px;
      padding: 4px 10px;
    }
    h2, h3, h4 {
      color: #111827;
      margin: 24px 0 10px;
      line-height: 1.35;
    }
    p {
      margin: 9px 0;
      text-align: justify;
      word-break: break-word;
    }
    ul {
      padding-left: 20px;
    }
    li {
      margin: 6px 0;
    }
    .table-block {
      white-space: pre-wrap;
      word-break: break-word;
      padding: 12px;
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 12px;
      line-height: 1.55;
    }
    .notice {
      margin-top: 30px;
      padding: 14px 16px;
      background: #fff7ed;
      border: 1px solid #fed7aa;
      border-radius: 8px;
      color: #7c2d12;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <main class="page">
    <div class="kicker">${escapeHtml(label)}</div>
    <h1>${escapeHtml(title)}</h1>
    <div class="meta">
      <span class="pill">完整 5000 字以上 PDF</span>
      <span class="pill">数据库报告字数：${wordCount || '待统计'}</span>
      <span class="pill">生成时间：${escapeHtml(new Date().toISOString().slice(0, 10))}</span>
    </div>
    ${renderMarkdownish(fullContent)}
    <div class="notice">本 PDF 来自已入库的${escapeHtml(label)}数据，用于志愿填报决策参考。录取规则、招生计划和就业数据以学校与考试院最新发布为准。</div>
  </main>
</body>
</html>`
}

function safePdfFilename(type, report) {
  const normalizedType = normalizeType(type)
  const id = normalizedType === 'major' ? report.code : report.name
  const digest = crypto.createHash('sha1').update(String(id || reportTitle(type, report))).digest('hex').slice(0, 12)
  const prefix = normalizedType === 'major' ? 'major' : 'university'
  return `${prefix}-${digest}.pdf`
}

async function generateDeepReportPdf({ type, report, outputDir }) {
  await fs.mkdir(outputDir, { recursive: true })
  const filename = safePdfFilename(type, report)
  const pdfPath = path.join(outputDir, filename)
  const htmlPath = path.join(outputDir, filename.replace(/\.pdf$/, '.html'))
  const html = buildDeepReportHtml({ type, report })

  await fs.writeFile(htmlPath, html, 'utf8')
  await generatePdfFromHtml(htmlPath, pdfPath)
  return {
    filename,
    pdfPath,
    title: reportTitle(type, report),
  }
}

module.exports = {
  buildDeepReportHtml,
  escapeHtml,
  extractFullContent,
  generateDeepReportPdf,
  renderMarkdownish,
  reportTitle,
  safePdfFilename,
}
