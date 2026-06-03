#!/usr/bin/env python3
"""
将爬取的分数线 Markdown 数据生成 SQL 导入文件
然后在服务器上通过 docker exec psql 执行

用法：
  python3 data/generate_score_sql.py                         # 生成全部 kb2-scores-*.md
  python3 data/generate_score_sql.py --files kb2-scores-广东.md
  python3 data/generate_score_sql.py --import                # 生成并直接通过 SSH 导入到服务器
  python3 data/generate_score_sql.py --stats                 # 查看服务器数据库统计
"""

import argparse
import os
import re
import subprocess
import sys

# ============================================================
# 配置
# ============================================================

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge-base")
SQL_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_import_scores.sql")

SERVER = os.environ.get("GAOKAO_API_SERVER", "ubuntu@159.75.110.157")

PROVINCE_TYPES = {
    "河北": "3+1+2", "辽宁": "3+1+2", "江苏": "3+1+2", "福建": "3+1+2",
    "湖北": "3+1+2", "湖南": "3+1+2", "广东": "3+1+2", "重庆": "3+1+2",
    "黑龙江": "3+1+2", "甘肃": "3+1+2", "吉林": "3+1+2", "安徽": "3+1+2",
    "江西": "3+1+2", "广西": "3+1+2", "贵州": "3+1+2", "山西": "3+1+2",
    "河南": "3+1+2", "陕西": "3+1+2", "四川": "3+1+2", "内蒙古": "3+1+2",
    "云南": "3+1+2",
    "北京": "3+3", "天津": "3+3", "上海": "3+3", "浙江": "3+3",
    "山东": "3+3", "海南": "3+3",
    "西藏": "传统", "新疆": "传统",
}

PROVINCE_CODES = {
    "河北": "13", "山西": "14", "内蒙古": "15", "辽宁": "21", "吉林": "22",
    "黑龙江": "23", "江苏": "32", "浙江": "33", "安徽": "34", "福建": "35",
    "江西": "36", "山东": "37", "河南": "41", "湖北": "42", "湖南": "43",
    "广东": "44", "广西": "45", "海南": "46", "重庆": "50", "四川": "51",
    "贵州": "52", "云南": "53", "西藏": "54", "陕西": "61", "甘肃": "62",
    "北京": "11", "天津": "12", "上海": "31", "新疆": "65",
}


# ============================================================
# Markdown 解析 → SQL
# ============================================================

