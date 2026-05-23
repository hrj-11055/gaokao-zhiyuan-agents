# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

高考志愿填报助手 — 小程序名「**峰哥咨询参考**」，AI 志愿填报咨询产品。MVP 阶段包含四大模块：数据深度研究、高考咨询智能体（Dify + DeepSeek）、测评填表、综合报告。

**当前阶段**：MVP 核心功能开发完成。数据采集（专业/院校评估报告）持续进行中。

## 关键脚本

### 专业评估报告

```bash
python3 run_major_eval.py 06                        # 跑指定门类（如历史学=06）
python3 run_major_eval.py 06 --retry                # 重跑该门类中失败的专业
python3 run_major_eval.py 06 --only 060101 060102   # 只跑指定专业
python3 run_major_eval.py --status                  # 查看所有门类进度总览
```

门类代码：01=哲学 02=经济学 03=法学 04=教育学 05=文学 06=历史学 07=理学 08=工学 09=农学 10=医学 11=军事学 12=管理学 13=艺术学 14=交叉学科

### 院校评估报告

```bash
# Gemini CLI 版（当前主力，需 GEMINI_API_KEY 环境变量，直接在终端运行）
python3 run_univ_eval_gemini_cli.py 广东省          # 跑广东省所有本科院校
python3 run_univ_eval_gemini_cli.py 广东省 --limit 3 # 只跑前 3 所（测试用）

# 旧版已归档到 scripts_archive/：run_univ_eval.py, run_univ_eval_cli.py, run_univ_eval_claude.py, run_univ_eval_gemini.py
```

提示词模板：`跑大学提示词-v4.txt`（最新版），`跑大学提示词-v2.txt`（Gemini 版）

### 质检与合并

```bash
python3 check_reports.py                 # 默认检查 data/专业评估报告/（8 模块完整性 + 字数）
python3 check_reports.py --min-chars 3000
python3 scripts/data_quality_check.py --all           # 全面数据质量检查（JSON/数据库）
```

### 爬取与上传

```bash
# 录取分数线（掌上高考 API → Markdown 知识库格式）
python3 data/crawl_scores_v5.py                      # 跑全部 31 个省份
python3 data/crawl_scores_v5.py --provinces 44       # 只跑广东
python3 data/crawl_scores_v5.py --status             # 查看各省份进度

# 上传到 Dify 知识库（统一脚本，替代旧版 upload_kb*_to_dify.py）
python3 data/upload_to_dify.py --status              # 查看 Dify 知识库状态
python3 data/upload_to_dify.py                       # 上传所有 kb2 文件
python3 data/upload_to_dify.py --dry-run             # 只检查不上传
python3 data/upload_to_dify.py --files kb2-scores-广东.md  # 上传指定文件

# 院校录取分数线（按院校维度，补充 crawl_scores_v5.py 的省份维度）
python3 data/crawl_school_scores.py                  # 爬全部院校
python3 data/crawl_school_scores.py --limit 10       # 测试用
python3 data/crawl_school_scores.py --status         # 查看进度

# 爬取 KB-4（院校研究）和 KB-5（就业数据）
python3 data/crawl_kb4_kb5.py
```

### 分数线 API 服务

```bash
# 分数数据导入 PostgreSQL（部署在服务器上）
python3 data/import_scores_to_pg.py --stats          # 查看导入状态
python3 data/generate_score_sql.py --stats           # 生成 SQL（--import 通过 SSH 执行）

# Flask API 服务（Dify HTTP 工具节点调用，Docker 容器名 gaokao-api）
# 端点：/api/health, /api/stats, /api/scores, /api/recommend,
#        /api/schools/<name>/scores, /api/major/<keyword>/scores
```

### 报告数据库（PostgreSQL on 159）

```bash
# 数据库结构：scripts/db_schema.sql
# 数据导入脚本：scripts/import_reports_to_pg.py

# 导入报告数据（需要 PG_PASSWORD 环境变量）
PG_PASSWORD=xxx python3 scripts/import_reports_to_pg.py                  # 导入全部
PG_PASSWORD=xxx python3 scripts/import_reports_to_pg.py --check-only     # 质量检查
PG_PASSWORD=xxx python3 scripts/import_reports_to_pg.py --skip-universities  # 只导入专业

# 报告查询 API（gaokao-proxy 内置，通过 PG_* 环境变量连接数据库）
# 端点：
#   GET /api/reports/health              数据库连接状态
#   GET /api/reports/stats               专业/院校统计
#   GET /api/reports/majors              专业列表（支持 search/category/level/min_score/page/page_size）
#   GET /api/reports/majors/:code        单个专业详情
#   GET /api/reports/universities        院校列表（支持 search/province/type/level/min_score/page/page_size）
#   GET /api/reports/universities/:name  单个院校详情

# API 测试
bash scripts/test_report_api.sh http://127.0.0.1:3099
```

