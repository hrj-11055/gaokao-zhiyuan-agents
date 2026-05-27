import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommerceStoreTests(unittest.TestCase):
    def run_node_test(self, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            db_path = Path(tmp) / "commerce.sqlite"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const {{ createCommerceStore }} = require('{ROOT / "gaokao-proxy" / "lib" / "commerce-store.js"}')

                    const dbPath = '{db_path}'
                    let nowValue = 1778740000000
                    let idValue = 0
                    const store = createCommerceStore({{
                      dbPath,
                      now: () => nowValue++,
                      idFactory: (prefix) => `${{prefix}}_${{++idValue}}`,
                      inviteRequired: 5,
                      priceCents: 2900,
                      deepReportDownloadLimit: 2,
                      vipCodes: ['FENGGE2026'],
                    }})

                    try {{
                      {test_body}
                    }} finally {{
                      store.close()
                    }}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_new_user_starts_inactive_with_empty_invite_progress(self):
        self.run_node_test("""
            const user = store.upsertWechatUser({ openid: 'openid-a' })
            const status = store.getMembershipStatus(user.userId)

            assert.equal(status.status, 'inactive')
            assert.equal(status.source, '')
            assert.equal(status.invite.effectiveCount, 0)
            assert.equal(status.invite.requiredCount, 5)
            assert.equal(status.features.comprehensiveReport, false)
        """)

    def test_profile_completion_counts_invite_once(self):
        self.run_node_test("""
            const inviter = store.upsertWechatUser({ openid: 'openid-inviter' })
            const invitee = store.upsertWechatUser({
              openid: 'openid-invitee',
              inviterId: inviter.userId,
            })

            const first = store.completeProfile(invitee.userId)
            const second = store.completeProfile(invitee.userId)
            const status = store.getMembershipStatus(inviter.userId)

            assert.equal(first.inviteCounted, true)
            assert.equal(second.inviteCounted, false)
            assert.equal(status.invite.effectiveCount, 1)
            assert.equal(status.status, 'inactive')
        """)

    def test_five_effective_invites_unlock_membership(self):
        self.run_node_test("""
            const inviter = store.upsertWechatUser({ openid: 'openid-inviter' })

            for (const openid of ['openid-1', 'openid-2', 'openid-3', 'openid-4', 'openid-5']) {
              const invitee = store.upsertWechatUser({ openid, inviterId: inviter.userId })
              store.completeProfile(invitee.userId)
            }

            const status = store.getMembershipStatus(inviter.userId)
            assert.equal(status.status, 'active')
            assert.equal(status.source, 'invite')
            assert.equal(status.invite.effectiveCount, 5)
            assert.equal(status.invite.requiredCount, 5)
            assert.equal(status.features.universityResearch, true)
        """)

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

    def test_paid_order_unlocks_membership(self):
        self.run_node_test("""
            const user = store.upsertWechatUser({ openid: 'openid-buyer' })
            const order = store.createPaymentOrder(user.userId)

            assert.equal(order.amountCents, 2900)
            assert.equal(order.status, 'created')

            const paid = store.markOrderPaid(order.outTradeNo, 'wx-transaction-1', { ok: true })
            const status = store.getMembershipStatus(user.userId)
            const saved = store.getOrder(order.orderId)

            assert.equal(paid.status, 'paid')
            assert.equal(saved.transactionId, 'wx-transaction-1')
            assert.equal(status.status, 'active')
            assert.equal(status.source, 'payment')
        """)

    def test_payment_notify_rejects_amount_mismatch_without_unlocking(self):
        self.run_node_test("""
            const user = store.upsertWechatUser({ openid: 'openid-amount-mismatch' })
            const order = store.createPaymentOrder(user.userId)

            assert.throws(
              () => store.markOrderPaid(order.outTradeNo, 'wx-transaction-mismatch', {
                resource: {
                  amount: { total: 100 },
                },
              }),
              (err) => err.code === 'PAYMENT_AMOUNT_MISMATCH' && /金额不一致/.test(err.message)
            )

            const saved = store.getOrder(order.orderId)
            const status = store.getMembershipStatus(user.userId)
            assert.equal(saved.status, 'abnormal')
            assert.equal(saved.transactionId, '')
            assert.equal(status.status, 'inactive')
        """)

    def test_payment_notify_is_idempotent_for_already_paid_order(self):
        self.run_node_test("""
            const user = store.upsertWechatUser({ openid: 'openid-duplicate-notify' })
            const order = store.createPaymentOrder(user.userId)

            const first = store.markOrderPaid(order.outTradeNo, 'wx-transaction-1', {
              resource: { amount: { total: 2900 } },
            })
            nowValue += 1000
            const second = store.markOrderPaid(order.outTradeNo, 'wx-transaction-duplicate', {
              resource: { amount: { total: 2900 } },
            })
            const saved = store.getOrder(order.orderId)

            assert.equal(first.status, 'paid')
            assert.equal(second.status, 'paid')
            assert.equal(saved.transactionId, 'wx-transaction-1')
            assert.equal(saved.paidAt, first.paidAt)
            assert.equal(store.getMembershipStatus(user.userId).status, 'active')
        """)

    def test_payment_notify_for_unknown_order_uses_stable_error_code(self):
        self.run_node_test("""
            assert.throws(
              () => store.markOrderPaid('missing-out-trade-no', 'wx-transaction-missing', {
                resource: { amount: { total: 2900 } },
              }),
              (err) => err.code === 'ORDER_NOT_FOUND' && /订单不存在/.test(err.message)
            )
        """)

    def test_unpaid_order_expires_when_queried_after_ttl(self):
        self.run_node_test("""
            const expiringStore = createCommerceStore({
              dbPath: `${dbPath}-expiring.sqlite`,
              now: () => nowValue,
              idFactory: (prefix) => `${prefix}_exp_${++idValue}`,
              priceCents: 2900,
              paymentOrderTtlMs: 30 * 60 * 1000,
            })

            try {
              const user = expiringStore.upsertWechatUser({ openid: 'openid-expiring-order' })
              const order = expiringStore.createPaymentOrder(user.userId)
              expiringStore.attachPrepayId(order.orderId, 'prepay-id')

              nowValue += 30 * 60 * 1000 + 1

              const saved = expiringStore.getOrder(order.orderId)
              assert.equal(saved.status, 'expired')
              assert.equal(expiringStore.getMembershipStatus(user.userId).status, 'inactive')
            } finally {
              expiringStore.close()
            }
        """)

    def test_payment_out_trade_no_is_wechat_pay_compatible(self):
        self.run_node_test("""
            const paymentStore = createCommerceStore({
              dbPath: `${dbPath}-payment.sqlite`,
              now: () => 1778740000000,
              inviteRequired: 5,
              priceCents: 2900,
            })

            try {
              const user = paymentStore.upsertWechatUser({ openid: 'openid-wechat-pay' })
              const order = paymentStore.createPaymentOrder(user.userId)

              assert.match(order.outTradeNo, /^[0-9A-Za-z_-]+$/)
              assert.ok(order.outTradeNo.length <= 32, order.outTradeNo)
            } finally {
              paymentStore.close()
            }
        """)


if __name__ == "__main__":
    unittest.main()
