# VIP Report Unlock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Historical note: this plan records the 2026-05-26 implementation pass. Current launch facts have moved to `docs/deployment/current-live-chain.md`, `docs/deployment/production-launch-todo.md`, and `docs/deployment/mvp-next-todo-2026-05-28.md`. Current formal price is `¥19.9` / `MEMBERSHIP_PRICE_CENTS=1990`.

**Goal:** Add a clear VIP conversion path for comprehensive report generation and deep report downloads, supporting payment, 5-user invitation unlock, VIP code unlock, and limited deep-report download counts.

**Architecture:** Keep the existing membership/paywall model, and extend it instead of replacing it. `gaokao-proxy/lib/commerce-store.js` remains the source of truth for membership status, invite progress, VIP code redemption, and download quota. The mini-program surfaces the same three unlock methods in the report tab, the generation intercept sheet, the deep-report download page, and the profile tab.

**Tech Stack:** Node.js Express, better-sqlite3, UniApp Vue 3, Pinia, Python unittest, WeChat mini-program build.

---

## File Structure

- Modify `gaokao-proxy/lib/commerce-store.js`: invite threshold default, VIP code tables/actions, download quota tables/actions, enriched membership status.
- Modify `gaokao-proxy/server.js`: VIP code redemption route, deep-report PDF quota check/recording, richer membership-required responses.
- Modify `gaokao-miniprogram/src/api/membership.js`: add VIP code redemption API.
- Modify `gaokao-miniprogram/src/stores/membership.js`: normalize invite requirement 5, expose VIP code unlock and download quota state.
- Modify `gaokao-miniprogram/src/pages/report/report.vue`: VIP rights hero, three unlock options, generation intercept sheet, generated-report deep report package.
- Modify `gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue`: show quota, handle quota exhausted, refresh quota after download.
- Modify `gaokao-miniprogram/src/pages/profile/profile.vue`: keep as status center, add VIP rights and code/invite entry points.
- Modify `gaokao-miniprogram/src/pages/index/index.vue`: replace stale "邀请 3 人" copy with dynamic 5-person copy.
- Modify `docs/architecture-and-apis.md` and `docs/deployment/production-launch-todo.md`: document invite threshold, VIP code route, quota env vars, and live deployment checks.
- Modify tests:
  - `tests/test_commerce_store.py`
  - `tests/test_membership_server_contracts.py`
  - `tests/test_membership_pages.py`
  - `tests/test_deep_report_download_flow.py`

## Product Decisions Locked For Implementation

- Invite unlock threshold is 5 effective registered users.
- A VIP code unlocks the same VIP membership as payment and invite unlock.
- Deep PDF downloads are VIP-only and have a default limit of 10 successful PDF downloads per user.
- The download limit is configurable with `MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT`.
- Initial VIP codes are configured by `MEMBERSHIP_VIP_CODES`, comma-separated, for example `FENGGE2026,VIP2026`.
- No admin UI is included in this pass. Admin code management can be a later task if needed.

---

### Task 1: Backend Commerce Store Contract

**Files:**
- Modify: `tests/test_commerce_store.py`
- Modify: `gaokao-proxy/lib/commerce-store.js`

- [ ] **Step 1: Write failing commerce tests for 5 invites, VIP code unlock, and download quota**

In `tests/test_commerce_store.py`, change the test harness default from `inviteRequired: 3` to `inviteRequired: 5`, and add `deepReportDownloadLimit: 2` plus `vipCodes: ['FENGGE2026']`:

```python
const store = createCommerceStore({
  dbPath: '{db_path}',
  now: () => nowValue++,
  idFactory: (prefix) => `${prefix}_${++idValue}`,
  inviteRequired: 5,
  priceCents: 1990,
  deepReportDownloadLimit: 2,
  vipCodes: ['FENGGE2026'],
})
```

Rename `test_three_effective_invites_unlock_membership` to `test_five_effective_invites_unlock_membership`, change the openid loop to five users, and assert:

```javascript
assert.equal(status.status, 'active')
assert.equal(status.source, 'invite')
assert.equal(status.invite.effectiveCount, 5)
assert.equal(status.invite.requiredCount, 5)
```

Add this test:

```python
    def test_vip_code_unlocks_membership_once(self):
        self.run_node_test("""
            const user = store.upsertWechatUser({ openid: 'openid-code-user' })

            const result = store.redeemVipCode(user.userId, ' fengge2026 ')
            const status = store.getMembershipStatus(user.userId)

            assert.equal(result.status, 'ok')
            assert.equal(status.status, 'active')
            assert.equal(status.source, 'vip_code')
            assert.equal(status.features.comprehensiveReport, true)

            assert.throws(
              () => store.redeemVipCode(user.userId, 'FENGGE2026'),
              /已经使用过/
            )
        """)
```

Add this test:

