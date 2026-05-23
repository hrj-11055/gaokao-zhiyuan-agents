import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QuestionnaireFlowTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def run_storage_node_test(self, test_body):
        source = self.read("gaokao-miniprogram/src/utils/storage.js")
        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "storage.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(source, encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(f"""
                    import assert from 'node:assert/strict'
                    import {{ loadQuestionnaire, saveQuestionnaire }} from './storage.mjs'

                    const storage = new Map()
                    globalThis.uni = {{
                      getStorageSync(key) {{ return storage.get(key) || '' }},
                      setStorageSync(key, value) {{ storage.set(key, value) }},
                      removeStorageSync(key) {{ storage.delete(key) }}
                    }}
                    Date.now = () => 1710000000000

                    {test_body}
                """),
                encoding="utf-8",
            )
            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_rank_position_question_is_removed(self):
        text = self.read("gaokao-miniprogram/src/pages/questionnaire/questionnaire.vue")

        self.assertNotIn("你的成绩在班级大概位置", text)
        self.assertNotIn("前 10%", text)
        self.assertNotIn("前 30%", text)
        self.assertNotIn("q9", text)

    def test_single_choice_auto_advances_after_selection(self):
        text = self.read("gaokao-miniprogram/src/pages/questionnaire/questionnaire.vue")

        single_branch = re.search(
            r"if \(type === 'single'\) \{(?P<body>.*?)\n  \}",
            text,
            flags=re.S,
        )
        self.assertIsNotNone(single_branch)
        self.assertIn("saveQuestionnaire(answers.value)", single_branch.group("body"))
        self.assertIn("setTimeout(() => { currentIndex.value++ }", single_branch.group("body"))

    def test_finish_returns_to_assessments_tab_without_confirmation_modal(self):
        text = self.read("gaokao-miniprogram/src/pages/questionnaire/questionnaire.vue")

        self.assertNotIn("uni.showModal", text)
        self.assertIn("uni.switchTab({ url: '/pages/assessments/assessments' })", text)

    def test_questionnaire_next_requires_current_answer(self):
        text = self.read("gaokao-miniprogram/src/pages/questionnaire/questionnaire.vue")

        self.assertIn("const isCurrentAnswered = computed(() => isAnswered(currentQ.value))", text)
        self.assertIn(":class=\"{ disabled: currentIndex === 0 }\"", text)
        self.assertIn(":class=\"{ disabled: !isCurrentAnswered }\"", text)
        self.assertIn("title: '请先选择本题答案'", text)
        next_body = re.search(r"function next\(\) \{(?P<body>.*?)\n\}", text, flags=re.S)
        self.assertIsNotNone(next_body)
        self.assertIn("if (!isCurrentAnswered.value)", next_body.group("body"))

    def test_mbti_and_holland_do_not_allow_unanswered_submission(self):
        expected = {
            "gaokao-miniprogram/src/pages/mbti/mbti.vue": [
                "const isCurrentAnswered = computed(() => answers.value[currentQuestion.value.id] !== undefined)",
                ":class=\"{ disabled: !isCurrentAnswered }\"",
                "title: '请先选择本题答案'",
                "const firstUnansweredIndex = activeQuestions.value.findIndex",
            ],
            "gaokao-miniprogram/src/pages/holland/holland.vue": [
                "const isCurrentAnswered = computed(() => answers.value[currentQuestion.value.id] !== undefined)",
                ":class=\"{ disabled: !isCurrentAnswered }\"",
                "title: '请先选择本题答案'",
                "const firstUnansweredIndex = activeQuestions.value.findIndex",
            ],
        }

        for relpath, snippets in expected.items():
            text = self.read(relpath)
            self.assertNotIn("确定要提交吗", text)
            for snippet in snippets:
                with self.subTest(relpath=relpath, snippet=snippet):
                    self.assertIn(snippet, text)

    def test_questionnaire_completion_threshold_is_21_after_question_removal(self):
        expected_snippets = {
            "gaokao-miniprogram/src/utils/storage.js": [
                "export const QUESTIONNAIRE_REQUIRED_COUNT = 21",
                "completedCount >= QUESTIONNAIRE_REQUIRED_COUNT",
            ],
            "gaokao-miniprogram/src/stores/assessment.js": [
                "const QUESTIONNAIRE_REQUIRED_COUNT = 21",
                "completedCount >= QUESTIONNAIRE_REQUIRED_COUNT",
            ],
            "gaokao-miniprogram/src/pages/index/index.vue": [
                "QUESTIONNAIRE_REQUIRED_COUNT",
                "`已答 ${questionnaire.completedCount} / ${QUESTIONNAIRE_REQUIRED_COUNT} 题`",
            ],
            "gaokao-miniprogram/src/pages/profile/profile.vue": [
                "QUESTIONNAIRE_REQUIRED_COUNT",
                "`已记录 ${questionnaire.value.completedCount} / ${QUESTIONNAIRE_REQUIRED_COUNT} 题`",
            ],
            "gaokao-miniprogram/src/pages/assessments/assessments.vue": [
                "QUESTIONNAIRE_REQUIRED_COUNT",
                "21 维全面学习风格",
            ],
            "gaokao-proxy/server.js": [
                "const QUESTIONNAIRE_REQUIRED_COUNT = 21",
                "questionCount < QUESTIONNAIRE_REQUIRED_COUNT",
            ],
        }

        for relpath, snippets in expected_snippets.items():
            text = self.read(relpath)
            for snippet in snippets:
                with self.subTest(relpath=relpath, snippet=snippet):
                    self.assertIn(snippet, text)

    def test_legacy_removed_question_is_not_counted_from_storage(self):
        self.run_storage_node_test("""
            uni.setStorageSync('questionnaire', JSON.stringify({
              answers: { q1: '先理解原理，再做题', q2: '先跳过，找会的做', q9: '前 10%' },
              completedCount: 22,
              updatedAt: 1700000000000
            }))

            const loaded = loadQuestionnaire()
            assert.deepEqual(loaded.answers, {
              q1: '先理解原理，再做题',
              q2: '先跳过，找会的做'
            })
            assert.equal(loaded.completedCount, 2)

            saveQuestionnaire({ q1: '先理解原理，再做题', q9: '前 30%', q10: '企业职员' })
            const saved = loadQuestionnaire()
            assert.deepEqual(saved.answers, {
              q1: '先理解原理，再做题',
              q10: '企业职员'
            })
            assert.equal(saved.completedCount, 2)
        """)


if __name__ == "__main__":
    unittest.main()
