import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProfileStorageAndInputsTests(unittest.TestCase):
    def run_node_test(self, module_source: str, imports: str, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "module.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(module_source, encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(f"""
                    import assert from 'node:assert/strict'
                    {imports}

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_user_profile_is_saved_loaded_and_checked(self):
        source = (ROOT / "gaokao-miniprogram" / "src" / "utils" / "storage.js").read_text(encoding="utf-8")

        self.run_node_test(
            source,
            "import { saveUserProfile, loadUserProfile, isProfileComplete, buildProfileInputs } from './module.mjs'",
            """
            const storage = new Map()
            globalThis.uni = {
              getStorageSync(key) {
                return storage.get(key) || ''
              },
              setStorageSync(key, value) {
                storage.set(key, value)
              }
            }
            Date.now = () => 1710000000000

            assert.equal(isProfileComplete({ province: '广东', category: '物理类', score: 600 }), true)
            assert.equal(isProfileComplete({ province: '广东', category: '物理类' }), false)

            saveUserProfile({
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000'
            })

            assert.deepEqual(loadUserProfile(), {
              province: '广东',
              category: '物理类',
              score: 600,
              rank: 32000,
              updatedAt: 1710000000000
            })
            assert.deepEqual(buildProfileInputs(loadUserProfile()), {
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000'
            })
            """.replace("1710000000000", str(1710000000000)),
        )

    def test_dify_stream_request_includes_profile_inputs(self):
        source = (ROOT / "gaokao-miniprogram" / "src" / "api" / "dify.js").read_text(encoding="utf-8")
        source = source.replace(
            "const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001'",
            "const API_BASE = 'http://localhost:3001'",
        )

        self.run_node_test(
            source,
            "import { sendMessageStream } from './module.mjs'",
            """
            let requestPayload = null
            globalThis.uni = {
              request(options) {
                requestPayload = options.data
                return {
                  onChunkReceived() {},
                  abort() {}
                }
              }
            }

            sendMessageStream({
              query: '帮我推荐学校',
              conversationId: '',
              user: 'user_1',
              inputs: { province: '广东', category: '物理类', score: '600', rank: '32000' },
              onChunk() {},
              onEnd() {},
              onError() {}
            })

            assert.deepEqual(requestPayload.inputs, {
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000'
            })
            """,
        )

    def test_proxy_forwards_chat_inputs_to_dify(self):
        text = (ROOT / "gaokao-proxy" / "server.js").read_text(encoding="utf-8")

        self.assertIn("inputs = {}", text)
        self.assertIn("inputs,", text)


if __name__ == "__main__":
    unittest.main()
