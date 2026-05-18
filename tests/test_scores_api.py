#!/usr/bin/env python3
"""
分数线 API 测试

运行: python3 tests/test_scores_api.py

环境变量:
  API_BASE: API 地址 (默认 http://localhost:5000)
"""

import os
import sys
import requests
from pathlib import Path

# API 配置
API_BASE = os.environ.get('API_BASE', 'http://localhost:5000')


def test_health():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试 1: 健康检查")
    print("="*60)

    try:
        resp = requests.get(f"{API_BASE}/api/health", timeout=5)
        data = resp.json()

        print(f"状态码: {resp.status_code}")
        print(f"响应: {data}")

        if resp.status_code == 200 and data.get('status') == 'ok':
            print("✅ 通过")
            return True
        else:
            print("❌ 失败")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_stats():
    """测试数据统计"""
    print("\n" + "="*60)
    print("测试 2: 数据统计")
    print("="*60)

    try:
        resp = requests.get(f"{API_BASE}/api/stats", timeout=10)
        data = resp.json()

        print(f"总记录数: {data.get('total', 'N/A')}")
        print(f"学校数量: {data.get('schools', 'N/A')}")
        print(f"年份覆盖: {data.get('years', 'N/A')}")
        print(f"省份覆盖: {data.get('provinces', 'N/A')}")

        if resp.status_code == 200 and data.get('total', 0) > 900000:
            print("✅ 通过")
            return True
        else:
            print("❌ 失败: 数据量不足")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_match_schools():
    """测试分数匹配学校"""
    print("\n" + "="*60)
    print("测试 3: 分数匹配 (广东600分物理类)")
    print("="*60)

    try:
        params = {
            'province': '广东',
            'score': 600,
            'category': '物理类',
            'year': 2024,
            'limit': 5
        }
        resp = requests.get(f"{API_BASE}/api/scores/match", params=params, timeout=10)
        data = resp.json()

        if 'error' in data:
            print(f"❌ 失败: {data['error']}")
            return False

        冲_count = len(data.get('冲', []))
        稳_count = len(data.get('稳', []))
        保_count = len(data.get('保', []))

        print(f"冲一档: {冲_count} 所")
        print(f"稳一档: {稳_count} 所")
        print(f"保一档: {保_count} 所")

        if data.get('冲'):
            print(f"  冲一档示例: {data['冲'][0]['school_name']}")

        if 冲_count >= 3 and 稳_count >= 3 and 保_count >= 3:
            print("✅ 通过")
            return True
        else:
            print("❌ 失败: 推荐数量不足")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_school_query():
    """测试学校查询"""
    print("\n" + "="*60)
    print("测试 4: 学校查询 (中山大学在广东)")
    print("="*60)

    try:
        url = f"{API_BASE}/api/scores/schools/中山大学/provinces/广东"
        resp = requests.get(url, params={'year': 2024}, timeout=10)
        data = resp.json()

        if 'error' in data:
            print(f"❌ 失败: {data['error']}")
            return False

        majors = data.get('majors', [])
        print(f"专业数量: {len(majors)}")

        if majors:
            print(f"  示例: {majors[0]['major_name']} - {majors[0].get('min_score', 'N/A')}分")

        if len(majors) >= 10:
            print("✅ 通过")
            return True
        else:
            print("❌ 失败: 专业数量不足")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_major_query():
    """测试专业查询"""
    print("\n" + "="*60)
    print("测试 5: 专业查询 (计算机)")
    print("="*60)

    try:
        url = f"{API_BASE}/api/scores/majors/计算机"
        resp = requests.get(url, params={'province': '广东', 'year': 2024, 'limit': 5}, timeout=10)
        data = resp.json()

        if 'error' in data:
            print(f"❌ 失败: {data['error']}")
            return False

        results = data.get('results', [])
        print(f"结果数量: {len(results)}")

        if results:
            print(f"  示例: {results[0]['school_name']} {results[0]['major_name']}")

        if len(results) >= 3:
            print("✅ 通过")
            return True
        else:
            print("❌ 失败: 结果数量不足")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_recommend():
    """测试推荐接口"""
    print("\n" + "="*60)
    print("测试 6: 推荐接口")
    print("="*60)

    try:
        params = {
            'province': '广东',
            'score': 600,
            'category': '物理类',
            'year': 2024,
            'limit': 10
        }
        resp = requests.get(f"{API_BASE}/api/scores/recommend", params=params, timeout=10)
        data = resp.json()

        if 'error' in data:
            print(f"❌ 失败: {data['error']}")
            return False

        recommendations = data.get('recommendations', [])
        print(f"推荐数量: {len(recommendations)}")

        # 统计冲稳保
        tiers = {}
        for r in recommendations:
            tier = r.get('tier', 'unknown')
            tiers[tier] = tiers.get(tier, 0) + 1

        print(f"冲稳保分布: {tiers}")

        if len(recommendations) >= 5:
            print("✅ 通过")
            return True
        else:
            print("❌ 失败: 推荐数量不足")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_performance():
    """测试性能 (响应时间)"""
    print("\n" + "="*60)
    print("测试 7: 性能测试 (响应时间)")
    print("="*60)

    try:
        import time

        times = []
        for i in range(10):
            start = time.time()
            resp = requests.get(
                f"{API_BASE}/api/scores/match",
                params={'province': '广东', 'score': 600, 'category': '物理类'},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"平均响应时间: {avg_time:.0f}ms")
        print(f"P95 响应时间: {p95_time:.0f}ms")

        if avg_time < 500 and p95_time < 1000:
            print("✅ 通过")
            return True
        else:
            print("❌ 失败: 响应时间过慢")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("分数线 API 测试套件")
    print(f"API 地址: {API_BASE}")
    print("="*60)

    results = []

    results.append(('健康检查', test_health()))
    results.append(('数据统计', test_stats()))
    results.append(('分数匹配', test_match_schools()))
    results.append(('学校查询', test_school_query()))
    results.append(('专业查询', test_major_query()))
    results.append(('推荐接口', test_recommend()))
    results.append(('性能测试', test_performance()))

    # 汇总报告
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count:.1%})")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
