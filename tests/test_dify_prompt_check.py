import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "data" / "dify_prompt_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("dify_prompt_check", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DifyPromptCheckTests(unittest.TestCase):
    def test_prompt_1_is_the_huanong_admission_question(self):
        module = load_module()

        self.assertEqual(
            "我广东省 580 分可以上华南农业大学吗？",
            module.TEST_PROMPTS[0]["query"],
        )

    def test_evaluator_accepts_specific_cautious_huanong_answer(self):
        module = load_module()
        answer = (
            "广东 580 分问华南农业大学，结论是：可以重点考虑，但不能说一定稳。"
            "你还没说物理类还是历史类，也没给位次，所以要按 2024 年广东录取数据"
            "再核一次。这个分数普通专业机会比较大，热门专业要看专业组和调剂，"
            "建议按冲稳保拆开填。"
        )

        result = module.evaluate_answer(module.TEST_PROMPTS[0], answer)

        self.assertEqual([], result["failures"])
        self.assertEqual("pass", result["status"])

    def test_evaluator_rejects_generic_overconfident_answer(self):
        module = load_module()

        result = module.evaluate_answer(
            module.TEST_PROMPTS[0],
            "580分肯定能上，放心报就行。",
        )

        self.assertEqual("fail", result["status"])
        self.assertIn("missing_school", result["failures"])
        self.assertIn("overconfident", result["failures"])

    def test_evaluator_rejects_followup_only_answer(self):
        module = load_module()

        result = module.evaluate_answer(
            module.TEST_PROMPTS[0],
            (
                "580分在广东，物理类还是历史类？这俩差别大了去了。"
                "你先告诉我选科，我才能给你精准定位。"
                "另外，家里经济情况怎么样？这决定了我推荐华南农大哪些专业。"
            ),
        )

        self.assertEqual("fail", result["status"])
        self.assertIn("missing_preliminary_conclusion", result["failures"])

    def test_evaluator_accepts_negated_confidence_language(self):
        module = load_module()
        answer = (
            "580分在广东，物理类还是历史类？这个不说，我没办法给你准话。"
            "但既然你问了华南农业大学，我默认你是物理类考生。"
            "按去年数据，这个位次报华南农业大学热门专业是冲一冲，"
            "不是稳上的，专业组和位次必须核清楚。建议把华农放前面冲，"
            "再用广东工业大学等学校做稳保，避免被调剂。"
        )

        result = module.evaluate_answer(module.TEST_PROMPTS[0], answer)

        self.assertNotIn("missing_uncertainty_guard", result["failures"])
        self.assertNotIn("overconfident", result["failures"])
        self.assertEqual("pass", result["status"])

    def test_evaluator_recognizes_risk_guard_but_flags_later_certainty(self):
        module = load_module()
        answer = (
            "580分在广东，想上华南农业大学有戏，但得看专业，不能闭着眼睛冲。"
            "物理类热门专业风险大，要看专业组和位次，建议按冲稳保填志愿。"
            "不过广东工业大学计算机你这个分数稳上。"
        )

        result = module.evaluate_answer(module.TEST_PROMPTS[0], answer)

        self.assertNotIn("missing_uncertainty_guard", result["failures"])
        self.assertIn("overconfident", result["failures"])


if __name__ == "__main__":
    unittest.main()
