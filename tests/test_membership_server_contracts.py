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
        virtual_pay_text = self.read("gaokao-proxy/lib/wechat-virtual-pay.js")

        self.assertIn("async function exchangeCodeForSession", auth_text)
        self.assertIn("function assertWechatPayConfig", pay_text)
        self.assertIn("async function createJsapiPayment", pay_text)
        self.assertIn("function buildFrontendPayParams", pay_text)
        self.assertIn("function buildAuthorization", pay_text)
        self.assertIn("function decryptWechatPayResource", pay_text)
        self.assertIn("function verifyWechatPayNotifySignature", pay_text)
        self.assertIn("'Wechatpay-Serial'", pay_text)
        self.assertIn("function createVirtualPayment", virtual_pay_text)
        self.assertIn("function calcPaySig", virtual_pay_text)
        self.assertIn("function calcUserSignature", virtual_pay_text)
        self.assertIn("function parseWechatXmlMessage", virtual_pay_text)
        self.assertIn("function parseVirtualPayGoodsNotify", virtual_pay_text)

    def test_virtual_payment_signatures_follow_wechat_algorithm(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const {{
                      calcPaySig,
                      calcUserSignature,
                      createVirtualPayment,
                    }} = require('{ROOT / "gaokao-proxy" / "lib" / "wechat-virtual-pay.js"}')

                    const signData = '{{"openid": "xxx", "user_ip": "127.0.0.1", "env": 0}}'
                    assert.equal(
                      calcPaySig('/xpay/query_user_balance', signData, '12345'),
                      'c37809f27c6d7fd1837ad2500a04512b66b34fd793a39a385fade56dca89a4b5'
                    )
                    assert.equal(
                      calcUserSignature(signData, '9hAb/NEYUlkaMBEsmFgzig=='),
                      '089d9e8dc5d308977360c4b79ec600a93d736802802a807d634192328032f6c7'
                    )

                    const payment = createVirtualPayment({{
                      order: {{
                        orderId: 'ord_1',
                        userId: 'u_1',
                        outTradeNo: 'GK1778740000000abc',
                        amountCents: 1990,
                      }},
                      sessionKey: 'session-key',
                      env: {{
                        WECHAT_VIRTUAL_PAY_ENV: '1',
                        WECHAT_VIRTUAL_PAY_SANDBOX_APP_KEY: 'sandbox-key',
                        WECHAT_VIRTUAL_PAY_OFFER_ID: '1450549807',
                        WECHAT_VIRTUAL_PAY_PRODUCT_ID: 'vip_report_1990',
                      }},
                    }})
                    const parsed = JSON.parse(payment.signData)
                    assert.equal(payment.mode, 'short_series_goods')
                    assert.equal(parsed.offerId, '1450549807')
                    assert.equal(parsed.productId, 'vip_report_1990')
                    assert.equal(parsed.goodsPrice, 1990)
                    assert.equal(parsed.env, 1)
                    assert.match(payment.paySig, /^[0-9a-f]{{64}}$/)
                    assert.match(payment.signature, /^[0-9a-f]{{64}}$/)
                """),
                encoding="utf-8",
            )
            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_wechat_pay_authorization_uses_comma_separated_v3_params(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            key_path = Path(tmp) / "apiclient_key.pem"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const crypto = require('node:crypto')
                    const {{ buildAuthorization }} = require('{ROOT / "gaokao-proxy" / "lib" / "wechat-pay.js"}')

                    const {{ privateKey, publicKey }} = crypto.generateKeyPairSync('rsa', {{
                      modulusLength: 2048,
                      privateKeyEncoding: {{ type: 'pkcs8', format: 'pem' }},
                      publicKeyEncoding: {{ type: 'spki', format: 'pem' }},
                    }})
                    require('node:fs').writeFileSync('{key_path}', privateKey)

                    const env = {{
                      WECHAT_MCH_ID: '1900000000',
                      WECHAT_PAY_SERIAL_NO: '46E9E7E4139421FD0CC12CF3F2A83311BDA28FCE',
                      WECHAT_PAY_PRIVATE_KEY_PATH: '{key_path}',
                    }}
                    const body = JSON.stringify({{ appid: 'wx123', mchid: '1900000000' }})
                    const auth = buildAuthorization({{
                      method: 'POST',
                      urlPath: '/v3/pay/transactions/jsapi',
                      body,
                      timestamp: '1778740000',
                      nonce: 'nonce123',
                      env,
                    }})

                    assert.match(auth, /^WECHATPAY2-SHA256-RSA2048 mchid="1900000000",nonce_str="nonce123",signature="[^"]+",timestamp="1778740000",serial_no="46E9E7E4139421FD0CC12CF3F2A83311BDA28FCE"$/)

                    const signature = auth.match(/signature="([^"]+)"/)[1]
                    const message = `POST\\n/v3/pay/transactions/jsapi\\n1778740000\\nnonce123\\n${{body}}\\n`
                    const ok = crypto.createVerify('RSA-SHA256').update(message).verify(publicKey, signature, 'base64')
                    assert.equal(ok, true)
                """),
                encoding="utf-8",
            )
            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_server_exposes_membership_and_payment_routes(self):
        text = self.read("gaokao-proxy/server.js")

        self.assertIn("app.post('/api/auth/wechat-login'", text)
        self.assertIn("app.get('/api/membership/status'", text)
        self.assertIn("app.post('/api/membership/redeem-code'", text)
        self.assertIn("commerceStore.redeemVipCode", text)
        self.assertIn("VIP_CODE_REDEEMED", text)
        self.assertIn("app.post('/api/profile/complete'", text)
        self.assertIn("app.post('/api/membership/limited-free-unlock'", text)
        self.assertIn("activateMembership(req.commerceAuth.userId, 'limited_free')", text)
        self.assertIn("app.post('/api/payment/create'", text)
        self.assertIn("app.get('/api/payment/order/:orderId'", text)
        self.assertIn("app.post('/api/payment/virtual/notify'", text)
        self.assertIn("app.get('/xpay/goods/deliver/notify'", text)
        self.assertIn("'/xpay/goods/deliver/notify'", text)
        self.assertIn("express.text", text)
        self.assertIn("requireWechatMessageSignature", text)
        self.assertIn("handleWechatMessageVerify", text)
        self.assertIn("createVirtualPayment", text)
        self.assertIn("parseVirtualPayGoodsNotify", text)

    def test_virtual_payment_notify_parses_wechat_xml_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const {{ parseVirtualPayGoodsNotify }} = require('{ROOT / "gaokao-proxy" / "lib" / "wechat-virtual-pay.js"}')

                    const notify = parseVirtualPayGoodsNotify(`
                      <xml>
                        <ToUserName><![CDATA[gh_xxx]]></ToUserName>
                        <FromUserName><![CDATA[official_openid]]></FromUserName>
                        <CreateTime>1778740000</CreateTime>
                        <MsgType><![CDATA[event]]></MsgType>
                        <Event><![CDATA[xpay_goods_deliver_notify]]></Event>
                        <OpenId><![CDATA[user_openid]]></OpenId>
                        <OutTradeNo><![CDATA[GK1778740000000abc]]></OutTradeNo>
                        <Env>0</Env>
                        <WeChatPayInfo>
                          <MchOrderNo><![CDATA[mch_order_1]]></MchOrderNo>
                          <TransactionId><![CDATA[transaction_1]]></TransactionId>
                          <PaidTime>1778740001</PaidTime>
                        </WeChatPayInfo>
                        <GoodsInfo>
                          <ProductId><![CDATA[vip_report_1990]]></ProductId>
                          <Quantity>1</Quantity>
                          <OrigPrice>1990</OrigPrice>
                          <ActualPrice>1990</ActualPrice>
                          <Attach><![CDATA[{{"orderId":"ord_1"}}]]></Attach>
                        </GoodsInfo>
                      </xml>
                    `)

                    assert.equal(notify.outTradeNo, 'GK1778740000000abc')
                    assert.equal(notify.transactionId, 'transaction_1')
                    assert.equal(notify.productId, 'vip_report_1990')
                    assert.equal(notify.amountCents, 1990)
                """),
                encoding="utf-8",
            )
            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_payment_notify_logs_order_context_on_failures(self):
        text = self.read("gaokao-proxy/server.js")

        for snippet in [
            "notifyLogContext",
            "outTradeNo",
            "transactionId",
            "productId",
            "errorCode: err.code",
            "WECHAT_VIRTUAL_PAY_NOTIFY_FAILED",
        ]:
            self.assertIn(snippet, text)

    def test_report_generation_membership_gate_is_bypassed_for_free_1_3_access(self):
        text = self.read("gaokao-proxy/server.js")

        self.assertIn("FREE_DEEP_REPORTS_ENABLED", text)
        self.assertIn("requireMembershipForReports", text)
        self.assertIn("if (FREE_DEEP_REPORTS_ENABLED)", text)
        self.assertIn("free_deep_reports_1_3", text)
        self.assertIn("MEMBERSHIP_REQUIRED", text)
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

    def test_wechat_pay_notify_rejects_invalid_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            pubkey_path = Path(tmp) / "wechatpay_public_key.pem"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const crypto = require('node:crypto')
                    const {{ verifyWechatPayNotifySignature }} = require('{ROOT / "gaokao-proxy" / "lib" / "wechat-pay.js"}')

                    const {{ publicKey }} = crypto.generateKeyPairSync('rsa', {{
                      modulusLength: 2048,
                      publicKeyEncoding: {{ type: 'spki', format: 'pem' }},
                      privateKeyEncoding: {{ type: 'pkcs8', format: 'pem' }},
                    }})
                    require('node:fs').writeFileSync('{pubkey_path}', publicKey)

                    assert.throws(
                      () => verifyWechatPayNotifySignature({{
                        headers: {{
                          'wechatpay-timestamp': '1778740000',
                          'wechatpay-nonce': 'nonce123',
                          'wechatpay-signature': Buffer.from('invalid-signature').toString('base64'),
                        }},
                        rawBody: '{{"id":"notify-id"}}',
                        env: {{ WECHAT_PAY_PUBLIC_KEY_PATH: '{pubkey_path}' }},
                      }}),
                      /签名校验失败/
                    )
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
            "PAYMENT_ORDER_TTL_MS",
            "WECHAT_SECRET",
            "WECHAT_MESSAGE_TOKEN",
            "WECHAT_VIRTUAL_PAY_ENV",
            "WECHAT_VIRTUAL_PAY_OFFER_ID",
            "WECHAT_VIRTUAL_PAY_PRODUCT_ID",
            "WECHAT_VIRTUAL_PAY_MODE",
            "WECHAT_VIRTUAL_PAY_SANDBOX_APP_KEY",
            "WECHAT_VIRTUAL_PAY_APP_KEY",
        ]:
            self.assertIn(key, text)


if __name__ == "__main__":
    unittest.main()
