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
    def test_shared_recommendation_context_supports_official_and_estimated_range(self):
        engine = load_module(
            "recommendation_context_contract",
            ROOT / "gaokao-api" / "recommendation_context.py",
        )
        records = [
            {"school_name": "冲刺大学", "major_name": "计算机类", "min_score": 615, "min_rank": 18000, "year": 2025},
            {"source_record_id": 42, "school_name": "稳妥大学", "major_name": "电子信息类", "min_score": 600, "min_rank": 22000, "year": 2025},
            {"school_name": "保底大学", "major_name": "自动化类", "min_score": 580, "min_rank": 28000, "year": 2025},
        ]

        official = engine.resolve_recommendation_query({"mode": "official", "score": 600, "rank": 22000})
        official.update({"province": "广东", "category": "物理类", "year": 2025})
        official_context = engine.build_recommendation_context(records, official)
        self.assertEqual("rank", official_context["match_basis"])
        self.assertEqual("正式冲稳保", official_context["positioning_label"])
        self.assertEqual("稳妥大学", official_context["稳"][0]["school_name"])
        self.assertEqual(42, official_context["稳"][0]["source_record_id"])

        estimated = engine.resolve_recommendation_query({"mode": "planning", "score_range": "580-620"})
        estimated.update({"province": "广东", "category": "物理类", "year": 2025})
        estimated_context = engine.build_recommendation_context(records, estimated)
        self.assertEqual(600, estimated_context["query"]["score"])
        self.assertEqual([580, 620], estimated_context["query"]["score_range"])
        self.assertEqual("预估院校层次", estimated_context["positioning_label"])

    def test_local_api_keeps_proxy_recommend_route_alias(self):
        module = load_module("gaokao_api_app_contract", ROOT / "gaokao-api" / "app.py")
        routes = route_rules(module)

        self.assertIn("/api/scores/recommend", routes)
        self.assertIn("/api/recommend", routes)
        self.assertIn("/api/scores/recommendation-context", routes)

    def test_remote_api_keeps_legacy_and_documented_score_routes(self):
        module = load_module("gaokao_api_remote_contract", ROOT / "gaokao-api" / "gaokao_api_remote.py")
        routes = route_rules(module)

        self.assertIn("/api/recommend", routes)
        self.assertIn("/api/scores/recommend", routes)
        self.assertIn("/api/scores/recommendation-context", routes)
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

    def test_deployed_data_api_exposes_unified_recommendation_context(self):
        module = load_module("gaokao_data_api_routes_contract", ROOT / "data" / "gaokao_api.py")
        self.assertIn("/api/scores/recommendation-context", route_rules(module))


if __name__ == "__main__":
    unittest.main()
