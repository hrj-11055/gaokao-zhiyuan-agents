# Chat Personality Assessment Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Insert one dismissible personality-test guide card after the first qualifying complete AI reply: a 500-character reply from round 3 onward, or any complete reply at round 6.

**Architecture:** Keep trigger selection in a pure chat-domain module, persistence in the existing storage boundary, and presentation in an isolated Vue component. The chat page composes these pieces and renders the card after the selected historical AI message without adding anything to Dify messages.

**Tech Stack:** UniApp, Vue 3 Composition API, JavaScript ES modules, Python `unittest` tests that execute Node snippets.

---

## File Map

- Create `gaokao-miniprogram/src/pages/chat/personalityAssessmentGuide.js`: visible-text counting and first qualifying AI-message index selection.
- Create `gaokao-miniprogram/src/components/PersonalityAssessmentGuide.vue`: guide copy and start/dismiss actions.
- Modify `gaokao-miniprogram/src/utils/storage.js`: persist the permanent dismissal flag and include it in full local-data clearing.
- Modify `gaokao-miniprogram/src/pages/chat/chat.vue`: refresh assessment/dismissal state, select the trigger index, render one guide card, and navigate or dismiss.
- Create `tests/test_chat_personality_assessment_guide.py`: executable trigger-rule tests and source-contract tests.
- Modify `tests/test_security_and_chat_regressions.py`: align the existing chat copy assertion with the approved guide copy.
- Modify `tests/test_profile_storage_and_inputs.py`: align the existing guide contract assertion with the approved multi-round component-based behavior.

### Task 1: Trigger Selection

**Files:**
- Create: `gaokao-miniprogram/src/pages/chat/personalityAssessmentGuide.js`
- Create: `tests/test_chat_personality_assessment_guide.py`

- [ ] **Step 1: Write failing trigger tests**

Create Node-backed tests that import `findPersonalityGuideMessageIndex()` and verify:

```js
assert.equal(findPersonalityGuideMessageIndex(rounds(2, 600)), -1)
assert.equal(findPersonalityGuideMessageIndex(rounds(3, 500)), 5)
assert.equal(findPersonalityGuideMessageIndex(rounds(5, 120)), -1)
assert.equal(findPersonalityGuideMessageIndex(rounds(6, 120)), 11)
assert.equal(findPersonalityGuideMessageIndex(rounds(6, 600, { truncatedRound: 3 })), 11)
assert.equal(findPersonalityGuideMessageIndex(rounds(7, 600)), 5)
```

Also verify Markdown markers and whitespace do not count toward the 500-character threshold.

- [ ] **Step 2: Run the trigger tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_chat_personality_assessment_guide
```

Expected: FAIL because `personalityAssessmentGuide.js` does not exist.

- [ ] **Step 3: Implement the pure trigger module**

Export these contracts:

```js
export const PERSONALITY_GUIDE_LONG_ANSWER_MIN_LENGTH = 500
export const PERSONALITY_GUIDE_LONG_ANSWER_MIN_ROUND = 3
export const PERSONALITY_GUIDE_FALLBACK_ROUND = 6
export function getVisibleAnswerLength(content = '') { /* strip Markdown and whitespace */ }
export function findPersonalityGuideMessageIndex(messages = []) { /* return first qualifying AI index or -1 */ }
```

An AI reply is eligible only when it is non-empty and has neither `truncated` nor `error` set. Count user messages encountered before each AI reply as its round number.

- [ ] **Step 4: Run the trigger tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_chat_personality_assessment_guide
```

Expected: trigger-rule tests pass; source-contract tests may still fail until later tasks.

### Task 2: Dismissal Persistence

**Files:**
- Modify: `gaokao-miniprogram/src/utils/storage.js`
- Modify: `tests/test_chat_personality_assessment_guide.py`

- [ ] **Step 1: Add failing persistence tests**

Execute the storage module with a fake `uni` store and verify:

