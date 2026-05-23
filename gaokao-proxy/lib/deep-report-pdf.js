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

function recommendationLabel(value) {
  const normalized = String(value || '').toLowerCase()
  if (normalized.includes('green') || normalized.includes('推荐')) return '建议重点关注'
  if (normalized.includes('yellow') || normalized.includes('谨慎')) return '需要核验后再定'
  if (normalized.includes('red') || normalized.includes('不推荐')) return '风险较高'
  return '待结合分数核验'
}

function buildSummaryCards(report) {
  const data = report?.data || {}
  const overview = data.layer1_overview || {}
  const core = data.layer2_core || {}
  return [
    {
      label: '推荐判断',
      value: recommendationLabel(overview.recommendation_level),
      detail: overview.summary || report.summary || '先看分数位次、培养方案和就业质量报告。',
    },
    {
      label: '重点结论',
      value: overview.weighted_score ? `${overview.weighted_score} 分` : '需核验',
      detail: core.summary || '把优势、风险和下一步动作放在同一页核对。',
    },
    {
      label: '行动建议',
      value: '先核验再下载',
      detail: '下载前先确认名称匹配，下载后重点看课程、就业、升学和风险章节。',
    },
  ]
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

function renderSectionContent(section) {
  const title = String(section?.title || '').trim()
  let content = String(section?.content || '').replace(/\r\n/g, '\n')
  if (title) {
    const lines = content.split('\n')
    const firstNonEmptyIndex = lines.findIndex(line => line.trim())
    if (firstNonEmptyIndex >= 0) {
      const first = lines[firstNonEmptyIndex].trim().replace(/^#{1,4}\s+/, '').trim()
      if (first === title) {
        lines.splice(firstNonEmptyIndex, 1)
        content = lines.join('\n')
      }
    }
  }
  return renderMarkdownish(content)
}

function buildDeepReportHtml({ type, report }) {
  const normalizedType = normalizeType(type)
  const title = reportTitle(normalizedType, report)
  const label = normalizedType === 'major' ? '专业深度评估' : '大学深度研究'
  const wordCount = Number(report.word_count || 0)
  const rawSections = extractRawSections(report?.data || {})
  const sections = rawSections.length > 0
    ? rawSections
    : [{ title: '完整研究内容', content: extractFullContent(report) }]
  const summaryCards = buildSummaryCards(report)

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} - ${escapeHtml(label)}</title>
  <style>
    body {
      margin: 0;
      background: #fff;
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
    .summary-title {
      margin: 22px 0 12px;
      color: #92400e;
      font-size: 15px;
      font-weight: 800;
    }
    .summary-card-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin: 0 0 24px;
    }
    .summary-card {
      border: 1px solid #fed7aa;
      border-radius: 12px;
      background: #fff7ed;
      padding: 12px;
    }
    .summary-card-label {
      color: #9a3412;
      font-size: 12px;
      font-weight: 700;
    }
    .summary-card-value {
      display: block;
      margin: 5px 0;
      color: #111827;
      font-size: 16px;
      font-weight: 800;
    }
    .summary-card-detail {
      color: #4b5563;
      font-size: 12px;
      line-height: 1.55;
    }
    .highlight-box {
      margin: 18px 0 24px;
      padding: 14px 16px;
      border: 1px solid #bfdbfe;
      border-radius: 10px;
      background: #eff6ff;
      color: #1e3a8a;
    }
    .toc {
      margin: 18px 0 28px;
      padding: 16px 18px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      background: #f9fafb;
    }
    .toc-title {
      margin-bottom: 8px;
      font-weight: 800;
      color: #111827;
    }
    .toc ol {
      margin: 0;
      padding-left: 20px;
    }
    .report-section {
      page-break-before: always;
      break-before: page;
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
    @media (max-width: 720px) {
      .summary-card-row {
        grid-template-columns: 1fr;
      }
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
    <div class="summary-title">摘要卡片</div>
    <section class="summary-card-row">
      ${summaryCards.map(card => `<article class="summary-card">
        <span class="summary-card-label">${escapeHtml(card.label)}</span>
        <strong class="summary-card-value">${escapeHtml(card.value)}</strong>
        <div class="summary-card-detail">${escapeHtml(card.detail)}</div>
      </article>`).join('\n')}
    </section>
    <div class="highlight-box"><strong>重点结论：</strong>${escapeHtml(summaryCards[1]?.detail || summaryCards[0]?.detail || '先核验关键数据，再进入长文细读。')}</div>
    <nav class="toc">
      <div class="toc-title">目录</div>
      <ol>
        ${sections.map((section, index) => `<li>${escapeHtml(section.title || `章节 ${index + 1}`)}</li>`).join('\n')}
      </ol>
    </nav>
    ${sections.map((section) => `<section class="report-section page-break">
      <h2>${escapeHtml(section.title || '研究章节')}</h2>
      ${renderSectionContent(section)}
    </section>`).join('\n')}
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
  buildSummaryCards,
  escapeHtml,
  extractFullContent,
  generateDeepReportPdf,
  renderMarkdownish,
  renderSectionContent,
  reportTitle,
  safePdfFilename,
}
