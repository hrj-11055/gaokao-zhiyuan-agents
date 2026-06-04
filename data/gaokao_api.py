#!/usr/bin/env python3
"""
高考分数线查询 API 服务

提供给 Dify HTTP Request 工具调用，支持精确的分数线检索。

部署：
  docker run -d --name gaokao-api --network docker_default \
    -e PG_HOST=172.20.0.5 -p 5001:5000 gaokao-api

端点：
  GET /api/health                    - 健康检查
  GET /api/stats                     - 数据统计
  GET /api/scores                    - 查询分数线（支持多种筛选）
  GET /api/recommend                 - 按分数推荐院校
  GET /api/schools/<name>/scores     - 查询指定院校分数线
  GET /api/schools/<name>/min-scores - 查询指定院校各省最低录取分（院校级）
  GET /api/major/<keyword>/scores    - 按专业关键词查询
  GET /api/reports/health            - 报告库健康检查
  GET /api/reports/majors            - 查询专业深度报告
  GET /api/reports/majors/<code>     - 查询单个专业深度报告
  GET /api/reports/universities      - 查询大学深度报告
  GET /api/reports/universities/<name> - 查询单个大学深度报告
"""

import os
import psycopg2
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "postgres"),
    "dbname": os.environ.get("PG_DB", "gaokao"),
}

REPORT_API_TOKEN = os.environ.get("REPORT_API_TOKEN", "")
REPORT_PG_CONFIG = {
    "host": os.environ.get("REPORT_PG_HOST", os.environ.get("PG_HOST", "localhost")),
    "port": int(os.environ.get("REPORT_PG_PORT", os.environ.get("PG_PORT", "5432"))),
    "user": os.environ.get("REPORT_PG_USER", os.environ.get("PG_USER", "postgres")),
    "password": os.environ.get("REPORT_PG_PASSWORD", os.environ.get("PG_PASSWORD", "postgres")),
    "dbname": os.environ.get("REPORT_PG_DB", "gaokao_db"),
}

THREE_PLUS_THREE_PROVINCES = {"北京", "天津", "上海", "浙江", "山东", "海南"}

# 全局连接
_conn = None
_report_conn = None


