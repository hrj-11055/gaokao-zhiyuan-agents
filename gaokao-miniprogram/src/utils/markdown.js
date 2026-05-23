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
  const lines = String(markdown).split('\n')
  const blocks = []
  let currentParagraph = null
  let currentList = null

  function closeCurrentParagraph() {
    if (currentParagraph) {
      blocks.push({ type: 'paragraph', lines: currentParagraph })
      currentParagraph = null
    }
  }

  function closeCurrentList() {
    if (currentList) {
      blocks.push({ type: 'list', listType: currentList.type, items: currentList.items })
      currentList = null
    }
  }

  lines.forEach((line) => {
    const trimmed = line.trim()

    // 1. Handle headings: ### Title, ## Title, # Title
    const headingMatch = line.match(/^(\s*)(#{1,6})\s+(.+)$/)
    if (headingMatch) {
      closeCurrentParagraph()
      closeCurrentList()
      blocks.push({
        type: 'heading',
        level: headingMatch[2].length,
        text: headingMatch[3]
      })
      return
    }

    // 2. Handle Unordered Lists: - item, * item
    const unorderedMatch = line.match(/^(\s*)[-*]\s+(.+)$/)
    if (unorderedMatch) {
      closeCurrentParagraph()
      if (currentList && currentList.type !== 'unordered') {
        closeCurrentList()
      }
      if (!currentList) {
        currentList = { type: 'unordered', items: [] }
      }
      currentList.items.push(unorderedMatch[2])
      return
    }

    // 3. Handle Ordered Lists: 1. item, 2. item
    const orderedMatch = line.match(/^(\s*)\d+\.\s+(.+)$/)
    if (orderedMatch) {
      closeCurrentParagraph()
      if (currentList && currentList.type !== 'ordered') {
        closeCurrentList()
      }
      if (!currentList) {
        currentList = { type: 'ordered', items: [] }
      }
      currentList.items.push(orderedMatch[2])
      return
    }

    // 4. Handle Blank/Empty lines
    if (!trimmed) {
      closeCurrentParagraph()
      closeCurrentList()
      blocks.push({ type: 'spacer' })
      return
    }

    // 5. Handle standard paragraph text
    closeCurrentList()
    if (!currentParagraph) {
      currentParagraph = []
    }
    currentParagraph.push(line)
  })

  closeCurrentParagraph()
  closeCurrentList()

  const hasOtherBlockTypes = blocks.some(b => b.type !== 'paragraph' && b.type !== 'spacer')
  const paragraphCount = blocks.filter(b => b.type === 'paragraph').length

  let htmlResult = ''

  blocks.forEach((block) => {
    if (block.type === 'heading') {
      const headingText = parseInlineMarkdownHtml(block.text)
      let fontSize = '30rpx'
      let margin = '16rpx 0 8rpx'
      if (block.level === 1) { fontSize = '36rpx'; margin = '24rpx 0 12rpx'; }
      else if (block.level === 2) { fontSize = '33rpx'; margin = '20rpx 0 10rpx'; }

      htmlResult += `<div style="font-size: ${fontSize}; font-weight: bold; color: #111827; margin: ${margin};">${headingText}</div>`
    }
    else if (block.type === 'list') {
      if (block.listType === 'unordered') {
        htmlResult += '<ul style="margin: 8rpx 0; padding-left: 28rpx; list-style-type: disc;">'
        block.items.forEach(item => {
          const itemText = parseInlineMarkdownHtml(item)
          htmlResult += `<li style="margin: 6rpx 0; font-size: 29rpx; color: #374151; line-height: 1.5;">${itemText}</li>`
        })
        htmlResult += '</ul>'
      } else {
        htmlResult += '<ol style="margin: 8rpx 0; padding-left: 28rpx; list-style-type: decimal;">'
        block.items.forEach(item => {
          const itemText = parseInlineMarkdownHtml(item)
          htmlResult += `<li style="margin: 6rpx 0; font-size: 29rpx; color: #374151; line-height: 1.5;">${itemText}</li>`
        })
        htmlResult += '</ol>'
      }
    }
    else if (block.type === 'spacer') {
      htmlResult += '<div style="height: 12rpx;"></div>'
    }
    else if (block.type === 'paragraph') {
      const paraContent = block.lines.map(line => parseInlineMarkdownHtml(line)).join('<br/>')
      if (!hasOtherBlockTypes && paragraphCount === 1) {
        htmlResult += paraContent
      } else {
        htmlResult += `<div style="margin-bottom: 6rpx; min-height: 32rpx; line-height: 1.6;">${paraContent}</div>`
      }
    }
  })

  return htmlResult
}
