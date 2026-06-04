# Parent-Friendly Planning Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the mini program from score-only Grade 12 usage to a parent-friendly planning flow with official score, estimated score, and no-score early planning report modes.

**Architecture:** Add profile mode fields at the storage boundary, then let existing progress gates consume a single `isProfileComplete()` contract. On the backend, classify report mode before prompt assembly so official-score, estimated-score, and no-score reports receive different mode instructions while sharing the JSON schema and quality gates.

**Tech Stack:** UniApp/Vue 3 mini program, Pinia, Node.js gaokao-proxy, Python `unittest` regression tests that run Node snippets.

---

## File Map

- Modify `gaokao-miniprogram/src/utils/storage.js`: normalize new profile fields, export score/profile helpers, update completion logic and Dify inputs.
- Modify `gaokao-miniprogram/src/stores/user.js`: use shared storage helpers instead of duplicating score-only completion and input logic.
- Modify `gaokao-proxy/lib/commerce-store.js`: persist new profile fields and validate early planning profiles without mandatory score.
- Modify `gaokao-proxy/lib/prompts/report-template.js`: classify report mode and assemble mode-specific prompt sections.
- Modify `gaokao-proxy/lib/report-builder.js`: continue passing profile to prompt; no API contract change expected unless tests reveal mode metadata is needed in HTML.
- Modify `gaokao-miniprogram/src/pages/index/index.vue`: replace heavy progress card with light workbench, add profile sheet mode selectors and optional score/range fields.
- Modify `gaokao-miniprogram/src/pages/chat/chat.vue`: update gate copy and readiness wording for early planning.
- Modify `gaokao-miniprogram/src/pages/chat/useChat.js`: include new profile fields in profile input key and user profile sync.
- Modify `gaokao-miniprogram/src/pages/chat/profileFollowup.js`: stop forcing score as a core field for early planning users.
- Modify `gaokao-miniprogram/src/pages/report/report.vue`: make readiness and button labels mode-aware, preserving any existing local changes.
- Modify `gaokao-miniprogram/src/pages/mbti/mbti-result.vue`: add low-presence next-step bar.
- Modify `gaokao-miniprogram/src/pages/holland/holland-result.vue`: add low-presence next-step bar.
- Modify `gaokao-miniprogram/src/pages/profile/profile.vue`: show score type or early planning status instead of assuming score always exists.
- Modify `tests/test_profile_storage_and_inputs.py`: profile completion, input construction, chat gate copy, and follow-up tests.
- Modify `tests/test_commerce_store.py`: commerce profile normalization/validation for new modes.
- Modify `tests/test_report_builder.py`: prompt classification and mode-specific prompt content tests.
- Modify `tests/test_miniprogram_report_flow.py`: report readiness and label contract checks where existing text assertions live.

---

### Task 1: Profile Model And Completion Rules

**Files:**
- Modify: `gaokao-miniprogram/src/utils/storage.js`
- Modify: `gaokao-miniprogram/src/stores/user.js`
- Test: `tests/test_profile_storage_and_inputs.py`

- [ ] **Step 1: Write failing storage tests**

Add Node assertions to `test_user_profile_is_saved_loaded_and_checked` in `tests/test_profile_storage_and_inputs.py`:

```js
assert.equal(isProfileComplete({ province: '广东', category: '物理类', planning_mode: 'early' }), true)
assert.equal(isProfileComplete({ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated', score: 560 }), true)
assert.equal(isProfileComplete({ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated' }), false)

const early = normalizeUserProfile({
  province: '广东',
  category: '物理类',
  planning_mode: 'early',
  grade: '高二',
  identity: '家长',
  score_range: '520-560'
})
assert.deepEqual(
  {
    planning_mode: early.planning_mode,
    score_type: early.score_type,
    grade: early.grade,
    identity: early.identity,
    score_range: early.score_range,
    report_mode: getProfileReportMode(early)
  },
  {
    planning_mode: 'early',
    score_type: '',
    grade: '高二',
    identity: '家长',
    score_range: '520-560',
    report_mode: 'planning'
  }
)

assert.deepEqual(
  buildProfileInputs(early),
  {
    province: '广东',
    category: '物理类',
    planning_mode: 'early',
    score_range: '520-560',
    grade: '高二',
    identity: '家长',
    report_mode: 'planning'
  }
)
```

