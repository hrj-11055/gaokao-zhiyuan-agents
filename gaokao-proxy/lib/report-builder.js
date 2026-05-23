'use strict'
const fs = require('fs').promises
const path = require('path')

const buildPrompt = require('./prompts/report-template')
const { fetchMajorReports, fetchUnivReports, fetchDifyMessages } = require('./data-api')

const REPORTS_DIR = process.env.REPORTS_DIR || path.join(__dirname, '../reports')
const REPORT_DRAFTS_DIR = process.env.REPORT_DRAFTS_DIR || path.join(REPORTS_DIR, 'drafts')
const DEEPSEEK_MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-v4-pro'
const RESPONSIVE_PATCH_ID = 'gaokao-report-responsive-fix'
const PRINT_PATCH_ID = 'gaokao-report-print-fix'

async function generateReport({ profile, questionnaire, assessments, conversationId, difyApiUrl, difyApiKey }) {
  if (!process.env.DEEPSEEK_API_KEY) {
    throw new Error('DEEPSEEK_API_KEY 环境变量未配置')
  }

  const [majorReports, univData, messages] = await Promise.all([
    fetchMajorReports(questionnaire),
    fetchUnivReports(profile),
    fetchDifyMessages(conversationId, difyApiUrl, difyApiKey),
  ])

  const prompt = buildPrompt(profile, questionnaire, messages, majorReports, univData, assessments)

  try {
    const res = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model: DEEPSEEK_MODEL,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 32768,
        temperature: 0.7,
      }),
      signal: AbortSignal.timeout(110000),
    })

    if (!res.ok) {
      const err = await res.text()
      throw new Error(`DeepSeek API error ${res.status}: ${err.slice(0, 200)}`)
    }

    const data = await res.json()
    return data.choices[0].message.content
  } catch (err) {
    console.error('DeepSeek generation failed:', err.message)
    throw new Error('AI 报告生成失败，请稍后重试')
  }
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
  let html = extractHtmlDocument(String(rawHtml || ''))
  html = humanizeReportCopy(html)
  html = ensureViewportMeta(html)
  html = injectResponsivePatch(html)
  html = injectPrintPatch(html)
  return html
}

function humanizeReportCopy(html) {
  return String(html || '')
    .replace(/AI\s*总评/g, '顾问结论')
    .replace(/AI\s*对话记录/g, '咨询对话记录')
    .replace(/大模型认为/g, '建议判断')
    .replace(/作为\s*AI[，,]?\s*/g, '')
    .replace(/作为一个?\s*AI[，,]?\s*/g, '')
}

function extractHtmlDocument(rawHtml) {
  const trimmed = rawHtml.trim()
  const fenced = Array.from(trimmed.matchAll(/```(?:html)?\s*([\s\S]*?)```/gi))
    .map(match => match[1].trim())
    .find(block => /<!doctype\s+html|<html[\s>]/i.test(block))

  let html = fenced || trimmed
  const starts = [
    html.search(/<!doctype\s+html/i),
    html.search(/<html[\s>]/i),
  ].filter(index => index >= 0)

  if (starts.length > 0) {
    const start = Math.min(...starts)
    const end = html.toLowerCase().lastIndexOf('</html>')
    html = end >= 0 ? html.slice(start, end + '</html>'.length) : html.slice(start)
  }

  return html
    .replace(/^```(?:html)?\s*/i, '')
    .replace(/\s*```\s*$/i, '')
    .trim()
}

