import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipServerContractTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_session_token_helper_exports_sign_and_verify(self):
        text = self.read("gaokao-proxy/lib/session-token.js")

        self.assertIn("function signSessionToken", text)
        self.assertIn("function verifySessionToken", text)
        self.assertIn("module.exports", text)

    def test_wechat_helpers_export_login_and_payment_functions(self):
        auth_text = self.read("gaokao-proxy/lib/wechat-auth.js")
        pay_text = self.read("gaokao-proxy/lib/wechat-pay.js")

        self.assertIn("async function exchangeCodeForSession", auth_text)
        self.assertIn("function assertWechatPayConfig", pay_text)
        self.assertIn("async function createJsapiPayment", pay_text)
        self.assertIn("function buildFrontendPayParams", pay_text)
        self.assertIn("function decryptWechatPayResource", pay_text)
        self.assertIn("function verifyWechatPayNotifySignature", pay_text)

    def test_server_exposes_membership_and_payment_routes(self):
        text = self.read("gaokao-proxy/server.js")

        self.assertIn("app.post('/api/auth/wechat-login'", text)
        self.assertIn("app.get('/api/membership/status'", text)
        self.assertIn("app.post('/api/profile/complete'", text)
        self.assertIn("app.post('/api/membership/limited-free-unlock'", text)
        self.assertIn("activateMembership(req.commerceAuth.userId, 'limited_free')", text)
        self.assertIn("app.post('/api/payment/create'", text)
        self.assertIn("app.get('/api/payment/order/:orderId'", text)
        self.assertIn("app.post('/api/payment/wechat/notify'", text)

    def test_report_generation_is_guarded_by_membership(self):
        text = self.read("gaokao-proxy/server.js")

        self.assertIn("MEMBERSHIP_REQUIRED", text)
        self.assertIn("requireMembershipForReports", text)
        self.assertIn("return res.status(402).json", text)
        self.assertIn("app.post('/api/report/generate', requireCommerceAuth, requireMembershipForReports", text)

    def test_wechat_pay_notify_decrypts_v3_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const crypto = require('node:crypto')
                    const {{ decryptWechatPayResource }} = require('{ROOT / "gaokao-proxy" / "lib" / "wechat-pay.js"}')

                    const key = '12345678901234567890123456789012'
                    const nonce = 'notifyNonce'
                    const associatedData = 'transaction'
                    const payload = JSON.stringify({{
                      out_trade_no: 'ord_1_1778740000000',
                      transaction_id: 'wx_tx_1',
                      trade_state: 'SUCCESS',
                    }})
                    const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(key), Buffer.from(nonce))
                    cipher.setAAD(Buffer.from(associatedData))
                    const encrypted = Buffer.concat([cipher.update(payload), cipher.final(), cipher.getAuthTag()])

                    const decoded = decryptWechatPayResource({{
                      algorithm: 'AEAD_AES_256_GCM',
                      ciphertext: encrypted.toString('base64'),
                      nonce,
                      associated_data: associatedData,
                    }}, {{ WECHAT_PAY_API_V3_KEY: key }})

                    assert.equal(decoded.trade_state, 'SUCCESS')
                    assert.equal(decoded.out_trade_no, 'ord_1_1778740000000')
                """),
                encoding="utf-8",
            )
            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_env_example_documents_commerce_and_wechat_config(self):
        text = self.read("gaokao-proxy/.env.example")

        for key in [
            "COMMERCE_DB_PATH",
            "COMMERCE_SESSION_SECRET",
            "MEMBERSHIP_PRICE_CENTS",
            "MEMBERSHIP_INVITE_REQUIRED",
            "WECHAT_APPID",
            "WECHAT_SECRET",
            "WECHAT_MCH_ID",
            "WECHAT_PAY_SERIAL_NO",
            "WECHAT_PAY_PRIVATE_KEY_PATH",
            "WECHAT_PAY_NOTIFY_URL",
        ]:
            self.assertIn(key, text)


if __name__ == "__main__":
    unittest.main()
