# Repository Guidelines

## Project Structure & Module Organization

This repository supports the “峰哥咨询参考” Gaokao advising MVP. Root-level Python scripts such as `run_major_eval.py`, `run_univ_eval.py`, and `check_reports.py` generate and validate research reports. Source data, generated reports, import scripts, and Dify knowledge-base Markdown live under `data/`; key outputs include `data/专业评估报告/` and `data/knowledge-base/`. The UniApp WeChat mini program is in `gaokao-miniprogram/src/`. The local Dify proxy service is in `gaokao-proxy/`. Specs and plans are in `docs/`; regression tests are in `tests/`.

## Build, Test, and Development Commands

- `python3 run_major_eval.py --status`: show major-report progress.
- `python3 run_major_eval.py 06 --limit 3`: run a small major-report batch for testing.
- `python3 check_reports.py --min-chars 3000`: validate generated major reports.
- `python3 -m unittest discover tests`: run repository regression tests.
- `cd gaokao-miniprogram && npm run dev:mp-weixin`: start UniApp WeChat mini program development build.
- `cd gaokao-miniprogram && npm run build:mp-weixin`: create the WeChat mini program production build.
- `cd gaokao-proxy && npm run dev`: run the proxy with Node watch mode.

## Live Service Reality Checks

As of 2026-05-14, the current deployed chain is split across two active servers:

- Dify, Dify PostgreSQL/Redis/vector stack, and `gaokao-api` are on `159.75.110.157`.
- `gaokao-proxy`, mini-program public API routes, report generation, and static report hosting are on `47.113.125.147`.
- `8.135.37.159` is historical only. Do not use it as the current Dify host, proxy host, report host, or mini-program API base.

Current source-of-truth doc: `docs/deployment/current-live-chain.md`.
Archived stale migration docs: `docs/archive/2026-05-stale-migration/`.

Mini program:

- `gaokao-miniprogram/.env` should use `VITE_API_BASE=http://47.113.125.147`.
- Do not point `VITE_API_BASE` at `159.75.110.157`; 159 is the Dify/data server, not the mini-program gateway.

47 `gaokao-proxy` verified facts:

- `GET http://47.113.125.147/api/health` returns `200 {"status":"ok"}`.
- `POST http://47.113.125.147/api/chat` returns Dify `advanced-chat` output through the proxy.
- `POST http://47.113.125.147/api/report/generate` returns a URL like `http://47.113.125.147/reports/<file>.html`.
- `GET http://47.113.125.147/reports/<file>.html` returns generated HTML.
- `root@47.113.125.147` is reachable with `/Users/MarkHuang/Downloads/mark123-.pem`.
- On 47, `/opt/gaokao-proxy/.env` includes `DIFY_API_URL=http://159.75.110.157`, `PORT=3001`, and `REPORT_BASE_URL=http://47.113.125.147`.
- PM2 process `gaokao-proxy` runs `/opt/gaokao-proxy/server.js`; Nginx routes `/api/chat`, `/api/report`, and `/reports` to `127.0.0.1:3001`.

159 Dify/data verified facts:

- `curl -I http://159.75.110.157/v1` returns `X-Version: 1.13.3` and `X-Env: PRODUCTION`.
- `ssh -i /Users/MarkHuang/.ssh/gaokao-new_ed25519 ubuntu@159.75.110.157` works.
- Docker containers on 159 include Dify `docker-nginx-1` exposing `8080->80`, healthy `docker-api-1`, Redis, Postgres, pgvector, sandbox, plugin daemon, and `gaokao-api` exposing `5001->5000`.
- `gaokao-api` health is verified on 159 itself at `http://127.0.0.1:5001/api/health` with `{"records":35978,"status":"ok"}`.
- If score API calls from 47 fail, treat `SCORE_API_URL=http://159.75.110.157:5000` as suspect. SSH verification showed `gaokao-api` maps `5001->5000`, while public checks to both `:5000` and `:5001` did not return healthy responses from this environment.

When debugging "生成失败 / 服务暂时不可用" on the report page, verify 47 first. When debugging Dify workflow, model, plugin, or knowledge-base behavior, verify 159 first.

## Coding Style & Naming Conventions

Use Python 3 with standard-library solutions where practical. Keep scripts executable from the repository root and prefer `pathlib.Path`. Python functions and variables use `snake_case`; constants use `UPPER_SNAKE_CASE`. Vue/JavaScript code uses two-space indentation, Composition API patterns, and descriptive names such as `chat.vue` and `dify.js`. Generated report filenames should follow `{专业代码}_{专业名称}.md`.

## Testing Guidelines

Tests use Python `unittest`. Name files `tests/test_*.py` and test classes after the behavior being protected. Add regression coverage when changing report quality gates, secret handling, SSE parsing, or proxy streaming. Some tests execute Node snippets, so install `gaokao-miniprogram/` dependencies before running the full suite.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commits, for example `feat: implement chat page with SSE streaming and history` and `fix: add 30s timeout to Dify blocking request`. Keep commits scoped and imperative. Pull requests should include a concise summary, test commands run, linked issue or plan document when relevant, and screenshots for mini program UI changes. Do not include secrets, generated dependency folders, or large transient files from `tmp/`.

## Security & Configuration Tips

Copy `.env.example` files instead of committing local `.env` changes. Keep Dify, Gemini, database, and server credentials in environment variables. Treat generated data as reproducible output; document unusual manual edits in the PR description.
