import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIGGER_SOURCE = (
    ROOT
    / "gaokao-miniprogram"
    / "src"
    / "pages"
    / "chat"
    / "personalityAssessmentGuide.js"
)
STORAGE_SOURCE = ROOT / "gaokao-miniprogram" / "src" / "utils" / "storage.js"
CHAT_SOURCE = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue"
COMPONENT_SOURCE = (
    ROOT / "gaokao-miniprogram" / "src" / "components" / "PersonalityAssessmentGuide.vue"
)


class ChatPersonalityAssessmentGuideTests(unittest.TestCase):
    def run_module_test(self, source_path: Path, imports: str, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "module.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(
                    f"""
                    import assert from 'node:assert/strict'
                    {imports}

                    {test_body}
                    """
                ),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def run_trigger_test(self, test_body: str):
        self.run_module_test(
            TRIGGER_SOURCE,
            """
            import {
              findPersonalityGuideMessageIndex,
              getVisibleAnswerLength
            } from './module.mjs'

            function buildRounds(answerLengths, options = {}) {
              const messages = []
              answerLengths.forEach((answerLength, index) => {
                const round = index + 1
                messages.push({ role: 'user', content: `问题 ${round}` })
                messages.push({
                  role: 'ai',
                  content: '答'.repeat(answerLength),
                  truncated: options.truncatedRounds?.includes(round) || false,
                  error: options.errorRounds?.includes(round) || false
                })
              })
              return messages
            }
            """,
            test_body,
        )

    def test_trigger_selects_first_qualified_complete_ai_reply(self):
        self.run_trigger_test(
            """
            assert.equal(findPersonalityGuideMessageIndex(buildRounds([600, 600])), -1)
            assert.equal(findPersonalityGuideMessageIndex(buildRounds([120, 120, 500])), 5)
            assert.equal(findPersonalityGuideMessageIndex(buildRounds([120, 120, 120, 120, 120])), -1)
            assert.equal(findPersonalityGuideMessageIndex(buildRounds([120, 120, 120, 120, 120, 120])), 11)
            assert.equal(
              findPersonalityGuideMessageIndex(
                buildRounds([120, 120, 600], { truncatedRounds: [2] })
              ),
              -1
            )
            assert.equal(
              findPersonalityGuideMessageIndex(
                buildRounds([120, 120, 600, 120, 120, 120], { truncatedRounds: [3] })
              ),
              -1
            )
            assert.equal(
              findPersonalityGuideMessageIndex(
                buildRounds([120, 120, 600, 120, 120, 120, 120], { truncatedRounds: [3] })
              ),
              13
            )
            assert.equal(
              findPersonalityGuideMessageIndex(
                buildRounds([120, 120, 600, 600, 600, 600, 600])
              ),
              5
            )
            """
        )

    def test_trigger_uses_visible_text_length_and_skips_failed_or_empty_replies(self):
        self.run_trigger_test(
            """
            assert.equal(getVisibleAnswerLength('## 标题\\n- **内容**\\n[链接](https://example.com)'), 6)
            assert.equal(
              findPersonalityGuideMessageIndex([
                ...buildRounds([120, 120]),
                { role: 'user', content: '问题 3' },
                { role: 'ai', content: `**${'答 '.repeat(499)}**` },
                { role: 'user', content: '问题 4' },
                { role: 'ai', content: '' },
                { role: 'user', content: '问题 5' },
                { role: 'ai', content: '答'.repeat(600), error: true }
              ]),
              -1
            )
            """
        )

    def test_dismissal_persists_independently_from_chat_history(self):
        self.run_module_test(
            STORAGE_SOURCE,
            """
            import {
              clearAllLocalData,
              clearHistory,
              dismissPersonalityGuide,
              isPersonalityGuideDismissed
            } from './module.mjs'
            """,
            """
            const storage = new Map()
            globalThis.uni = {
              getStorageSync(key) {
                return storage.get(key) ?? ''
              },
              setStorageSync(key, value) {
                storage.set(key, value)
              },
              removeStorageSync(key) {
                storage.delete(key)
              }
            }

            assert.equal(isPersonalityGuideDismissed(), false)
            dismissPersonalityGuide()
            assert.equal(isPersonalityGuideDismissed(), true)
            clearHistory()
            assert.equal(isPersonalityGuideDismissed(), true)
            clearAllLocalData()
            assert.equal(isPersonalityGuideDismissed(), false)
            """,
        )

    def test_guide_component_exposes_approved_copy_and_actions(self):
        text = COMPONENT_SOURCE.read_text(encoding="utf-8")

        self.assertIn("还不确定自己适合什么方向？", text)
        self.assertIn("做一份约 3 分钟的性格测试", text)
        self.assertIn("去做性格测试", text)
        self.assertIn("继续性格测试", text)
        self.assertIn("稍后再说", text)
        self.assertIn("defineProps", text)
        self.assertIn("started", text)
        self.assertIn("defineEmits(['start', 'dismiss'])", text)

    def test_chat_renders_one_guide_at_the_selected_historical_reply(self):
        text = CHAT_SOURCE.read_text(encoding="utf-8")

        self.assertIn("import PersonalityAssessmentGuide", text)
        self.assertIn("findPersonalityGuideMessageIndex", text)
        self.assertIn("isPersonalityGuideDismissed", text)
        self.assertIn("dismissPersonalityGuide", text)
        self.assertIn('v-if="index === personalityGuideMessageIndex"', text)
        self.assertIn(':started="hasStartedPersonalityTest"', text)
        self.assertIn('@start="goPersonalityTest"', text)
        self.assertIn('@dismiss="dismissPersonalityGuideCard"', text)
        self.assertIn("!isStreaming.value", text)
        self.assertIn("assessments.value.mbti.completed", text)
        self.assertIn("personalityGuideDismissed.value", text)
        self.assertIn("uni.navigateTo({ url: '/pages/mbti/mbti' })", text)
        self.assertNotIn("shouldShowPersonalityNextStep", text)


if __name__ == "__main__":
    unittest.main()
