# Random Profile Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hard-coded profile avatar and name with a persistent randomized “personality + animal” identity whose avatar matches the animal.

**Architecture:** Put identity generation and persistence in a focused `profile-identity.js` utility, separate from candidate profile data. The profile page consumes the resolved presentation object, while the existing global clear-data function removes the new storage key.

**Tech Stack:** UniApp, Vue 3 Composition API, JavaScript ES modules, WeChat mini-program local static assets, Python `unittest` with Node assertions.

---

### Task 1: Protect Identity Generation And Persistence

**Files:**
- Create: `gaokao-miniprogram/src/utils/profile-identity.js`
- Create: `tests/test_profile_identity.py`

- [ ] **Step 1: Write the failing identity utility tests**

Add Node-backed assertions that import `generateProfileIdentity` and `getOrCreateProfileIdentity`, inject a deterministic random sequence, and verify:

```js
const generated = generateProfileIdentity(sequenceRandom([0.99, 0]))
assert.equal(generated.personality, PROFILE_PERSONALITIES.at(-1))
assert.equal(generated.animal, PROFILE_ANIMALS[0].key)
assert.equal(generated.nickname, `${PROFILE_PERSONALITIES.at(-1)}的${PROFILE_ANIMALS[0].label}`)
assert.equal(generated.avatar, PROFILE_ANIMALS[0].avatar)
```

Also verify the first `getOrCreateProfileIdentity()` call saves `profile_identity`, the second returns the saved identity without consuming new randomness, and corrupt storage is regenerated.

- [ ] **Step 2: Run the identity test to verify it fails**

Run:

```bash
python3 -m unittest tests.test_profile_identity -v
```

Expected: FAIL because `gaokao-miniprogram/src/utils/profile-identity.js` does not exist.

- [ ] **Step 3: Implement the minimal identity utility**

Create:

```js
export const PROFILE_IDENTITY_KEY = 'profile_identity'
export const PROFILE_PERSONALITIES = [
  '勇敢', '温柔', '好奇', '沉稳', '浪漫', '热情', '机灵', '从容',
  '坚定', '自在', '认真', '开朗',
]
export const PROFILE_ANIMALS = [
  { key: 'panda', label: '熊猫', avatar: '/static/avatars/panda.png' },
  { key: 'penguin', label: '企鹅', avatar: '/static/avatars/penguin.png' },
  { key: 'otter', label: '水獭', avatar: '/static/avatars/otter.png' },
  { key: 'fox', label: '狐狸', avatar: '/static/avatars/fox.png' },
  { key: 'rabbit', label: '兔子', avatar: '/static/avatars/rabbit.png' },
  { key: 'owl', label: '猫头鹰', avatar: '/static/avatars/owl.png' },
  { key: 'bear', label: '小熊', avatar: '/static/avatars/bear.png' },
  { key: 'shiba', label: '柴犬', avatar: '/static/avatars/shiba.png' },
]
```

Implement `generateProfileIdentity(random = Math.random)` using separate random calls for personality and animal. Implement `getOrCreateProfileIdentity(random = Math.random)` to validate stored JSON, return its presentation, or generate and save `{ personality, animal }`.

- [ ] **Step 4: Run the identity tests to verify they pass**

Run:

```bash
python3 -m unittest tests.test_profile_identity -v
```

Expected: PASS.

### Task 2: Add Local Cartoon Avatar Assets

**Files:**
- Create: `gaokao-miniprogram/src/static/avatars/panda.png`
- Create: `gaokao-miniprogram/src/static/avatars/penguin.png`
- Create: `gaokao-miniprogram/src/static/avatars/otter.png`
- Create: `gaokao-miniprogram/src/static/avatars/fox.png`
- Create: `gaokao-miniprogram/src/static/avatars/rabbit.png`
- Create: `gaokao-miniprogram/src/static/avatars/owl.png`
- Create: `gaokao-miniprogram/src/static/avatars/bear.png`
- Create: `gaokao-miniprogram/src/static/avatars/shiba.png`

