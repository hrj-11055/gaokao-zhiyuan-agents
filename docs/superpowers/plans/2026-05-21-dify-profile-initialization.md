# Dify Profile Initialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the student's province, score, subject category, and optional rank on the backend, then use that profile as the default Dify conversation initialization context.

**Architecture:** The mini program keeps its existing local profile cache, but every complete profile is also synced to `gaokao-proxy`. Chat requests are normalized on the proxy by merging the stored server profile with the request `inputs`, so Dify receives stable `province`, `category`, `score`, and `rank` variables even when the frontend cache is stale. Dify workflow configuration is documented to treat those variables as trusted initialization context and only ask follow-up questions for fields that remain missing.

**Tech Stack:** UniApp/Vue mini program, Pinia stores, Express proxy, `better-sqlite3`, Python `unittest` regression tests, Node module smoke tests.

---

## File Structure

- Modify `gaokao-proxy/lib/commerce-store.js`: add `profile_json` storage on `users`, profile normalization, `saveProfile`, and `getProfile`.
- Modify `gaokao-proxy/server.js`: add `POST /api/profile` and `GET /api/profile`; merge server profile into `/api/chat` and `/api/chat/stream` Dify `inputs`.
- Modify `gaokao-miniprogram/src/api/membership.js`: add `saveUserProfileToServer` and `fetchUserProfileFromServer`.
- Modify `gaokao-miniprogram/src/stores/membership.js`: expose profile sync actions.
- Modify `gaokao-miniprogram/src/pages/index/index.vue`: sync complete profile payload to backend after local save.
- Modify `gaokao-miniprogram/src/pages/chat/profileFollowup.js`: define the one-question-at-a-time follow-up sequence for recommendation requests.
- Modify `gaokao-miniprogram/src/pages/chat/useChat.js`: pause recommendation requests until missing profile fields are collected one by one.
- Modify `gaokao-proxy/lib/profile-followup-gate.js`: add the same deterministic gate as a backend fallback before Dify.
- Modify `docs/dify/agent-config-v1.md`: document Start variables, information gate, and prompt rules for initialized student profile.
- Modify `tests/test_profile_storage_and_inputs.py`: add regression checks for server profile persistence, chat input merge, frontend API payload, and Dify docs.

## Task 1: Backend Profile Storage

**Files:**
- Modify: `tests/test_profile_storage_and_inputs.py`
- Modify: `gaokao-proxy/lib/commerce-store.js`

- [ ] **Step 1: Write the failing tests**

Add tests that create an in-memory commerce store, save a profile, verify normalization, and verify incomplete/invalid values are rejected.

Expected assertions:

```python
self.assertIn("saveProfile", text)
self.assertIn("getProfile", text)
self.assertIn("profile_json", text)
```

Add a Node behavior test that imports `createCommerceStore`, creates a user, calls `saveProfile(userId, { province: '广东', category: '物理类', score: '600', rank: '32000' })`, and expects:

```js
{
  province: '广东',
  category: '物理类',
  score: 600,
  rank: 32000,
  updatedAt: 1710000000000
}
```

- [ ] **Step 2: Run the tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: FAIL because `saveProfile`, `getProfile`, and `profile_json` do not exist.

- [ ] **Step 3: Implement backend profile storage**

Add `profile_json TEXT` to `users`, run an `ALTER TABLE` migration guarded by `PRAGMA table_info(users)`, and implement:

```js
function normalizeProfile(profile = {}, timestamp = now()) {
  const score = toIntOrEmpty(profile.score)
  const rank = toIntOrEmpty(profile.rank)
  return {
    province: typeof profile.province === 'string' ? profile.province.trim() : '',
    category: typeof profile.category === 'string' ? profile.category.trim() : '',
    score,
    rank,
    updatedAt: timestamp,
  }
}

function validateProfile(profile) {
  if (!profile.province) throw new Error('province is required')
  if (!['物理类', '历史类'].includes(profile.category)) throw new Error('category is invalid')
  if (typeof profile.score !== 'number' || profile.score < 0 || profile.score > 750) {
    throw new Error('score is invalid')
  }
}
```

Expose `saveProfile(userId, profile)` and `getProfile(userId)` from the store.

- [ ] **Step 4: Run the tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: PASS for the new backend storage tests, with any unrelated pre-existing failures handled before moving on.

## Task 2: Proxy Profile API and Dify Input Merge

**Files:**
- Modify: `tests/test_profile_storage_and_inputs.py`
- Modify: `gaokao-proxy/server.js`

- [ ] **Step 1: Write the failing tests**

Add text-level regression checks that `server.js` contains:

