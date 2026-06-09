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
            "固定 HTML 模板",
            "家长先看结论",
            "志愿执行清单",
            "每个模块的中文正文内容都必须不少于 1000 字",
            "每条建议必须包含动作、原因、核验材料",
            "家长核验动作",
            "不要生成额外的目录页、Table 页或单独的表格页",
            "不要使用“AI 总评”",
            "顾问结论",
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
            assert.equal(html.includes('Noto Sans CJK SC'), true)
        """)

    def test_deep_report_uses_structured_sections_without_repeating_full_raw_content(self):
        self.run_node_test(r"""
            const report = {
              code: '080710T',
              name: '集成电路设计与集成系统',
              word_count: 6800,
              data: {
                layer3_detail: {
                  overview: {
                    title: '专业画像',
                    raw_content: '精排章节唯一内容😀'
                  }
                },
                layer4_supplement: {
                  full_raw_content: '精排章节唯一内容😀\n原始全文不应再次展示'
                }
              }
            }

            const pdfHtml = deep.buildDeepReportHtml({ type: 'major', report })
            const readerHtml = deep.buildDeepReportReaderHtml({ type: 'major', report })

            assert.equal(pdfHtml.includes('完整原始研究'), false)
            assert.equal(readerHtml.includes('完整原始研究'), false)
            assert.equal(pdfHtml.includes('原始全文不应再次展示'), false)
            assert.equal(readerHtml.includes('原始全文不应再次展示'), false)
            assert.equal(readerHtml.includes('<span class="hero-pill">9 字</span>'), true)
        """)

    def test_report_pdf_generation_forces_cjk_fonts_and_regenerates_old_pdfs(self):
        builder = self.read("gaokao-proxy/lib/report-builder.js")
        pdf_generator = self.read("gaokao-proxy/lib/pdf-generator.js")
        server = self.read("gaokao-proxy/server.js")

        for snippet in [
            "pdf-print-report",
            "@media print",
            "Noto Sans CJK SC",
            "WenQuanYi Micro Hei",
        ]:
            self.assertIn(snippet, builder)

        for snippet in [
            "PDF_GENERATOR_VERSION",
            "document.fonts.ready",
            "isGeneratedPdfFresh",
            "Noto Sans CJK SC",
        ]:
            self.assertIn(snippet, pdf_generator)

        self.assertIn("isGeneratedPdfFresh", server)
        self.assertIn("PDF is stale", server)

    def test_report_generation_timeout_matches_real_wait_time(self):
        builder = self.read("gaokao-proxy/lib/report-builder.js")
        client = self.read("gaokao-miniprogram/src/api/report.js")

        self.assertIn("REPORT_GENERATION_TIMEOUT_MS", builder)
        self.assertIn("REPORT_GENERATION_TIMEOUT_MS || 600000", builder)
        # Client timeout should not be dramatically shorter than server timeout
        self.assertIn("timeout: 360000", client)

    def test_miniprogram_deep_report_cards_expose_actionable_summary(self):
        page = self.read("gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue")

        for snippet in [
            "summary-card-row",
            "decisionBadges",
            "summaryTakeaways",
            "关键判断",
            "下一步核验",
            "school-logo",
            "/api/reports/universities/logo",
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