- [ ] **Step 1: Generate a consistent local avatar set**

Generate eight square, text-free, front-facing cartoon animal portraits with rounded composition, pastel backgrounds, and a consistent illustration style. Resize and optimize each final asset for the profile’s 100rpx display size.

- [ ] **Step 2: Validate asset names and dimensions**

Run:

```bash
file gaokao-miniprogram/src/static/avatars/*.png
```

Expected: eight valid PNG images with consistent dimensions.

### Task 3: Display The Persistent Identity On “我的”

**Files:**
- Modify: `gaokao-miniprogram/src/pages/profile/profile.vue`
- Modify: `tests/test_profile_identity.py`

- [ ] **Step 1: Write the failing profile-page contract test**

Assert the page imports and calls `getOrCreateProfileIdentity`, renders an `<image>` using `profileIdentity.avatar`, renders `profileIdentity.nickname`, and no longer contains:

```text
<text class="avatar-text">峰</text>
<text class="user-name">志愿同学</text>
```

- [ ] **Step 2: Run the profile-page test to verify it fails**

Run:

```bash
python3 -m unittest tests.test_profile_identity -v
```

Expected: FAIL because the page still contains the hard-coded avatar and nickname.

- [ ] **Step 3: Update profile page presentation**

Replace the avatar text view with:

```vue
<image class="avatar-image" :src="profileIdentity.avatar" mode="aspectFill" />
```

Render `{{ profileIdentity.nickname }}`, initialize it with `getOrCreateProfileIdentity()`, reload it on `onShow`, and update avatar styles for image clipping and a subtle border.

- [ ] **Step 4: Run the profile-page test to verify it passes**

Run:

```bash
python3 -m unittest tests.test_profile_identity -v
```

Expected: PASS.

### Task 4: Clear Identity With All Local Data

**Files:**
- Modify: `gaokao-miniprogram/src/utils/storage.js`
- Modify: `tests/test_profile_storage_and_inputs.py`

- [ ] **Step 1: Write the failing clear-data regression assertion**

Extend the storage test’s `uni.removeStorageSync` stub and assert:

```js
clearAllLocalData()
assert.equal(removedKeys.includes('profile_identity'), true)
```

- [ ] **Step 2: Run the storage regression test to verify it fails**

Run:

```bash
python3 -m unittest tests.test_profile_storage_and_inputs -v
```

Expected: FAIL because `profile_identity` is not removed.

- [ ] **Step 3: Add the identity storage key to global clearing**

Define `PROFILE_IDENTITY_KEY = 'profile_identity'` beside the other storage keys and include it in `clearAllLocalData()`.

- [ ] **Step 4: Run focused regression tests**

Run:

```bash
python3 -m unittest tests.test_profile_identity tests.test_profile_storage_and_inputs -v
```

Expected: PASS.

### Task 5: Verify The Mini Program

**Files:**
- Verify only

- [ ] **Step 1: Run repository regressions**

Run:

```bash
python3 -m unittest discover tests
```

Expected: PASS.

- [ ] **Step 2: Run the production compilation check**

Run:

```bash
cd gaokao-miniprogram && npm run build:mp-weixin
```

Expected: successful UniApp WeChat mini-program build.

- [ ] **Step 3: Inspect the final diff**

Run:

```bash
git diff -- gaokao-miniprogram/src/utils/profile-identity.js gaokao-miniprogram/src/pages/profile/profile.vue gaokao-miniprogram/src/utils/storage.js tests/test_profile_identity.py tests/test_profile_storage_and_inputs.py docs/superpowers/specs/2026-06-04-random-profile-identity-design.md docs/superpowers/plans/2026-06-04-random-profile-identity.md
```

Expected: only the approved random profile identity feature and its tests/docs.
