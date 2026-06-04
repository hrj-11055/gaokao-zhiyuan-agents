# 2026-06-03 Report Generation JSON Prompt Drift

## Symptom

Mini program report page showed the support fallback modal:

- Title: 报告生成失败
- Message: 生成失败，已保留草稿，可稍后重试...

This appeared after attempting to generate the comprehensive report.

## Root Cause

47 server `/opt/gaokao-proxy` had a deployment drift:

- `lib/report-builder.js` had already switched to DeepSeek `response_format: { type: 'json_object' }` and parsed model output as JSON.
- `lib/prompts/report-template.js` was still the older HTML prompt asking the model to output complete HTML and did not contain the required `json` instruction.

DeepSeek rejected the request with:

`Prompt must contain the word 'json' in some form to use 'response_format' of type 'json_object'.`

PM2 logs showed this at `2026-06-03T01:59:26`, `2026-06-03T01:59:40`, and `2026-06-03T02:08:27`.

## Fix

Backed up the old remote prompt:

`/opt/gaokao-proxy/lib/prompts/report-template.js.bak-json-prompt-20260603-0210`

Synced the local JSON prompt to:

`/opt/gaokao-proxy/lib/prompts/report-template.js`

Restarted PM2 process `gaokao-proxy`.

## Evidence

- `node --check lib/prompts/report-template.js`
- `node --check lib/report-builder.js`
- `node --check server.js`
- `GET https://gaokao.aicoming.cn/api/health` returned `{"status":"ok"}`
- Remote prompt assertion returned:
  `{"hasJson":true,"hasJsonObject":true,"asksHtml":false,"length":2318}`

## Remaining Verification

A full authenticated report generation request still needs a valid mini program member session token, so live end-to-end generation should be retried from the mini program UI.

## 2026-06-03 Mobile Scroll Interaction Follow-up

The report contract was rechecked:

- DeepSeek is only asked to fill report content JSON. Prompt explicitly says the server has a fixed HTML template and the model must not generate HTML/CSS/JS/Markdown.
- The fixed HTML template renders all `modules` as continuous vertical sections in one page.
- Removed the sticky click-based chapter navigation (`@click`, `scrollToModule`, `activeSection`) from `lib/report-builder.js`.
- The generated report now shows a passive "阅读顺序" overview, then users read modules by normal vertical scrolling on mobile.

Remote 47 deployment:

- Backed up `/opt/gaokao-proxy/lib/report-builder.js` to `lib/report-builder.js.bak-mobile-scroll-20260603-0220`.
- Synced updated `lib/report-builder.js`.
- `node --check` passed for `lib/report-builder.js`, `lib/prompts/report-template.js`, and `server.js`.
- Restarted PM2 `gaokao-proxy`; health checks returned OK.
