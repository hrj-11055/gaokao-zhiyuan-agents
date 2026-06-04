import unittest

from data.gaokao_api import calculate_report_word_count, public_major
from scripts.import_reports_to_pg import ReportImporter


class ReportVisibleWordCountTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "layer3_detail": {
                "module1": {"raw_content": "精排章节一"},
                "module2": {"raw_content": "精排章节二"},
            },
            "layer4_supplement": {
                "full_raw_content": "精排章节一精排章节二原始全文",
            },
        }

    def test_api_word_count_uses_structured_sections_without_full_raw_duplicate(self):
        expected = len("精排章节一") + len("精排章节二")

        self.assertEqual(expected, calculate_report_word_count(self.data))
        self.assertEqual(
            expected,
            public_major({
                "code": "080710T",
                "name": "集成电路设计与集成系统",
                "category": "工学",
                "data": self.data,
                "word_count": 99999,
            })["word_count"],
        )

    def test_import_word_count_uses_full_raw_content_only_as_fallback(self):
        importer = ReportImporter.__new__(ReportImporter)
        expected = len("精排章节一") + len("精排章节二")

        self.assertEqual(expected, importer.calculate_word_count(self.data))
        self.assertEqual(
            len("只有原始全文"),
            importer.calculate_word_count({
                "layer3_detail": {},
                "layer4_supplement": {"full_raw_content": "只有原始全文"},
            }),
        )


if __name__ == "__main__":
    unittest.main()