```js
assert.equal(isPersonalityGuideDismissed(), false)
dismissPersonalityGuide()
assert.equal(isPersonalityGuideDismissed(), true)
clearHistory()
assert.equal(isPersonalityGuideDismissed(), true)
clearAllLocalData()
assert.equal(isPersonalityGuideDismissed(), false)
```

- [ ] **Step 2: Run the persistence test and verify RED**

Run:

```bash
python3 -m unittest tests.test_chat_personality_assessment_guide.ChatPersonalityAssessmentGuideTests.test_dismissal_persists_independently_from_chat_history
```

Expected: FAIL because the persistence exports do not exist.

- [ ] **Step 3: Add the storage contract**

Add an independent `chat_personality_guide_dismissed` key and exports:

```js
export function isPersonalityGuideDismissed() {
  return uni.getStorageSync(PERSONALITY_GUIDE_DISMISSED_KEY) === true
}

export function dismissPersonalityGuide() {
  uni.setStorageSync(PERSONALITY_GUIDE_DISMISSED_KEY, true)
}
```

Add the key to `clearAllLocalData()` but leave `clearHistory()` unchanged.

- [ ] **Step 4: Run the persistence test and verify GREEN**

Run the targeted command from Step 2. Expected: PASS.

### Task 3: Guide Card And Chat Integration

**Files:**
- Create: `gaokao-miniprogram/src/components/PersonalityAssessmentGuide.vue`
- Modify: `gaokao-miniprogram/src/pages/chat/chat.vue`
- Modify: `tests/test_chat_personality_assessment_guide.py`
- Modify: `tests/test_security_and_chat_regressions.py`
- Modify: `tests/test_profile_storage_and_inputs.py`

- [ ] **Step 1: Add failing source-contract tests**

Verify the component contains the approved title, description, dynamic `去做性格测试` / `继续性格测试` label, and `稍后再说`; verify the chat page imports the component and trigger selector, renders only at `personalityGuideMessageIndex`, blocks display while streaming/completed/dismissed, navigates to `/pages/mbti/mbti`, and persists dismissal.

- [ ] **Step 2: Run source-contract tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_chat_personality_assessment_guide tests.test_security_and_chat_regressions tests.test_profile_storage_and_inputs
```

Expected: FAIL on missing component/integration and old guide assertions.

- [ ] **Step 3: Implement the component and chat composition**

The component accepts:

```js
defineProps({ started: { type: Boolean, default: false } })
defineEmits(['start', 'dismiss'])
```

In the chat page, refresh `loadAssessments()` and `isPersonalityGuideDismissed()` in `onShow`. Compute the selected index only when the test is incomplete, the guide is not dismissed, and streaming is false. Treat saved MBTI answers or `questionIndex > 0` as “started”. Render the component after the selected AI message and wire start/dismiss events.

- [ ] **Step 4: Run source-contract and regression tests**

Run the command from Step 2. Expected: PASS.

### Task 4: Build And Completion Audit

**Files:**
- Verify all files above.

- [ ] **Step 1: Run focused regression tests**

```bash
python3 -m unittest tests.test_chat_personality_assessment_guide tests.test_security_and_chat_regressions tests.test_profile_storage_and_inputs
```

Expected: PASS with zero failures.

- [ ] **Step 2: Run full repository regression suite**

```bash
python3 -m unittest discover tests
```

Expected: PASS, or report unrelated pre-existing failures with exact evidence.

- [ ] **Step 3: Compile the mini program**

```bash
cd gaokao-miniprogram && npm run build:mp-weixin
```

Expected: exit code 0 with no Vue template or JavaScript syntax errors.

- [ ] **Step 4: Audit the approved requirements**

Confirm from current files and test output that: the card appears only after round 3 plus a 500-character complete reply or at round 6; only one historical position is selected; completed/dismissed users never see it; started users see the continue label; dismissal survives chat clearing; and no card data enters chat messages.
