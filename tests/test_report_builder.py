import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportBuilderTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def run_node_test(self, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const {{ normalizeReportHtml, extractHtmlDocument }} = require('{ROOT / "gaokao-proxy" / "lib" / "report-builder.js"}')

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_extracts_html_from_markdown_fence_and_drops_intro(self):
        self.run_node_test(r"""
            const raw = '以下是报告。\n```html\n<!DOCTYPE html>\n<html><head><title>x</title></head><body>ok</body></html>\n```'
            const html = extractHtmlDocument(raw)

            assert.equal(html.startsWith('<!DOCTYPE html>'), true)
            assert.equal(html.includes('以下是报告'), false)
            assert.equal(html.includes('```'), false)
        """)

    def test_normalize_injects_viewport_and_mobile_patch(self):
        self.run_node_test(r"""
            const raw = '<html><head><title>x</title></head><body><div class="grid-2">ok</div></body></html>'
            const html = normalizeReportHtml(raw)

            assert.equal(html.includes('name="viewport"'), true)
            assert.equal(html.includes('gaokao-report-responsive-fix'), true)
            assert.equal(html.includes('@media (max-width: 640px)'), true)
        """)

    def test_normalize_adds_print_layout_and_removes_ai_flavored_labels(self):
        self.run_node_test(r"""
            const raw = '<html><head><title>x</title></head><body><h2>AI 总评</h2><p>作为AI，我建议先了解更多信息。</p><div class="highlight">重点</div></body></html>'
            const html = normalizeReportHtml(raw)

            assert.equal(html.includes('gaokao-report-print-fix'), true)
            assert.equal(html.includes('@page'), true)
            assert.equal(html.includes('page-break'), true)
            assert.equal(html.includes('font-size: 11pt'), true)
            assert.equal(html.includes('font-size: 14px !important'), true)
            assert.equal(html.includes('AI 总评'), false)
            assert.equal(html.includes('作为AI'), false)
            assert.equal(html.includes('顾问结论'), true)
        """)

    def test_pdf_print_layout_expands_all_tabbed_report_sections(self):
        self.run_node_test(r"""
            const raw = '<html><head><title>x</title><style>.tab-pane{display:none}.tab-pane.active{display:block}</style></head><body><div id="tab1" class="tab-pane active">自我评估</div><div id="tab2" class="tab-pane">个人特质</div><div id="tab6" class="tab-content">综合决策</div></body></html>'
            const html = normalizeReportHtml(raw)

            assert.equal(html.includes('.tab-pane,'), true)
            assert.equal(html.includes('.tab-content,'), true)
            assert.equal(html.includes('display: block !important;'), true)
            assert.equal(html.includes('break-before: page;'), true)
        """)

    def test_pdf_generator_runtime_style_expands_legacy_tabbed_reports(self):
        text = self.read("gaokao-proxy/lib/pdf-generator.js")

        self.assertIn("const PDF_GENERATOR_VERSION = 'tab-print-v3'", text)
        self.assertIn(".tab-pane,", text)
        self.assertIn(".tab-content,", text)
        self.assertIn("display: block !important;", text)


if __name__ == "__main__":
    unittest.main()