- [ ] **Step 2: Run failing profile tests**

Run: `python3 -m unittest tests.test_profile_storage_and_inputs.ProfileStorageAndInputsTests.test_user_profile_is_saved_loaded_and_checked`

Expected: FAIL because `planning_mode`, `score_type`, `score_range`, `grade`, `identity`, and `getProfileReportMode` are not implemented.

- [ ] **Step 3: Implement profile helpers**

In `gaokao-miniprogram/src/utils/storage.js`, add:

```js
export const PROFILE_PLANNING_MODES = {
  SCORE: 'score',
  EARLY: 'early',
}

export const PROFILE_SCORE_TYPES = {
  OFFICIAL: 'official',
  ESTIMATED: 'estimated',
}

function normalizePlanningMode(value) {
  return value === PROFILE_PLANNING_MODES.EARLY ? PROFILE_PLANNING_MODES.EARLY : PROFILE_PLANNING_MODES.SCORE
}

function normalizeScoreType(value, planningMode, hasScore) {
  if (planningMode === PROFILE_PLANNING_MODES.EARLY) return ''
  if (value === PROFILE_SCORE_TYPES.ESTIMATED) return PROFILE_SCORE_TYPES.ESTIMATED
  return hasScore ? PROFILE_SCORE_TYPES.OFFICIAL : ''
}

export function hasProfileScore(profile = {}) {
  const data = normalizeUserProfile(profile)
  return typeof data.score === 'number' && data.score >= 0 && data.score <= 750
}

export function getProfileReportMode(profile = {}) {
  const data = normalizeUserProfile(profile)
  if (data.planning_mode === PROFILE_PLANNING_MODES.EARLY && !hasProfileScore(data)) return 'planning'
  if (data.score_type === PROFILE_SCORE_TYPES.ESTIMATED) return 'estimated'
  if (hasProfileScore(data)) return 'official'
  return 'planning'
}
```

Update `normalizeUserProfile()` to return these additional fields after `category`:

```js
planning_mode: planningMode,
score_type: normalizeScoreType(profile.score_type, planningMode, hasScore),
score_range: toTrimmedString(profile.score_range),
grade: toTrimmedString(profile.grade),
identity: toTrimmedString(profile.identity),
```

Update `isProfileComplete()`:

```js
export function isProfileComplete(profile) {
  const data = normalizeUserProfile(profile)
  const hasBase = Boolean(data.province && (data.category === '物理类' || data.category === '历史类'))
  if (!hasBase) return false
  if (data.planning_mode === PROFILE_PLANNING_MODES.EARLY) return true
  return hasProfileScore(data)
}
```

Update `buildProfileInputs()` to include:

```js
inputs.planning_mode = data.planning_mode
inputs.report_mode = getProfileReportMode(data)
if (data.score_type) inputs.score_type = data.score_type
if (data.score_range) inputs.score_range = data.score_range
if (data.grade) inputs.grade = data.grade
if (data.identity) inputs.identity = data.identity
```

- [ ] **Step 4: Update user store to use helpers**

In `gaokao-miniprogram/src/stores/user.js`, import and use:

```js
import {
  buildProfileInputs,
  isProfileComplete,
  normalizeUserProfile,
} from '../utils/storage.js'
```

Replace the getter bodies:

```js
isProfileComplete(state) {
  return isProfileComplete(state.profile)
},

profileInputs(state) {
  return buildProfileInputs(state.profile)
}
```

- [ ] **Step 5: Run profile tests**

Run: `python3 -m unittest tests.test_profile_storage_and_inputs`

Expected: PASS after follow-up tests are adjusted in Task 2.

