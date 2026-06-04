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

  if (sections.length > 0) {
    return sections
  }

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

function visibleWordCount(report, sections) {
  const count = sections.reduce(
    (total, section) => total + Array.from(String(section?.content || '')).length,
    0
  )
  return count || Number(report?.word_count || 0)
}

function recommendationLabel(value) {
  const normalized = String(value || '').toLowerCase()
  if (normalized.includes('green') || normalized.includes('推荐')) return '建议重点关注'
  if (normalized.includes('yellow') || normalized.includes('谨慎')) return '需要核验后再定'
  if (normalized.includes('red') || normalized.includes('不推荐')) return '风险较高'
  return '待结合分数核验'
}

function renderInline(text) {
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

function renderTable(tableLines) {
  const rows = tableLines
    .map((line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim()))
    .filter((cells) => cells.length > 0)

  if (rows.length === 0) return ''

  const isDivider = (cells) => cells.every(cell => /^:?-{3,}:?$/.test(cell))
  const header = rows[0]
  const bodyRows = rows.slice(isDivider(rows[1] || []) ? 2 : 1)

  return `<div class="table-scroll"><table>
    <thead><tr>${header.map(cell => `<th>${renderInline(cell)}</th>`).join('')}</tr></thead>
    <tbody>${bodyRows.map(row => `<tr>${row.map(cell => `<td>${renderInline(cell)}</td>`).join('')}</tr>`).join('\n')}</tbody>
  </table></div>`
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
  let listOpen = ''
  let tableLines = []

  const flushList = () => {
    if (listOpen) {
      html.push(`</${listOpen}>`)
      listOpen = ''
    }
  }

  const flushTable = () => {
    if (tableLines.length > 0) {
      html.push(renderTable(tableLines))
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
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`)
      continue
    }

    const bullet = line.match(/^[-*]\s+(.+)$/)
    if (bullet) {
      if (listOpen !== 'ul') {
        flushList()
        html.push('<ul>')
        listOpen = 'ul'
      }
      html.push(`<li>${renderInline(bullet[1])}</li>`)
      continue
    }

    const ordered = line.match(/^\d+[.)]\s+(.+)$/)
    if (ordered) {
      if (listOpen !== 'ol') {
        flushList()
        html.push('<ol>')
        listOpen = 'ol'
      }
      html.push(`<li>${renderInline(ordered[1])}</li>`)
      continue
    }

    const quote = line.match(/^>\s+(.+)$/)
    if (quote) {
      flushList()
      html.push(`<blockquote>${renderInline(quote[1])}</blockquote>`)
      continue
    }

    flushList()
    html.push(`<p>${renderInline(line)}</p>`)
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
  const rawSections = extractRawSections(report?.data || {})
  const sections = rawSections.length > 0
    ? rawSections
    : [{ title: '完整研究内容', content: extractFullContent(report) }]
  const wordCount = visibleWordCount(report, sections)
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
      font-family: "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Color Emoji", Arial, sans-serif;
      line-height: 1.75;
      font-size: 14px;
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
      font-size: 26px;
      line-height: 1.25;
    }
    .meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 30px;
      color: #52616f;
      font-size: 12px;
    }
    .pill {
      border: 1px solid #e5e7eb;
      border-radius: 999px;
      padding: 4px 10px;
    }
    .summary-title {
      margin: 22px 0 12px;
      color: #92400e;
      font-size: 14px;
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
      margin-top: 28px;
      padding-top: 18px;
      border-top: 1px solid #e5e7eb;
      page-break-before: auto;
      break-before: auto;
    }
    .report-section:first-of-type {
      margin-top: 18px;
      padding-top: 0;
      border-top: 0;
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
    .table-scroll {
      overflow-x: auto;
      margin: 14px 0;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    th, td {
      padding: 8px 10px;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #fff7ed;
      color: #9a3412;
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

function buildDeepReportReaderHtml({ type, report }) {
  const normalizedType = normalizeType(type)
  const title = reportTitle(normalizedType, report)
  const label = normalizedType === 'major' ? '专业深度评估' : '大学深度研究'
  const rawSections = extractRawSections(report?.data || {})
  const sections = (rawSections.length > 0
    ? rawSections
    : [{ title: '完整研究内容', content: extractFullContent(report) }]
  ).map((section, index) => ({
    ...section,
    id: `section-${index + 1}`,
  }))
  const wordCount = visibleWordCount(report, sections)
  const summaryCards = buildSummaryCards(report)
  const generatedDate = new Date().toISOString().slice(0, 10)

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} - 在线阅读</title>
  <style>
    :root {
      --paper: #fffdf8;
      --ink: #172033;
      --muted: #667085;
      --line: #e8dfd0;
      --blue: #2563eb;
      --green: #0f766e;
      --amber: #d97706;
      --rose: #be123c;
      --soft-blue: #eff6ff;
      --soft-amber: #fff7ed;
      --soft-green: #ecfdf5;
      --shadow: 0 20px 60px rgba(23, 32, 51, 0.12);
    }
    * { box-sizing: border-box; }
    html {
      scroll-behavior: smooth;
      background: #f5f1ea;
    }
    body {
      margin: 0;
      color: var(--ink);
      background:
        linear-gradient(180deg, rgba(255, 253, 248, 0.3), rgba(245, 241, 234, 0.98)),
        repeating-linear-gradient(90deg, rgba(23, 32, 51, 0.025) 0, rgba(23, 32, 51, 0.025) 1px, transparent 1px, transparent 96px);
      font-family: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", serif;
      line-height: 1.82;
      -webkit-font-smoothing: antialiased;
    }
    a { color: inherit; text-decoration: none; }
    .reader-hero {
      position: relative;
      overflow: hidden;
      min-height: 320px;
      padding: 48px clamp(20px, 5vw, 72px) 34px;
      color: #fff;
      background:
        linear-gradient(132deg, rgba(21, 32, 54, 0.96), rgba(25, 82, 93, 0.92) 54%, rgba(146, 64, 14, 0.9)),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 160 160'%3E%3Cpath d='M0 80h160M80 0v160' stroke='rgba(255,255,255,.12)' stroke-width='1'/%3E%3Ccircle cx='80' cy='80' r='38' fill='none' stroke='rgba(255,255,255,.12)'/%3E%3C/svg%3E");
    }
    .hero-inner {
      position: relative;
      max-width: 1180px;
      margin: 0 auto;
    }
    .kicker {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: #fde68a;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.12em;
    }
    .kicker::before {
      content: "";
      width: 26px;
      height: 2px;
      background: #fde68a;
    }
    h1 {
      max-width: 920px;
      margin: 18px 0 18px;
      font-size: clamp(32px, 5vw, 60px);
      line-height: 1.08;
      letter-spacing: 0;
    }
    .hero-note {
      max-width: 760px;
      color: rgba(255, 255, 255, 0.82);
      font-size: 16px;
      margin: 0;
    }
    .hero-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 28px;
    }
    .hero-pill {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 6px 12px;
      border: 1px solid rgba(255, 255, 255, 0.22);
      border-radius: 999px;
      color: rgba(255, 255, 255, 0.9);
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(12px);
      font-size: 13px;
    }
    .reader-shell {
      display: grid;
      grid-template-columns: minmax(230px, 300px) minmax(0, 1fr);
      gap: 28px;
      max-width: 1180px;
      margin: -34px auto 80px;
      padding: 0 clamp(16px, 4vw, 36px);
      position: relative;
      z-index: 2;
    }
    .side-panel {
      position: sticky;
      top: 16px;
      align-self: start;
      padding: 18px;
      border: 1px solid rgba(232, 223, 208, 0.92);
      border-radius: 18px;
      background: rgba(255, 253, 248, 0.94);
      box-shadow: var(--shadow);
    }
    .search-box {
      display: grid;
      gap: 10px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }
    .search-row {
      display: flex;
      gap: 8px;
    }
    input[type="search"] {
      width: 100%;
      min-width: 0;
      height: 42px;
      border: 1px solid #d7cbbb;
      border-radius: 12px;
      background: #fff;
      color: var(--ink);
      padding: 0 12px;
      font-size: 15px;
      outline: none;
    }
    input[type="search"]:focus {
      border-color: var(--blue);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    }
    .tool-btn {
      height: 42px;
      border: 0;
      border-radius: 12px;
      padding: 0 12px;
      color: #fff;
      background: var(--ink);
      font-weight: 800;
      cursor: pointer;
    }
    .tool-btn.secondary {
      color: var(--ink);
      background: #efe7da;
    }
    .search-count {
      color: var(--muted);
      font-size: 13px;
      min-height: 20px;
    }
    .toc-title {
      margin: 16px 0 8px;
      color: var(--amber);
      font-size: 13px;
      font-weight: 900;
      letter-spacing: 0.08em;
    }
    .toc-list {
      display: grid;
      gap: 4px;
      max-height: 54vh;
      overflow: auto;
      padding-right: 4px;
    }
    .toc-link {
      display: block;
      padding: 8px 10px;
      border-radius: 10px;
      color: #344054;
      font-size: 14px;
      line-height: 1.35;
    }
    .toc-link:hover {
      background: var(--soft-blue);
      color: #1d4ed8;
    }
    .reader-main {
      min-width: 0;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }
    .summary-card {
      min-height: 150px;
      padding: 18px;
      border: 1px solid rgba(232, 223, 208, 0.98);
      border-radius: 18px;
      background: rgba(255, 253, 248, 0.96);
      box-shadow: 0 12px 36px rgba(23, 32, 51, 0.08);
    }
    .summary-card:nth-child(1) { border-top: 4px solid var(--green); }
    .summary-card:nth-child(2) { border-top: 4px solid var(--blue); }
    .summary-card:nth-child(3) { border-top: 4px solid var(--amber); }
    .summary-label {
      color: var(--muted);
      font-size: 13px;
      font-weight: 800;
    }
    .summary-value {
      display: block;
      margin: 8px 0;
      color: var(--ink);
      font-size: 22px;
      line-height: 1.25;
      font-weight: 900;
    }
    .summary-detail {
      color: #475467;
      font-size: 14px;
      line-height: 1.65;
      margin: 0;
    }
    .reader-section {
      margin-top: 18px;
      padding: clamp(22px, 4vw, 38px);
      border: 1px solid rgba(232, 223, 208, 0.98);
      border-radius: 22px;
      background: var(--paper);
      box-shadow: 0 12px 36px rgba(23, 32, 51, 0.07);
      scroll-margin-top: 18px;
    }
    .section-index {
      color: var(--amber);
      font-size: 13px;
      font-weight: 900;
      letter-spacing: 0.1em;
    }
    h2 {
      margin: 8px 0 20px;
      color: var(--ink);
      font-size: clamp(24px, 3vw, 36px);
      line-height: 1.22;
      letter-spacing: 0;
    }
    .section-content h3,
    .section-content h4 {
      margin: 26px 0 10px;
      color: #1d2939;
      line-height: 1.35;
    }
    .section-content p {
      margin: 11px 0;
      color: #344054;
      text-align: justify;
      word-break: break-word;
    }
    .section-content ul,
    .section-content ol {
      padding-left: 24px;
      color: #344054;
    }
    .section-content li {
      margin: 7px 0;
    }
    blockquote {
      margin: 16px 0;
      padding: 12px 16px;
      border-left: 4px solid var(--blue);
      background: var(--soft-blue);
      color: #1e3a8a;
      border-radius: 0 12px 12px 0;
    }
    code {
      padding: 2px 5px;
      border-radius: 6px;
      background: #f2eadc;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 0.92em;
    }
    .table-scroll {
      overflow-x: auto;
      margin: 18px 0;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 620px;
      font-size: 14px;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid #efe7da;
      text-align: left;
      vertical-align: top;
    }
    th {
      color: #7c2d12;
      background: var(--soft-amber);
      font-weight: 900;
    }
    mark {
      padding: 1px 3px;
      border-radius: 5px;
      background: #fde68a;
      color: #111827;
    }
    mark.active {
      background: var(--rose);
      color: #fff;
    }
    .notice {
      margin-top: 18px;
      padding: 16px 18px;
      border: 1px solid #bfdbfe;
      border-radius: 16px;
      background: rgba(239, 246, 255, 0.88);
      color: #1e3a8a;
      font-size: 14px;
    }
    @media (max-width: 860px) {
      .reader-hero {
        min-height: auto;
        padding: 34px 20px 50px;
      }
      .reader-shell {
        display: block;
        margin-top: -30px;
        padding: 0 12px 56px;
      }
      .side-panel {
        position: relative;
        top: auto;
        margin-bottom: 14px;
        border-radius: 18px;
      }
      .toc-list {
        display: flex;
        gap: 8px;
        max-height: none;
        overflow-x: auto;
        padding-bottom: 4px;
      }
      .toc-link {
        flex: 0 0 auto;
        max-width: 210px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border: 1px solid var(--line);
        background: #fff;
      }
      .summary-grid {
        grid-template-columns: 1fr;
      }
      .reader-section {
        border-radius: 18px;
      }
    }
    @media print {
      .side-panel { display: none; }
      .reader-shell {
        display: block;
        margin: 0;
        max-width: none;
      }
      .reader-hero {
        color: var(--ink);
        background: #fff;
        min-height: 0;
      }
      .hero-note,
      .hero-pill,
      .kicker { color: var(--ink); }
      .reader-section,
      .summary-card {
        box-shadow: none;
        break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <header class="reader-hero">
    <div class="hero-inner">
      <div class="kicker">${escapeHtml(label)}</div>
      <h1>${escapeHtml(title)}</h1>
      <p class="hero-note">${escapeHtml(summaryCards[0]?.detail || '围绕适配度、风险点和下一步核验动作阅读这份深度报告。')}</p>
      <div class="hero-meta">
        <span class="hero-pill">在线阅读</span>
        <span class="hero-pill">${wordCount || '待统计'} 字</span>
        <span class="hero-pill">生成时间 ${escapeHtml(generatedDate)}</span>
      </div>
    </div>
  </header>
  <div class="reader-shell">
    <aside class="side-panel">
      <div class="search-box">
        <div class="search-row">
          <input id="reportSearch" type="search" placeholder="查找关键词" autocomplete="off">
          <button id="searchClear" class="tool-btn secondary" type="button">清除</button>
        </div>
        <div class="search-row">
          <button id="searchPrev" class="tool-btn secondary" type="button">上一个</button>
          <button id="searchNext" class="tool-btn" type="button">下一个</button>
        </div>
        <div id="searchCount" class="search-count"></div>
        <button class="tool-btn secondary" type="button" onclick="window.print()">打印</button>
      </div>
      <div class="toc-title">目录</div>
      <nav class="toc-list">
        ${sections.map((section, index) => `<a class="toc-link" href="#${escapeHtml(section.id)}">${index + 1}. ${escapeHtml(section.title || `章节 ${index + 1}`)}</a>`).join('\n')}
      </nav>
    </aside>
    <main class="reader-main">
      <section class="summary-grid" aria-label="摘要">
        ${summaryCards.map(card => `<article class="summary-card">
          <span class="summary-label">${escapeHtml(card.label)}</span>
          <strong class="summary-value">${escapeHtml(card.value)}</strong>
          <p class="summary-detail">${escapeHtml(card.detail)}</p>
        </article>`).join('\n')}
      </section>
      ${sections.map((section, index) => `<section id="${escapeHtml(section.id)}" class="reader-section">
        <div class="section-index">CHAPTER ${String(index + 1).padStart(2, '0')}</div>
        <h2>${escapeHtml(section.title || `章节 ${index + 1}`)}</h2>
        <div class="section-content">${renderSectionContent(section)}</div>
      </section>`).join('\n')}
      <div class="notice">本报告来自已入库的${escapeHtml(label)}数据，用于志愿填报决策参考。招生计划、录取规则和就业数据以学校与考试院最新发布为准。</div>
    </main>
  </div>
  <script>
    (function () {
      var input = document.getElementById('reportSearch')
      var count = document.getElementById('searchCount')
      var prev = document.getElementById('searchPrev')
      var next = document.getElementById('searchNext')
      var clear = document.getElementById('searchClear')
      var containers = Array.prototype.slice.call(document.querySelectorAll('.section-content'))
      var marks = []
      var active = -1

      containers.forEach(function (node) {
        node.setAttribute('data-original-html', node.innerHTML)
      })

      function escapeRegExp(value) {
        return String(value).replace(/[-/\\\\^$*+?.()|[\\]{}]/g, '\\\\$&')
      }

      function reset() {
        containers.forEach(function (node) {
          node.innerHTML = node.getAttribute('data-original-html') || ''
        })
        marks = []
        active = -1
      }

      function setActive(index) {
        marks.forEach(function (mark) { mark.classList.remove('active') })
        if (!marks.length) return
        active = (index + marks.length) % marks.length
        marks[active].classList.add('active')
        marks[active].scrollIntoView({ block: 'center', behavior: 'smooth' })
        count.textContent = (active + 1) + ' / ' + marks.length
      }

      function search() {
        reset()
        var keyword = input.value.trim()
        if (!keyword) {
          count.textContent = ''
          return
        }
        var pattern = new RegExp(escapeRegExp(keyword), 'gi')
        containers.forEach(function (node) {
          node.innerHTML = (node.getAttribute('data-original-html') || '').replace(pattern, function (match) {
            return '<mark>' + match + '</mark>'
          })
        })
        marks = Array.prototype.slice.call(document.querySelectorAll('mark'))
        if (!marks.length) {
          count.textContent = '未找到'
          return
        }
        setActive(0)
      }

      input.addEventListener('input', search)
      clear.addEventListener('click', function () {
        input.value = ''
        reset()
        count.textContent = ''
        input.focus()
      })
      prev.addEventListener('click', function () { if (marks.length) setActive(active - 1) })
      next.addEventListener('click', function () { if (marks.length) setActive(active + 1) })
    })()
  </script>
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
  buildDeepReportReaderHtml,
  buildSummaryCards,
  escapeHtml,
  extractFullContent,
  generateDeepReportPdf,
  renderMarkdownish,
  renderSectionContent,
  reportTitle,
  safePdfFilename,
}