```python
    def test_deep_report_download_quota_counts_successful_downloads(self):
        self.run_node_test("""
            const user = store.upsertWechatUser({ openid: 'openid-quota-user' })
            store.activateMembership(user.userId, 'payment')

            let status = store.getMembershipStatus(user.userId)
            assert.equal(status.downloadQuota.limit, 2)
            assert.equal(status.downloadQuota.used, 0)
            assert.equal(status.downloadQuota.remaining, 2)

            store.recordDeepReportDownload({
              userId: user.userId,
              reportType: 'major',
              reportId: '080901',
              filename: 'computer.pdf',
            })
            store.recordDeepReportDownload({
              userId: user.userId,
              reportType: 'university',
              reportId: '中山大学',
              filename: 'sysu.pdf',
            })

            status = store.getMembershipStatus(user.userId)
            assert.equal(status.downloadQuota.used, 2)
            assert.equal(status.downloadQuota.remaining, 0)
            assert.equal(store.canDownloadDeepReport(user.userId).allowed, false)
            assert.equal(store.canDownloadDeepReport(user.userId).code, 'DOWNLOAD_QUOTA_EXHAUSTED')
        """)
```

- [ ] **Step 2: Run commerce tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_commerce_store.py
```

Expected: fail with missing `deepReportDownloadLimit`, `vipCodes`, `redeemVipCode`, `recordDeepReportDownload`, or `canDownloadDeepReport`.

- [ ] **Step 3: Implement store schema and actions**

In `gaokao-proxy/lib/commerce-store.js`, extend `createCommerceStore` options:

```javascript
  inviteRequired = Number(process.env.MEMBERSHIP_INVITE_REQUIRED || 5),
  priceCents = Number(process.env.MEMBERSHIP_PRICE_CENTS || 1990),
  deepReportDownloadLimit = Number(process.env.MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT || 10),
  vipCodes = String(process.env.MEMBERSHIP_VIP_CODES || '')
    .split(',')
    .map((code) => code.trim())
    .filter(Boolean),