---

### Task 2: Chat Gate And Follow-Up Logic

**Files:**
- Modify: `gaokao-miniprogram/src/pages/chat/chat.vue`
- Modify: `gaokao-miniprogram/src/pages/chat/useChat.js`
- Modify: `gaokao-miniprogram/src/pages/chat/profileFollowup.js`
- Test: `tests/test_profile_storage_and_inputs.py`

- [ ] **Step 1: Write failing chat contract tests**

Update tests that currently expect score-only gating:

```python
def test_chat_page_allows_early_planning_profile(self):
    chat_page = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue").read_text(encoding="utf-8")
    self.assertIn("基础资料可以先不填正式分数", chat_page)
    self.assertNotIn("请先补全省份、科类和分数", chat_page)
```

Update the Node follow-up test:

```js
assert.equal(getNextCoreProfileFollowup({ province: '广东', category: '物理类', planning_mode: 'early', report_mode: 'planning' }), null)
const score = getNextCoreProfileFollowup({ province: '广东', category: '物理类', planning_mode: 'score' })
assert.equal(score.field, 'score')
```

- [ ] **Step 2: Run failing chat tests**

Run: `python3 -m unittest tests.test_profile_storage_and_inputs`

Expected: FAIL because the chat page and follow-up logic still require score.

- [ ] **Step 3: Make chat copy mode-friendly**

In `chat.vue`, change gate copy:

```vue
<text class="profile-gate-title">先补充基础资料</text>
<text class="profile-gate-desc">基础资料可以先不填正式分数；有预估分就按预估定位，没有分数也能先做专业规划。</text>
```

Change placeholder:

```js
isProfileReady.value ? '写下你的纠结，或直接选上面的处境...' : '先补充省份和科类，可暂不填正式分数'
```

Change toast in `handleSend()`:

```js
uni.showToast({ title: '请先补充基础资料', icon: 'none' })
```

- [ ] **Step 4: Include new profile fields in chat key**

In `useChat.js`, add to `getProfileInputsKey()`:

```js
planning_mode: inputs.planning_mode || '',
score_type: inputs.score_type || '',
score_range: inputs.score_range || '',
grade: inputs.grade || '',
identity: inputs.identity || '',
report_mode: inputs.report_mode || '',
```

Change the `onSend()` toast to `请先补充基础资料`.

- [ ] **Step 5: Adjust core follow-up**

In `profileFollowup.js`, make score non-core when `inputs.planning_mode === 'early'` or `inputs.report_mode === 'planning'`:

```js
function isEarlyPlanningInputs(inputs = {}) {
  return inputs.planning_mode === 'early' || inputs.report_mode === 'planning'
}
```

Inside `getNextCoreProfileFollowup(inputs)`, return `null` after province/category when `isEarlyPlanningInputs(inputs)` is true. Keep asking score for score mode.

- [ ] **Step 6: Run chat/profile tests**

Run: `python3 -m unittest tests.test_profile_storage_and_inputs`

Expected: PASS.

---

### Task 3: Backend Profile Persistence

**Files:**
- Modify: `gaokao-proxy/lib/commerce-store.js`
- Test: `tests/test_commerce_store.py`

- [ ] **Step 1: Write failing commerce tests**

Add assertions to the commerce profile tests:

```js
const earlyProfile = store.saveProfile(user.id, {
  province: '广东',
  category: '物理类',
  planning_mode: 'early',
  grade: '高二',
  identity: '家长',
  score_range: '520-560'
})
assert.equal(earlyProfile.planning_mode, 'early')
assert.equal(earlyProfile.score_type, '')
assert.equal(earlyProfile.score, '')
assert.equal(earlyProfile.score_range, '520-560')

const estimatedProfile = store.saveProfile(user.id, {
  province: '广东',
  category: '物理类',
  planning_mode: 'score',
  score_type: 'estimated',
  score: 560
})
assert.equal(estimatedProfile.score_type, 'estimated')
```