数据库连接：gaokao_db @ docker-db_postgres-1（159 服务器 Docker 内），772 条专业 + 956 条院校，通过 SSH 隧道导入。

### 测试

```bash
python3 data/run_test_20q.py             # 跑 20 题标准测试集（调用 Dify API）
python3 data/test_v5_profile.py          # 多轮会话测试（Prompt v5 用户画像收集）
python3 -m unittest discover tests       # 跑单元测试（SSE 解析、安全检查、质量门控）
```

## 技术架构

```
UniApp 小程序（Vue 3 + Vite + Sass）→ 编译为微信小程序
├── src/pages/index/        首页（聊天入口 + 测评/报告卡片）
├── src/pages/chat/         AI 对话页
├── src/pages/questionnaire/ 五环问卷页（22 题）
├── src/pages/report/       报告结果页（显示生成链接）
├── src/pages/report-view/  报告 H5 展示页
├── src/api/dify.js         SSE 解析器 + Dify API 封装
├── src/components/         ChatBubble、QuickQuestions
├── src/utils/storage.js    聊天记录持久化 + 用户 ID
        │
        ├── gaokao-proxy（Express，端口 3001；本地代码包含报告接口）
        │   ├── POST /api/chat             阻塞式
        │   ├── POST /api/chat/stream      SSE 流式转发
        │   ├── POST /api/report/generate  综合报告生成（DeepSeek）
        │   ├── GET  /reports/:file        静态报告托管
        │   ├── GET  /api/health           健康检查
        │   ├── GET  /api/reports/*        报告查询（专业/院校，直连 PostgreSQL）
        │   ├── POST /api/auth/wechat-login 微信登录
        │   ├── GET  /api/membership/status 会员状态查询
        │   ├── POST /api/payment/create   微信支付下单
        │   ├── POST /api/payment/wechat/notify 支付回调
        │   ├── POST /api/tts              语音合成
        │   ├── POST /api/chat/feedback    对话反馈
        │   └── 限流 / CORS / Token 鉴权 / 超时控制 / Redis 冷却
        │
        ├── 腾讯云服务器（159.75.110.157）
        │   ├── Dify 社区版 v1.13.3（Docker）— Chatflow + RAG
        │   ├── PostgreSQL / Redis / pgvector — Dify 数据层
        │   ├── gaokao-api 容器 — 分数查询接口（5001->5000）
        │   └── DeepSeek / 智谱插件
        │
        └── 阿里云服务器（47.113.125.147）
            ├── gaokao-proxy（PM2，端口 3001）
            ├── Nginx 反代 /api/chat、/api/report、/reports
            └── 综合报告 HTML 静态托管
```

- **对话传输**：小程序 `wx.request({ enableChunked: true })` → gaokao-proxy → Dify API（SSE），手动解析 ArrayBuffer
- **小程序配置**：WeChat AppID `wx52fc7943bf6e76aa`，环境变量 `VITE_API_BASE` 控制代理地址（默认 `http://localhost:3001`）
- **数据源**：掌上高考 API（`api.zjzw.cn`）、教育部公开数据

### 线上接口真实状态（2026-05-14 实测）

当前 `gaokao-miniprogram/.env` 和代码默认值都指向：

```bash
VITE_API_BASE=http://47.113.125.147
```

47 服务器是小程序唯一 API Base，已通过 Nginx 暴露当前 `gaokao-proxy`，接口状态如下：

```bash
GET  http://47.113.125.147/api/health          # 200 {"status":"ok"}
POST http://47.113.125.147/api/chat            # 200，聊天代理可用
POST http://47.113.125.147/api/report/generate # 200，返回 http://47.113.125.147/reports/<file>.html
GET  http://47.113.125.147/reports/<file>.html # 200，报告 HTML 可访问
```

159 服务器是 Dify/数据服务器，不是小程序 API Base：

```bash
GET  http://159.75.110.157:8080                # Dify 控制台入口
HEAD http://159.75.110.157/v1                  # X-Version: 1.13.3, X-Env: PRODUCTION
ssh -i /Users/MarkHuang/.ssh/gaokao-new_ed25519 ubuntu@159.75.110.157
```