```

Add tables inside the existing `db.exec` block:

```sql
    CREATE TABLE IF NOT EXISTS vip_invite_codes (
      code TEXT PRIMARY KEY,
      status TEXT NOT NULL,
      max_uses INTEGER,
      used_count INTEGER NOT NULL DEFAULT 0,
      created_at INTEGER NOT NULL,
      expires_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS vip_code_redemptions (
      id TEXT PRIMARY KEY,
      code TEXT NOT NULL,
      user_id TEXT NOT NULL,
      redeemed_at INTEGER NOT NULL,
      UNIQUE(code, user_id)
    );

    CREATE TABLE IF NOT EXISTS deep_report_downloads (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      report_type TEXT NOT NULL,
      report_id TEXT NOT NULL,
      filename TEXT NOT NULL,
      created_at INTEGER NOT NULL
    );
```

Seed env-configured codes after prepared statements are created:

```javascript
  const upsertVipCode = db.prepare(`
    INSERT INTO vip_invite_codes (code, status, max_uses, used_count, created_at, expires_at)
    VALUES (@code, 'active', NULL, 0, @createdAt, NULL)
    ON CONFLICT(code) DO UPDATE SET status = 'active'
  `)

  for (const rawCode of vipCodes) {
    const code = normalizeVipCode(rawCode)
    if (code) upsertVipCode.run({ code, createdAt: now() })
  }
```

Add helper:

```javascript
function normalizeVipCode(code) {
  return String(code || '').trim().toUpperCase()
}
```

Add prepared statements:

```javascript
  const getVipCode = db.prepare('SELECT * FROM vip_invite_codes WHERE code = ?')
  const insertVipRedemption = db.prepare(`
    INSERT INTO vip_code_redemptions (id, code, user_id, redeemed_at)
    VALUES (@id, @code, @userId, @redeemedAt)
  `)
  const incrementVipCodeUse = db.prepare(`
    UPDATE vip_invite_codes
    SET used_count = used_count + 1
    WHERE code = @code
  `)
  const countDeepReportDownloads = db.prepare(`
    SELECT COUNT(*) AS count FROM deep_report_downloads WHERE user_id = ?
  `)
  const insertDeepReportDownload = db.prepare(`
    INSERT INTO deep_report_downloads (
      id, user_id, report_type, report_id, filename, created_at
    ) VALUES (
      @id, @userId, @reportType, @reportId, @filename, @createdAt
    )
  `)
```

Extend `getMembershipStatus(userId)`:

```javascript
    const usedDownloads = countDeepReportDownloads.get(userId)?.count || 0
    const limit = Number.isFinite(deepReportDownloadLimit) ? deepReportDownloadLimit : 10
```

Return:

```javascript
      downloadQuota: {
        used: usedDownloads,
        limit,
        remaining: Math.max(0, limit - usedDownloads),
      },
```

Add actions:

```javascript
  const redeemVipCodeTx = db.transaction((userId, rawCode) => {
    const row = getUserById.get(userId)
    if (!row) throw new Error('user not found')

    const code = normalizeVipCode(rawCode)
    if (!code) throw new Error('请输入会员邀请码')

    const codeRow = getVipCode.get(code)
    if (!codeRow || codeRow.status !== 'active') {
      throw new Error('会员邀请码无效')
    }
    if (codeRow.expires_at && codeRow.expires_at < now()) {
      throw new Error('会员邀请码已过期')
    }
    if (codeRow.max_uses && codeRow.used_count >= codeRow.max_uses) {
      throw new Error('会员邀请码已用完')
    }

    const redeemedAt = now()
    try {
      insertVipRedemption.run({
        id: idFactory('vipred'),
        code,
        userId,
        redeemedAt,
      })
    } catch (err) {
      if (String(err.message || '').includes('UNIQUE')) {
        throw new Error('该会员邀请码已经使用过')
      }
      throw err
    }
    incrementVipCodeUse.run({ code })
    upsertMembership.run({ userId, source: 'vip_code', unlockedAt: redeemedAt })

    return { status: 'ok', membership: getMembershipStatus(userId) }
  })

  function canDownloadDeepReport(userId) {
    const membership = getMembershipStatus(userId)
    if (membership.status !== 'active') {
      return { allowed: false, code: 'MEMBERSHIP_REQUIRED', membership }
    }
    if (membership.downloadQuota.remaining <= 0) {
      return { allowed: false, code: 'DOWNLOAD_QUOTA_EXHAUSTED', membership }
    }
    return { allowed: true, membership }
  }

  function recordDeepReportDownload({ userId, reportType, reportId, filename }) {
    const check = canDownloadDeepReport(userId)
    if (!check.allowed) {
      const error = new Error(check.code === 'DOWNLOAD_QUOTA_EXHAUSTED' ? '深度报告下载次数已用完' : '请先开通会员')
      error.code = check.code
      error.membership = check.membership
      throw error
    }
    insertDeepReportDownload.run({
      id: idFactory('drdl'),
      userId,
      reportType: String(reportType || ''),
      reportId: String(reportId || ''),
      filename: String(filename || ''),
      createdAt: now(),
    })
    return getMembershipStatus(userId)
  }
```

Export these functions from the returned store object:

```javascript
    redeemVipCode: redeemVipCodeTx,
    canDownloadDeepReport,
    recordDeepReportDownload,
```

- [ ] **Step 4: Run commerce tests and verify they pass**

Run:

```bash
python3 -m unittest tests/test_commerce_store.py
```

Expected: pass.

- [ ] **Step 5: Commit backend store contract**

```bash
git add tests/test_commerce_store.py gaokao-proxy/lib/commerce-store.js
git commit -m "feat: add VIP code and deep report quota store"
```

---

### Task 2: Backend Routes And Deep PDF Quota Enforcement

**Files:**
- Modify: `tests/test_membership_server_contracts.py`
- Modify: `tests/test_deep_report_download_flow.py`
- Modify: `gaokao-proxy/server.js`

- [ ] **Step 1: Write route contract tests**

In `tests/test_membership_server_contracts.py`, assert these snippets exist:

```python
for snippet in [
    "app.post('/api/membership/redeem-code'",
    "commerceStore.redeemVipCode",
    "VIP_CODE_REDEEMED",
]:
    self.assertIn(snippet, text)
```

In `tests/test_deep_report_download_flow.py`, add assertions inside `test_proxy_routes_include_paid_deep_pdf_endpoint`:

```python
for snippet in [
    "commerceStore.canDownloadDeepReport",
    "DOWNLOAD_QUOTA_EXHAUSTED",
    "commerceStore.recordDeepReportDownload",
]:
    self.assertIn(snippet, server)
```

- [ ] **Step 2: Run route tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_membership_server_contracts.py tests/test_deep_report_download_flow.py
```

Expected: fail because the route and quota checks are not implemented.

- [ ] **Step 3: Add VIP code route**

In `gaokao-proxy/server.js`, after `/api/membership/status`, add:

```javascript
app.post('/api/membership/redeem-code', requireCommerceAuth, (req, res) => {
  try {
    const result = commerceStore.redeemVipCode(req.commerceAuth.userId, req.body?.code || '')
    res.json({
      code: 'VIP_CODE_REDEEMED',
      membership: result.membership,
    })
  } catch (err) {
    res.status(400).json({
      code: 'VIP_CODE_INVALID',
      error: err.message || '会员邀请码兑换失败',
    })
  }
})
```

- [ ] **Step 4: Add deep PDF quota check and recording**

In `app.get('/api/reports/deep/pdf', ...)`, after membership auth and before PDF generation, add:

```javascript
  const quotaCheck = commerceStore.canDownloadDeepReport(req.commerceAuth.userId)
  if (!quotaCheck.allowed) {
    const statusCode = quotaCheck.code === 'DOWNLOAD_QUOTA_EXHAUSTED' ? 429 : 402
    res.status(statusCode).json({
      code: quotaCheck.code,
      error: quotaCheck.code === 'DOWNLOAD_QUOTA_EXHAUSTED'
        ? '深度报告下载次数已用完'
        : '请先解锁深度填报会员',
      membership: quotaCheck.membership,
      downloadQuota: quotaCheck.membership?.downloadQuota,
    })
    return
  }
```

After `generateDeepReportPdf` succeeds and before `res.sendFile(pdfPath)`, add:

```javascript
    const membership = commerceStore.recordDeepReportDownload({
      userId: req.commerceAuth.userId,
      reportType: type,
      reportId: id,
      filename,
    })
    res.setHeader('X-Deep-Report-Downloads-Remaining', String(membership.downloadQuota.remaining))
```

- [ ] **Step 5: Run route tests and verify they pass**

Run:

```bash
python3 -m unittest tests/test_membership_server_contracts.py tests/test_deep_report_download_flow.py
```

Expected: pass.

- [ ] **Step 6: Commit backend routes**

```bash
git add tests/test_membership_server_contracts.py tests/test_deep_report_download_flow.py gaokao-proxy/server.js
git commit -m "feat: gate deep report downloads by quota"
```

---

### Task 3: Mini-Program Membership API And Store

**Files:**
- Modify: `gaokao-miniprogram/src/api/membership.js`
- Modify: `gaokao-miniprogram/src/stores/membership.js`
- Modify: `tests/test_membership_pages.py`

- [ ] **Step 1: Write frontend contract tests**

In `tests/test_membership_pages.py`, add store/API assertions:

```python
    def test_membership_store_supports_vip_code_and_download_quota(self):
        api = self.read("gaokao-miniprogram/src/api/membership.js")
        store = self.read("gaokao-miniprogram/src/stores/membership.js")

        for snippet in [
            "redeemMembershipCode",
            "url: '/api/membership/redeem-code'",
            "data: { code }",
        ]:
            self.assertIn(snippet, api)

        for snippet in [
            "downloadQuota",
            "redeemCode",
            "requiredInviteCount: 5",
            "请先邀请 5 位同学免费解锁",
        ]:
            self.assertIn(snippet, store)
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
python3 -m unittest tests/test_membership_pages.py
```

Expected: fail because VIP code and quota state are absent.

- [ ] **Step 3: Add API function**

In `gaokao-miniprogram/src/api/membership.js`, add:

```javascript
export function redeemMembershipCode(code, sessionToken = getStoredSession().sessionToken) {
  return request({
    url: '/api/membership/redeem-code',
    method: 'POST',
    data: { code },
    token: sessionToken,
  })
}
```

- [ ] **Step 4: Normalize quota and invite count in store**

In `gaokao-miniprogram/src/stores/membership.js`, import the API:

```javascript
  redeemMembershipCode,
```

Extend `normalizeStatus`:

```javascript
  const quota = data.downloadQuota || data.membership?.downloadQuota || {}
```

Return:

```javascript
    requiredInviteCount: Number(invite.requiredCount ?? data.membership?.invite?.requiredCount ?? 5),
    downloadQuota: {
      used: Number(quota.used ?? 0),
      limit: Number(quota.limit ?? 10),
      remaining: Number(quota.remaining ?? quota.limit ?? 10),
    },
```

Set default state:

```javascript
      requiredInviteCount: 5,
      downloadQuota: {
        used: 0,
        limit: 10,
        remaining: 10,
      },
```

In `applyStatus`, assign:

```javascript
      this.downloadQuota = status.downloadQuota
```

Change `paymentUnavailableText`:

```javascript
      return '支付功能正在备案配置中，请先邀请 5 位同学免费解锁，或输入会员邀请码。'
```

Add action:

```javascript
    async redeemCode(code) {
      await this.ensureLogin()
      const data = await redeemMembershipCode(code, this.sessionToken)
      this.applyStatus(data.membership || data)
      return data
    },
```

- [ ] **Step 5: Run frontend membership tests**

Run:

```bash
python3 -m unittest tests/test_membership_pages.py
```

Expected: pass.

- [ ] **Step 6: Commit frontend store/API**

```bash
git add gaokao-miniprogram/src/api/membership.js gaokao-miniprogram/src/stores/membership.js tests/test_membership_pages.py
git commit -m "feat: expose VIP code unlock in membership store"
```

---

### Task 4: Report Tab VIP Conversion UI

**Files:**
- Modify: `gaokao-miniprogram/src/pages/report/report.vue`
- Modify: `tests/test_membership_pages.py`
- Modify: `tests/test_deep_report_download_flow.py`

- [ ] **Step 1: Write report page UI assertions**

In `tests/test_membership_pages.py`, add assertions under `test_report_page_has_membership_lock_and_auth_header`:

```python
for snippet in [
    "VIP 报告权益",
    "解锁完整志愿报告",
    "邀请 5 位新用户",
    "输入会员邀请码",
    "showUnlockSheet",
    "redeemCodeFromSheet",
    "deep-report-package",
    "院校深度研究报告",
    "专业研究报告",
    "剩余下载次数",
]:
    self.assertIn(snippet, text)
```

In `tests/test_deep_report_download_flow.py`, replace the stale `openDeepReportDownload` assertion if absent with:

```python
self.assertIn("goDeepReportDownload", report_page)
self.assertIn("/pages/deep-report-download/deep-report-download", report_page)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_membership_pages.py tests/test_deep_report_download_flow.py
```

Expected: fail because the UI strings and functions do not exist.

- [ ] **Step 3: Add VIP rights copy to locked report hero**

In `gaokao-miniprogram/src/pages/report/report.vue`, replace the locked hero subtitle and price block with explicit VIP value:

```vue
<text class="hero-title">综合志愿参考报告</text>
<text class="hero-sub">
  {{
    allAssessmentsDone
      ? '资料已就绪，解锁后可生成完整报告并下载深度研究资料'
      : '完成测评后，可生成综合报告并查看院校/专业深度资料'
  }}
</text>
<view class="vip-benefit-list">
  <text class="vip-benefit">综合志愿报告</text>
  <text class="vip-benefit">院校深度 PDF</text>
  <text class="vip-benefit">专业研究 PDF</text>
  <text class="vip-benefit">家长分享</text>
</view>
<text class="hero-price">VIP 报告权益 · &#165;29</text>
```

- [ ] **Step 4: Replace unlock cards with three unlock methods**

Use the backend-driven invite count:

```vue
<view v-if="allAssessmentsDone && !membershipStore.isActive && !generating" class="unlock-options">
  <view class="unlock-card primary" @click="onPayWithWechat">
    <view class="unlock-card-icon">&#128179;</view>
    <text class="unlock-card-title">解锁完整志愿报告</text>
    <text class="unlock-card-price">&#165;29</text>
    <text class="unlock-card-hint">报告生成 + 深度 PDF 下载</text>
  </view>
  <view class="unlock-card invite" @click="onInviteFriends">
    <view class="unlock-card-icon">&#128101;</view>
    <text class="unlock-card-title">邀请 5 位新用户</text>
    <view class="invite-dots">
      <view
        v-for="i in membershipStore.requiredInviteCount"
        :key="i"
        class="invite-dot"
        :class="{ filled: i <= membershipStore.effectiveInviteCount }"
      />
    </view>
    <text class="unlock-card-hint">{{ membershipStore.inviteProgressText }}</text>
  </view>
  <view class="unlock-card code" @click="openUnlockSheet('code')">
    <view class="unlock-card-icon">&#127915;</view>
    <text class="unlock-card-title">输入会员邀请码</text>
    <text class="unlock-card-hint">已有邀请码可直接开通</text>
  </view>
</view>
```

- [ ] **Step 5: Add generation intercept sheet**

Add reactive state:

```javascript
const showUnlockSheet = ref(false)
const unlockCode = ref('')
const unlockSheetReason = ref('')
```

Add helpers:

```javascript
function openUnlockSheet(reason = 'generate') {
  unlockSheetReason.value = reason
  showUnlockSheet.value = true
}

function closeUnlockSheet() {
  showUnlockSheet.value = false
  unlockCode.value = ''
}

async function redeemCodeFromSheet() {
  try {
    await membershipStore.redeemCode(unlockCode.value)
    await membershipStore.loadStatus()
    closeUnlockSheet()
    uni.showToast({ title: 'VIP 已开通', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message || '邀请码无效', icon: 'none' })
  }
}
```

In `onGenerate`, replace the inactive-membership throw:

```javascript
    if (!membershipStore.isActive) {
      openUnlockSheet('generate')
      return
    }
```

Add template near the end of the page:

```vue
<view v-if="showUnlockSheet" class="unlock-sheet-mask" @click="closeUnlockSheet">
  <view class="unlock-sheet" @click.stop>
    <text class="sheet-title">生成完整志愿报告需要 VIP</text>
    <text class="sheet-desc">开通后可生成综合报告，并下载院校深度研究报告、专业研究报告。</text>
    <button class="sheet-primary" @click="onPayWithWechat">¥19.9 开通 VIP</button>
    <button class="sheet-secondary" open-type="share">邀请 5 位新用户解锁</button>
    <view class="code-row">
      <input v-model.trim="unlockCode" class="code-input" placeholder="输入会员邀请码" />
      <button class="code-btn" @click="redeemCodeFromSheet">兑换</button>
    </view>
  </view>
</view>
```

- [ ] **Step 6: Add generated-report deep report package**

Under the latest report card, add:

```vue
<view v-if="membershipStore.isActive && latestReport && !generating" class="deep-report-package">
  <view class="package-header">
    <text class="package-title">深度资料包</text>
    <text class="package-quota">剩余下载次数 {{ membershipStore.downloadQuota.remaining }}/{{ membershipStore.downloadQuota.limit }}</text>
  </view>
  <view class="package-grid">
    <view class="package-item" @click="goDeepReportDownload('university')">
      <text class="package-name">院校深度研究报告</text>
      <text class="package-desc">查看学校定位、转专业、就业与风险</text>
    </view>
    <view class="package-item" @click="goDeepReportDownload('major')">
      <text class="package-name">专业研究报告</text>
      <text class="package-desc">查看课程难度、就业方向和适配风险</text>
    </view>
  </view>
</view>
```

Add function:

```javascript
function goDeepReportDownload(mode = 'university') {
  uni.navigateTo({
    url: `/pages/deep-report-download/deep-report-download?mode=${encodeURIComponent(mode)}`,
  })
}
```

- [ ] **Step 7: Add minimal styles**

Add styles for `.vip-benefit-list`, `.vip-benefit`, `.unlock-card.code`, `.unlock-sheet-mask`, `.unlock-sheet`, `.sheet-primary`, `.sheet-secondary`, `.code-row`, `.code-input`, `.code-btn`, `.deep-report-package`, `.package-header`, `.package-title`, `.package-quota`, `.package-grid`, `.package-item`, `.package-name`, and `.package-desc`. Keep card radii at `8rpx` or less, use existing `$text-primary`, `$text-secondary`, and orange/green variables already in `uni.scss`.

- [ ] **Step 8: Run page tests**

Run:

```bash
python3 -m unittest tests/test_membership_pages.py tests/test_deep_report_download_flow.py
```

Expected: pass.

- [ ] **Step 9: Commit report tab UI**

```bash
git add gaokao-miniprogram/src/pages/report/report.vue tests/test_membership_pages.py tests/test_deep_report_download_flow.py
git commit -m "feat: add VIP unlock paths on report tab"
```

---

### Task 5: Deep Report Download Quota UI

**Files:**
- Modify: `gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue`
- Modify: `tests/test_deep_report_download_flow.py`

- [ ] **Step 1: Write quota UI assertions**

In `tests/test_deep_report_download_flow.py`, add:

```python
for snippet in [
    "downloadQuota",
    "剩余下载次数",
    "DOWNLOAD_QUOTA_EXHAUSTED",
    "深度报告下载次数已用完",
    "onLoad",
]:
    self.assertIn(snippet, download_page)
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
python3 -m unittest tests/test_deep_report_download_flow.py
```

Expected: fail because quota UI and route query handling are not present.

- [ ] **Step 3: Support report tab mode query**

Import `onLoad`:

```javascript
import { onLoad } from '@dcloudio/uni-app'
```

Add:

```javascript
onLoad((options = {}) => {
  if (options.mode === 'major' || options.mode === 'university') {
    mode.value = options.mode
  }
})
```

- [ ] **Step 4: Show quota in access card**

Replace access card description with:

```vue
<text class="access-desc">
  {{
    membershipStore.isActive
      ? `可下载完整 PDF，剩余下载次数 ${membershipStore.downloadQuota.remaining}/${membershipStore.downloadQuota.limit}`
      : '可先搜索查看报告是否入库，下载完整 PDF 时再开通。'
  }}
</text>
```

- [ ] **Step 5: Handle quota exhausted before download**

In `ensureMembership`, add:

```javascript
  if (membershipStore.downloadQuota.remaining <= 0) {
    const error = new Error('深度报告下载次数已用完')
    error.code = 'DOWNLOAD_QUOTA_EXHAUSTED'
    throw error
  }
```

In the modal catch branch:

```javascript
      title: err.code === 'DOWNLOAD_QUOTA_EXHAUSTED' ? '下载次数已用完' : '需要会员权益',
      content: err.message || '请先开通会员后下载完整 PDF。',
```

After `uni.openDocument` success, refresh quota:

```javascript
success: async () => {
  await membershipStore.loadStatus().catch(() => {})
  uni.hideLoading()
},
```

- [ ] **Step 6: Parse backend quota errors**

In the non-PDF branch inside `uni.downloadFile.success`, use the response status:

```javascript
      } else {
        uni.hideLoading()
        if (res.statusCode === 429) {
          uni.showToast({ title: '深度报告下载次数已用完', icon: 'none' })
        } else {
          uni.showToast({ title: 'PDF 生成失败，请稍后重试', icon: 'none' })
        }
      }
```

- [ ] **Step 7: Run tests**

Run:

```bash
python3 -m unittest tests/test_deep_report_download_flow.py
```

Expected: pass.

- [ ] **Step 8: Commit quota UI**

```bash
git add gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue tests/test_deep_report_download_flow.py
git commit -m "feat: show deep report download quota"
```

---

### Task 6: Profile And Home Copy Cleanup

**Files:**
- Modify: `gaokao-miniprogram/src/pages/profile/profile.vue`
- Modify: `gaokao-miniprogram/src/pages/index/index.vue`
- Modify: `tests/test_membership_pages.py`

- [ ] **Step 1: Write copy assertions**

In `tests/test_membership_pages.py`, extend profile/home assertions:

```python
for snippet in [
    "VIP 权益",
    "邀请进度",
    "会员邀请码",
    "剩余下载次数",
]:
    self.assertIn(snippet, text)

home = self.read("gaokao-miniprogram/src/pages/index/index.vue")
self.assertIn("邀请 5 人免费", home)
self.assertNotIn("邀请 3 人免费", home)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_membership_pages.py
```

Expected: fail on missing copy.

- [ ] **Step 3: Add profile VIP status card**

In `profile.vue`, add a compact card below the header:

```vue
<view class="vip-status-card" :class="{ active: membershipStore.isActive }">
  <view class="vip-status-header">
    <text class="vip-status-title">VIP 权益</text>
    <text class="vip-status-badge">{{ membershipStore.isActive ? '已开通' : '未开通' }}</text>
  </view>
  <text class="vip-status-desc">
    {{ membershipStore.isActive ? `剩余下载次数 ${membershipStore.downloadQuota.remaining}/${membershipStore.downloadQuota.limit}` : `邀请进度 ${membershipStore.inviteProgressText}` }}
  </text>
  <view class="vip-status-actions">
    <button class="vip-action" @click="goReport">去报告页</button>
    <button class="vip-action secondary" @click="onShare">邀请好友</button>
  </view>
</view>
```

Add:

```javascript
function goReport() {
  uni.switchTab({ url: '/pages/report/report' })
}
```

Change the invitation menu label from `邀请好友` to `邀请好友 / 会员邀请码` only if it still fits visually; otherwise keep `邀请好友` and add secondary text `会员邀请码在报告页输入`.

- [ ] **Step 4: Replace home stale invite text**

In `index.vue`, replace:

```vue
<text class="hero-invite-hint">邀请 5 人免费</text>
```

with:

```vue
<text class="hero-invite-hint">邀请 5 人免费</text>
```

Replace:

```javascript
return '¥19.9 一次解锁 · 邀请 5 人免费'
```

with:

```javascript
return '¥19.9 一次解锁 · 邀请 5 人免费'
```

- [ ] **Step 5: Run tests**

Run:

```bash
python3 -m unittest tests/test_membership_pages.py
```

Expected: pass.

- [ ] **Step 6: Commit profile/home cleanup**

```bash
git add gaokao-miniprogram/src/pages/profile/profile.vue gaokao-miniprogram/src/pages/index/index.vue tests/test_membership_pages.py
git commit -m "feat: surface VIP status in profile"
```

---

### Task 7: Documentation And Deployment Configuration

**Files:**
- Modify: `docs/architecture-and-apis.md`
- Modify: `docs/deployment/production-launch-todo.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Document server environment variables**

In `docs/deployment/production-launch-todo.md`, add:

```markdown
会员解锁与下载次数：

- `MEMBERSHIP_INVITE_REQUIRED=5`
- `MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT=10`
- `MEMBERSHIP_VIP_CODES=FENGGE2026,VIP2026`（上线前替换为真实发放码）

上线检查：

- 新用户邀请 5 位完成资料后自动开通 VIP。
- 已登录用户输入有效会员邀请码后 `GET /api/membership/status` 返回 `status=active`。
- 深度 PDF 下载次数用完后 `/api/reports/deep/pdf` 返回 `429 DOWNLOAD_QUOTA_EXHAUSTED`。
```

- [ ] **Step 2: Update API architecture docs**

In `docs/architecture-and-apis.md`, update membership section:

```markdown
会员可通过三种方式激活：

1. 微信支付 19.9 元。
2. 邀请 5 位新用户注册并完成考生资料。
3. 输入后台配置的会员邀请码。

会员状态响应增加：

```json
{
  "downloadQuota": {
    "used": 0,
    "limit": 10,
    "remaining": 10
  }
}
```
```

Add route:

```markdown
#### ④ 兑换会员邀请码

- 路由：`POST /api/membership/redeem-code`
- 鉴权：`Authorization: Bearer <sessionToken>`
- 请求：`{ "code": "FENGGE2026" }`
- 成功：`{ "code": "VIP_CODE_REDEEMED", "membership": {...} }`
- 失败：`400 { "code": "VIP_CODE_INVALID", "error": "会员邀请码无效" }`
```

- [ ] **Step 3: Update repository guidance**

In `AGENTS.md`, under live service facts or mini-program notes, add:

```markdown
- VIP can be unlocked by payment, 5 effective invites, or a configured member invite code.
- Deep university/major PDF downloads are VIP-only and count against `MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT`.
```

- [ ] **Step 4: Commit docs**

```bash
git add docs/architecture-and-apis.md docs/deployment/production-launch-todo.md AGENTS.md
git commit -m "docs: document VIP unlock and download quota"
```

---

### Task 8: Full Verification And Live Rollout

**Files:**
- No source files unless verification finds defects.

- [ ] **Step 1: Run focused backend/frontend contract tests**

Run:

```bash
python3 -m unittest tests/test_commerce_store.py tests/test_membership_server_contracts.py tests/test_membership_pages.py tests/test_deep_report_download_flow.py
```

Expected: pass.

- [ ] **Step 2: Run wider regression suite**

Run:

```bash
python3 -m unittest discover tests
```

Expected: pass. If unrelated generated-report tests fail because of stale local artifacts, record exact failures and do not mask membership failures.

- [ ] **Step 3: Build mini-program**

Run:

```bash
cd gaokao-miniprogram && npm run build:mp-weixin
```

Expected: build exits 0.

- [ ] **Step 4: Verify backend starts locally**

Run:

```bash
cd gaokao-proxy && npm test
```

Expected: package tests pass if configured. If `npm test` is not configured, run:

```bash
cd gaokao-proxy && node -c server.js && node -c lib/commerce-store.js
```

Expected: syntax checks pass.

- [ ] **Step 5: Deploy backend to 47 after approval**

On `47.113.125.147`, set the real launch values in `/opt/gaokao-proxy/.env`. For a trial build smoke test before public release, use this deterministic single test code and remove it after verification:

```bash
MEMBERSHIP_INVITE_REQUIRED=5
MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT=10
MEMBERSHIP_VIP_CODES=FENGGE-TRIAL-2026
```

Restart:

```bash
pm2 restart gaokao-proxy
pm2 logs gaokao-proxy --lines 80
```

Expected: no startup error.

- [ ] **Step 6: Live API smoke tests**

Run against `https://gaokao.aicoming.cn`:

```bash
curl -sS https://gaokao.aicoming.cn/api/health
```

Expected:

```json
{"status":"ok"}
```

Then create a dev login session and capture the token:

```bash
LOGIN_JSON=$(curl -sS -X POST https://gaokao.aicoming.cn/api/auth/wechat-login \
  -H 'Content-Type: application/json' \
  -d '{"code":"dev_vip_plan_smoke"}')
TOKEN=$(node -e "const data = JSON.parse(process.argv[1]); process.stdout.write(data.sessionToken || '')" "$LOGIN_JSON")
test -n "$TOKEN"
```

Redeem the trial VIP code and verify membership status returns active and quota:

```bash
curl -sS -X POST https://gaokao.aicoming.cn/api/membership/redeem-code \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"code":"FENGGE-TRIAL-2026"}'
```

Expected:

```json
{"code":"VIP_CODE_REDEEMED","membership":{"status":"active"}}
```

- [ ] **Step 7: Mini-program manual QA**

Check in WeChat DevTools or a trial build:

1. Report tab locked state shows `VIP 报告权益`.
2. Ready-but-unpaid state shows payment, invite 5 users, and member invite code.
3. Clicking generate while unpaid opens the unlock sheet instead of a plain toast.
4. Valid member invite code unlocks VIP and returns to generation state.
5. Generated report page shows `深度资料包`.
6. Deep-report download page shows remaining quota.
7. Downloading a PDF decrements remaining quota.
8. Quota exhausted state prevents further downloads with a clear message.

- [ ] **Step 8: Final commit if verification fixes were required**

If any fixes were made during verification, stage the exact files reported by `git status --short`:

```bash
git status --short
git add gaokao-proxy/server.js gaokao-proxy/lib/commerce-store.js gaokao-miniprogram/src/pages/report/report.vue gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue gaokao-miniprogram/src/pages/profile/profile.vue gaokao-miniprogram/src/pages/index/index.vue gaokao-miniprogram/src/api/membership.js gaokao-miniprogram/src/stores/membership.js tests/test_commerce_store.py tests/test_membership_server_contracts.py tests/test_membership_pages.py tests/test_deep_report_download_flow.py docs/architecture-and-apis.md docs/deployment/production-launch-todo.md AGENTS.md
git commit -m "fix: polish VIP unlock verification issues"
```

---

## Self-Review

- Spec coverage: payment, invite unlock, VIP code unlock, report-tab entrance, generate-time intercept, post-generation deep package, profile status, and download quota are all covered.
- Scope control: no admin code-management UI, no new payment product, no separate quota-purchase flow.
- Type consistency: `downloadQuota`, `redeemCode`, `redeemMembershipCode`, `redeemVipCode`, `canDownloadDeepReport`, and `recordDeepReportDownload` are named consistently across tasks.
- Verification: focused unit/contract tests, full unittest discovery, mini-program build, backend syntax, live API smoke, and manual mini-program QA are included.
