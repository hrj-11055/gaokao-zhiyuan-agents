'use strict'
const puppeteer = require('puppeteer')
const fs = require('fs').promises
const path = require('path')

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
    
  } finally {
    if (browser) {
      await browser.close()
    }
  }
}

module.exports = {
  generatePdfFromHtml
}