因此报告页出现“生成失败 / 服务暂时不可用”时，先确认小程序是否仍编译到了错误的 `VITE_API_BASE=http://159.75.110.157`。当前必须使用 `VITE_API_BASE=http://47.113.125.147`。本地 `gaokao-proxy/server.js` 和 47 服务器 `/opt/gaokao-proxy/server.js` 已有报告接口，并配置了 `DIFY_API_URL=http://159.75.110.157`、`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`REPORT_BASE_URL`、`REPORTS_DIR` 等环境变量。

`47.113.125.147` 的真实状态（使用 `/Users/MarkHuang/Downloads/mark123-.pem` 实测）：

```bash
ssh -i /Users/MarkHuang/Downloads/mark123-.pem root@47.113.125.147 # 可登录
```

- 服务器内运行 `/opt/gaokao-proxy/server.js`，PM2 进程名 `gaokao-proxy`，监听 `3001`。
- `/opt/gaokao-proxy/.env` 中 `DIFY_API_URL=http://159.75.110.157`、`PORT=3001`、`REPORT_BASE_URL=http://47.113.125.147`、`DIFY_API_KEY`、`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`REPORTS_DIR` 均已设置。
- 服务器本机 `GET http://127.0.0.1:3001/api/health` 返回 `200 {"status":"ok"}`。
- 服务器本机 `POST http://127.0.0.1:3001/api/report/generate` 可返回报告 URL，例如 `http://aicoming.com.cn/reports/debug-1778672764911.html`。
- 2026-05-13 已修正公网 Nginx：`server_name 47.113.125.147` 下 `/api/health`、`/api/chat`、`/api/report`、`/reports` 反代到 `127.0.0.1:3001`；原通用 `/api/` 仍保留给 3002。
- 2026-05-13 已将 `/opt/gaokao-proxy/.env` 的 `REPORT_BASE_URL` 改为 `http://47.113.125.147` 并重启 PM2，报告接口现在返回 IP 链接而不是被 ICP 拦截的 `aicoming.com.cn` 链接。
- 2026-05-14 已确认 47 本机 `POST http://127.0.0.1:3001/api/chat` 返回 Dify `advanced-chat` 响应，说明 47 的 proxy 当前实际连到 159 Dify。
- 2026-05-14 已确认 159 上 Dify Docker 栈运行，`curl -I http://159.75.110.157/v1` 返回 `X-Version: 1.13.3`，并且 `gaokao-api` 容器暴露 `0.0.0.0:5001->5000`。从 159 本机 `curl http://127.0.0.1:5001/api/health` 返回 `{"records":35978,"status":"ok"}`；如 47 到分数 API 异常，优先检查 47 `.env` 中 `SCORE_API_URL` 和 159 端口暴露，而不是默认相信当前 `:5000` 配置。

### 小程序开发命令

```bash
cd gaokao-miniprogram
npm install
npm run dev:mp-weixin      # 开发模式（编译到 dist/dev/mp-weixin）
npm run build:mp-weixin    # 生产构建
```

用微信开发者工具导入 `dist/dev/mp-weixin` 目录预览。

### 代理服务器

```bash
cd gaokao-proxy
npm install
cp .env.example .env      # 填入 DIFY_API_URL 和 DIFY_API_KEY
npm run dev                # 开发（node server.js）
npm start                  # 生产
```

`.env` 关键变量：
- **基础**：`DIFY_API_URL`、`DIFY_API_KEY`、`PORT`（默认 3001）、`PROXY_API_TOKEN`
- **超时**：`REQUEST_TIMEOUT_MS`（默认 30s）、`STREAM_TIMEOUT_MS`（默认 120s）
- **限流**：`RATE_LIMIT_WINDOW_MS`、`RATE_LIMIT_MAX`、`MAX_QUERY_LENGTH`
- **报告生成**：`DEEPSEEK_API_KEY`、`REPORT_BASE_URL`、`REPORTS_DIR`
- **数据路径**：`MAJOR_REPORTS_DIR`、`UNIV_REPORTS_DIR`（已废弃，报告改为 PG 直查）、`SCORE_API_URL`
- **报告数据库**：`PG_HOST`、`PG_PORT`、`PG_DATABASE`、`PG_USER`、`PG_PASSWORD`
- **Redis**：`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`
- **TTS**：`VOLC_TTS_APPID`、`VOLC_TTS_TOKEN`（必须设置，无默认值）
- **会话**：`COMMERCE_SESSION_SECRET`、`JWT_SECRET`

