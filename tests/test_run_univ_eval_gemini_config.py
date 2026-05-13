import importlib
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import run_univ_eval_gemini


class GeminiModelConfigTests(unittest.TestCase):
    def test_default_model_uses_available_flash_preview_name(self):
        self.assertEqual("gemini-3-flash-preview", run_univ_eval_gemini.GEMINI_MODEL)

    def test_model_can_be_overridden_from_environment(self):
        with patch.dict("os.environ", {"GEMINI_MODEL": "gemini-2.5-flash"}):
            module = importlib.reload(run_univ_eval_gemini)

        self.assertEqual("gemini-2.5-flash", module.GEMINI_MODEL)
        importlib.reload(run_univ_eval_gemini)

    def test_generation_config_requests_large_output_budget(self):
        config = run_univ_eval_gemini.build_generation_config()

        self.assertGreaterEqual(config.max_output_tokens, 30000)


class GeminiReportQualityTests(unittest.TestCase):
    def make_report(self, body: str) -> str:
        return "\n".join([
            "## 模块一：学术资本",
            "## 模块二：生源竞争力",
            "## 模块三：毕业生价值实现",
            "## 模块四：区位与产业势能",
            "## 模块五：学生体验与风险",
            "## 模块六：综合评估与量化评分",
            "## 模块七：报考建议",
            "## 模块八：原始数据汇总",
            "## Google 搜索来源",
            body,
        ])

    def test_cjk_counter_excludes_markdown_table_noise(self):
        text = "中文内容" + "\n| --- | --- |\n" + "https://example.com/a?x=1"

        self.assertEqual(4, run_univ_eval_gemini.count_cjk_chars(text))

    def test_short_visible_chinese_report_fails_quality(self):
        text = self.make_report("短报告" * 1000)

        result = run_univ_eval_gemini.validate_report_text(text)

        self.assertEqual("FAIL", result["status"])
        self.assertIn("中文正文过短", "；".join(result["errors"]))

    def test_five_thousand_visible_chinese_chars_pass_length_gate(self):
        text = self.make_report("合格正文" * 1300)

        result = run_univ_eval_gemini.validate_report_text(text)

        self.assertNotIn("中文正文过短", "；".join(result["errors"]))

    def test_short_report_is_expanded_before_marking_done(self):
        univ = {
            "name": "测试大学",
            "code": "0000000000",
            "authority": "测试",
            "city": "广州市",
            "remark": "",
        }
        short_report = self.make_report("短报告" * 1000)
        expanded_report = self.make_report("合格正文" * 1600)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            progress_path = output_dir / "_progress_gemini_广东.json"

            with patch.object(run_univ_eval_gemini, "OUTPUT_DIR", output_dir), \
                patch.object(run_univ_eval_gemini, "DELAY_SECONDS", 0), \
                patch.object(run_univ_eval_gemini, "progress_file", return_value=progress_path), \
                patch.object(run_univ_eval_gemini, "load_template", return_value="[大学名称：XXX]"), \
                patch.object(run_univ_eval_gemini, "load_universities", return_value=[univ]), \
                patch.object(run_univ_eval_gemini, "load_progress", return_value=set()), \
                patch.object(run_univ_eval_gemini, "run_one", side_effect=[short_report, expanded_report]) as run_one, \
                patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                run_univ_eval_gemini.run_province("广东省")

            self.assertEqual(2, run_one.call_count)
            self.assertTrue(progress_path.exists())
            self.assertTrue((output_dir / "测试大学.md").exists())
            self.assertFalse((output_dir / "_failed_gemini" / "测试大学.md").exists())

    def test_transient_gemini_disconnect_is_retried(self):
        good_report = self.make_report("合格正文" * 1600)

        with patch.object(run_univ_eval_gemini, "GEMINI_API_RETRIES", 1), \
            patch.object(run_univ_eval_gemini, "GEMINI_API_RETRY_DELAY_SECONDS", 0), \
            patch.object(
                run_univ_eval_gemini,
                "run_one",
                side_effect=[RuntimeError("Server disconnected without sending a response."), good_report],
            ) as run_one:
            text, quality, api_retries = run_univ_eval_gemini.run_one_with_retries("prompt")

        self.assertEqual(good_report, text)
        self.assertEqual("PASS", quality["status"])
        self.assertEqual(1, api_retries)
        self.assertEqual(2, run_one.call_count)

    def test_failed_report_is_not_marked_done(self):
        univ = {
            "name": "测试大学",
            "code": "0000000000",
            "authority": "测试",
            "city": "广州市",
            "remark": "",
        }
        short_report = self.make_report("短报告" * 1000)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            progress_path = output_dir / "_progress_gemini_广东.json"

            with patch.object(run_univ_eval_gemini, "OUTPUT_DIR", output_dir), \
                patch.object(run_univ_eval_gemini, "DELAY_SECONDS", 0), \
                patch.object(run_univ_eval_gemini, "progress_file", return_value=progress_path), \
                patch.object(run_univ_eval_gemini, "load_template", return_value="[大学名称：XXX]"), \
                patch.object(run_univ_eval_gemini, "load_universities", return_value=[univ]), \
                patch.object(run_univ_eval_gemini, "load_progress", return_value=set()), \
                patch.object(run_univ_eval_gemini, "run_one", return_value=short_report), \
                patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                run_univ_eval_gemini.run_province("广东省")

            self.assertFalse(progress_path.exists())
            self.assertFalse((output_dir / "测试大学.md").exists())
            self.assertTrue((output_dir / "_failed_gemini" / "测试大学.md").exists())


if __name__ == "__main__":
    unittest.main()
