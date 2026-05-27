'use strict'
const puppeteer = require('puppeteer')
const fs = require('fs').promises
const path = require('path')

const PDF_GENERATOR_VERSION = 'tab-print-v3'
const CJK_FONT_STACK = '"Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Color Emoji", Arial, sans-serif'
const TAB_PRINT_PATCH_CSS = `
  .tabs,
  .tab-nav,
  .tab-buttons {
    display: none !important;
  }
  .tab-pane,
  .tab-panel,
  .tab-content,
  [role="tabpanel"],
  [id^="tab"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
  }
  .tab-pane:not(:first-child),
  .tab-panel:not(:first-child),
  .tab-content:not(:first-child),
  [role="tabpanel"]:not(:first-child),
  [id^="tab"]:not(:first-child) {
    break-before: page;
    page-break-before: always;
  }
`

function pdfMetaPath(pdfFilePath) {
  return `${pdfFilePath}.meta.json`
}

async function isGeneratedPdfFresh(pdfFilePath, htmlFilePath) {
  try {
    const [pdfStat, htmlStat, metaRaw] = await Promise.all([
      fs.stat(pdfFilePath),
      fs.stat(htmlFilePath),
      fs.readFile(pdfMetaPath(pdfFilePath), 'utf8'),
    ])
    const meta = JSON.parse(metaRaw)
    return Boolean(
      pdfStat.size > 0 &&
      meta.version === PDF_GENERATOR_VERSION &&
      Number(meta.htmlMtimeMs || 0) >= Math.floor(htmlStat.mtimeMs)
    )
  } catch {
    return false
  }
}

/**
 * Generate a PDF from a local HTML file
 * @param {string} htmlFilePath - Absolute path to the HTML file
 * @param {string} pdfFilePath - Absolute path to save the PDF
 */
async function generatePdfFromHtml(htmlFilePath, pdfFilePath) {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    })
    const page = await browser.newPage()
    
    // Load the HTML file
    const fileUrl = `file://${htmlFilePath}`
    await page.goto(fileUrl, { waitUntil: 'networkidle0' })
    await page.addStyleTag({
      content: `
        html,
        body,
        body *:not(code):not(pre) {
          font-family: ${CJK_FONT_STACK} !important;
        }
        html,
        body {
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        ${TAB_PRINT_PATCH_CSS}
      `
    })
    await page.evaluate(async () => {
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready
      }
    })
    
    // Generate PDF with background styles enabled
    await page.pdf({
      path: pdfFilePath,
      format: 'A4',
      printBackground: true,
      margin: {
        top: '20px',
        bottom: '20px',
        left: '20px',
        right: '20px'
      }
    })
    const htmlStat = await fs.stat(htmlFilePath)
    await fs.writeFile(pdfMetaPath(pdfFilePath), JSON.stringify({
      version: PDF_GENERATOR_VERSION,
      htmlFile: path.basename(htmlFilePath),
      htmlMtimeMs: Math.floor(htmlStat.mtimeMs),
      generatedAt: new Date().toISOString(),
    }, null, 2), 'utf8')
    
  } finally {
    if (browser) {
      await browser.close()
    }
  }
}

module.exports = {
  generatePdfFromHtml,
  isGeneratedPdfFresh,
  PDF_GENERATOR_VERSION,
}
