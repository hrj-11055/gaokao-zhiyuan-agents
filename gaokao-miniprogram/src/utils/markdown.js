const BOLD_STYLE = 'font-weight: 700;'

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function pushText(nodes, text) {
  if (!text) return
  nodes.push({ type: 'text', text })
}

function parseInlineMarkdown(text) {
  const nodes = []
  let cursor = 0

  while (cursor < text.length) {
    const open = text.indexOf('**', cursor)
    if (open === -1) {
      pushText(nodes, text.slice(cursor))
      break
    }

    const close = text.indexOf('**', open + 2)
    if (close === -1) {
      pushText(nodes, text.slice(cursor))
      break
    }

    pushText(nodes, text.slice(cursor, open))
    const boldText = text.slice(open + 2, close)
    if (boldText) {
      nodes.push({
        name: 'strong',
        attrs: { style: BOLD_STYLE },
        children: [{ type: 'text', text: boldText }]
      })
    }
    cursor = close + 2
  }

  return nodes
}

export function markdownToRichTextNodes(markdown = '') {
  const nodes = []
  const lines = String(markdown).split('\n')

  lines.forEach((line, index) => {
    if (index > 0) {
      nodes.push({ name: 'br' })
    }
    nodes.push(...parseInlineMarkdown(line))
  })

  return nodes
}

function parseInlineMarkdownHtml(text) {
  let html = ''
  let cursor = 0

  while (cursor < text.length) {
    const open = text.indexOf('**', cursor)
    if (open === -1) {
      html += escapeHtml(text.slice(cursor))
      break
    }

    const close = text.indexOf('**', open + 2)
    if (close === -1) {
      html += escapeHtml(text.slice(cursor))
      break
    }

    html += escapeHtml(text.slice(cursor, open))
    const boldText = text.slice(open + 2, close)
    if (boldText) {
      html += `<strong style="${BOLD_STYLE}">${escapeHtml(boldText)}</strong>`
    }
    cursor = close + 2
  }

  return html
}

export function markdownToRichTextHtml(markdown = '') {
  return String(markdown)
    .split('\n')
    .map((line) => parseInlineMarkdownHtml(line))
    .join('<br/>')
}