- [ ] **Step 2: Run failing commerce tests**

Run: `python3 -m unittest tests.test_commerce_store`

Expected: FAIL because commerce profile validation requires score for every profile.

- [ ] **Step 3: Implement commerce normalization**

In `commerce-store.js`, add `planning_mode`, `score_type`, `score_range`, `grade`, and `identity` to `normalizeProfile()` using the same semantics as the mini program:

```js
const planningMode = profile.planning_mode === 'early' ? 'early' : 'score'
const hasScore = typeof score === 'number' && score >= 0 && score <= 750
const scoreType = planningMode === 'early'
  ? ''
  : (profile.score_type === 'estimated' ? 'estimated' : (hasScore ? 'official' : ''))
```

Return:

```js
planning_mode: planningMode,
score_type: scoreType,
score_range: typeof profile.score_range === 'string' ? profile.score_range.trim() : '',
grade: typeof profile.grade === 'string' ? profile.grade.trim() : '',
identity: typeof profile.identity === 'string' ? profile.identity.trim() : '',
```

Update `validateProfile()`:

```js
if (profile.planning_mode === 'early') return
if (typeof profile.score !== 'number' || profile.score < 0 || profile.score > 750) {
  throw new Error('score is invalid')
}
```

- [ ] **Step 4: Run commerce tests**

Run: `python3 -m unittest tests.test_commerce_store`

Expected: PASS.

---

### Task 4: Report Prompt Modes

**Files:**
- Modify: `gaokao-proxy/lib/prompts/report-template.js`
- Modify: `gaokao-proxy/lib/report-builder.js` only if export wiring requires it
- Test: `tests/test_report_builder.py`

- [ ] **Step 1: Write failing prompt tests**

In `tests/test_report_builder.py`, add a Node test that imports `report-template.js`:

```js
const buildPrompt = require('/absolute/path/to/gaokao-proxy/lib/prompts/report-template.js')

assert.equal(buildPrompt.classifyReportMode({ province: '广东', category: '物理类', score: 600 }), 'official')
assert.equal(buildPrompt.classifyReportMode({ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated', score: 560 }), 'estimated')
assert.equal(buildPrompt.classifyReportMode({ province: '广东', category: '物理类', planning_mode: 'early' }), 'planning')

const officialPrompt = buildPrompt({ province: '广东', category: '物理类', score: 600 }, [], [], { recommendations: [{ school_name: '中山大学', min_score: 600 }] }, {})
assert.equal(officialPrompt.includes('2025 年结构化冲稳保候选池'), true)
assert.equal(officialPrompt.includes('Tab 5 可围绕候选池学校做院校定位'), true)

const estimatedPrompt = buildPrompt({ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated', score: 560 }, [], [], { recommendations: [] }, {})
assert.equal(estimatedPrompt.includes('预估分数'), true)
assert.equal(estimatedPrompt.includes('不是分数预测产品'), true)
assert.equal(estimatedPrompt.includes('不要反复用校准提醒打断报告'), true)

const planningPrompt = buildPrompt({ province: '广东', category: '物理类', planning_mode: 'early', grade: '高二', identity: '家长' }, [], [], { recommendations: [] }, {})
assert.equal(planningPrompt.includes('出分后、家长和考生集中填报志愿的关键阶段'), false)
assert.equal(planningPrompt.includes('院校层次认知与后续校准策略'), true)
assert.equal(planningPrompt.includes('严禁输出精确冲稳保院校排序'), true)
```

- [ ] **Step 2: Run failing prompt tests**

Run: `python3 -m unittest tests.test_report_builder.ReportBuilderTests`

Expected: FAIL because `classifyReportMode` and mode-specific prompt strings do not exist.

- [ ] **Step 3: Implement prompt classifier**

Refactor `report-template.js`:

```js
function hasUsableScore(profile = {}) {
  const score = Number(profile.score)
  return Number.isFinite(score) && score >= 0 && score <= 750
}

function classifyReportMode(profile = {}) {
  if ((profile.planning_mode === 'early' || profile.report_mode === 'planning') && !hasUsableScore(profile)) {
    return 'planning'
  }
  if (profile.score_type === 'estimated' || profile.report_mode === 'estimated') {
    return 'estimated'
  }
  if (hasUsableScore(profile)) return 'official'
  return 'planning'
}
```

- [ ] **Step 4: Add mode-specific prompt sections**

Add helpers:

```js
function buildTimeAndModeSection(mode) {
  if (mode === 'planning') {
    return `【时间与数据背景】\n当前是提前规划场景，用户可能是高一/高二家长，尚未掌握正式分数。报告重点是专业方向、孩子画像、能力差距、学习路径、目标分数段和家长行动。严禁输出精确冲稳保院校排序。`
  }
  if (mode === 'estimated') {
    return `【时间与数据背景】\n当前使用的是预估分数。预估分数只作为粗定位参考，不是分数预测产品；允许合理误差。报告核心价值必须来自专业适配、孩子画像、家庭约束、风险判断和行动质量。可以给出大致院校层次参考，但不要把预估分建议写成录取承诺，也不要反复用校准提醒打断报告。`
  }
  return `【时间与数据背景】\n当前时间背景是 2026 年 6 月至 7 月，正处于高考出分后、家长和考生集中填报志愿的关键阶段。2025 年录取分数线已经可作为核心历史参考；2023、2024 年数据可辅助判断波动趋势。报告读者是家长和孩子，必须把“能不能上、值不值得上、适不适合上、风险在哪里、下一步怎么核验”讲清楚。`
}
```

Add Tab 5 instructions:

```js
function buildTab5ModeRules(mode) {
  if (mode === 'planning') {
    return `- Tab 5 标题和内容应转为“院校层次认知与后续校准策略”，解释未来如何看院校层次、需要收集哪些分数/位次/专业组数据、什么时候回来校准；严禁输出精确冲稳保院校排序。`
  }
  if (mode === 'estimated') {
    return `- Tab 5 可以结合候选池做粗定位和层次参考，但必须用“预估定位”口径表达；只需要在关键位置提示正式分数/位次出来后再校准，不要让校准提醒压过专业和行动分析。`
  }
  return `- Tab 5 必须基于“2025 年结构化冲稳保候选池”中的学校，严禁虚构学校、专业、分数线和位次；每个候选解释都要说明“历史数据参考，不等于 2026 年录取承诺”。`
}
```

Use `const reportMode = classifyReportMode(profile)` near the top and replace the current fixed time section and Tab 5 rules with helpers.

Export helper:

```js
module.exports = Object.assign(buildPrompt, {
  classifyReportMode,
})
```

- [ ] **Step 5: Run prompt/report tests**

Run: `python3 -m unittest tests.test_report_builder tests.test_report_quality_improvements`

Expected: PASS.

---

### Task 5: Home Light Workbench And Profile Sheet Modes

**Files:**
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`
- Test: `tests/test_miniprogram_report_flow.py` or add text assertions to `tests/test_profile_storage_and_inputs.py`

- [ ] **Step 1: Write failing UI text contract test**

Add a text assertion test:

```python
home = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "index" / "index.vue").read_text(encoding="utf-8")
self.assertIn("规划进度", home)
self.assertIn("成绩/预估成绩", home)
self.assertIn("提前规划", home)
self.assertIn("预估分数区间", home)
self.assertIn("无分数看专业规划，有分数看院校定位", home)
self.assertNotIn("progress-card.ready", home)
```

- [ ] **Step 2: Run failing UI contract test**

Run: `python3 -m unittest tests.test_profile_storage_and_inputs`

Expected: FAIL until the home page is updated.

- [ ] **Step 3: Update `createDraft()`**

In `index.vue`, include:

```js
planning_mode: source.planning_mode || 'score',
score_type: source.score_type || (source.score !== '' && source.score !== undefined ? 'official' : ''),
score_range: source.score_range || '',
grade: source.grade || '',
identity: source.identity || '',
```

- [ ] **Step 4: Add profile sheet controls**

Add segmented controls for:

```vue
<text class="field-label">当前阶段</text>
<view class="mode-cards">
  <view class="mode-card" :class="{ active: draft.planning_mode === 'score' }" @click="selectPlanningMode('score')">
    <text class="mode-title">成绩/预估成绩</text>
    <text class="mode-desc">适合已有正式分或大致预估分</text>
  </view>
  <view class="mode-card" :class="{ active: draft.planning_mode === 'early' }" @click="selectPlanningMode('early')">
    <text class="mode-title">提前规划</text>
    <text class="mode-desc">可先不填分数，先看专业方向</text>
  </view>
