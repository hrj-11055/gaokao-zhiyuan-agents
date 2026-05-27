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
                    const {{
                      buildFinalHtml,
                      humanizeReportCopy,
                      normalizeReportHtml,
                    }} = require('{ROOT / "gaokao-proxy" / "lib" / "report-builder.js"}')

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_build_final_html_contains_static_print_report(self):
        self.run_node_test(r"""
            const content = JSON.stringify({
              conclusions: ['先稳层次，再看专业适配。'],
              modules: [
                {
                  id: 'tab1',
                  title: '总览',
                  summary: '摘要',
                  blocks: [{ type: 'text', title: '判断', content: '正文内容' }]
                },
                {
                  id: 'tab2',
                  title: '测评画像',
                  blocks: [{ type: 'list', title: '方向', items: ['计算机类', '电子信息类'] }]
                }
              ]
            })
            const html = buildFinalHtml(content, { province: '广东', category: '物理类', score: 600 }, {
              holland: { scores: { R: 20, I: 30, A: 10, S: 25, E: 15, C: 22 } }
            })

            assert.equal(html.includes('class="pdf-print-report"'), true)
            assert.equal(html.includes('@media print'), true)
            assert.equal(html.includes('家长先看结论'), true)
            assert.equal(html.includes('先稳层次，再看专业适配。'), true)
            assert.equal(html.includes('测评画像'), true)
            assert.equal(html.includes('霍兰德职业兴趣图谱'), true)
        """)

    def test_normalize_and_humanize_report_copy_remove_ai_flavored_labels(self):
        self.run_node_test(r"""
            const raw = '<h2>AI 总评</h2><p>作为AI，我建议先了解更多信息。</p><p>大模型认为需要谨慎。</p>'
            const html = normalizeReportHtml(raw)
            const copy = humanizeReportCopy(raw)

            assert.equal(html.includes('AI 总评'), false)
            assert.equal(html.includes('作为AI'), false)
            assert.equal(html.includes('大模型认为'), false)
            assert.equal(copy.includes('顾问结论'), true)
            assert.equal(copy.includes('建议判断'), true)
        """)

    def test_pdf_generator_runtime_style_uses_print_layout_v4(self):
        text = self.read("gaokao-proxy/lib/pdf-generator.js")

        self.assertIn("const PDF_GENERATOR_VERSION = 'print-layout-v4'", text)
        self.assertIn("await page.emulateMediaType('print')", text)
        self.assertIn("preferCSSPageSize: true", text)
        self.assertIn(".tab-pane,", text)
        self.assertIn(".tab-content,", text)
        self.assertIn("display: block !important;", text)
        self.assertIn("#app [style*=\"display: none\"]", text)


if __name__ == "__main__":
    unittest.main()
