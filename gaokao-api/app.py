#!/usr/bin/env python3
"""
高考分数线 API 服务
提供查询接口供 Dify 和综合报告使用

运行:
  python3 gaokao-api/app.py

环境变量:
  DATABASE_URL: PostgreSQL 连接字符串
  API_PORT: 端口 (默认 5000)
"""

import os
import sys
import json
from flask import Flask, jsonify, request
from flask_cors import CORS

# ============================================================
# 配置
# ============================================================

app = Flask(__name__)
CORS(app)  # 允许跨域

# 数据源配置
USE_JSON = os.environ.get('USE_JSON', 'false').lower() == 'true'
JSON_PATH = os.environ.get('JSON_PATH', '/Users/MarkHuang/Desktop/高考志愿填报项目/scores.json')

# 数据库配置（兼容 PG_* 和 DATABASE_URL 两种格式）
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    pg_host = os.environ.get('PG_HOST', 'localhost')
    pg_port = os.environ.get('PG_PORT', '5432')
    pg_db = os.environ.get('PG_DB', 'gaokao')
    pg_user = os.environ.get('PG_USER', 'postgres')
    pg_pass = os.environ.get('PG_PASSWORD', 'postgres')
    DATABASE_URL = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'

# 省份 ID 映射（全局常量，避免重复定义）
PROVINCE_ID_MAP = {
    "河北": "13", "江苏": "32", "广东": "44", "湖北": "42", "湖南": "43",
    "福建": "35", "辽宁": "21", "重庆": "50", "安徽": "34", "江西": "36",
    "甘肃": "62", "广西": "45", "贵州": "52", "黑龙江": "23", "吉林": "22",
    "山西": "14", "河南": "41", "陕西": "61", "内蒙古": "15", "四川": "51",
    "云南": "53", "宁夏": "64", "青海": "63", "上海": "31", "浙江": "33",
    "天津": "12", "山东": "37", "北京": "11", "海南": "46", "西藏": "54",
    "新疆": "65",
}

# 科类别名映射：理科↔物理类, 文科↔历史类
CATEGORY_ALIASES = {
    '物理类': ['物理类', '理科'],
    '历史类': ['历史类', '文科'],
    '综合': ['综合'],
}

# 本地数据缓存
_local_data = None
_local_data_by_province_year_cat = None


def load_local_data():
    """加载本地 JSON 数据，构建查询索引"""
    global _local_data, _local_data_by_province_year_cat
    if _local_data is None:
        print(f"加载本地数据: {JSON_PATH}")
        with open(JSON_PATH, encoding='utf-8') as f:
            _local_data = json.load(f)

        # 构建索引: (province, year, normalized_category) -> [records]
        _local_data_by_province_year_cat = {}
        for r in _local_data:
            cat = r.get('category', '综合')
            # 归一化: 理科→物理类, 文科→历史类
            if cat in ('理科', '蒙授理科'):
                norm_cat = '物理类'
            elif cat in ('文科', '蒙授文科'):
                norm_cat = '历史类'
            elif cat.startswith('体育') or cat.startswith('艺术'):
                continue  # 跳过体育/艺术类，不参与冲稳保匹配
            else:
                norm_cat = cat

            key = (r['province_name'], r['year'], norm_cat)
            if key not in _local_data_by_province_year_cat:
                _local_data_by_province_year_cat[key] = []
            _local_data_by_province_year_cat[key].append(r)

        print(f"已加载 {len(_local_data):,} 条记录 (索引 {len(_local_data_by_province_year_cat)} 个分组)")

    return _local_data


def _get_filtered_data(province, year, category):
    """通过索引快速获取筛选后的数据"""
    load_local_data()
    key = (province, year, category)
    return _local_data_by_province_year_cat.get(key, [])


# 数据库支持 (延迟初始化)
_db_pool = None
HAS_DB = False

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import SimpleConnectionPool
    HAS_DB = True
except ImportError:
    pass


