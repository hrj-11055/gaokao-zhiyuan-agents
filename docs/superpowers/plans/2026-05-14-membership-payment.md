# Membership Payment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the confirmed “我的” membership center, ¥29 unlock, invite-based unlock, WeChat identity, payment order scaffolding, and backend report paywall.

**Architecture:** Add a focused commerce module to `gaokao-proxy` backed by SQLite, keep WeChat login/payment concerns behind small helper modules, and enforce membership in the report endpoint. Add a miniprogram membership API/store, refactor `profile.vue` into the membership center, and make `report.vue` show a paid lock before report generation.

**Tech Stack:** Node.js Express, better-sqlite3, Node crypto, UniApp/Vue 3, Pinia, Python unittest driving Node snippets.

---

### Task 1: Backend Commerce Store

**Files:**
- Create: `gaokao-proxy/lib/commerce-store.js`
- Test: `tests/test_commerce_store.py`
- Modify: `gaokao-proxy/package.json`

- [ ] **Step 1: Add dependency declaration**

Add `better-sqlite3` to `gaokao-proxy/package.json` dependencies.

- [ ] **Step 2: Write failing store tests**

Create `tests/test_commerce_store.py` with Node snippet tests for:
- schema initialization
- invitee profile completion increments inviter effective count once
- 3 effective invites unlock membership
- paid order unlocks membership

Run: `python3 -m unittest tests/test_commerce_store.py`

Expected: FAIL because `gaokao-proxy/lib/commerce-store.js` does not exist.

- [ ] **Step 3: Implement store**

Create `gaokao-proxy/lib/commerce-store.js` with:
- `createCommerceStore({ dbPath, now, idFactory, inviteRequired, priceCents })`
- `upsertWechatUser({ openid, unionid, inviterId })`
- `completeProfile(userId)`
- `getMembershipStatus(userId)`
- `activateMembership(userId, source)`
- `createPaymentOrder(userId)`
- `markOrderPaid(outTradeNo, transactionId, rawNotify)`
- `getOrder(orderId)`
- `close()`

Use `better-sqlite3` transactions for invite completion and order payment.

- [ ] **Step 4: Verify store tests**

Run: `python3 -m unittest tests/test_commerce_store.py`

Expected: PASS.

### Task 2: Backend Auth, Payment Helpers, and Routes

**Files:**
- Create: `gaokao-proxy/lib/session-token.js`
- Create: `gaokao-proxy/lib/wechat-auth.js`
- Create: `gaokao-proxy/lib/wechat-pay.js`
- Modify: `gaokao-proxy/server.js`
- Modify: `gaokao-proxy/.env.example`
- Test: `tests/test_membership_server_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_membership_server_contracts.py` checking server/helper source contracts:
- exports exist for session token helpers
- `/api/auth/wechat-login`, `/api/membership/status`, `/api/profile/complete`, `/api/payment/create`, `/api/payment/order/:orderId`, `/api/payment/wechat/notify` routes exist
- `/api/report/generate` returns `MEMBERSHIP_REQUIRED` when membership is absent
- `.env.example` documents commerce and WeChat payment env vars

Run: `python3 -m unittest tests/test_membership_server_contracts.py`

Expected: FAIL because routes/helpers do not exist.

- [ ] **Step 2: Implement helpers**

Implement:
- HMAC session token signing and verification in `session-token.js`
- `exchangeCodeForSession()` in `wechat-auth.js`
- JSAPI order request signing, frontend pay param signing, config validation, and notify skeleton in `wechat-pay.js`

- [ ] **Step 3: Wire routes**

Modify `server.js` to:
- create a commerce store
- add optional auth middleware for bearer tokens
- add membership/auth/payment routes
- call `requireMembershipForReports` before report generation
- keep existing report cooldown and generation behavior after membership passes

- [ ] **Step 4: Verify contract tests**

Run: `python3 -m unittest tests/test_membership_server_contracts.py`

Expected: PASS.

### Task 3: Miniprogram Membership API and Store

**Files:**
- Create: `gaokao-miniprogram/src/api/membership.js`
- Create: `gaokao-miniprogram/src/stores/membership.js`
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`
- Test: `tests/test_membership_miniprogram_contracts.py`

- [ ] **Step 1: Write failing frontend contract tests**

Create `tests/test_membership_miniprogram_contracts.py` checking:
- membership API functions exist
- membership Pinia store tracks status, invite count, session token, payment flow
- index page captures `inviterId`
- profile completion calls membership store after required profile fields exist

Run: `python3 -m unittest tests/test_membership_miniprogram_contracts.py`

Expected: FAIL because files/functions are missing.

- [ ] **Step 2: Implement API/store**

Implement login, status, profile complete, payment create, order query, and token persistence. Use `wx.login`/`uni.login` where available and degrade cleanly in non-Weixin builds.

- [ ] **Step 3: Wire home profile completion**

Modify `index.vue` so saving a complete profile calls `membershipStore.markProfileCompleted(profile)`.

- [ ] **Step 4: Verify frontend contracts**

Run: `python3 -m unittest tests/test_membership_miniprogram_contracts.py`

Expected: PASS.

### Task 4: Refactor Profile and Report Pages

**Files:**
- Modify: `gaokao-miniprogram/src/pages/profile/profile.vue`
- Modify: `gaokao-miniprogram/src/pages/report/report.vue`
- Test: `tests/test_membership_pages.py`

- [ ] **Step 1: Write failing page tests**

Create `tests/test_membership_pages.py` checking:
- profile page contains ¥29 membership center copy, invite progress, benefits, and payment CTA
- report page contains locked membership state before generation
- report generation includes auth token header and handles `MEMBERSHIP_REQUIRED`

Run: `python3 -m unittest tests/test_membership_pages.py`

Expected: FAIL until pages are refactored.

- [ ] **Step 2: Refactor profile page**

Update `profile.vue` to render:
- header
- membership card
- invite card
- benefit grid
- paid report entry
- assessment records
- order/settings area

- [ ] **Step 3: Refactor report page**

Update `report.vue` to load membership status first, show lock UI when inactive, support pay/unlock flow, then generate only when active.

- [ ] **Step 4: Verify page tests**

Run: `python3 -m unittest tests/test_membership_pages.py`

Expected: PASS.

### Task 5: Build and Regression Verification

**Files:**
- Modify as needed only for failures.

- [ ] **Step 1: Install backend dependency**

Run: `cd gaokao-proxy && npm install`

Expected: `package-lock.json` includes `better-sqlite3`.

- [ ] **Step 2: Run focused tests**

Run:
- `python3 -m unittest tests/test_commerce_store.py tests/test_membership_server_contracts.py tests/test_membership_miniprogram_contracts.py tests/test_membership_pages.py`
- `python3 -m unittest tests/test_security_and_chat_regressions.py tests/test_report_builder.py`

Expected: PASS.

- [ ] **Step 3: Build miniprogram**

Run: `cd gaokao-miniprogram && npm run build:mp-weixin`

Expected: build succeeds.

- [ ] **Step 4: Summarize deployment blockers**

Document that real WeChat payment requires `WECHAT_*` credentials, HTTPS `WECHAT_PAY_NOTIFY_URL`, and deployment of the SQLite DB path on `47.113.125.147`.
