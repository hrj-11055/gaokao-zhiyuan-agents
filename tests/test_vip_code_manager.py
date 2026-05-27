import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "gaokao-proxy" / "scripts" / "manage-vip-codes.js"
STORE = ROOT / "gaokao-proxy" / "lib" / "commerce-store.js"


class VipCodeManagerTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            ["node", str(SCRIPT), *args],
            check=True,
            text=True,
            capture_output=True,
            cwd=ROOT,
        ).stdout

    def test_cli_generates_lists_disables_and_redeems_database_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "commerce.sqlite")
            generated = json.loads(self.run_script(
                "generate",
                "--db", db_path,
                "--count", "2",
                "--prefix", "FG",
                "--max-uses", "1",
                "--expires-days", "30",
                "--json",
            ))

            self.assertEqual(len(generated), 2)
            code = generated[0]["code"]
            self.assertRegex(code, r"^FG-\d{6}-[A-Z2-9]{6}$")
            self.assertEqual(generated[0]["maxUses"], 1)

            listed = json.loads(self.run_script("list", "--db", db_path, "--json"))
            self.assertEqual(len(listed), 2)
            self.assertIn(code, {item["code"] for item in listed})

            shown = json.loads(self.run_script("show", "--db", db_path, "--code", code, "--json"))
            self.assertEqual(shown["code"], code)
            self.assertEqual(shown["redemptions"], [])

            subprocess.run(
                [
                    "node",
                    "-e",
                    textwrap.dedent(f"""
                        const assert = require('node:assert/strict')
                        const {{ createCommerceStore }} = require('{STORE}')
                        const store = createCommerceStore({{
                          dbPath: '{db_path}',
                          now: () => 1778740000000,
                          idFactory: (prefix) => `${{prefix}}_test_${{Math.random().toString(36).slice(2, 8)}}`,
                          vipCodes: [],
                        }})
                        try {{
                          const first = store.upsertWechatUser({{ openid: 'openid-vip-manager-1' }})
                          const second = store.upsertWechatUser({{ openid: 'openid-vip-manager-2' }})
                          const result = store.redeemVipCode(first.userId, '{code}')
                          assert.equal(result.membership.status, 'active')
                          assert.equal(result.membership.source, 'vip_code')
                          assert.throws(() => store.redeemVipCode(second.userId, '{code}'), /已用完/)
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

            redeemed = json.loads(self.run_script("show", "--db", db_path, "--code", code, "--json"))
            self.assertEqual(redeemed["usedCount"], 1)
            self.assertEqual(len(redeemed["redemptions"]), 1)

            disabled = json.loads(self.run_script("disable", "--db", db_path, "--code", code, "--json"))
            self.assertEqual(disabled["status"], "inactive")


if __name__ == "__main__":
    unittest.main()
