import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportQualityImprovementTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def run_node_test(self, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const deep = require('{ROOT / "gaokao-proxy" / "lib" / "deep-report-pdf.js"}')

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_prompt_requires_parent_readable_action_plan_and_less_ai_tone(self):
        prompt = self.read("gaokao-proxy/lib/prompts/report-template.js")

        for snippet in [
            "家长先看结论",
            "志愿执行清单",
            "每条建议必须包含：动作、原因、核验材料",
            "综合报告正文总字数不少于 4500 字",
            "每个 Tab 至少 650 字",
            "字体可以适当小一些",
            "不要使用“AI 总评”",
            "少用空泛形容词",
        ]:
            self.assertIn(snippet, prompt)

    def test_deep_report_pdf_has_summary_cards_toc_page_breaks_and_highlights(self):
        self.run_node_test(r"""
            const html = deep.buildDeepReportHtml({
              type: 'major',
              report: {
                code: '080901',
                name: '计算机科学与技术',
                word_count: 6200,
                category: '工学',
                data: {
                  layer1_overview: {
                    recommendation_level: 'green',
                    weighted_score: 86,
                    summary: '适合数学基础好、能接受持续学习的学生。'
                  },
                  layer2_core: {
                    summary: '重点看课程强度、就业城市和保研条件。'
                  },
                  layer3_detail: {
                    career: {
                      title: '就业路径',
                      raw_content: '# 就业路径\n- 先核验学校培养方案\n- 对比近三年就业质量报告'
                    }
                  }
                }
              }
            })

            assert.equal(html.includes('摘要卡片'), true)
            assert.equal(html.includes('重点结论'), true)
            assert.equal(html.includes('目录'), true)
            assert.equal(html.includes('class="toc"'), true)
            assert.equal(html.includes('page-break-before'), true)
            assert.equal(html.includes('highlight-box'), true)
            assert.equal(html.includes('font-size: 14px'), true)
            assert.equal(html.includes('font-size: 26px'), true)
        """)

    def test_miniprogram_deep_report_cards_expose_actionable_summary(self):
        page = self.read("gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue")

        for snippet in [
            "summary-card-row",
            "decisionBadges",
            "summaryTakeaways",
            "重点摘要",
            "行动建议",
        ]:
            self.assertIn(snippet, page)

    def test_report_generation_failure_keeps_server_draft_and_client_message(self):
        server = self.read("gaokao-proxy/server.js")
        builder = self.read("gaokao-proxy/lib/report-builder.js")
        page = self.read("gaokao-miniprogram/src/pages/report/report.vue")

        for snippet in [
            "saveReportDraft",
            "draftId",
            "REPORT_DRAFTS_DIR",
        ]:
            self.assertIn(snippet, builder + server)

        self.assertIn("已保留草稿", page)
        self.assertIn("draftId", page)


if __name__ == "__main__":
    unittest.main()
