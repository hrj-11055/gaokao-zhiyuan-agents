import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipMiniprogramContractTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_membership_api_exports_backend_calls(self):
        text = self.read("gaokao-miniprogram/src/api/membership.js")

        for name in [
            "loginWithWechat",
            "fetchMembershipStatus",
            "markProfileComplete",
            "activateLimitedFreeMembership",
            "createMembershipPayment",
            "fetchPaymentOrder",
            "getStoredSession",
        ]:
            self.assertIn(f"export function {name}", text)

        self.assertIn("/api/auth/wechat-login", text)
        self.assertIn("/api/membership/status", text)
        self.assertIn("/api/profile/complete", text)
        self.assertIn("/api/membership/limited-free-unlock", text)
        self.assertIn("/api/payment/create", text)
        self.assertIn("/api/payment/order/", text)

    def test_membership_store_tracks_status_invites_and_payment(self):
        text = self.read("gaokao-miniprogram/src/stores/membership.js")

        self.assertIn("defineStore('membership'", text)
        self.assertIn("sessionToken", text)
        self.assertIn("effectiveInviteCount", text)
        self.assertIn("requiredInviteCount", text)
        self.assertIn("isActive", text)
        self.assertIn("async login", text)
        self.assertIn("async loadStatus", text)
        self.assertIn("async markProfileCompleted", text)
        self.assertIn("async activateLimitedFree", text)
        self.assertIn("async createPayment", text)
        self.assertIn("async pollOrder", text)
        self.assertIn("uni.requestPayment", text)
        self.assertIn("paymentUnavailableText", text)
        self.assertIn("isPaymentEnabled", text)

    def test_membership_store_normalizes_payment_exceptions(self):
        text = self.read("gaokao-miniprogram/src/stores/membership.js")

        for snippet in [
            "normalizeRequestPaymentError",
            "PAYMENT_CANCELLED",
            "支付已取消",
            "PAYMENT_FAILED",
            "支付失败，请稍后重试",
            "PAYMENT_PENDING",
            "支付结果确认中，请稍后刷新会员状态",
            "createPendingPaymentError",
        ]:
            self.assertIn(snippet, text)

    def test_index_captures_inviter_and_marks_profile_complete(self):
        text = self.read("gaokao-miniprogram/src/pages/index/index.vue")

        self.assertIn("onLoad", text)
        self.assertIn("useMembershipStore", text)
        self.assertIn("membershipStore.setInviterId", text)
        self.assertIn("membershipStore.markProfileCompleted", text)
        self.assertIn("isProfileComplete(draft.value)", text)


if __name__ == "__main__":
    unittest.main()
