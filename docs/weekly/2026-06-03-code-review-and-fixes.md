# 周报：代码审查 + 报告生成失败兜底修复

> 日期：2026-06-03
> 分支：`codex/vip-report-unlock`

## 本周完成

### 1. 全量代码审查（3 角度 × 6 候选 → 验证）

对 `codex/vip-report-unlock` 分支（51 文件，+5870/-2453 行）做高力度代码审查：
- **Angle A**：逐行 diff 扫描（null 解引用、竞态、未 await）
- **Angle B**：删除行为审计（被移除的守卫、校验、超时）
- **Angle C**：跨文件追踪（函数签名变更、调用方兼容性）

独立验证后确认 **5 个有效缺陷**，按严重性：

| # | 严重性 | 问题 | 文件 |
|---|--------|------|------|
| 1 | 高 | DeepSeek API 返回空 choices 时崩溃（无 null 检查） | `report-builder.js:84` |
| 2 | 高 | 非缓存路径进度条冻结 0% 达 1-3 分钟，与缓存命中 5.5s 流畅动画形成 UX 断崖 | `report.vue` |
| 3 | 中 | `countUserMessages()` 用 `Object.values()` 遍历扁平对象，碰巧工作但脆弱 | `useHomeProgress.js:40` |
| 4 | 中 | pregen 缓存命中后"重新生成"触发 429 冷却，显示客服弹窗而非友好提示 | `report.vue` |
| 5 | 低 | `buildFinalHtml` 内部调用做了一次冗余 `JSON.stringify → JSON.parse` | `report-builder.js:51` |

额外发现：客户端超时 180s vs 服务端默认 600s，客户端提前断开。

### 2. 修复与测试（6 项修复 + 8 个新测试）

**修复清单：**

1. **DeepSeek 空 choices null 检查** — `data?.choices?.[0]?.message?.content`，空内容抛明确错误含 `finish_reason`
2. **正常生成路径进度动画** — 新增 `startSlowProgress()` 函数，7 阶段慢速动画（0→88%），与 pregen 缓存路径体验对齐
3. **429 冷却友好处理** — catch 中检测 `err.statusCode === 429`，toast 提示"请稍后再试"并恢复 latestReport
4. **客户端超时对齐** — `api/report.js` timeout 180s → 300s
5. **countUserMessages 修复** — 从 `Object.values(history)` 改为 `history.messages` 直接取值
6. **消除双重 JSON parse** — `buildFinalHtml` 直接接受对象，同时保留字符串向后兼容；增加 null/空对象降级兜底

**测试结果：155 passed，0 failed**

新增测试：
- `test_build_final_html_accepts_parsed_object_directly` — 对象和字符串两种输入
- `test_request_deep_seek_json_rejects_empty_choices` — null 检查守卫
- `test_report_generation_timeout_matches_real_wait_time` — 客户端 300s 对齐
- `test_normal_generation_path_has_progress_animation` — 慢进度条存在性
- `test_count_user_messages_uses_messages_array_directly` — 不再 Object.values
- `test_report_page_handles_429_cooldown_gracefully` — 429 检测

### 3. 服务器同步与差异验证

**部署操作：**
- scp 同步 `report-builder.js` 到 `47.113.125.147:/opt/gaokao-proxy/`
- 更新 `.env`：`REPORT_GENERATION_TIMEOUT_MS` 170000 → 300000
- `pm2 restart gaokao-proxy --update-env`

**本地 vs 服务器差异测试（服务器 9/9 通过）：**

| 场景 | 结果 |
|------|------|
| buildFinalHtml(对象/字符串/null/空) | 全部 PASS + 降级兜底 |
| 公网 health/stats/auth | 全部正常 |
| PostgreSQL 连接 | 777 专业 + 1361 院校 |
| PM2 启动日志 | 无错误 |

**发现的服务器特殊状态：**
- Redis 未配置（`In-Memory Fallback`）→ PM2 重启后冷却 Map 清空
- 旧日志有 `DeepSeek generation failed: aborted due to timeout` — 正是本次修复的 170s 超时问题

## 报告生成失败场景兜底清单

| 失败路径 | 原行为 | 修复后行为 |
|----------|--------|-----------|
| DeepSeek 返回空 choices | TypeError 崩溃，通用错误 | 明确错误 "DeepSeek 返回空内容 (finish_reason: ...)" |
| DeepSeek 超时 (>170s) | 服务器 abort，客户端也超时 | 服务端 300s + 客户端 300s 对齐 |
| JSON 解析失败 | buildFinalHtml 内降级 | 增加 null/空对象/非法 JSON 统一降级页面 |
| pregen→重新生成→429 | 客服弹窗 | toast "请稍后再试" + 恢复当前报告 |
| 正常生成进度条 | 冻结 0%，1-3 分钟 | 7 阶段慢速动画，最高 88% |

## 下一步

- [ ] 前端改动（report.vue / useHomeProgress.js / index.vue）编译后通过微信开发者工具实测
- [ ] 确认 Redis 配置后冷却机制是否需要持久化
- [ ] 合并 `codex/vip-report-unlock` 到 main
