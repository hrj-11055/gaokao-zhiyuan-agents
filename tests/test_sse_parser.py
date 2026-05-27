import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SSEParserTests(unittest.TestCase):
    def run_node_parser_test(self, test_body: str):
        source_path = ROOT / "gaokao-miniprogram" / "src" / "api" / "dify.js"
        source = source_path.read_text(encoding="utf-8")
        source = re.sub(r"import \{ API_BASE \} from '../config\.js'\n", "const API_BASE = 'http://localhost:3001'\n", source)
        source = re.sub(
            r"import \{ requestBackend \} from './backend\.js'\n",
            "const requestBackend = () => Promise.reject(new Error('unused'))\n",
            source,
        )
        source = re.sub(
            r"import \{ getStoredSession \} from './membership\.js'\n",
            "const getStoredSession = () => ({ userId: '', sessionToken: '' })\n",
            source,
        )

        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "dify.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(source, encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(f"""
                    import assert from 'node:assert/strict'
                    import {{ SSEParser, Utf8StreamDecoder, isTruncatedSseEvent }} from './dify.mjs'

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_parser_handles_crlf_and_split_chunks(self):
        self.run_node_parser_test("""
            const messages = []
            const parser = new SSEParser(
              (data) => messages.push(data.answer),
              () => messages.push('END'),
              (data) => messages.push(`ERR:${data.message}`)
            )

            parser.feed('data: {"event":"message","answer":"你')
            parser.feed('好","conversation_id":"c1"}\\r\\n\\r\\n')

            assert.deepEqual(messages, ['你好'])
        """)

    def test_parser_flushes_final_buffer_without_trailing_blank_line(self):
        self.run_node_parser_test("""
            const events = []
            const parser = new SSEParser(
              (data) => events.push(data.event),
              (data) => events.push(data.event),
              (data) => events.push(data.event)
            )

            parser.feed('data: {"event":"message_end","conversation_id":"c1","message_id":"m1"}')
            parser.flush()

            assert.deepEqual(events, ['message_end'])
        """)

    def test_parser_marks_partial_stream_as_truncated_when_no_end_event_arrives(self):
        self.run_node_parser_test("""
            const events = []
            const parser = new SSEParser(
              (data) => events.push(`message:${data.answer}`),
              (data) => events.push(data.truncated ? 'end:truncated' : 'end:complete'),
              (data) => events.push(`error:${data.message}`)
            )

            parser.feed('data: {"event":"message","answer":"先看结论"}\\n\\n')
            parser.flush({ markIncomplete: true })

            assert.deepEqual(events, ['message:先看结论', 'end:truncated'])
        """)

    def test_parser_recognizes_proxy_length_finish_as_truncated(self):
        self.run_node_parser_test("""
            assert.equal(isTruncatedSseEvent({ metadata: { proxy_truncated: true } }), true)
            assert.equal(isTruncatedSseEvent({ metadata: { finish_reason: 'length' } }), true)
            assert.equal(isTruncatedSseEvent({ data: { process_data: { finish_reason: 'length' } } }), true)
            assert.equal(isTruncatedSseEvent({ metadata: { finish_reason: 'stop' } }), false)
        """)

    def test_utf8_stream_decoder_preserves_split_chinese_characters(self):
        self.run_node_parser_test("""
            const encoder = new TextEncoder()
            const bytes = encoder.encode('data: {"event":"message","answer":"你好"}\\n\\n')
            const decoder = new Utf8StreamDecoder()

            const first = decoder.decode(bytes.slice(0, 41))
            const second = decoder.decode(bytes.slice(41))
            const final = decoder.flush()

            assert.equal(first + second + final, 'data: {"event":"message","answer":"你好"}\\n\\n')
        """)

    def test_utf8_stream_decoder_falls_back_without_textdecoder(self):
        self.run_node_parser_test("""
            const originalTextDecoder = globalThis.TextDecoder
            globalThis.TextDecoder = undefined
            try {
              const encoder = new TextEncoder()
              const bytes = encoder.encode('data: {"event":"message","answer":"你好"}\\n\\n')
              const decoder = new Utf8StreamDecoder()

              const first = decoder.decode(bytes.slice(0, 41))
              const second = decoder.decode(bytes.slice(41))
              const final = decoder.flush()

              assert.equal(first + second + final, 'data: {"event":"message","answer":"你好"}\\n\\n')
            } finally {
                globalThis.TextDecoder = originalTextDecoder
            }
        """)

    def test_chat_timeouts_allow_two_minute_plus_answers(self):
        api = (ROOT / "gaokao-miniprogram" / "src" / "api" / "dify.js").read_text(encoding="utf-8")
        manifest = (ROOT / "gaokao-miniprogram" / "src" / "manifest.json").read_text(encoding="utf-8")
        server = (ROOT / "gaokao-proxy" / "server.js").read_text(encoding="utf-8")
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("CHAT_RESPONSE_TIMEOUT_MS = 180000", api)
        self.assertIn("timeout: CHAT_RESPONSE_TIMEOUT_MS", api)
        self.assertIn('"request": 180000', manifest)
        self.assertIn("STREAM_TIMEOUT_MS || 180000", server)
        self.assertIn("REQUEST_TIMEOUT_MS || 120000", server)
        self.assertIn("本次回复中途断开", use_chat)
        self.assertIn("finish_reason", server)


if __name__ == "__main__":
    unittest.main()
