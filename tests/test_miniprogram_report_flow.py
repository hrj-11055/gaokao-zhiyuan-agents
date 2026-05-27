import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MiniprogramReportFlowTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_home_step4_done_requires_real_report_url(self):
        progress = self.read("gaokao-miniprogram/src/composables/useHomeProgress.js")
        index = self.read("gaokao-miniprogram/src/pages/index/index.vue")

        self.assertIn("loadReport", progress)
        self.assertIn("reportDone", progress)
        self.assertIn("Boolean(report.value?.url)", progress)
        self.assertIn("if (reportDone.value) return StepStatus.DONE", progress)
        self.assertNotIn("if (membershipStore.isActive) return StepStatus.DONE", index)
        self.assertIn("会员特权已解锁，一键生成", index)

    def test_report_generation_submits_stored_assessments_and_bearer_token(self):
        page = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        api = self.read("gaokao-miniprogram/src/api/report.js")

        for snippet in [
            "const questionnaire = loadQuestionnaire()",
            "const assessments = loadAssessments()",
            "const chatHistory = loadHistory()",
            "questionnaire: questionnaireAnswers",
            "assessments,",
            "conversationId: chatHistory.conversationId || ''",
            "sessionToken: membershipStore.sessionToken",
        ]:
            self.assertIn(snippet, page)

        self.assertIn("Authorization: `Bearer ${sessionToken}`", api)
        self.assertIn("path: '/api/report/generate'", api)

    def test_major_insights_extractor_reads_courses_abilities_and_salary(self):
        script = textwrap.dedent(f"""
            const assert = require('node:assert/strict')
            const {{ buildMajorInsight }} = require('{ROOT / "gaokao-proxy" / "lib" / "major-insights.js"}')

            const insight = buildMajorInsight({{
              code: '071201',
              name: '统计学',
              category: '理学',
              data: {{
                layer1_overview: {{ summary: '数据时代的硬通货专业。' }},
                layer2_core: {{
                  employment: {{
                    starting_salary: '7000-9000 元/月',
                    salary_5yr: '15000-25000 元/月'
                  }}
                }},
                full_raw_content: '核心可迁移能力：量化分析思维、数据建模能力、概率判断\\n课程表里排满了数学分析、概率论、数理统计。'
              }}
            }}, '统计学')

            assert.equal(insight.source, 'database')
            assert.equal(insight.courses.includes('数学分析'), true)
            assert.equal(insight.abilities.includes('量化分析思维'), true)
            assert.equal(insight.salarySummary.includes('起薪 7000-9000 元/月'), true)
        """)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "major-insight-test.js"
            path.write_text(script, encoding="utf-8")
            subprocess.run(["node", str(path)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
