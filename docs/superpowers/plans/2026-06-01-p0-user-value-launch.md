# P0 User Value Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the pre-launch mini program clearly deliver the paid user value: complete report, school/major judgment, risk warnings, next actions, concrete benefits, invitation rules, and support fallback.

**Architecture:** Keep the change inside the existing UniApp mini program and deployment docs. Reuse `useHomeProgress`, `membershipStore`, local profile storage, and existing report/payment APIs; add only lightweight UI state and copy, not new backend capabilities.

**Tech Stack:** Vue 3 Composition API, UniApp WeChat mini program, Pinia stores, Python `unittest`, existing deployment Markdown docs.

---

### Task 1: Write Launch Value Document

**Files:**
- Create: `docs/deployment/p0-user-value-launch-plan.md`
- Modify: `docs/deployment/customer-support-playbook.md`

- [x] **Step 1: Create the launch document**

Add a Markdown document covering: 10 representative personas, paid-result quality gates, four-step homepage acceptance, concrete `¥19.9` benefit language, invitation validity rules, trust signals, customer support fallback, and evidence required before release.

- [x] **Step 2: Extend customer support playbook**

Add sections for invitation count disputes, paid report not worth the price, and refund/abnormal payment handling. Include the evidence support must request and the final user-facing promise.

### Task 2: Fix Shared Home Progress Semantics

**Files:**
- Modify: `gaokao-miniprogram/src/composables/useHomeProgress.js`
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

- [x] **Step 1: Track actual report completion**

Import `loadReport`, keep a `report` ref, refresh it in `refresh()`, expose `reportDone = computed(() => Boolean(report.value?.url))`, and count step 4 as done only when a real report URL exists.

- [x] **Step 2: Stop treating membership as generated report**

In `index.vue`, use `statusFor(4)` for step 4. Show `会员特权已解锁，一键生成` when membership is active but no report URL exists, and show report-done copy only when `reportDone` is true.

### Task 3: Restore Homepage Profile Completion

**Files:**
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

- [x] **Step 1: Add profile draft state**

Import `ref`, `onUnload`, `saveUserProfile`, `isProfileComplete`, and `QUESTIONNAIRE_REQUIRED_COUNT`. Add `draft`, `showProfileSheet`, `openProfileSheet()`, `closeProfileSheet()`, `selectCategory()`, and `saveProfileDraft()`.

- [x] **Step 2: Save profile and activate invitation counting**

In `saveProfileDraft()`, validate `isProfileComplete(draft.value)`, call `saveUserProfile(draft.value)`, call `refresh()`, call `membershipStore.syncProfile(profile.value)`, and call `membershipStore.markProfileCompleted()`.

- [x] **Step 3: Wire step 1 and profile page event**

Make step 1 open the profile sheet. Listen for `open-profile-sheet` on load and remove the listener on unload so the profile page “修改档案” action works.

### Task 4: Make Chat Input Respect Profile Gate

**Files:**
- Modify: `gaokao-miniprogram/src/pages/chat/chat.vue`

- [x] **Step 1: Add readiness computed**

Import `isProfileComplete`, add `const isProfileReady = computed(() => isProfileComplete(profile.value))`, and update `showWelcomeSuggestions` to `messages.value.length === 0 && isProfileReady.value`.

- [x] **Step 2: Add visible gate and disable input**

Show a profile gate when `!isProfileReady`, route the user back to the homepage profile sheet, disable the input with `:disabled="isStreaming || !isProfileReady"`, and do not activate quick questions before the profile is complete.

### Task 5: Align Report Page Prerequisites and Unlock Copy

**Files:**
- Modify: `gaokao-miniprogram/src/pages/report/report.vue`

- [x] **Step 1: Gate report generation on all four prerequisites**

Use `step1Done`, `step2Done`, and `allAssessmentsDone` from `useHomeProgress()`. Before generating, redirect missing profile to the homepage sheet, missing chat to the chat tab, and missing assessments to the assessment card flow.

- [x] **Step 2: Replace generic VIP copy with concrete benefits**

In the unlock sheet, list complete志愿报告、院校/专业深度阅读、PDF 下载额度、客服兜底. Include invitation progress and the rule: a new user must enter via share and complete province/category/score.

- [x] **Step 3: Add support fallback for payment and generation errors**

Import `CUSTOMER_WECHAT_ID`; when payment or generation fails, show a modal that tells the user what happened and offers to copy the support WeChat ID.

### Task 6: Align Profile Membership Center

**Files:**
- Modify: `gaokao-miniprogram/src/pages/profile/profile.vue`

- [x] **Step 1: Add benefit bullets**

Keep existing membership center structure, but add concrete benefit rows: complete report, deep school/major reading, PDF quota, and payment support fallback.

- [x] **Step 2: Add invitation rule clarity**

Show `有效邀请：新用户 + 完成省份、科类、分数基础资料` and current invite progress near the share button.

### Task 7: Verify

**Files:**
- Test: `tests/test_membership_pages.py`
- Test: `tests/test_membership_miniprogram_contracts.py`
- Test: `tests/test_miniprogram_report_flow.py`
- Test: `tests/test_profile_storage_and_inputs.py`
- Test: `tests/test_questionnaire_flow.py`

- [x] **Step 1: Run focused regression tests**

Run:

```bash
python3 -m unittest tests.test_membership_pages tests.test_membership_miniprogram_contracts tests.test_miniprogram_report_flow tests.test_profile_storage_and_inputs tests.test_questionnaire_flow
```

Expected: focused tests pass, or any remaining failure is unrelated and documented.

- [x] **Step 2: Build mini program**

Run:

```bash
cd gaokao-miniprogram && npm run build:mp-weixin
```

Expected: build succeeds; Sass legacy API warnings are acceptable if unchanged from previous builds.