</view>
```

For score mode, render score type and score fields. For early mode, render grade/identity and score range fields.

- [ ] **Step 5: Relax save validation**

Use `isProfileComplete(draft.value)` after Task 1. Change toast:

```js
uni.showToast({ title: '请先补充省份和科类', icon: 'none' })
```

Call `membershipStore.markProfileCompleted()` only when `isProfileComplete()` returns true.

- [ ] **Step 6: Replace progress card styling with light workbench**

Update template copy:

```vue
<text class="progress-label">规划进度</text>
<text class="progress-hint">{{ nextActionText }}</text>
<text class="progress-guide">无分数看专业规划，有分数看院校定位</text>
```

Update CSS to white card, thin border, four segment bar, no dark/heavy hero.

- [ ] **Step 7: Run UI/profile tests**

Run: `python3 -m unittest tests.test_profile_storage_and_inputs`

Expected: PASS.

---

### Task 6: Report Page Readiness And Mode Labels

**Files:**
- Modify: `gaokao-miniprogram/src/pages/report/report.vue`
- Test: `tests/test_miniprogram_report_flow.py`

- [ ] **Step 1: Inspect dirty file before editing**

Run: `git diff -- gaokao-miniprogram/src/pages/report/report.vue`

Expected: Review existing user changes and preserve them.

- [ ] **Step 2: Write failing report text tests**

Add assertions:

```python
report_page = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "report" / "report.vue").read_text(encoding="utf-8")
self.assertIn("reportModeLabel", report_page)
self.assertIn("专业规划报告", report_page)
self.assertIn("预估定位报告", report_page)
self.assertIn("院校定位报告", report_page)
self.assertIn("completedSteps", report_page)
```

- [ ] **Step 3: Implement mode labels**

Import `getProfileReportMode` and compute:

```js
const currentProfile = computed(() => loadUserProfile())
const reportMode = computed(() => getProfileReportMode(currentProfile.value))
const reportModeLabel = computed(() => {
  if (reportMode.value === 'planning') return '专业规划报告'
  if (reportMode.value === 'estimated') return '预估定位报告'
  return '院校定位报告'
})
```

Use `reportModeLabel` in page title, hero title, generate button, loading title, and unlock copy where natural.

- [ ] **Step 4: Align readiness with four steps**

Use `completedSteps` from `useHomeProgress()` and compute progress as `completedSteps / 4`, not `completedAssessments / 2`.

- [ ] **Step 5: Run report tests**

Run: `python3 -m unittest tests.test_miniprogram_report_flow`

Expected: PASS.

---

### Task 7: Assessment Result Next-Step Bars

**Files:**
- Modify: `gaokao-miniprogram/src/pages/mbti/mbti-result.vue`
- Modify: `gaokao-miniprogram/src/pages/holland/holland-result.vue`
- Test: `tests/test_assessment_result_reports.py`

- [ ] **Step 1: Write failing result-page tests**

Add text assertions:

```python
mbti = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "mbti" / "mbti-result.vue").read_text(encoding="utf-8")
holland = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "holland" / "holland-result.vue").read_text(encoding="utf-8")
for page in [mbti, holland]:
    self.assertIn("next-step-bar", page)
    self.assertIn("下一步", page)
    self.assertIn("goNextStep", page)
