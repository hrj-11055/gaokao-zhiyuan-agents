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

## Coding Style & Naming Conventions

Use Python 3 with standard-library solutions where practical. Keep scripts executable from the repository root and prefer `pathlib.Path`. Python functions and variables use `snake_case`; constants use `UPPER_SNAKE_CASE`. Vue/JavaScript code uses two-space indentation, Composition API patterns, and descriptive names such as `chat.vue` and `dify.js`. Generated report filenames should follow `{专业代码}_{专业名称}.md`.

## Testing Guidelines

Tests use Python `unittest`. Name files `tests/test_*.py` and test classes after the behavior being protected. Add regression coverage when changing report quality gates, secret handling, SSE parsing, or proxy streaming. Some tests execute Node snippets, so install `gaokao-miniprogram/` dependencies before running the full suite.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commits, for example `feat: implement chat page with SSE streaming and history` and `fix: add 30s timeout to Dify blocking request`. Keep commits scoped and imperative. Pull requests should include a concise summary, test commands run, linked issue or plan document when relevant, and screenshots for mini program UI changes. Do not include secrets, generated dependency folders, or large transient files from `tmp/`.

## Security & Configuration Tips

Copy `.env.example` files instead of committing local `.env` changes. Keep Dify, Gemini, database, and server credentials in environment variables. Treat generated data as reproducible output; document unusual manual edits in the PR description.
