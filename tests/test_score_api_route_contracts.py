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


if __name__ == "__main__":
    unittest.main()
