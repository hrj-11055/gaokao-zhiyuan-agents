# Day 1 迁移提示词（已归档）

> 状态：已归档，不再代表当前线上部署。
> 当前事实请以 `docs/deployment/current-live-chain.md` 和 `AGENTS.md` 为准。

旧提示词已经移动到：

- `docs/archive/2026-05-stale-migration/day1-migration-prompt.md`

不要再使用旧提示词中的 `8.135.37.159` 作为 Dify 当前服务器，也不要把 `159.75.110.157` 当作小程序 `VITE_API_BASE`。当前线上链路是：

- 小程序 `VITE_API_BASE=http://47.113.125.147`
- `47.113.125.147` 的 `gaokao-proxy` 通过 `DIFY_API_URL=http://159.75.110.157` 调 Dify
- Dify 控制台：`http://159.75.110.157:8080`