```

- [ ] **Step 2: Implement MBTI next-step bar**

Import `loadReport` and add computed next action:

```js
const assessmentsState = computed(() => loadAssessments())
const nextStepText = computed(() => {
  if (!assessmentsState.value.holland.completed) return '下一步：完成霍兰德职业兴趣'
  if (!loadReport()?.url) return '下一步：生成规划报告'
  return '报告已生成，点击查看'
})

function goNextStep() {
  if (!assessmentsState.value.holland.completed) {
    uni.navigateTo({ url: '/pages/holland/holland' })
    return
  }
  uni.switchTab({ url: '/pages/report/report' })
}
```

Add a bottom bar with class `next-step-bar`.

- [ ] **Step 3: Implement Holland next-step bar**

Mirror MBTI logic, but route to `/pages/mbti/mbti` if MBTI is incomplete.

- [ ] **Step 4: Run assessment result tests**

Run: `python3 -m unittest tests.test_assessment_result_reports`

Expected: PASS.

---

### Task 8: Profile Summary Polish

**Files:**
- Modify: `gaokao-miniprogram/src/pages/profile/profile.vue`
- Test: `tests/test_membership_pages.py` if it owns profile text checks; otherwise add to `tests/test_profile_storage_and_inputs.py`.

- [ ] **Step 1: Write failing text test**

Assert profile page includes mode-aware text:

```python
profile_page = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "profile" / "profile.vue").read_text(encoding="utf-8")
self.assertIn("profileModeText", profile_page)
self.assertIn("预估成绩", profile_page)
self.assertIn("提前规划", profile_page)
```

- [ ] **Step 2: Implement mode summary**

Import `getProfileReportMode` and compute:

```js
const profileModeText = computed(() => {
  const mode = getProfileReportMode(profile.value)
  if (mode === 'planning') return '提前规划'
  if (mode === 'estimated') return '预估成绩'
  return '正式成绩'
})
```

Display mode near score/rank summary. If score is empty, show `暂未填写`.

- [ ] **Step 3: Run profile page tests**

Run: `python3 -m unittest tests.test_membership_pages tests.test_profile_storage_and_inputs`

Expected: PASS.

---

### Task 9: Full Verification

**Files:**
- All modified files above.

- [ ] **Step 1: Run focused regression tests**

Run:

```bash
python3 -m unittest \
  tests.test_profile_storage_and_inputs \
  tests.test_commerce_store \
  tests.test_report_builder \
  tests.test_report_quality_improvements \
  tests.test_miniprogram_report_flow \
  tests.test_assessment_result_reports \
  tests.test_membership_pages
```

Expected: PASS.

- [ ] **Step 2: Run full repository tests**

Run: `python3 -m unittest discover tests`

Expected: PASS or document unrelated failures with file/test names.

- [ ] **Step 3: Compile the mini program**

Run: `cd gaokao-miniprogram && npm run build:mp-weixin`

Expected: build completes without Vue/template errors.

- [ ] **Step 4: Optional iterative dev server**

If visual verification in WeChat DevTools is needed after code passes, run: `cd gaokao-miniprogram && npm run dev:mp-weixin`

Expected: UniApp dev build watches files. Stop the process before final response.

- [ ] **Step 5: Final git check**

Run: `git status --short`

Expected: only intended implementation files are modified plus pre-existing unrelated files such as `营销/README.md`.

---

## Self-Review Notes

- Spec coverage: profile modes, light workbench, early planning/no-score report behavior, estimated score rough positioning, result-page next-step bars, backend prompt modes, and tests are all mapped to tasks.
- Placeholder scan: no task uses open-ended `TODO` work; each task has concrete files, snippets, commands, and expected outcomes.
- Type consistency: the plan uses `planning_mode`, `score_type`, `score_range`, `grade`, `identity`, and `report_mode` consistently across frontend storage, backend persistence, and prompt classification.