## Dify 知识库结构

| ID | 名称 | 内容 | 文件位置 |
|----|------|------|---------|
| KB-1 | 张雪峰语料库 | 20+ Q&A 对，覆盖 4 种意图 | `data/knowledge-base/kb1-*.md` |
| KB-2 | 录取分数线 | 全国 31 省份 × 3 年（2023-2025） | `data/knowledge-base/kb2-scores-*.md` |
| KB-3 | 专业百科 | 按学科分类的专业详细资料 | `data/knowledge-base/kb3-*.md` |
| KB-4 | 院校研究 | 院校独立报告 | 爬取脚本生成 |
| KB-5 | 就业数据 | 各专业就业率/薪资 | 爬取脚本生成 |
| KB-6 | 张雪峰金句 | 精选语录 | `data/knowledge-base/kb6-zhangxuefeng-quotes.md` |

## 数据文件

- `data/本科专业目录_2025.csv` — 教育部专业目录，839 条本科专业（CSV 编码 UTF-8 BOM，列：学科门类代码,学科门类,专业类代码,专业类,专业代码,专业名称,备注）
- `高等院校名单.csv` — 全国高等学校名单（列：序号,学校名称,学校标识码,主管部门,所在地,办学层次,备注）— 院校评估脚本的数据源
- `data/专业评估报告/` — 专业深度研究报告（`{专业代码}_{专业名称}.md`），含 `_progress_*.json` 进度文件
- `data/专业评估报告_json_v2/` — 专业报告结构化 JSON（773 条，4 层结构，完整保留原文）
- `data/大学评估报告/` — 院校评估报告（`{大学名称}.md`），含 `_progress_*.json` / `_progress_gemini_*.json` 进度文件
- `data/大学评估报告_json_v2/` — 院校报告结构化 JSON（956 条，4 层结构，完整保留原文）
- `data/knowledge-base/` — Dify 知识库源文件
- `data/test-runs/` — 手动测试记录
- `data/_import_scores.sql` — 分数线 SQL 导入文件（~14MB，由 generate_score_sql.py 生成）
- `scripts/db_schema.sql` — 报告数据库 Schema（PostgreSQL，159 服务器 gaokao_db）

## 核心文档索引

| 文档 | 说明 |
|------|------|
| `docs/superpowers/specs/2026-04-14-gaokao-zhiyuan-mvp-prd.md` | MVP PRD v3.0（四大模块设计，免费/付费分层） |
| `docs/superpowers/specs/2026-04-01-gaokao-zhiyuan-design.md` | 技术设计（微信云开发架构、数据模型） |
| `docs/superpowers/specs/2026-04-13-dify-agent-design.md` | Dify Agent 设计（Workflow、知识库、提示词评估） |
| `docs/superpowers/specs/2026-04-27-mvp-chat-design.md` | MVP 对话页设计 |
| `docs/superpowers/specs/2026-05-10-comprehensive-report-design.md` | 综合志愿报告设计（五环问卷 + 报告生成） |
| `docs/superpowers/plans/2026-04-27-mvp-chat.md` | MVP 对话页实施计划 |
| `docs/okr-plan.md` | 6 周 OKR 实施计划（W1-W6） |
| `docs/roadmap/00-overview.md` | 开发路线图总览（11 个阶段） |
| `docs/dify/agent-config-v1.md` | Dify Agent 配置文档 |
| `docs/testing/` | 测试报告（phase1-3）和 prompt tuning 指南 |
| `docs/design/user-profile-tracking.md` | 用户画像追踪设计（Phase 3.2） |

## 提示词与评估

- 专业评估：`跑专业的提示词-v2.txt`，要求 8 个模块完整输出
- 院校评估：`跑大学提示词-v4.txt`（最新，run_univ_eval.py），`跑大学提示词-v2.txt`（上一版）
- 评估智能体回答质量四维度打分：准确性（40%）、实用性（30%）、风格一致性（20%）、追问能力（10%）。满分 5 分，≥ 4.0 合格
- 准确性维度有编造数据则一票否决
- 标准测试集 20 题在 Dify Agent 设计文档第 4.2 节

## 服务器连接

```bash
ssh root@47.113.125.147   # proxy 后端（4C16G 阿里云），gaokao-proxy 运行于此
ssh ubuntu@159.75.110.157  # Dify 服务器（腾讯云），PostgreSQL + Flask API 也在此
```

Dify 控制台：`http://159.75.110.157:8080`。插件仅保留 deepseek + zhipuai。

