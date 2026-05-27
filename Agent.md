# Agent Notes

Use `AGENTS.md` as the canonical agent instruction file. This file exists because some prompts refer to `Agent.md`.

Current live-service source of truth:

- Dify / PostgreSQL / gaokao-api: `159.75.110.157`
- gaokao-proxy / mini-program API base / report generation: `47.113.125.147`
- Archived old migration docs: `docs/archive/2026-05-stale-migration/`
- Current chain doc: `docs/deployment/current-live-chain.md`

## WeChat Mini Program Development Rule
- **Dev Mode (`npm run dev:mp-weixin`)**: ALWAYS use this mode for coding, UI iteration, and active development. It enables hot reloading (real-time frontend changes) and Source Map debugging.
- **Build Mode (`npm run build:mp-weixin`)**: ONLY use this for final production builds, uploading to WeChat, or release testing. It lacks file-watching and hot-reload.
