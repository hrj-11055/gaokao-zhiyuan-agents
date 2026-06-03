import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "gaokao-proxy" / "scripts" / "commerce-ops.js"
STORE = ROOT / "gaokao-proxy" / "lib" / "commerce-store.js"


class CommerceOpsCliTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            ["node", str(SCRIPT), *args],
            check=True,
            text=True,
            capture_output=True,
            cwd=ROOT,
        ).stdout

    def seed_paid_order(self, db_path):
        seed = subprocess.run(
            [
                "node",
                "-e",
                textwrap.dedent(f"""
                    const {{ createCommerceStore }} = require('{STORE}')
                    let nowValue = 1778740000000
                    let idValue = 0
                    const store = createCommerceStore({{
                      dbPath: '{db_path}',
                      now: () => nowValue++,
                      idFactory: (prefix) => `${{prefix}}_ops_${{++idValue}}`,
                      priceCents: 1990,
                    }})
                    try {{
                      const user = store.upsertWechatUser({{ openid: 'openid-ops-paid' }})
                      const order = store.createPaymentOrder(user.userId)
                      store.attachPrepayId(order.orderId, 'prepay-ops-1')
                      const paid = store.markOrderPaid(order.outTradeNo, 'wx-transaction-ops-1', {{
                        resource: {{ amount: {{ total: 1990 }} }},
                      }})
                      console.log(JSON.stringify({{ user, order: paid }}))
                    }} finally {{
                      store.close()
                    }}
                """),
            ],
            check=True,
            text=True,
            capture_output=True,
            cwd=ROOT,
        ).stdout
        return json.loads(seed)

    def test_lookup_finds_status_by_user_openid_order_and_out_trade_no(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "commerce.sqlite")
            seeded = self.seed_paid_order(db_path)

            for flag, value in [
                ("--user-id", seeded["user"]["userId"]),
                ("--openid", seeded["user"]["openid"]),
                ("--order-id", seeded["order"]["orderId"]),
                ("--out-trade-no", seeded["order"]["outTradeNo"]),
            ]:
                output = json.loads(self.run_script("lookup", "--db", db_path, flag, value, "--json"))
                self.assertEqual(output["user"]["userId"], seeded["user"]["userId"])
                self.assertEqual(output["user"]["openid"], "openid-ops-paid")
                self.assertEqual(output["membership"]["status"], "active")
                self.assertEqual(output["membership"]["source"], "payment")
                self.assertEqual(output["orders"][0]["status"], "paid")
                self.assertEqual(output["orders"][0]["transactionId"], "wx-transaction-ops-1")

    def test_activate_membership_by_openid_records_support_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "commerce.sqlite")
            subprocess.run(
                [
                    "node",
                    "-e",
                    textwrap.dedent(f"""
                        const {{ createCommerceStore }} = require('{STORE}')
                        const store = createCommerceStore({{ dbPath: '{db_path}', now: () => 1778740000000 }})
                        try {{
                          store.upsertWechatUser({{ openid: 'openid-ops-manual' }})
                        }} finally {{
                          store.close()
                        }}
                    """),
                ],
                check=True,
                text=True,
                capture_output=True,
                cwd=ROOT,
            )

            activated = json.loads(self.run_script(
                "activate-membership",
                "--db", db_path,
                "--openid", "openid-ops-manual",
                "--operator", "support-a",
                "--reason", "paid order manually verified",
                "--json",
            ))
            self.assertEqual(activated["membership"]["status"], "active")
            self.assertEqual(activated["membership"]["source"], "support_manual")
            self.assertEqual(activated["operation"]["type"], "activate_membership")

            lookup = json.loads(self.run_script("lookup", "--db", db_path, "--openid", "openid-ops-manual", "--json"))
            self.assertEqual(lookup["membership"]["status"], "active")
            self.assertEqual(lookup["supportOperations"][0]["operator"], "support-a")
            self.assertIn("paid order manually verified", lookup["supportOperations"][0]["reason"])

    def test_issue_compensation_code_creates_one_use_code_and_operation_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "commerce.sqlite")
            code = json.loads(self.run_script(
                "issue-code",
                "--db", db_path,
                "--recipient", "openid-ops-comp",
                "--operator", "support-b",
                "--reason", "payment callback delayed",
                "--json",
            ))

            self.assertRegex(code["code"], r"^COMP-\d{6}-[A-Z2-9]{6}$")
            self.assertEqual(code["status"], "active")
            self.assertEqual(code["maxUses"], 1)
            self.assertEqual(code["operation"]["type"], "issue_compensation_code")

            shown = json.loads(subprocess.run(
                [
                    "node",
                    str(ROOT / "gaokao-proxy" / "scripts" / "manage-vip-codes.js"),
                    "show",
                    "--db", db_path,
                    "--code", code["code"],
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                cwd=ROOT,
            ).stdout)
            self.assertEqual(shown["code"], code["code"])
            self.assertEqual(shown["maxUses"], 1)


if __name__ == "__main__":
    unittest.main()
