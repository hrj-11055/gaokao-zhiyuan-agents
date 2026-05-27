# 离线验收 TODO（2026-05-25）

目标：在不做真机上传、不提交微信审核的前提下，尽可能把本地代码、构建产物、公开服务和关键上线开关跑完，最后只留下必须由人工真机确认的事项。

## 1. 范围确认

- [x] 记录当前 git 状态，避免误动已有生成产物和用户改动。
- [x] 确认小程序生产 API 基线为 `https://gaokao.aicoming.cn`。
- [x] 确认 PDF 下载构建开关应使用 `VITE_PDF_DOWNLOAD_ENABLED=true`。
- [x] 确认本轮不执行微信开发者工具上传、体验版分享、提审、发布。

## 2. Python / 数据工具

- [x] 运行全量 `python3 -m unittest discover tests`，记录失败项。
- [x] 运行上线相关聚焦测试：会员、报告、PDF、SSE、分数线、问卷、配置。
- [x] 对 `gaokao-api/app.py` 做 Python 语法检查。
- [x] 对根目录关键 Python 脚本做批量语法检查，排除生成文件和归档目录。

## 3. gaokao-proxy

- [x] 对 `gaokao-proxy/server.js` 和 `gaokao-proxy/lib/*.js` 运行 `node --check`。
- [x] 检查会员、支付、微信登录、报告生成、深度 PDF、数据 API 模块是否可加载或至少语法通过。
- [x] 检查 `.env.example` / 文档中上线域名、报告域名、支付回调是否一致。
- [x] 检查 `SCORE_API_URL` 默认值和当前 live 文档是否冲突。

## 4. gaokao-miniprogram

- [x] 检查 `src/config.js` 的 API、支付、PDF 开关。
- [x] 用生产参数运行 `npm run build:mp-weixin`。
- [x] 验证 `dist/build/mp-weixin` 产物存在，且包含关键页面。
- [x] 扫描构建产物中是否残留错误的 API 域名或 HTTP IP 入口。

## 5. 公开服务离线验证

- [x] 验证 `https://gaokao.aicoming.cn/api/health`。
- [x] 验证 HTTP 到 HTTPS 跳转。
- [x] 验证公开综合报告 PDF 返回 `application/pdf`。
- [x] 验证未登录访问深度 PDF 返回预期 `401`，不是 HTML 乱码或 404。
- [x] 验证 `/api/reports/health` 是否可用。
- [x] 验证 47 到 159 分数线 API 当前是否可达；如果不可达，标记为上线前阻塞。

## 6. 结果处理

- [x] 对可本地修复的问题直接修复并复测。
- [x] 对需要微信后台、商户号、真机支付、上传体验版的问题，保留为人工验收项。
- [x] 输出最终验收报告：通过项、失败项、修复项、剩余阻塞项、建议你最后真机验收的顺序。

## 7. 本轮结果摘要

- `python3 -m unittest discover tests`：87 个测试通过。
- `tests/test_scores_api.py` against `http://159.75.110.157/score-api`：7/7 通过。
- `node --check`：`gaokao-proxy/server.js` 与 `gaokao-proxy/lib/*.js` 通过。
- `npm run build:mp-weixin`：默认生产构建通过；额外开启 `VITE_PAYMENT_ENABLED=true` 的支付构建也通过。
- Live 公共服务：health 200、HTTP 301 到 HTTPS、报告库 PG connected、公开 PDF `application/pdf`、未登录深度 PDF 401。
- Live 会员链路：dev 登录 200、未登录支付 401、已登录但微信支付未配置时返回结构化 503。
- Live 完整报告链路：测试会员限免解锁 200，综合报告生成 200，用时约 48.6 秒，新报告 HTML 200，新 PDF `application/pdf`。
- Live 深度 PDF：会员 token 请求 `/api/reports/deep/pdf?type=major&id=080901` 返回 `200 application/pdf`，文件头 `%PDF-`。
