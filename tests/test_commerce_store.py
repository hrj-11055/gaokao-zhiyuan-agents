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

                    let nowValue = 1778740000000
                    let idValue = 0
                    const store = createCommerceStore({{
                      dbPath: '{db_path}',
                      now: () => nowValue++,
                      idFactory: (prefix) => `${{prefix}}_${{++idValue}}`,
                      inviteRequired: 3,
                      priceCents: 2900,
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
            assert.equal(status.invite.requiredCount, 3)
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

    def test_three_effective_invites_unlock_membership(self):
        self.run_node_test("""
            const inviter = store.upsertWechatUser({ openid: 'openid-inviter' })

            for (const openid of ['openid-1', 'openid-2', 'openid-3']) {
              const invitee = store.upsertWechatUser({ openid, inviterId: inviter.userId })
              store.completeProfile(invitee.userId)
            }

            const status = store.getMembershipStatus(inviter.userId)
            assert.equal(status.status, 'active')
            assert.equal(status.source, 'invite')
            assert.equal(status.invite.effectiveCount, 3)
            assert.equal(status.features.universityResearch, true)
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


if __name__ == "__main__":
    unittest.main()
