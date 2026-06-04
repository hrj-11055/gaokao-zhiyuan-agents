import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_MODULE = ROOT / "gaokao-miniprogram" / "src" / "utils" / "profile-identity.js"
PROFILE_PAGE = ROOT / "gaokao-miniprogram" / "src" / "pages" / "profile" / "profile.vue"


class ProfileIdentityTests(unittest.TestCase):
    def run_identity_test(self, test_body: str):
        source = IDENTITY_MODULE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "profile-identity.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(source, encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(f"""
                    import assert from 'node:assert/strict'
                    import {{
                      PROFILE_ANIMALS,
                      PROFILE_IDENTITY_KEY,
                      PROFILE_PERSONALITIES,
                      generateProfileIdentity,
                      getOrCreateProfileIdentity,
                    }} from './profile-identity.mjs'

                    function sequenceRandom(values) {{
                      let index = 0
                      return () => {{
                        if (index >= values.length) throw new Error('random called too many times')
                        return values[index++]
                      }}
                    }}

                    {test_body}
                """),
                encoding="utf-8",
            )
            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_generation_randomizes_personality_and_animal_independently(self):
        self.run_identity_test(
            """
            const generated = generateProfileIdentity(sequenceRandom([0.999999, 0]))

            assert.equal(generated.personality, PROFILE_PERSONALITIES.at(-1))
            assert.equal(generated.animal, PROFILE_ANIMALS[0].key)
            assert.equal(generated.nickname, `${PROFILE_PERSONALITIES.at(-1)}的${PROFILE_ANIMALS[0].label}`)
            assert.equal(generated.avatar, PROFILE_ANIMALS[0].avatar)
            """,
        )

    def test_identity_is_persisted_and_invalid_storage_is_regenerated(self):
        self.run_identity_test(
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

            const first = getOrCreateProfileIdentity(sequenceRandom([0, 0]))
            assert.deepEqual(JSON.parse(storage.get(PROFILE_IDENTITY_KEY)), {
              personality: first.personality,
              animal: first.animal
            })

            const second = getOrCreateProfileIdentity(() => {
              throw new Error('persisted identity should not randomize again')
            })
            assert.deepEqual(second, first)

            storage.set(PROFILE_IDENTITY_KEY, JSON.stringify({
              personality: '不存在',
              animal: 'dragon'
            }))
            const repaired = getOrCreateProfileIdentity(sequenceRandom([0.5, 0.5]))
            assert.notEqual(repaired.personality, '不存在')
            assert.notEqual(repaired.animal, 'dragon')

            storage.set(PROFILE_IDENTITY_KEY, '{broken json')
            const repairedJson = getOrCreateProfileIdentity(sequenceRandom([0.25, 0.25]))
            assert.equal(Boolean(repairedJson.nickname), true)
            assert.equal(Boolean(repairedJson.avatar), true)
            """,
        )

    def test_profile_page_renders_persistent_identity(self):
        page = PROFILE_PAGE.read_text(encoding="utf-8")

        self.assertIn("getOrCreateProfileIdentity", page)
        self.assertIn(':src="profileIdentity.avatar"', page)
        self.assertIn("{{ profileIdentity.nickname }}", page)
        self.assertNotIn('<text class="avatar-text">峰</text>', page)
        self.assertNotIn('<text class="user-name">志愿同学</text>', page)

    def test_profile_identity_catalog_assets_exist(self):
        assets_dir = ROOT / "gaokao-miniprogram" / "src" / "static" / "avatars"
        expected_assets = {
            "panda.png",
            "penguin.png",
            "otter.png",
            "fox.png",
            "rabbit.png",
            "owl.png",
            "bear.png",
            "shiba.png",
        }

        self.assertEqual({path.name for path in assets_dir.glob("*.png")}, expected_assets)
