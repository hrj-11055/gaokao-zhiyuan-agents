import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.clean_report_sources import clean_text


ROOT = Path(__file__).resolve().parents[1]


class CleanReportSourcesTests(unittest.TestCase):
    def test_clean_text_removes_collection_tags_but_keeps_decision_data(self):
        raw = textwrap.dedent(
            """
            研究数据收集完成，现在输出完整报告。

            ### 1.1 AI 总评 (Executive Summary) `[直接回答]`

            > 适合高分段理科生。[待核实，需看当年招生简章]
            > 新专业就业率：[无数据，新专业]
            > QS 前 50 比例：[未检索到]
            > 特色社团：[未检索到全国知名社团
            [供不应求]
            [数据敏感] [规则意识]

            ### 维度一：市场准入与回报指数（权重 30%）

            | 维度 | 分数 | 权重 | 加权得分 |
            |------|------|------|---------|
            | 市场回报 | 4.2 | 30% | 1.26 |
            | 数据来源 | [社区观点/待核实] | 0% | 0 |
            | **加权总分** | | **100%** | **3.86** |

            **宿舍条件** `[社区观点 — 来源：知乎]`：四人间，上床下桌。

            *本报告由 AI 数据分析师根据公开信息生成。*
            """
        )

        cleaned, stats = clean_text(raw)

        self.assertNotIn("数据收集完成", cleaned)
        self.assertNotIn("AI 总评", cleaned)
        self.assertNotIn("Executive Summary", cleaned)
        self.assertNotIn("[直接回答]", cleaned)
        self.assertNotIn("[待核实]", cleaned)
        self.assertNotIn("[无数据", cleaned)
        self.assertNotIn("[未检索到]", cleaned)
        self.assertNotIn("[未检索到全国", cleaned)
        self.assertNotIn("AI 数据分析师", cleaned)
        self.assertNotIn("权重 30%", cleaned)
        self.assertNotIn("| 权重 |", cleaned)
        self.assertNotIn("[社区观点/待核实]", cleaned)
        self.assertNotIn("加权得分", cleaned)
        self.assertNotIn("加权总分", cleaned)
        self.assertIn("顾问结论", cleaned)
        self.assertIn("适合高分段理科生", cleaned)
        self.assertIn("（需核验：需看当年招生简章）", cleaned)
        self.assertIn("暂无数据（新专业）", cleaned)
        self.assertIn("暂未检索到", cleaned)
        self.assertIn("暂未检索到全国知名社团", cleaned)
        self.assertIn("供不应求", cleaned)
        self.assertIn("数据敏感 规则意识", cleaned)
        self.assertIn("| 维度 | 分数 |", cleaned)
        self.assertIn("| 市场回报 | 4.2 |", cleaned)
        self.assertIn("| 数据来源 | （社区反馈，需核验） |", cleaned)
        self.assertIn("四人间，上床下桌", cleaned)
        self.assertIn("社区反馈，需核验；来源：知乎", cleaned)
        self.assertGreaterEqual(stats.table_columns_removed, 2)
        self.assertGreaterEqual(stats.inline_tags_removed, 3)

    def test_cli_apply_cleans_json_with_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "report.json"
            target.write_text(
                json.dumps(
                    {
                        "meta": {"version": "2.0.0"},
                        "layer3_detail": {
                            "module": {
                                "raw_content": "## 模块一（权重 30%）`[直接回答]`\n\n| 评估维度 | 维度得分 | 权重 | 加权得分 |\n|---|---|---|---|\n| 学术资本 | 4.6 | 30% | 1.38 |"
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            backup_dir = tmp_path / "backup"

            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "clean_report_sources.py"),
                    str(target),
                    "--apply",
                    "--backup-dir",
                    str(backup_dir),
                ],
                check=True,
                text=True,
                capture_output=True,
                cwd=ROOT,
            )

            cleaned = json.loads(target.read_text(encoding="utf-8"))
            raw_content = cleaned["layer3_detail"]["module"]["raw_content"]
            self.assertEqual(cleaned["meta"]["cleaning_version"], "report-source-clean-v1")
            self.assertNotIn("[直接回答]", raw_content)
            self.assertNotIn("权重 30%", raw_content)
            self.assertNotIn("| 权重 |", raw_content)
            self.assertIn("| 评估维度 | 维度得分 |", raw_content)
            self.assertTrue((backup_dir / target).exists())


if __name__ == "__main__":
    unittest.main()
