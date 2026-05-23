import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MiniprogramAppConfigTests(unittest.TestCase):
    def test_pages_config_declares_empty_subpackages_for_devtools(self):
        pages_config = json.loads((ROOT / "gaokao-miniprogram/src/pages.json").read_text())

        self.assertIn("subPackages", pages_config)
        self.assertEqual([], pages_config["subPackages"])


if __name__ == "__main__":
    unittest.main()