function ensureViewportMeta(html) {
  if (/<meta[^>]+name=["']viewport["']/i.test(html)) return html
  return html.replace(
    /<head([^>]*)>/i,
    '<head$1>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
  )
}

function injectResponsivePatch(html) {
  if (html.includes(`id="${RESPONSIVE_PATCH_ID}"`) || html.includes(`id='${RESPONSIVE_PATCH_ID}'`)) {
    return html
  }

  const css = `
    <style id="${RESPONSIVE_PATCH_ID}">
      html, body {
        max-width: 100%;
        overflow-x: hidden;
        -webkit-text-size-adjust: 100%;
      }
      body {
        margin: 0;
        word-break: break-word;
      }
      img, video, canvas, svg, table, pre, code {
        max-width: 100%;
      }
      table {
        display: block;
        overflow-x: auto;
      }
      pre {
        overflow-x: auto;
        white-space: pre-wrap;
      }
      @media (max-width: 640px) {
        body {
          display: block !important;
          padding: 0 !important;
        }
        .report-wrapper,
        .report-container,
        .container,
        .wrapper,
        main {
          width: 100% !important;
          max-width: 100% !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        .header,
        .header-gradient,
        .hero {
          border-radius: 0 0 20px 20px !important;
          padding: 20px 16px !important;
        }
        h1,
        .header h1,
        .header-gradient h1,
        .hero h1 {
          font-size: 28px !important;
          line-height: 1.25 !important;
          letter-spacing: 0 !important;
        }
        h2 {
          font-size: 22px !important;
          line-height: 1.35 !important;
        }
        h3 {
          font-size: 18px !important;
          line-height: 1.4 !important;
        }
        .tab-nav {
          position: sticky !important;
          top: 0 !important;
          z-index: 10 !important;
          display: flex !important;
          flex-wrap: nowrap !important;
          gap: 8px !important;
          overflow-x: auto !important;
          padding: 8px 8px 0 !important;
          -webkit-overflow-scrolling: touch;
        }
        .tab-btn {
          flex: 0 0 auto !important;
          white-space: nowrap !important;
          padding: 10px 12px !important;
          font-size: 14px !important;
        }
        .tab-content,
        .section,
        .card {
          width: auto !important;
          max-width: 100% !important;
          margin: 12px 8px !important;
          padding: 16px !important;
          border-radius: 16px !important;
        }
        .grid-2,
        .grid-3,
        .cards,
        .columns,
        [class*="grid"] {
          display: block !important;
          grid-template-columns: 1fr !important;
        }
        .grid-2 > *,
        .grid-3 > *,
        .cards > *,
        .columns > *,
        [class*="grid"] > * {
          width: 100% !important;
          max-width: 100% !important;
          margin-bottom: 12px !important;
        }
        p,
        li,
        td,
        th {
          font-size: 15px !important;
          line-height: 1.7 !important;
        }
        canvas {
          width: 100% !important;
          height: 260px !important;
        }
      }
    </style>`

  if (/<\/head>/i.test(html)) {
    return html.replace(/<\/head>/i, `${css}\n</head>`)
  }

  return `${css}\n${html}`
}

function injectPrintPatch(html) {
  if (html.includes(`id="${PRINT_PATCH_ID}"`) || html.includes(`id='${PRINT_PATCH_ID}'`)) {
    return html
  }

  const css = `
    <style id="${PRINT_PATCH_ID}">
      @page {
        size: A4;
        margin: 16mm 14mm 18mm;
      }
      .report-toc,
      .toc {
        break-after: page;
        page-break-after: always;
      }
      .page-break {
        break-before: page;
        page-break-before: always;
      }
      .highlight,
      .highlight-box,
      .key-point,
      .action-list {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 10px;
        padding: 12px 14px;
      }
      @media print {
        html, body {
          background: #fff !important;
          color: #111827 !important;
        }
        body {
          font-size: 12pt;
          line-height: 1.65;
        }
        h1, h2, h3 {
          break-after: avoid;
          page-break-after: avoid;
        }
        p, li, table, .card, .section {
          break-inside: avoid;
          page-break-inside: avoid;
        }
        a {
          color: inherit;
          text-decoration: none;
        }
      }
    </style>`

  if (/<\/head>/i.test(html)) {
    return html.replace(/<\/head>/i, `${css}\n</head>`)
  }

  return `${css}\n${html}`
}

module.exports = {
  generateReport,
  saveReport,
  saveReportDraft,
  REPORTS_DIR,
  REPORT_DRAFTS_DIR,
  normalizeReportHtml,
  extractHtmlDocument,
  humanizeReportCopy,
}