def escape_sql(s):
    """转义 SQL 单引号"""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def parse_and_generate_sql(file_path):
    """解析 Markdown 并生成 SQL INSERT 语句"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r"# KB-2 (\S+)省?高考录取分数线", content)
    if not m:
        print(f"  Cannot determine province from {file_path}")
        return [], ""
    province_name = m.group(1)

    sql_lines = []
    records = []
    current_school = None
    current_year = None
    current_batch = None

    # 生成省份 UPSERT（用 code 做 conflict key，同时更新 name）
    code = PROVINCE_CODES.get(province_name, "00")
    gk_type = PROVINCE_TYPES.get(province_name, "3+1+2")
    sql_lines.append(
        f"INSERT INTO provinces (code, name, gaokao_type) "
        f"VALUES ({escape_sql(code)}, {escape_sql(province_name)}, {escape_sql(gk_type)}) "
        f"ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, gaokao_type = EXCLUDED.gaokao_type;"
    )

    school_names = set()

    for line in content.split("\n"):
        line = line.strip()

        m = re.match(r"^## (.+?) - (\d{4})年$", line)
        if m:
            current_school = m.group(1).strip()
            current_year = int(m.group(2))
            school_names.add(current_school)
            continue

        m = re.match(r"^### (.+)$", line)
        if m and current_school:
            current_batch = m.group(1).strip()
            continue

        if line.startswith("|") and current_school and current_batch:
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 6:
                continue
            if cols[2] in ("科类", "---", ""):
                continue
            if not cols[2]:
                continue

            def to_int(s):
                s = s.strip().rstrip("|")
                if s in ("-", "", "None"):
                    return None
                try:
                    return int(s)
                except ValueError:
                    return None

            major_name = cols[1]
            category = cols[2]
            min_score = to_int(cols[3])
            min_rank = to_int(cols[4])
            avg_score = to_int(cols[5].rstrip("|").strip() if len(cols) > 5 else "-")

            records.append({
                "school": current_school,
                "year": current_year,
                "batch": current_batch,
                "category": category,
                "major_name": major_name,
                "min_score": min_score,
                "min_rank": min_rank,
                "avg_score": avg_score,
            })

    # 生成院校 INSERT（去重）
    for name in sorted(school_names):
        sql_lines.append(
            f"INSERT INTO schools (name) VALUES ({escape_sql(name)}) "
            f"ON CONFLICT DO NOTHING;"
        )

    # 生成分数 INSERT（使用子查询获取 id）
    for rec in records:
        school_esc = escape_sql(rec["school"])
        prov_esc = escape_sql(province_name)
        batch_esc = escape_sql(rec["batch"])
        cat_esc = escape_sql(rec["category"])
        major_esc = escape_sql(rec["major_name"])
        min_s = rec["min_score"] if rec["min_score"] is not None else "NULL"
        min_r = rec["min_rank"] if rec["min_rank"] is not None else "NULL"
        avg_s = rec["avg_score"] if rec["avg_score"] is not None else "NULL"

        sql_lines.append(
            f"INSERT INTO scores (school_id, province_id, year, batch, category, "
            f"major_name, min_score, min_rank, avg_score) "
            f"VALUES ("
            f"(SELECT id FROM schools WHERE name = {school_esc} LIMIT 1), "
            f"(SELECT id FROM provinces WHERE name = {prov_esc} LIMIT 1), "
            f"{rec['year']}, {batch_esc}, {cat_esc}, {major_esc}, "
            f"{min_s}, {min_r}, {avg_s});"
        )

    print(f"  {province_name}: {len(records)} records, {len(school_names)} schools")
    return records, "\n".join(sql_lines)


# ============================================================
# 服务器操作
# ============================================================

def remote_sql(sql, show_output=True):
    """通过 SSH + docker exec 执行 SQL"""
    # 先把 SQL 写到临时文件
    tmp_path = "/tmp/_gaokao_import.sql"
    with open(tmp_path, "w") as f:
        f.write(sql)

    # 传到服务器
    subprocess.run(
        ["scp", tmp_path, f"{SERVER}:/tmp/_gaokao_import.sql"],
        capture_output=True, timeout=30,
    )

    # 通过 docker exec psql 执行
    result = subprocess.run(
        ["ssh", SERVER,
         "docker exec -i docker-db_postgres-1 psql -U postgres -d gaokao "
         "< /tmp/_gaokao_import.sql"],
        capture_output=True, text=True, timeout=120,
    )

    if show_output:
        # 只显示非 INSERT 的输出（错误等）
        lines = result.stdout.strip().split("\n")
        errors = [l for l in lines if "ERROR" in l.upper() or "FATAL" in l.upper()]
        if errors:
            for e in errors[:10]:
                print(f"  SQL ERROR: {e}")
        inserts = [l for l in lines if l.startswith("INSERT")]
        print(f"  SQL executed: {len(inserts)} statements")

    return result


def show_stats():
    """远程查看数据库统计"""
    sql = """
    SELECT '--- 数据库统计 ---' AS info;
    SELECT '省份' AS metric, COUNT(*)::text AS value FROM provinces
    UNION ALL SELECT '院校', COUNT(*)::text FROM schools
    UNION ALL SELECT '分数记录', COUNT(*)::text FROM scores;

    SELECT '--- 各省统计 ---' AS info;
    SELECT p.name AS province,
           COUNT(s.id) AS records,
           COUNT(DISTINCT s.school_id) AS schools,
           string_agg(DISTINCT s.year::text, ', ' ORDER BY s.year::text) AS years
    FROM scores s JOIN provinces p ON s.province_id = p.id
    GROUP BY p.name ORDER BY records DESC;

    -- 示例：广东 2024 物理类 590-610 分
    SELECT '--- 示例：广东 2024 物理类 590-610 分 ---' AS info;
    SELECT sch.name, s.major_name, s.min_score, s.min_rank, s.batch
    FROM scores s
    JOIN schools sch ON s.school_id = sch.id
    JOIN provinces p ON s.province_id = p.id
    WHERE p.name = '广东' AND s.year = 2024
      AND s.category = '物理类' AND s.min_score BETWEEN 590 AND 610
    ORDER BY s.min_score DESC LIMIT 10;
    """
    result = remote_sql(sql, show_output=False)
    print(result.stdout)


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="导入分数线到 PostgreSQL")
    parser.add_argument("--files", nargs="+", help="只处理指定文件")
    parser.add_argument("--import", dest="do_import", action="store_true",
                        help="生成 SQL 并直接导入到服务器")
    parser.add_argument("--stats", action="store_true", help="查看服务器数据库统计")
    parser.add_argument("--reimport", action="store_true", help="清空后重新导入")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    # 获取待处理文件
    if args.files:
        files = []
        for f in args.files:
            if os.path.isabs(f):
                files.append(f)
            else:
                files.append(os.path.join(KB_DIR, f))
    else:
        files = []
        for f in sorted(os.listdir(KB_DIR)):
            if f.startswith("kb2-scores-") and f.endswith(".md") and "_part" not in f:
                files.append(os.path.join(KB_DIR, f))

    if not files:
        print("No kb2-scores-*.md files found")
        return

    # 生成 SQL
    all_sql_parts = []
    if args.reimport:
        all_sql_parts.append("TRUNCATE scores, schools, provinces RESTART IDENTITY CASCADE;")

    print(f"Processing {len(files)} files...\n")
    total_records = 0
    for fpath in files:
        records, sql = parse_and_generate_sql(fpath)
        total_records += len(records)
        all_sql_parts.append(sql)

    full_sql = "\n\n".join(all_sql_parts)

    # 写入 SQL 文件
    with open(SQL_OUTPUT, "w", encoding="utf-8") as f:
        f.write(full_sql)
    print(f"\nGenerated {total_records} INSERT statements → {SQL_OUTPUT}")

    if args.do_import:
        print("\nImporting to server...")
        remote_sql(full_sql)
        print("\nImport complete!")
        show_stats()
    else:
        print(f"\nUse --import to execute on server, or manually:")
        print(f"  scp {SQL_OUTPUT} {SERVER}:/tmp/")
        print(f"  ssh {SERVER} 'docker exec -i docker-db_postgres-1 psql -U postgres -d gaokao < /tmp/_import_scores.sql'")


if __name__ == "__main__":
    main()
