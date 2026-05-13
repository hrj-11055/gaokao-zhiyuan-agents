import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_major_eval


class GeneratedReportQualityTests(unittest.TestCase):
    def test_fail_quality_result_is_not_accepted(self):
        result = {"status": "FAIL", "errors": ["缺少模块"], "warnings": []}

        self.assertFalse(run_major_eval.quality_allows_completion(result))

    def test_warn_quality_result_is_accepted(self):
        result = {"status": "WARN", "errors": [], "warnings": ["数据来源引用偏少"]}

        self.assertTrue(run_major_eval.quality_allows_completion(result))

    def test_failed_report_is_not_marked_done(self):
        major = {
            "code": "010101",
            "name": "哲学",
            "category": "哲学",
            "sub": "哲学类",
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            progress_path = output_dir / "_progress_哲学.json"

            with patch.object(run_major_eval, "OUTPUT_DIR", output_dir), \
                patch.object(run_major_eval, "DELAY_SECONDS", 0), \
                patch.object(run_major_eval, "progress_file", return_value=progress_path), \
                patch.object(run_major_eval, "load_template", return_value="[专业编号：XXXXX    专业名称：XXX]"), \
                patch.object(run_major_eval, "load_majors", return_value=[major]), \
                patch.object(run_major_eval, "load_progress", return_value=set()), \
                patch.object(run_major_eval, "run_one", return_value="这是一份结构不完整的报告。" * 80), \
                patch("run_major_eval.subprocess.run"):
                run_major_eval.run_category("01")

            self.assertFalse(progress_path.exists())
            self.assertFalse((output_dir / "010101_哲学.md").exists())
            self.assertTrue((output_dir / "_failed" / "010101_哲学.md").exists())


if __name__ == "__main__":
    unittest.main()
