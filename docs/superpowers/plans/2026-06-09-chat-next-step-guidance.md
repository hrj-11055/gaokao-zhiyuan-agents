# Chat Next-Step Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace low-value chat suggestions with decision-grade prompts and guide users from a completed long AI answer directly into the personality test.

**Architecture:** Keep profile-aware initial prompt generation in `profileFollowup.js`. Remove repeated post-answer question chips from `chat.vue` and add a local assessment-aware action card that appears only after a complete long AI response while MBTI remains unfinished.

**Tech Stack:** Vue 3 Composition API, UniApp, JavaScript, Python `unittest`

---

### Task 1: Protect the New Prompt and CTA Contracts

**Files:**
- Modify: `tests/test_profile_storage_and_inputs.py`
- Modify: `tests/test_security_and_chat_regressions.py`

- [ ] Add assertions that score-mode and planning-mode prompts contain decision, risk, route, and action language and exclude the removed low-value questions.
- [ ] Replace the old post-answer suggestion-panel assertions with assertions for the personality-test next-step card, long-answer threshold, truncation guard, assessment completion guard, and `/pages/mbti/mbti` navigation.
- [ ] Run `python3 -m unittest tests.test_profile_storage_and_inputs tests.test_security_and_chat_regressions` and confirm the new assertions fail before implementation.

### Task 2: Upgrade Initial Questions

**Files:**
- Modify: `gaokao-miniprogram/src/pages/chat/profileFollowup.js`

- [ ] Replace the current score-mode questions with four profile-aware questions about opportunity/risk, trade-off priority, multiple routes, and unsuitable popular majors.
- [ ] Replace the current planning-mode questions with four questions about professional-direction validation, real experiences, capability gaps, and staged action planning.
- [ ] Run `python3 -m unittest tests.test_profile_storage_and_inputs` and confirm the prompt-generation assertions pass.

### Task 3: Add the Post-Answer Personality-Test Action

**Files:**
- Modify: `gaokao-miniprogram/src/pages/chat/chat.vue`

- [ ] Load local assessment state on page show.
- [ ] Remove the repeated post-answer question list.
- [ ] Add a complete-long-answer predicate that rejects streaming, truncated, short, non-latest, and already-completed-MBTI states.
- [ ] Add the next-step action card and direct navigation to `/pages/mbti/mbti`.
- [ ] Run `python3 -m unittest tests.test_profile_storage_and_inputs tests.test_security_and_chat_regressions`.

### Task 4: Verify the Mini Program

**Files:**
- Verify only

- [ ] Run `cd gaokao-miniprogram && npm run build:mp-weixin`.
- [ ] Run `python3 -m unittest discover tests`.
- [ ] Review `git diff -- gaokao-miniprogram/src/pages/chat/chat.vue gaokao-miniprogram/src/pages/chat/profileFollowup.js tests/test_profile_storage_and_inputs.py tests/test_security_and_chat_regressions.py` to confirm the changes remain scoped.