def query(sql, params=None):
    global _conn
    try:
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(**PG_CONFIG)
        with _conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                cols = [desc[0] for desc in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
                _conn.rollback()  # 读操作后 rollback 释放事务
                return rows
            _conn.rollback()
            return []
    except Exception:
        _conn = None
        raise


def report_query(sql, params=None):
    global _report_conn
    try:
        if _report_conn is None or _report_conn.closed:
            _report_conn = psycopg2.connect(**REPORT_PG_CONFIG)
        with _report_conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                cols = [desc[0] for desc in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
                _report_conn.rollback()
                return rows
            _report_conn.rollback()
            return []
    except Exception:
        _report_conn = None
        raise


def require_report_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if REPORT_API_TOKEN and request.headers.get("X-Report-Token") != REPORT_API_TOKEN:
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


def normalize_province_name(province):
    return (
        str(province or "")
        .replace("壮族自治区", "")
        .replace("回族自治区", "")
        .replace("维吾尔自治区", "")
        .replace("省", "")
        .replace("市", "")
        .replace("自治区", "")
        .replace("特别行政区", "")
        .strip()
    )


def normalize_score_category(province, category):
    province_clean = normalize_province_name(province)
    category_clean = str(category or "").strip()
    if province_clean in THREE_PLUS_THREE_PROVINCES and category_clean in ("物理类", "历史类", "理科", "文科", "综合"):
        return "综合"
    if category_clean == "理科":
        return "物理类"
    if category_clean == "文科":
        return "历史类"
    return category_clean


def score_category_aliases(province, category):
    province_clean = normalize_province_name(province)
    category_clean = str(category or "").strip()
    if province_clean in THREE_PLUS_THREE_PROVINCES and category_clean in ("物理类", "历史类", "理科", "文科", "综合"):
        return ["综合"]
    if category_clean in ("物理类", "理科"):
        return ["物理类", "理科"]
    if category_clean in ("历史类", "文科"):
        return ["历史类", "文科"]
    return [category_clean] if category_clean else []


def add_category_condition(conditions, params, column, province, category):
    aliases = score_category_aliases(province, category)
    if not aliases:
        return
    if len(aliases) == 1:
        conditions.append(f"{column} = %s")
        params.append(aliases[0])
        return
    placeholders = ",".join(["%s"] * len(aliases))
    conditions.append(f"{column} IN ({placeholders})")
    params.extend(aliases)


def parse_pagination_args():
    page = max(1, request.args.get("page", 1, type=int))
    page_size = min(100, max(1, request.args.get("page_size", 20, type=int)))
    return page, page_size, (page - 1) * page_size


def wants_full_report():
    return request.args.get("full", "").lower() in ("1", "true", "yes")


def report_summary(data):
    if not isinstance(data, dict):
        return ""
    layer2 = data.get("layer2_core") or {}
    if isinstance(layer2, dict) and layer2.get("summary"):
        return layer2["summary"]
    layer1 = data.get("layer1_overview") or {}
    if isinstance(layer1, dict) and layer1.get("summary"):
        return layer1["summary"]
    layer4 = data.get("layer4_supplement") or {}
    if isinstance(layer4, dict) and layer4.get("full_raw_content"):
        return layer4["full_raw_content"][:260]
    return ""


def calculate_report_word_count(data):
    """按深度报告阅读器实际展示的正文计算字数。"""
    if not isinstance(data, dict):
        return 0

    count = 0
    layer3 = data.get("layer3_detail") or data.get("layer3_details") or {}
    if isinstance(layer3, dict):
        for module in layer3.values():
            if isinstance(module, dict):
                count += len(module.get("raw_content") or "")
    if count > 0:
        return count

    layer4 = data.get("layer4_supplement") or {}
    if isinstance(layer4, dict):
        return len(layer4.get("full_raw_content") or "")
    return 0


def with_visible_word_count(row):
    normalized = dict(row)
    normalized["word_count"] = calculate_report_word_count(normalized.get("data"))
    return normalized


def public_major(row):
    row = with_visible_word_count(row)
    data = row.get("data") or {}
    return {
        "code": row.get("code"),
        "name": row.get("name"),
        "category": row.get("category"),
        "overview": data.get("layer1_overview") if isinstance(data, dict) else None,
        "summary": report_summary(data),
        "word_count": row.get("word_count") or 0,
        "available_pdf": (row.get("word_count") or 0) >= 5000,
    }


def public_university(row):
    row = with_visible_word_count(row)
    data = row.get("data") or {}
    return {
        "name": row.get("name"),
        "province": row.get("province"),
        "univ_type": row.get("univ_type"),
        "overview": data.get("layer1_overview") if isinstance(data, dict) else None,
        "summary": report_summary(data),
        "word_count": row.get("word_count") or 0,
        "available_pdf": (row.get("word_count") or 0) >= 5000,
    }


def build_major_where():
    conditions = []
    params = []

    category = request.args.get("category", "")
    if category:
        conditions.append("category LIKE %s")
        params.append(f"{category}%")

    level = request.args.get("level", "")
    if level:
        conditions.append("(data->'layer1_overview'->>'recommendation_level') = %s")
        params.append(level)

    search = request.args.get("search", "")
    if search:
        conditions.append("(name ILIKE %s OR code ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    min_score = request.args.get("min_score", type=float)
    if min_score is not None:
        conditions.append("NULLIF(data->'layer1_overview'->>'weighted_score', '')::float >= %s")
        params.append(min_score)

    return conditions, params


def build_university_where():
    conditions = []
    params = []

    province = request.args.get("province", "")
    if province:
        conditions.append("province LIKE %s")
        params.append(f"%{province}%")

    univ_type = request.args.get("type", "")
    if univ_type:
        conditions.append("univ_type = %s")
        params.append(univ_type)

    level = request.args.get("level", "")
    if level:
        conditions.append("(data->'layer1_overview'->>'recommendation_level') = %s")
        params.append(level)

    search = request.args.get("search", "")
    if search:
        conditions.append("name ILIKE %s")
        params.append(f"%{search}%")

    min_score = request.args.get("min_score", type=float)
    if min_score is not None:
        conditions.append("NULLIF(data->'layer1_overview'->>'weighted_score', '')::float >= %s")
        params.append(min_score)

    return conditions, params


# ============================================================
# API 路由
# ============================================================

@app.route("/api/health")
def health():
    try:
        result = query("SELECT COUNT(*) as cnt FROM scores")
        return jsonify({"status": "ok", "records": result[0]["cnt"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stats")
def stats():
    prov = query("SELECT name, gaokao_type FROM provinces ORDER BY name")
    total = query("SELECT COUNT(*) as scores FROM scores")
    schools = query("SELECT COUNT(*) as schools FROM schools")
    by_prov = query("""
        SELECT p.name, COUNT(s.id) as records,
               COUNT(DISTINCT s.school_id) as schools,
               array_agg(DISTINCT s.year) as years
        FROM scores s JOIN provinces p ON s.province_id = p.id
        GROUP BY p.name ORDER BY records DESC
    """)
    return jsonify({
        "provinces": prov,
        "total_scores": total[0]["scores"],
        "total_schools": schools[0]["schools"],
        "by_province": by_prov,
    })


@app.route("/api/scores")
def search_scores():
    """
    通用分数线查询

    参数：
      province   - 省份名（如"广东"或"广东省"），支持模糊匹配
      year       - 年份（如 2024）
      category   - 科类（如"物理类"、"历史类"）
      batch      - 批次（如"本科批"）
      school     - 院校名关键词
      major      - 专业名关键词
      min_score  - 最低分下限
      max_score  - 最低分上限
      min_rank   - 最低位次上限（即排名更高）
      max_rank   - 最低位次下限
      limit      - 返回条数（默认 50，最大 200）
      offset     - 偏移量
    """
    conditions = []
    params = []

    province = request.args.get("province", "")
    if province:
        province_clean = normalize_province_name(province)
        conditions.append("p.name LIKE %s")
        params.append(f"%{province_clean}%")

    year = request.args.get("year", type=int)
    if year:
        conditions.append("s.year = %s")
        params.append(year)

    category = request.args.get("category", "")
    if category:
        add_category_condition(conditions, params, "s.category", province, category)

    batch = request.args.get("batch", "")
    if batch:
        conditions.append("s.batch = %s")
        params.append(batch)

    school = request.args.get("school", "")
    if school:
        conditions.append("sch.name LIKE %s")
        params.append(f"%{school}%")

    major = request.args.get("major", "")
    if major:
        conditions.append("s.major_name LIKE %s")
        params.append(f"%{major}%")

    min_score = request.args.get("min_score", type=int)
    if min_score:
        conditions.append("s.min_score >= %s")
        params.append(min_score)

    max_score = request.args.get("max_score", type=int)
    if max_score:
        conditions.append("s.min_score <= %s")
        params.append(max_score)

    min_rank = request.args.get("min_rank", type=int)
    if min_rank:
        conditions.append("s.min_rank <= %s")
        params.append(min_rank)

    max_rank = request.args.get("max_rank", type=int)
    if max_rank:
        conditions.append("s.min_rank >= %s")
        params.append(max_rank)

    limit = min(request.args.get("limit", 50, type=int), 200)
    offset = request.args.get("offset", 0, type=int)

    where = " AND ".join(conditions) if conditions else "1=1"

    # 总数
    count_sql = """
        SELECT COUNT(*) as total
        FROM scores s
        JOIN schools sch ON s.school_id = sch.id
        JOIN provinces p ON s.province_id = p.id
        WHERE {where}
    """.format(where=where)
    total = query(count_sql, params)[0]["total"]

    # 数据
    data_sql = """
        SELECT sch.name as school, p.name as province, s.year, s.batch,
               s.category, s.major_name, s.min_score, s.min_rank, s.avg_score
        FROM scores s
        JOIN schools sch ON s.school_id = sch.id
        JOIN provinces p ON s.province_id = p.id
        WHERE {where}
        ORDER BY s.min_score DESC
        LIMIT %s OFFSET %s
    """.format(where=where)
    rows = query(data_sql, params + [limit, offset])

    return jsonify({"total": total, "limit": limit, "offset": offset, "data": rows})


@app.route("/api/recommend")
def recommend():
    """
    按分数推荐院校

    参数：
      province   - 省份（必填）
      score      - 考生分数（必填）
      category   - 科类（如"物理类"，必填）
      year       - 年份（默认 2024）
      range      - 分数浮动范围（默认 ±30）
      batch      - 批次筛选
      limit      - 返回条数（默认 30）
    """
    province = request.args.get("province", "")
    score = request.args.get("score", type=int)
    category = request.args.get("category", "")
    year = request.args.get("year", 2024, type=int)
    score_range = request.args.get("range", 30, type=int)
    batch = request.args.get("batch", "")
    limit = min(request.args.get("limit", 30, type=int), 100)

    if not province or not score or not category:
        return jsonify({"error": "province, score, category are required"}), 400

    conditions = [
        "p.name LIKE %s",
        "s.year = %s",
        "s.min_score BETWEEN %s AND %s",
        "s.min_score IS NOT NULL",
    ]
    province_clean = normalize_province_name(province)
    params = [f"%{province_clean}%", year, score - score_range, score + score_range]
    add_category_condition(conditions, params, "s.category", province_clean, category)

    if batch:
        conditions.append("s.batch = %s")
        params.append(batch)

    where = " AND ".join(conditions)

    sql = """
        SELECT sch.name as school, s.major_name, s.min_score, s.min_rank,
               s.avg_score, s.batch, s.category,
               ({score} - s.min_score) as score_diff
        FROM scores s
        JOIN schools sch ON s.school_id = sch.id
        JOIN provinces p ON s.province_id = p.id
        WHERE {where}
        ORDER BY ABS({score} - s.min_score), s.min_score DESC
        LIMIT {limit}
    """.format(where=where, score=score, limit=limit)
    rows = query(sql, params)

    # 按院校汇总
    school_summary = {}
    for row in rows:
        sch = row["school"]
        if sch not in school_summary:
            school_summary[sch] = {
                "school": sch,
                "min_score": row["min_score"],
                "max_score": row["min_score"],
                "majors": [],
                "match_count": 0,
            }
        school_summary[sch]["min_score"] = min(
            school_summary[sch]["min_score"], row["min_score"]
        )
        school_summary[sch]["max_score"] = max(
            school_summary[sch]["max_score"], row["min_score"]
        )
        school_summary[sch]["match_count"] += 1
        school_summary[sch]["majors"].append({
            "name": row["major_name"],
            "min_score": row["min_score"],
            "min_rank": row["min_rank"],
            "score_diff": row["score_diff"],
        })

    # 按匹配专业数排序
    summary_list = sorted(
        school_summary.values(), key=lambda x: (-x["match_count"], abs(x["min_score"] - score))
    )

    return jsonify({
        "query": {"province": province, "score": score, "category": category, "query_category": normalize_score_category(province, category), "year": year},
        "total_majors": len(rows),
        "total_schools": len(summary_list),
        "schools": summary_list,
        "sample_majors": rows[:20],
    })


@app.route("/api/schools/<name>/scores")
def school_scores(name):
    """查询指定院校的分数线"""
    province = request.args.get("province", "")
    year = request.args.get("year", type=int)
    category = request.args.get("category", "")
    limit = min(request.args.get("limit", 100, type=int), 500)

    conditions = ["sch.name LIKE %s"]
    params = [f"%{name}%"]

    if province:
        province_clean = normalize_province_name(province)
        conditions.append("p.name LIKE %s")
        params.append(f"%{province_clean}%")
    if year:
        conditions.append("s.year = %s")
        params.append(year)
    if category:
        add_category_condition(conditions, params, "s.category", province, category)

    where = " AND ".join(conditions)
    sql = """
        SELECT sch.name as school, p.name as province, s.year, s.batch,
               s.category, s.major_name, s.min_score, s.min_rank, s.avg_score
        FROM scores s
        JOIN schools sch ON s.school_id = sch.id
        JOIN provinces p ON s.province_id = p.id
        WHERE {where}
        ORDER BY s.year DESC, s.min_score DESC
        LIMIT %s
    """.format(where=where)
    rows = query(sql, params + [limit])
    return jsonify({"total": len(rows), "data": rows})


@app.route("/api/schools/<name>/min-scores")
def school_min_scores(name):
    """
    查询指定院校在全国各省的最低录取分（院校级）

    参数：
      year       - 年份（默认 2024）
      category   - 科类（如"物理类"、"历史类"）
      enrollment - 招生类型（默认"普通类"）
      limit      - 返回条数（默认 200）
    """
    year = request.args.get("year", 2024, type=int)
    category = request.args.get("category", "")
    enrollment = request.args.get("enrollment", "普通类")
    limit = min(request.args.get("limit", 200, type=int), 500)

    conditions = ["school_name LIKE %s", "year = %s", "min_score IS NOT NULL"]
    params = [f"%{name}%", year]

    if category:
        add_category_condition(conditions, params, "type_name", "", category)
    if enrollment:
        conditions.append("enrollment_type = %s")
        params.append(enrollment)

    where = " AND ".join(conditions)

    sql = """
        SELECT province, type_name, batch_name, enrollment_type,
               MIN(min_score) as min_score,
               MIN(min_rank) as min_rank,
               MAX(max_score) as max_score
        FROM school_scores
        WHERE {where}
        GROUP BY province, type_name, batch_name, enrollment_type
        ORDER BY province, type_name
        LIMIT %s
    """.format(where=where)
    rows = query(sql, params + [limit])

    school_info = query("""
        SELECT DISTINCT school_name, is_985, is_211, nature
        FROM school_scores
        WHERE school_name LIKE %s
        LIMIT 1
    """, [f"%{name}%"])

    return jsonify({
        "school": school_info[0] if school_info else None,
        "year": year,
        "total": len(rows),
        "data": rows,
    })


@app.route("/api/major/<keyword>/scores")
def major_scores(keyword):
    """按专业关键词查询分数线"""
    province = request.args.get("province", "")
    year = request.args.get("year", type=int)
    limit = min(request.args.get("limit", 100, type=int), 500)

    conditions = ["s.major_name LIKE %s"]
    params = [f"%{keyword}%"]

    if province:
        province_clean = normalize_province_name(province)
        conditions.append("p.name LIKE %s")
        params.append(f"%{province_clean}%")
    if year:
        conditions.append("s.year = %s")
        params.append(year)

    where = " AND ".join(conditions)
    sql = """
        SELECT sch.name as school, p.name as province, s.year, s.batch,
               s.category, s.major_name, s.min_score, s.min_rank, s.avg_score
        FROM scores s
        JOIN schools sch ON s.school_id = sch.id
        JOIN provinces p ON s.province_id = p.id
        WHERE {where}
        ORDER BY s.min_score DESC
        LIMIT %s
    """.format(where=where)
    rows = query(sql, params + [limit])
    return jsonify({"total": len(rows), "data": rows})


@app.route("/api/reports/health")
@require_report_token
def reports_health():
    try:
        majors = report_query("SELECT COUNT(*) AS total FROM majors")[0]["total"]
        universities = report_query("SELECT COUNT(*) AS total FROM universities")[0]["total"]
        return jsonify({
            "status": "ok",
            "postgres": "connected",
            "majors": majors,
            "universities": universities,
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "postgres": "disconnected",
            "message": str(e),
        }), 500


@app.route("/api/reports/stats")
@require_report_token
def reports_stats():
    rows = report_query("SELECT * FROM stats_overview")
    stats = {}
    for row in rows:
        stats[row["table_name"]] = {
            "total": int(row["total_count"]),
            "green": int(row["green_count"]),
            "yellow": int(row["yellow_count"]),
            "red": int(row["red_count"]),
            "avg_score": float(row["avg_score"] or 0),
        }
    return jsonify(stats)


@app.route("/api/reports/majors")
@require_report_token
def reports_majors():
    page, page_size, offset = parse_pagination_args()
    conditions, params = build_major_where()
    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = report_query(f"SELECT COUNT(*) AS total FROM majors {where}", params)[0]["total"]
    rows = report_query(
        f"""
        SELECT code, name, category, data, word_count
        FROM majors {where}
        ORDER BY NULLIF(data->'layer1_overview'->>'weighted_score', '')::float DESC NULLS LAST
        LIMIT %s OFFSET %s
        """,
        params + [page_size, offset],
    )

    data = [with_visible_word_count(row) for row in rows] if wants_full_report() else [public_major(row) for row in rows]
    return jsonify({
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "data": data,
    })


@app.route("/api/reports/majors/<code>")
@require_report_token
def reports_major_detail(code):
    rows = report_query(
        "SELECT code, name, category, data, word_count FROM majors WHERE code = %s",
        [code],
    )
    if not rows:
        return jsonify({"error": "专业不存在"}), 404
    row = rows[0]
    return jsonify(with_visible_word_count(row) if wants_full_report() else public_major(row))


@app.route("/api/reports/universities")
@require_report_token
def reports_universities():
    page, page_size, offset = parse_pagination_args()
    conditions, params = build_university_where()
    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = report_query(f"SELECT COUNT(*) AS total FROM universities {where}", params)[0]["total"]
    rows = report_query(
        f"""
        SELECT name, province, univ_type, data, word_count
        FROM universities {where}
        ORDER BY NULLIF(data->'layer1_overview'->>'weighted_score', '')::float DESC NULLS LAST
        LIMIT %s OFFSET %s
        """,
        params + [page_size, offset],
    )

    data = [with_visible_word_count(row) for row in rows] if wants_full_report() else [public_university(row) for row in rows]
    return jsonify({
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "data": data,
    })


@app.route("/api/reports/universities/<path:name>")
@require_report_token
def reports_university_detail(name):
    rows = report_query(
        "SELECT name, province, univ_type, data, word_count FROM universities WHERE name = %s",
        [name],
    )
    if not rows:
        return jsonify({"error": "院校不存在"}), 404
    row = rows[0]
    return jsonify(with_visible_word_count(row) if wants_full_report() else public_university(row))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
