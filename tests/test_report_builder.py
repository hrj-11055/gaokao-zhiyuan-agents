import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportBuilderTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
