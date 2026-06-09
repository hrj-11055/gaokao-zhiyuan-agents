import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RecommendationContextClientTests(unittest.TestCase):
    def test_client_builds_official_and_planning_requests_and_balances_tiers(self):
        client = ROOT / "gaokao-proxy" / "lib" / "recommendation-context-client.js"
        script = textwrap.dedent(
            f"""
            const assert = require('node:assert/strict')
            const client = require({json.dumps(str(client))})

            const official = client.buildRecommendationContextUrl(
              {{ province: '广东', category: '物理类', score: 600, rank: 22000 }},
              {{ scoreApiUrl: 'http://score-api', year: 2025 }}
            )
            assert.equal(official.pathname, '/api/scores/recommendation-context')
            assert.equal(official.searchParams.get('mode'), 'official')
            assert.equal(official.searchParams.get('rank'), '22000')

            const planning = client.buildRecommendationContextUrl(
              {{ province: '广东', category: '物理类', planning_mode: 'early', score_range: '540-570' }},
              {{ scoreApiUrl: 'http://score-api', year: 2025 }}
            )
            assert.equal(planning.searchParams.get('mode'), 'planning')
            assert.equal(planning.searchParams.get('score_range'), '540-570')

            const flattened = client.flattenRecommendationContext({{
              tiers: {{
                '冲': [{{ school_name: '冲1' }}, {{ school_name: '冲2' }}],
                '稳': [{{ school_name: '稳1' }}, {{ school_name: '稳2' }}],
                '保': [{{ school_name: '保1' }}]
              }}
            }})
            assert.deepEqual(
              flattened.map((item) => item.school_name),
              ['稳1', '冲1', '保1', '稳2', '冲2']
            )
            """
        )
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)

    def test_client_caches_identical_candidate_pool_requests(self):
        client = ROOT / "gaokao-proxy" / "lib" / "recommendation-context-client.js"
        script = textwrap.dedent(
            f"""
            const assert = require('node:assert/strict')
            let calls = 0
            global.fetch = async () => {{
              calls += 1
              return {{
                ok: true,
                json: async () => ({{ data_version: 'scores-2025-v1', tiers: {{ '冲': [], '稳': [], '保': [] }} }})
              }}
            }}
            const client = require({json.dumps(str(client))})
            const profile = {{ province: '广东', category: '物理类', score: 600, rank: 22000 }}
            ;(async () => {{
              await client.fetchRecommendationContext(profile, {{ scoreApiUrl: 'http://score-api', year: 2025 }})
              await client.fetchRecommendationContext(profile, {{ scoreApiUrl: 'http://score-api', year: 2025 }})
              assert.equal(calls, 1)
            }})().catch((err) => {{
              console.error(err)
              process.exitCode = 1
            }})
            """
        )
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