```text
app.post('/api/profile'
app.get('/api/profile'
mergeProfileInputs
const finalInputs = mergeProfileInputs
inputs: finalInputs
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: FAIL because the profile routes and merge helper are missing.

- [ ] **Step 3: Implement proxy routes and merge helper**

Add helper functions:

```js
function sanitizeProfileInputs(inputs = {}) {
  const clean = {}
  if (typeof inputs.province === 'string' && inputs.province.trim()) clean.province = inputs.province.trim()
  if (typeof inputs.category === 'string' && inputs.category.trim()) clean.category = inputs.category.trim()
  if (inputs.score !== undefined && inputs.score !== '') clean.score = String(Number(inputs.score))
  if (inputs.rank !== undefined && inputs.rank !== '') clean.rank = String(Number(inputs.rank))
  return clean
}

function buildProfileInputs(profile = {}) {
  const inputs = {}
  if (profile.province) inputs.province = profile.province
  if (profile.category) inputs.category = profile.category
  if (typeof profile.score === 'number') inputs.score = String(profile.score)
  if (typeof profile.rank === 'number' && profile.rank > 0) inputs.rank = String(profile.rank)
  return inputs
}

function mergeProfileInputs(userId, requestInputs = {}) {
  const serverProfile = userId ? commerceStore.getProfile(userId) : {}
  return {
    ...buildProfileInputs(serverProfile),
    ...sanitizeProfileInputs(requestInputs),
  }
}
```

Use `finalInputs` instead of raw `inputs` in both blocking and streaming Dify requests.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: PASS.

## Task 3: Mini Program Profile Sync

**Files:**
- Modify: `tests/test_profile_storage_and_inputs.py`
- Modify: `gaokao-miniprogram/src/api/membership.js`
- Modify: `gaokao-miniprogram/src/stores/membership.js`
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`

- [ ] **Step 1: Write the failing tests**

Add source checks for:

```text
saveUserProfileToServer
fetchUserProfileFromServer
syncProfile(profile)
membershipStore.syncProfile(profile.value)
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: FAIL because the frontend profile sync symbols are missing.

- [ ] **Step 3: Implement profile sync API and store action**

In `membership.js`, add:

```js
export function saveUserProfileToServer(profile, sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/profile',
    method: 'POST',
    data: { profile },
    token: sessionToken,
  })
}
```

In `stores/membership.js`, add:

```js
async syncProfile(profile) {
  await this.ensureLogin()
  const data = await saveUserProfileToServer(profile, this.sessionToken)
  this.applyStatus(data.membership || data)
  return data
}
```

In `index.vue`, call `membershipStore.syncProfile(profile.value)` after a complete profile is saved.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: PASS.

## Task 4: Dify Workflow Documentation

**Files:**
- Modify: `tests/test_profile_storage_and_inputs.py`
- Modify: `docs/dify/agent-config-v1.md`

- [ ] **Step 1: Write the failing tests**

Add checks that the Dify config document includes:

```text
Start 输入变量
province
category
score
rank
信息完整性闸门
禁止默认物理类
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: FAIL because the current doc does not describe the initialization gate.

- [ ] **Step 3: Update the Dify config document**

Document the required Start variables, the information completeness branch, and the prompt rule that initialized profile values are trusted unless the user explicitly updates them in chat.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: PASS.

## Task 5: Final Verification

**Files:**
- Verify changed files only.

- [ ] **Step 1: Run targeted Python tests**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests
```

Expected: PASS.

- [ ] **Step 2: Run proxy syntax check**

Run:

```bash
cd gaokao-proxy && DIFY_API_KEY=test node -e "require('./server'); setTimeout(() => process.exit(0), 100)"
```

Expected: server starts without syntax errors.

- [ ] **Step 3: Inspect diff**

Run:

```bash
git diff -- gaokao-proxy/lib/commerce-store.js gaokao-proxy/server.js gaokao-miniprogram/src/api/membership.js gaokao-miniprogram/src/stores/membership.js gaokao-miniprogram/src/pages/index/index.vue docs/dify/agent-config-v1.md tests/test_profile_storage_and_inputs.py docs/superpowers/plans/2026-05-21-dify-profile-initialization.md
```

Expected: diff contains only profile initialization, Dify input merge, docs, and tests.

## Self-Review

- Spec coverage: The plan covers backend persistence, frontend sync, proxy-to-Dify initialization inputs, Dify workflow documentation, and regression tests.
- Placeholder scan: No task relies on vague placeholders; each task names the exact symbols and files.
- Type consistency: The profile shape is consistently `{ province, category, score, rank, updatedAt }`, while Dify `inputs` stringify `score` and `rank`.
