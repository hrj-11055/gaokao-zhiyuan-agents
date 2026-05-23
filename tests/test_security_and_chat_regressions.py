import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SecurityAndChatRegressionTests(unittest.TestCase):
    def test_dify_credentials_are_not_hardcoded_in_scripts(self):
        patterns = [
            re.compile(r'app-[0-9a-f]{20,}'),
            re.compile(r'dataset-[0-9a-f]{20,}'),
            re.compile(r'PASSWORD\s*=\s*["\'][^"\']+["\']'),
            re.compile(r'API_KEY\s*=\s*["\']app-[^"\']+["\']'),
            re.compile(r'DATASET_TOKEN\s*=\s*["\']dataset-[^"\']+["\']'),
        ]
        offenders = []

        for path in (ROOT / "data").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                if pattern.search(text):
                    offenders.append(str(path.relative_to(ROOT)))

        self.assertEqual([], sorted(set(offenders)))

    def test_chat_error_handler_uses_ref_value_length(self):
        chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js"
        text = chat_path.read_text(encoding="utf-8")

        self.assertNotIn("messages.value[messages.length - 1]", text)
        self.assertIn("chatStore.messages[chatStore.messages.length - 1]", text)

    def test_miniprogram_api_base_is_build_configurable(self):
        config_path = ROOT / "gaokao-miniprogram" / "src" / "config.js"
        text = config_path.read_text(encoding="utf-8")

        self.assertIn("import.meta.env.VITE_API_BASE", text)
        self.assertNotIn("const API_BASE = 'http://localhost:3001'", text)
        self.assertNotIn("aicoming.com.cn", text)

    def test_report_api_base_uses_same_live_proxy(self):
        config_path = ROOT / "gaokao-miniprogram" / "src" / "config.js"
        report_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "report" / "report.vue"
        text = config_path.read_text(encoding="utf-8")
        report_text = report_path.read_text(encoding="utf-8")

        self.assertIn("import.meta.env.VITE_API_BASE", text)
        self.assertIn("http://47.113.125.147", text)
        self.assertIn("requestBackend", report_text)
        self.assertNotIn("aicoming.com.cn", text)

    def test_chat_bubble_renders_markdown_as_rich_text(self):
        bubble_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "ChatBubble.vue"
        text = bubble_path.read_text(encoding="utf-8")

        self.assertIn(":nodes=\"contentHtml\"", text)
        self.assertIn("markdownToRichTextHtml", text)

    def test_proxy_has_basic_abuse_and_stream_cleanup_guards(self):
        server_path = ROOT / "gaokao-proxy" / "server.js"
        text = server_path.read_text(encoding="utf-8")

        self.assertIn("express.json({", text)
        self.assertIn("limit: JSON_BODY_LIMIT", text)
        self.assertIn("rateLimit", text)
        self.assertIn("res.on('close'", text)
        self.assertNotIn("req.on('close'", text)
        self.assertIn("await pump()", text)
        self.assertIn("AbortController", text)
        self.assertIn("STREAM_TIMEOUT_MS", text)
        self.assertIn("X-Accel-Buffering", text)
        self.assertIn("res.flushHeaders", text)


if __name__ == "__main__":
    unittest.main()
