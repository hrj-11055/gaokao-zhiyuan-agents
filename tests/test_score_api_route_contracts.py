import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def route_rules(module):
    return {rule.rule for rule in module.app.url_map.iter_rules()}


class ScoreApiRouteContractTests(unittest.TestCase):
    def test_local_api_keeps_proxy_recommend_route_alias(self):
        module = load_module("gaokao_api_app_contract", ROOT / "gaokao-api" / "app.py")
        routes = route_rules(module)

        self.assertIn("/api/scores/recommend", routes)
        self.assertIn("/api/recommend", routes)

    def test_remote_api_keeps_legacy_and_documented_score_routes(self):
        module = load_module("gaokao_api_remote_contract", ROOT / "gaokao-api" / "gaokao_api_remote.py")
        routes = route_rules(module)

        self.assertIn("/api/recommend", routes)
        self.assertIn("/api/scores/recommend", routes)
        self.assertIn("/api/scores/match", routes)
        self.assertIn("/api/scores/schools/<name>/provinces/<province>", routes)
        self.assertIn("/api/scores/majors/<keyword>", routes)

    def test_score_category_normalizes_three_plus_three_provinces(self):
        local = load_module("gaokao_api_app_category_contract", ROOT / "gaokao-api" / "app.py")
        remote = load_module("gaokao_api_remote_category_contract", ROOT / "gaokao-api" / "gaokao_api_remote.py")
        data_source = load_module("gaokao_data_api_category_contract", ROOT / "data" / "gaokao_api.py")

        for module in (local, remote, data_source):
            self.assertEqual("广西", module.normalize_province_name("广西壮族自治区"))
            self.assertEqual("新疆", module.normalize_province_name("新疆维吾尔自治区"))
            self.assertEqual("综合", module.normalize_score_category("山东", "物理类"))
            self.assertEqual("综合", module.normalize_score_category("浙江省", "历史类"))
            self.assertEqual("物理类", module.normalize_score_category("广东", "理科"))
            self.assertEqual("历史类", module.normalize_score_category("广东", "文科"))
            self.assertEqual(["综合"], module.score_category_aliases("山东", "物理类"))
            self.assertEqual(["物理类", "理科"], module.score_category_aliases("四川", "理科"))
            self.assertEqual(["历史类", "文科"], module.score_category_aliases("河南省", "历史类"))


if __name__ == "__main__":
    unittest.main()
