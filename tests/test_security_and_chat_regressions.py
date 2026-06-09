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
        self.assertIn("https://gaokao.aicoming.cn", text)
        self.assertNotIn("aicoming.com.cn", text)

    def test_report_api_base_uses_same_live_proxy(self):
        config_path = ROOT / "gaokao-miniprogram" / "src" / "config.js"
        report_api_path = ROOT / "gaokao-miniprogram" / "src" / "api" / "report.js"
        text = config_path.read_text(encoding="utf-8")
        report_api_text = report_api_path.read_text(encoding="utf-8")

        self.assertIn("import.meta.env.VITE_API_BASE", text)
        self.assertIn("https://gaokao.aicoming.cn", text)
        self.assertIn("requestBackendData", report_api_text)
        self.assertNotIn("aicoming.com.cn", text)

    def test_chat_bubble_renders_markdown_as_rich_text(self):
        bubble_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "ChatBubble.vue"
        text = bubble_path.read_text(encoding="utf-8")

        self.assertIn(":nodes=\"contentHtml\"", text)
        self.assertIn("markdownToRichTextHtml", text)

    def test_quick_questions_guides_uncertain_students(self):
        quick_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "QuickQuestions.vue"
        guide_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "PersonalityAssessmentGuide.vue"
        chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue"
        quick_text = quick_path.read_text(encoding="utf-8")
        guide_text = guide_path.read_text(encoding="utf-8")
        chat_text = chat_path.read_text(encoding="utf-8")

        self.assertIn("不知道怎么问，就按真实处境开始", quick_text)
        self.assertIn("先把问题变小", quick_text)
        self.assertIn("普通家庭，请真诚地告诉我", quick_text)
        self.assertIn("必须带最低分和位次证据", quick_text)
        self.assertIn("专业排雷", quick_text)
        self.assertIn("你不用先想出一个完美问题", chat_text)
        self.assertIn("从关键决策开始", chat_text)
        self.assertIn("PersonalityAssessmentGuide", chat_text)
        self.assertIn("去做性格测试", guide_text)
        self.assertNotIn("物理类更适合工科还是理科", chat_text)
        self.assertNotIn("quick-chip", quick_text)

    def test_early_planning_chat_avoids_score_first_guidance(self):
        quick_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "QuickQuestions.vue"
        chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue"
        quick_text = quick_path.read_text(encoding="utf-8")
        chat_text = chat_path.read_text(encoding="utf-8")

        self.assertIn("isEarlyPlanning", quick_text)
        self.assertIn("升学规划", quick_text)
        self.assertIn("welcomeMsg", chat_text)
        self.assertIn("提前升学规划", chat_text)

    def test_chat_regenerate_replaces_tts_action(self):
        bubble_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "ChatBubble.vue"
        chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue"
        use_chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js"
        bubble_text = bubble_path.read_text(encoding="utf-8")
        chat_text = chat_path.read_text(encoding="utf-8")
        use_chat_text = use_chat_path.read_text(encoding="utf-8")

        self.assertIn("defineEmits(['regenerate'])", bubble_text)
        self.assertIn("canRegenerate", bubble_text)
        self.assertIn("重新生成", bubble_text)
        self.assertNotIn("fetchTTSAudio", bubble_text)
        self.assertNotIn("createInnerAudioContext", bubble_text)
        self.assertIn("@regenerate=\"handleRetry\"", chat_text)
        self.assertIn(":show-actions=\"false\"", chat_text)
        self.assertIn("content: '', canRegenerate: true", use_chat_text)
        self.assertIn("[...chatStore.messages].reverse().find((msg) => msg.role === 'user')", use_chat_text)

    def test_chat_bubble_keeps_compact_feedback_actions(self):
        bubble_path = ROOT / "gaokao-miniprogram" / "src" / "components" / "ChatBubble.vue"
        icons_path = ROOT / "gaokao-miniprogram" / "src" / "utils" / "icons.js"
        bubble_text = bubble_path.read_text(encoding="utf-8")
        icons_text = icons_path.read_text(encoding="utf-8")

        self.assertIn("复制", bubble_text)
        self.assertIn("ThumbsUp", bubble_text)
        self.assertIn("有用", bubble_text)
        self.assertIn("ThumbsDown", bubble_text)
        self.assertIn("不准", bubble_text)
        self.assertIn("action-btn-active", bubble_text)
        self.assertIn("max-width: 96%", bubble_text)
        self.assertNotIn("avatar-outer", bubble_text)
        self.assertNotIn("🤖", bubble_text)
        self.assertIn("font-size: 28rpx", bubble_text)
        self.assertIn("ThumbsDown:", icons_text)

    def test_cloud_tts_is_removed_from_runtime_surface(self):
        server_path = ROOT / "gaokao-proxy" / "server.js"
        dify_path = ROOT / "gaokao-miniprogram" / "src" / "api" / "dify.js"
        privacy_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "privacy" / "privacy.vue"
        proxy_package_path = ROOT / "gaokao-proxy" / "package.json"

        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [server_path, dify_path, privacy_path, proxy_package_path]
        )

        self.assertNotIn("/api/tts", combined)
        self.assertNotIn("textToSpeech", combined)
        self.assertNotIn("fetchTTSAudio", combined)
        self.assertNotIn("VOLC_TTS", combined)
        self.assertNotIn("火山引擎", combined)

    def test_recommendation_prompt_no_longer_shortens_answers(self):
        gate_path = ROOT / "gaokao-proxy" / "lib" / "profile-followup-gate.js"
        server_path = ROOT / "gaokao-proxy" / "server.js"
        text = gate_path.read_text(encoding="utf-8")
        server_text = server_path.read_text(encoding="utf-8")

        self.assertNotIn("总字数控制在 600 字以内", text)
        self.assertIn("不要为了压缩篇幅删减关键判断", text)
        self.assertIn("fetchScoreMatchContext(query, finalInputs)", server_text)
        self.assertIn("fetchSchoolScoreData(query, finalInputs)", server_text)
        self.assertIn("formatScoreMatchContext", server_text)
        self.assertIn("buildDirectSchoolScoreAnswer", server_text)
        self.assertIn("buildDeepProfileGateAnswer", server_text)
        self.assertNotIn("buildDirectScoreMatchAnswer", server_text)
        self.assertIn("proxy_direct", server_text)

    def test_recommendation_prompt_requires_score_line_context(self):
        gate_path = ROOT / "gaokao-proxy" / "lib" / "profile-followup-gate.js"
        text = gate_path.read_text(encoding="utf-8")

        self.assertIn("后端分数线查询结果", text)
        self.assertIn("后端学校分数线查询结果", text)
        self.assertIn("最低分/位次等分数线证据", text)
        self.assertIn("不能编造分数线", text)

    def test_chat_input_bar_stays_inside_native_nav_viewport(self):
        chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue"
        text = chat_path.read_text(encoding="utf-8")

        self.assertIn("page {\n  height: 100%;", text)
        self.assertIn(".chat-page {\n  display: flex;\n  flex-direction: column;\n  height: 100%;", text)
        self.assertNotIn("height: 100vh;", text)
        self.assertIn(".chat-scroll {\n  flex: 1;\n  height: 0;\n  min-height: 0;", text)
        self.assertIn("flex-shrink: 0;", text)

    def test_chat_send_focuses_user_message_without_forcing_bottom(self):
        chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue"
        use_chat_path = ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js"
        chat_text = chat_path.read_text(encoding="utf-8")
        use_chat_text = use_chat_path.read_text(encoding="utf-8")

        self.assertIn(":id=\"`message-${index}`\"", chat_text)
        self.assertIn("function focusUserMessage(index)", chat_text)
        self.assertIn("onUserMessageAppended: focusUserMessage", chat_text)
        self.assertIn("onAiResponseStarted: () => {}", chat_text)
        self.assertIn("callbacks.onUserMessageAppended(messageIndex)", use_chat_text)
        self.assertIn("if (onAiResponseStarted)", use_chat_text)

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
