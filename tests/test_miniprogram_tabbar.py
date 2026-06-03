import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MiniProgramTabBarTests(unittest.TestCase):
    def test_ai_consultation_tab_is_in_bottom_tabbar(self):
        pages_json = json.loads((ROOT / "gaokao-miniprogram/src/pages.json").read_text(encoding="utf-8"))
        tab_items = pages_json["tabBar"]["list"]

        self.assertEqual(
            [item["pagePath"] for item in tab_items],
            [
                "pages/index/index",
                "pages/chat/chat",
                "pages/report/report",
                "pages/profile/profile",
            ],
        )

        chat_tab = tab_items[1]
        self.assertEqual(chat_tab["text"], "AI 咨询")
        self.assertEqual(chat_tab["iconPath"], "static/tabbar/chat.png")
        self.assertEqual(chat_tab["selectedIconPath"], "static/tabbar/chat-active.png")
        self.assertTrue((ROOT / "gaokao-miniprogram/src/static/tabbar/chat.png").exists())
        self.assertTrue((ROOT / "gaokao-miniprogram/src/static/tabbar/chat-active.png").exists())


if __name__ == "__main__":
    unittest.main()
