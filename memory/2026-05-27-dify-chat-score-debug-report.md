# 2026-05-27 Dify Chat Score Debug Report

## Symptom

- `http://159.75.110.157:8080` user-facing open failed.
- Chatflow documentation required core profile gating, score tools, and post-answer follow-up, but live behavior did not fully match.
- Complete score questions could still produce school recommendations not present in the backend score API result.
- Query text such as `四川530分理科能报什么？` was not reliably converted into province/category/score inputs.

## Root Cause

1. Dify published workflow for `张雪峰高考志愿填报助手` has only Start, knowledge retrieval, LLM, and answer nodes. It does not contain IF/ELSE gates or `score_match` / `school_scores` tools.
2. The proxy had started injecting backend score context, but still let Dify generate factual score-line answers. Dify retrieval could mix unrelated KB snippets into the response.
3. `buildProfileGateAnswer` was gating second-layer personal profile fields before answering, contradicting `docs/dify/agent-config-v1.md`.
4. The proxy only trusted `inputs`; it did not extract province/category/score/rank facts from the user's current query.
5. `gaokao-api` `score_match` returned school score ranges but not `min_rank`, weakening evidence in direct answers.

## Fix

- `gaokao-proxy/lib/profile-followup-gate.js`
  - Replaced broad keyword intent matching with stricter recommendation patterns.
  - Added query extraction for province, category (`理科 -> 物理类`, `文科 -> 历史类`), score, and rank.
  - Changed core gate to block only missing province/category/score.
  - Added post-answer follow-up priority with rank first, then personal profile fields.

- `gaokao-proxy/server.js`
  - Merges extracted query facts into final Dify inputs.
  - Handles score recommendation and school score lookup directly from `score-api` with `metadata.proxy_direct=true`.
  - Keeps Dify for general consultation and non-score factual questions.

- `gaokao-api/gaokao_api_remote.py` and `gaokao-api/app.py`
  - Added `min_rank` to `score_match` school summaries.

- `docs/dify/agent-config-v1.md`
  - Clarified that rank is not a hard gate and should be asked after answering when missing.

## Live Verification

- `http://159.75.110.157:8080`: empty reply, not a reliable user-facing entrance.
- `http://159.75.110.157/v1`: Dify responds with `X-Version: 1.13.3`.
- Dify published workflow model: `deepseek-v4-pro`, provider `langgenius/deepseek/deepseek`, max tokens 900, temperature 0.2.
- Dify draft workflow model: `deepseek-v4-pro`, max tokens 2048, temperature 0.8.
- Published Dify workflow still has no IF/ELSE or score tools, so the proxy now owns factual score routing.
- `https://gaokao.aicoming.cn/api/health`: OK.
- `http://159.75.110.157/score-api/api/health`: OK, 894681 records.
- `score_match` now returns `min_rank`.

## 10 Prompt Acceptance

All 10 live prompts passed after deployment:

1. `你好，我想咨询高考志愿` -> Dify general consultation, no proxy gate.
2. `我考了580分，能上什么学校？` -> `profile_gate:province`.
3. `广东考生，580分能上什么学校？` -> `profile_gate:category`.
4. `广东物理类能上什么学校？` -> `profile_gate:score`.
5. `广东600分物理类能上什么学校？` -> `proxy_direct:score_match`, includes backend schools and ranks.
6. `四川530分理科能报什么？` -> query extraction maps to `四川/物理类/530`, `proxy_direct:score_match`; no backend schools returned for 2024.
7. `广东历史类580分推荐学校` -> `proxy_direct:score_match`.
8. `中山大学在广东录取线是多少？` -> `proxy_direct:score_lookup`.
9. `中山大学在广东物理类录取线是多少？我600分有机会吗` -> `proxy_direct:score_lookup`, includes score gap judgment.
10. `张雪峰怎么看计算机专业` -> Dify general major consultation, no proxy gate/direct score route.

## Regression Tests

- `python3 -m unittest tests.test_profile_storage_and_inputs tests.test_security_and_chat_regressions tests.test_score_api_route_contracts`: 28 tests OK.
- `python3 -m unittest discover tests`: 121 tests OK.

## Status

DONE