def _get_pool():
    global _db_pool
    if _db_pool is None and HAS_DB:
        _db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL
        )
    return _db_pool


def get_db():
    pool = _get_pool()
    if pool is None:
        raise Exception("数据库不可用")
    return pool.getconn()


def release_db(conn):
    if _db_pool is not None:
        _db_pool.putconn(conn)


# DB 模式下科类查询也需归一化
def _db_category_filter(category):
    """返回 SQL 查询的科类条件及参数"""
    aliases = CATEGORY_ALIASES.get(category, [category])
    if len(aliases) == 1:
        return "category = %s", aliases
    placeholders = ','.join(['%s'] * len(aliases))
    return f"category IN ({placeholders})", aliases


# ============================================================
# API 端点
# ============================================================

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    if USE_JSON:
        try:
            data = load_local_data()
            return jsonify({
                'status': 'ok',
                'mode': 'json',
                'records': len(data)
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        try:
            conn = get_db()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM scores LIMIT 1")
                cursor.close()
                return jsonify({'status': 'ok', 'database': 'connected'})
            finally:
                release_db(conn)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """数据统计"""
    if USE_JSON:
        try:
            data = load_local_data()

            result = {
                'total': len(data),
                'schools': len(set(r['school_name'] for r in data)),
                'years': len(set(r['year'] for r in data)),
                'provinces': len(set(r['province_name'] for r in data))
            }
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            conn = get_db()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                cursor.execute("""
                    SELECT 'total' as metric, COUNT(*) as count FROM scores
                    UNION ALL
                    SELECT 'schools', COUNT(DISTINCT school_name) FROM scores
                    UNION ALL
                    SELECT 'years', COUNT(DISTINCT year) FROM scores
                    UNION ALL
                    SELECT 'provinces', COUNT(DISTINCT province_id) FROM scores
                """)

                result = {row['metric']: row['count'] for row in cursor.fetchall()}
                cursor.close()

                return jsonify(result)
            finally:
                release_db(conn)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/scores/match', methods=['GET'])
def match_schools():
    """
    按分数匹配学校 (冲稳保三档)

    参数:
      province: 省份名称 (如: 广东)
      score: 分数
      category: 科类 (物理类/历史类, 默认: 物理类)
      year: 年份 (默认: 2024)
      limit: 每档返回数量 (默认: 10, 最大: 50)
    """
    try:
        province = request.args.get('province')
        score = int(request.args.get('score', 0))
        category = request.args.get('category', '物理类')
        year = int(request.args.get('year', 2025))
        limit = min(int(request.args.get('limit', 10)), 50)

        if not province or score == 0:
            return jsonify({'error': '缺少必要参数: province, score'}), 400

        if USE_JSON:
            filtered = _get_filtered_data(province, year, category)

            # 按学校分组
            schools = {}
            for r in filtered:
                if r.get('min_score') is None:
                    continue
                school = r['school_name']
                if school not in schools:
                    schools[school] = {
                        'school_name': school,
                        'majors': [],
                        'max_score': r['min_score'],
                        'min_score': r['min_score']
                    }
                schools[school]['majors'].append(r['major_name'])
                schools[school]['max_score'] = max(schools[school]['max_score'], r['min_score'])
                schools[school]['min_score'] = min(schools[school]['min_score'], r['min_score'])

            for s in schools.values():
                s['majors'] = '; '.join(s['majors'][:10])

            冲 = [s for s in schools.values() if score + 10 <= s['min_score'] <= score + 30]
            稳 = [s for s in schools.values() if score - 10 <= s['min_score'] <= score + 10]
            保 = [s for s in schools.values() if score - 30 <= s['min_score'] <= score - 10]

            冲.sort(key=lambda x: x['min_score'], reverse=True)
            稳.sort(key=lambda x: x['min_score'], reverse=True)
            保.sort(key=lambda x: x['min_score'], reverse=True)

            return jsonify({
                'province': province,
                'score': score,
                'category': category,
                'year': year,
                '冲': 冲[:limit],
                '稳': 稳[:limit],
                '保': 保[:limit]
            })

        else:
            conn = get_db()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                province_id = PROVINCE_ID_MAP.get(province, province)
                cat_cond, cat_params = _db_category_filter(category)

                base_where = f"province_id = %s AND {cat_cond} AND year = %s AND min_score >= %s AND min_score <= %s"
                base_params_prefix = [province_id] + cat_params + [year]

                cursor.execute(f"""
                    SELECT DISTINCT school_name, STRING_AGG(major_name, '; ') as majors,
                           MAX(min_score) as max_score, MIN(min_score) as min_score
                    FROM scores
                    WHERE {base_where}
                    GROUP BY school_name
                    ORDER BY min_score DESC
                    LIMIT %s
                """, base_params_prefix + [score + 10, score + 30, limit])

                冲 = cursor.fetchall()

                cursor.execute(f"""
                    SELECT DISTINCT school_name, STRING_AGG(major_name, '; ') as majors,
                           MAX(min_score) as max_score, MIN(min_score) as min_score
                    FROM scores
                    WHERE {base_where}
                    GROUP BY school_name
                    ORDER BY min_score DESC
                    LIMIT %s
                """, base_params_prefix + [score - 10, score + 10, limit])

                稳 = cursor.fetchall()

                cursor.execute(f"""
                    SELECT DISTINCT school_name, STRING_AGG(major_name, '; ') as majors,
                           MAX(min_score) as max_score, MIN(min_score) as min_score
                    FROM scores
                    WHERE {base_where}
                    GROUP BY school_name
                    ORDER BY min_score DESC
                    LIMIT %s
                """, base_params_prefix + [score - 30, score - 10, limit])

                保 = cursor.fetchall()

                cursor.close()

                return jsonify({
                    'province': province,
                    'score': score,
                    'category': category,
                    'year': year,
                    '冲': [dict(r) for r in 冲],
                    '稳': [dict(r) for r in 稳],
                    '保': [dict(r) for r in 保]
                })
            finally:
                release_db(conn)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scores/schools/<school_name>/provinces/<province>', methods=['GET'])
def get_school_scores(school_name, province):
    """查询学校在某省的专业分数线"""
    try:
        year = int(request.args.get('year', 2025))

        if USE_JSON:
            data = load_local_data()

            majors = [r for r in data if
                      r['school_name'] == school_name and
                      r['province_name'] == province and
                      r['year'] == year]

            majors.sort(key=lambda x: (x.get('batch', '本科批'), -(x.get('min_score') or 0)))

            return jsonify({
                'school_name': school_name,
                'province': province,
                'year': year,
                'majors': majors
            })

        else:
            conn = get_db()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                cursor.execute("""
                    SELECT major_name, category, batch, min_score, min_rank, avg_score
                    FROM scores
                    WHERE school_name = %s AND province_name = %s AND year = %s
                    ORDER BY batch, min_score DESC
                """, (school_name, province, year))

                majors = cursor.fetchall()
                cursor.close()

                return jsonify({
                    'school_name': school_name,
                    'province': province,
                    'year': year,
                    'majors': [dict(m) for m in majors]
                })
            finally:
                release_db(conn)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scores/majors/<keyword>', methods=['GET'])
def get_majors_by_keyword(keyword):
    """按专业关键词查询学校分数线"""
    try:
        province = request.args.get('province')
        year = int(request.args.get('year', 2025))
        limit = min(int(request.args.get('limit', 20)), 100)

        if USE_JSON:
            data = load_local_data()

            results = [r for r in data if
                       keyword.lower() in r['major_name'].lower() and
                       r['year'] == year]

            if province:
                results = [r for r in results if r['province_name'] == province]

            results.sort(key=lambda x: -(x.get('min_score') or 0))

            return jsonify({
                'keyword': keyword,
                'results': results[:limit]
            })

        else:
            conn = get_db()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                if province:
                    cursor.execute("""
                        SELECT school_name, province_name, major_name, min_score, min_rank
                        FROM scores
                        WHERE major_name LIKE %s AND province_name = %s AND year = %s
                        ORDER BY min_score DESC
                        LIMIT %s
                    """, (f'%{keyword}%', province, year, limit))
                else:
                    cursor.execute("""
                        SELECT school_name, province_name, major_name, min_score, min_rank
                        FROM scores
                        WHERE major_name LIKE %s AND year = %s
                        ORDER BY min_score DESC
                        LIMIT %s
                    """, (f'%{keyword}%', year, limit))

                results = cursor.fetchall()
                cursor.close()

                return jsonify({
                    'keyword': keyword,
                    'results': [dict(r) for r in results]
                })
            finally:
                release_db(conn)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scores/recommend', methods=['GET'])
def recommend():
    """
    推荐接口 (综合报告用)
    根据省份、分数、选科推荐学校

    参数:
      province: 省份
      score: 分数
      category: 科类
      year: 年份
      limit: 返回数量 (默认: 10, 最大: 50)
    """
    try:
        province = request.args.get('province')
        score = int(request.args.get('score', 0))
        category = request.args.get('category', '物理类')
        year = int(request.args.get('year', 2025))
        limit = min(int(request.args.get('limit', 10)), 50)

        if not province or score == 0:
            return jsonify({'error': '缺少必要参数'}), 400

        if USE_JSON:
            filtered = _get_filtered_data(province, year, category)

            # 按学校分组
            schools = {}
            for r in filtered:
                if r.get('min_score') is None:
                    continue
                if not (score - 30 <= r['min_score'] <= score + 30):
                    continue
                school = r['school_name']
                if school not in schools:
                    schools[school] = {
                        'school_name': school,
                        'min_score': r['min_score'],
                        'majors': [],
                        'has_985': r.get('is_985', False),
                        'has_211': r.get('is_211', False)
                    }
                schools[school]['majors'].append(r['major_name'])
                schools[school]['min_score'] = min(schools[school]['min_score'], r['min_score'])
                if r.get('is_985'):
                    schools[school]['has_985'] = True
                if r.get('is_211'):
                    schools[school]['has_211'] = True

            for s in schools.values():
                s['majors'] = '; '.join(list(set(s['majors']))[:10])

            recommendations = list(schools.values())
            for r in recommendations:
                s = r['min_score']
                if s > score + 10:
                    r['tier'] = '冲'
                elif s >= score - 10:
                    r['tier'] = '稳'
                else:
                    r['tier'] = '保'

            recommendations.sort(key=lambda x: -x['min_score'])

            return jsonify({
                'recommendations': recommendations[:limit]
            })

        else:
            conn = get_db()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                province_id = PROVINCE_ID_MAP.get(province, province)
                cat_cond, cat_params = _db_category_filter(category)

                cursor.execute(f"""
                    SELECT DISTINCT school_name, MIN(min_score) as min_score,
                           STRING_AGG(DISTINCT major_name, '; ') as majors,
                           BOOL_OR(is_985) as has_985, BOOL_OR(is_211) as has_211
                    FROM scores
                    WHERE province_id = %s AND {cat_cond} AND year = %s
                      AND min_score >= %s AND min_score <= %s
                    GROUP BY school_name
                    ORDER BY min_score DESC
                    LIMIT %s
                """, [province_id] + cat_params + [year, score - 30, score + 30, limit])

                recommendations = cursor.fetchall()
                cursor.close()

                for r in recommendations:
                    s = r['min_score']
                    if s > score + 10:
                        r['tier'] = '冲'
                    elif s >= score - 10:
                        r['tier'] = '稳'
                    else:
                        r['tier'] = '保'

                return jsonify({
                    'recommendations': [dict(r) for r in recommendations]
                })
            finally:
                release_db(conn)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 错误处理
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================
# 主程序
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
