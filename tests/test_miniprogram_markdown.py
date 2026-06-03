import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MiniProgramMarkdownTests(unittest.TestCase):
    def run_node_test(self, test_body):
        source_path = ROOT / "gaokao-miniprogram" / "src" / "utils" / "markdown.js"

        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "markdown.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(f"""
                    import assert from 'node:assert/strict'
                    import {{ markdownToRichTextHtml, markdownToRichTextNodes }} from './markdown.mjs'

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_bold_markdown_becomes_strong_node(self):
        self.run_node_test("""
            const nodes = markdownToRichTextNodes('这是**重点**内容')

            assert.deepEqual(nodes, [
              { type: 'text', text: '这是' },
              {
                name: 'strong',
                attrs: { style: 'font-weight: 700;' },
                children: [{ type: 'text', text: '重点' }]
              },
              { type: 'text', text: '内容' }
            ])
        """)

    def test_unclosed_bold_marker_is_preserved_as_text(self):
        self.run_node_test("""
            const nodes = markdownToRichTextNodes('这是**未闭合')

            assert.deepEqual(nodes, [
              { type: 'text', text: '这是**未闭合' }
            ])
        """)

    def test_newlines_become_br_nodes(self):
        self.run_node_test("""
            const nodes = markdownToRichTextNodes('第一行\\n**第二行**')

            assert.deepEqual(nodes, [
              { type: 'text', text: '第一行' },
              { name: 'br' },
              {
                name: 'strong',
                attrs: { style: 'font-weight: 700;' },
                children: [{ type: 'text', text: '第二行' }]
              }
            ])
        """)

    def test_bold_markdown_becomes_safe_rich_text_html(self):
        self.run_node_test("""
            const html = markdownToRichTextHtml('这是**重点<内容>**\\n下一行')

            assert.equal(
              html,
              '这是<strong style="font-weight: 700;">重点&lt;内容&gt;</strong><br/>下一行'
            )
        """)

    def test_agent_markdown_headings_lists_and_bold_render_as_rich_text_html(self):
        self.run_node_test("""
            const html = markdownToRichTextHtml('## 结论\\n- **冲**：A大学\\n- **稳**：B大学')

            assert.match(html, /font-size: 33rpx/)
            assert.match(html, /<ul/)
            assert.match(html, /<strong style="font-weight: 700;">冲<\\/strong>/)
            assert.match(html, /<strong style="font-weight: 700;">稳<\\/strong>/)
        """)


if __name__ == "__main__":
    unittest.main()
