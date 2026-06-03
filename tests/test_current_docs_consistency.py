import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CurrentDocsConsistencyTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_current_docs_describe_two_assessment_report_contract(self):
        current_docs = [
            "docs/README.md",
            "docs/deployment/current-live-chain.md",
            "docs/architecture-and-apis.md",
            "docs/miniprogram-call-chain-visual.md",
            "docs/deployment/mvp-content-launch-plan.md",
            "docs/deployment/release-readiness-and-iteration-methodology.md",
            "docs/deployment/customer-support-playbook.md",
            "docs/deployment/payment-followup-workplan.md",
            "docs/deployment/p0-user-value-launch-plan.md",
        ]

        forbidden = [
            "三项测评",
            "3 项测评",
            "全部 3 项测评",
            "问卷 >=22",
            "问卷>=22",
            "questionnaire completion",
            "fetchMajorReports(questionnaire)",
            "questionnaire / MBTI / Holland",
        ]

        for relpath in current_docs:
            text = self.read(relpath)
            for snippet in forbidden:
                with self.subTest(relpath=relpath, snippet=snippet):
                    self.assertNotIn(snippet, text)

        readme = self.read("docs/README.md")
        self.assertIn("当前报告生成前置测评：只要求性格类型定位", readme)
        self.assertIn("五环问卷入口已关闭", readme)

        api_doc = self.read("docs/architecture-and-apis.md")
        self.assertIn("五环问卷入口已关闭", api_doc)
        self.assertIn("请先完成性格测试和霍兰德职业兴趣测试后再生成综合报告", api_doc)


if __name__ == "__main__":
    unittest.main()
