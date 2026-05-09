# Home Student Profile Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the mini program home page around an auto-saved student profile card and pass that profile into chat requests.

**Architecture:** Store the student profile in `gaokao-miniprogram/src/utils/storage.js`, render/edit it directly on `pages/index/index.vue`, pass sanitized profile inputs through `api/dify.js`, and forward them unchanged from `gaokao-proxy/server.js` to Dify.

**Tech Stack:** UniApp Vue 3, local `uni` storage, Express proxy, Python unittest with Node snippets.

---

## File Map

- Modify `gaokao-miniprogram/src/utils/storage.js`: add profile persistence, normalization, completeness check, and Dify input builder.
- Modify `gaokao-miniprogram/src/api/dify.js`: accept optional `inputs` in stream and blocking requests.
- Modify `gaokao-miniprogram/src/pages/chat/chat.vue`: load saved profile inputs and pass them into streaming chat.
- Modify `gaokao-proxy/server.js`: read `inputs` from request body and forward to Dify.
- Modify `gaokao-miniprogram/src/pages/index/index.vue`: replace the old entry layout with the student profile card.
- Add `tests/test_profile_storage_and_inputs.py`: lock storage and input forwarding behavior.

## Tasks

- [x] Add failing profile storage and inputs tests.
- [x] Implement profile storage helpers.
- [x] Add Dify inputs passthrough in frontend API and proxy.
- [x] Redesign homepage with the profile card and auto-save behavior.
- [x] Run targeted Python/Node regression tests.
- [x] Run mini program build if dependencies are available.