注意：`root@47.113.125.147` 使用 `/Users/MarkHuang/Downloads/mark123-.pem` 可登录。`ubuntu@159.75.110.157` 使用 `/Users/MarkHuang/.ssh/gaokao-new_ed25519` 可登录；2026-05-14 已用该 key 确认 Dify Docker 栈和 `gaokao-api` 容器运行。

## 报告生成功能

```bash
# 综合志愿报告（小程序 → gaokao-proxy → DeepSeek API）
POST /api/report/generate  # 生成 HTML 报告，返回可分享链接
GET  /reports/:filename    # 静态托管生成的报告文件
```

部署注意：该接口已确认在 `47.113.125.147` 的 `/opt/gaokao-proxy` 内部和公网 IP 路由上可用。修改小程序报告页前，先用 `curl -X POST "$VITE_API_BASE/api/report/generate"` 验证公网目标是否已返回非 404。

报告生成使用 `lib/report-builder.js`，数据源：
- 个人信息（`profile`）：省份、科目、分数、位次
- 问卷答案（`questionnaire`）：五环 22 题
- 对话历史：通过 `conversationId` 调 Dify API 拉取
- 专业/院校报告：从 `MAJOR_REPORTS_DIR` / `UNIV_REPORTS_DIR` 匹配读取

## Python 依赖

大部分脚本只用标准库。例外：

| 包 | 使用脚本 |
|----|---------|
| `requests` | `upload_to_dify.py`、`crawl_kb4_kb5.py`、`run_univ_eval_gemini.py` |
| `psycopg2` | `import_scores_to_pg.py`、`generate_score_sql.py`、`gaokao_api.py` |
| `flask`, `flask-cors` | `gaokao_api.py` |

## Node.js 依赖（gaokao-proxy）

| 包 | 用途 |
|----|------|
| `express` | Web 服务器 |
| `cors` | 跨域支持 |
| `dotenv` | 环境变量 |
| `ioredis` | Redis 客户端（报告生成冷却） |
| `@google/generative-ai` | Gemini API（报告生成备选） |
| `pg` | PostgreSQL 客户端（报告数据查询） |

## 注意事项

- `run_univ_eval.py` 通过 `claude -p` CLI 生成，需 Claude Code 已安装且配置 open-websearch MCP。**必须在终端直接运行，不能在 Claude Code 会话中嵌套调用**（MCP 工具会冲突）
- Gemini 版院校评估需 `GEMINI_API_KEY` 环境变量
- 爬取脚本使用 `ssl._create_unverified_context()` 跳过 SSL 验证（掌上高考 API 限制）
- `run_major_eval.py` 每条报告自带 5 秒延迟，避免 API 限流
- 历史遗留脚本（`run_edu_eval.py`、`run_edu_eval_v2.py`、`run_edu_majors.py`、`run_law_majors.py`）为早期单门类版本，已归档到 `scripts_archive/`
- 历史遗留院校评估脚本（`run_univ_eval.py`、`run_univ_eval_cli.py`、`run_univ_eval_claude.py`、`run_univ_eval_gemini.py`）已归档到 `scripts_archive/`，当前主力为 `run_univ_eval_gemini_cli.py`
- 历史遗留爬取脚本（`crawl_scores.py` v1-v4、`crawl_scores.sh`）已被 `crawl_scores_v5.py` 替代
- 历史遗留上传脚本（`upload_kb1_to_dify.py`、`upload_kb1_v2.py`、`upload_kb2_to_dify.py`）已被 `upload_to_dify.py` 替代

## 文档维护

本文件是项目知识的权威索引。以下操作触发更新：

| 触发条件 | 需要更新的内容 |
|---------|--------------|
| 新增 Python 脚本到根目录 | 关键脚本章节 + Python 依赖表 |
| 新增知识库文件 | 知识库结构表 |
| 新增 docs/ 下的核心文档 | 核心文档索引 |
| 新增小程序页面/组件 | 技术架构章节 |
| 新增 proxy API 端点 | 技术架构 + 代理服务器章节 |
| 修改技术架构（服务器/框架/模型） | 技术架构 + 服务器连接 |
| 项目阶段变更 | 项目概述中的阶段描述 |
| 新增数据目录或数据源 | 数据文件章节 |

> **原则**：CLAUDE.md 记录"需要跨文件理解"的架构决策和运行时信息。单文件可发现的细节（函数列表、文件内容）不记录。进度数字用约数，精确数据由脚本 `--status` 提供。
