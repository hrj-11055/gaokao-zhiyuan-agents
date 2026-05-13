#!/usr/bin/env python3
"""
将爬取的分数线 Markdown 数据导入 PostgreSQL

用法：
  python3 data/import_scores_to_pg.py                        # 导入全部 kb2-scores-*.md
  python3 data/import_scores_to_pg.py --files kb2-scores-广东.md  # 只导入指定文件
  python3 data/import_scores_to_pg.py --stats                 # 查看数据库统计
  python3 data/import_scores_to_pg.py --reimport              # 清空后重新导入

环境变量（或直接修改下方配置）：
  PG_HOST: PostgreSQL 地址（默认 localhost）
  PG_PORT: 端口（默认 5432）
  PG_USER: 用户名（默认 postgres）
  PG_PASSWORD: 密码（默认 postgres）
  PG_DB: 数据库名（默认 gaokao）
"""

import argparse
import os
import re
import sys

try:
    import psycopg2
except ImportError:
    print("需要 psycopg2: pip3 install psycopg2-binary")
    sys.exit(1)

# ============================================================
# 配置
# ============================================================

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge-base")

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "postgres"),
    "dbname": os.environ.get("PG_DB", "gaokao"),
}

# 省份编码映射（code → gaokao_type）
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

# 省份名称 → code 映射
PROVINCE_CODES = {
    "河北": "13", "山西": "14", "内蒙古": "15", "辽宁": "21", "吉林": "22",
    "黑龙江": "23", "江苏": "32", "浙江": "33", "安徽": "34", "福建": "35",
    "江西": "36", "山东": "37", "河南": "41", "湖北": "42", "湖南": "43",
    "广东": "44", "广西": "45", "海南": "46", "重庆": "50", "四川": "51",
    "贵州": "52", "云南": "53", "西藏": "54", "陕西": "61", "甘肃": "62",
    "北京": "11", "天津": "12", "上海": "31", "新疆": "65",
}


# ============================================================
# Markdown 解析
# ============================================================

def parse_score_md(file_path):
    """
    解析 kb2-scores-{省份}.md 文件
    返回: (province_name, records)
    records = [
        {
            "school": "清华大学", "year": 2024,
            "batch": "本科批", "category": "物理类",
            "major_name": "计算机类", "min_score": 701,
            "min_rank": 7, "avg_score": None,
        },
        ...
    ]
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取省份名
    m = re.search(r"# KB-2 (\S+)省?高考录取分数线", content)
    if not m:
        print(f"  Cannot determine province from file: {file_path}")
        return None, []
    province_name = m.group(1)

    records = []
    current_school = None
    current_year = None
    current_batch = None

    for line in content.split("\n"):
        line = line.strip()

        # 学校-年份标题: ## 清华大学 - 2024年
        m = re.match(r"^## (.+?) - (\d{4})年$", line)
        if m:
            current_school = m.group(1).strip()
            current_year = int(m.group(2))
            continue

        # 批次标题: ### 本科批
        m = re.match(r"^### (.+)$", line)
        if m and current_school:
            current_batch = m.group(1).strip()
            continue

        # 数据行: | 计算机类 | 物理类 | 701 | 7 | - |
        if line.startswith("|") and current_school and current_batch:
            cols = [c.strip() for c in line.split("|")]
            # 过滤表头和分隔行
            if len(cols) < 6:
                continue
            if cols[2] in ("科类", "---", ""):
                continue
            if not cols[2]:  # 科类为空
                continue

            major_name = cols[1]
            category = cols[2]
            min_score_str = cols[3]
            min_rank_str = cols[4]
            avg_score_str = cols[5].rstrip("|").strip() if len(cols) > 5 else "-"

            def to_int(s):
                s = s.strip().rstrip("|")
                if s in ("-", "", "None"):
                    return None
                try:
                    return int(s)
                except ValueError:
                    return None

            records.append({
                "school": current_school,
                "year": current_year,
                "batch": current_batch,
                "category": category,
                "major_name": major_name,
                "min_score": to_int(min_score_str),
                "min_rank": to_int(min_rank_str),
                "avg_score": to_int(avg_score_str),
            })

    return province_name, records


# ============================================================
# 数据库操作
# ============================================================

def get_or_create_province(cur, name):
    """获取或创建省份，返回 id"""
    code = PROVINCE_CODES.get(name, "00")
    gk_type = PROVINCE_TYPES.get(name, "3+1+2")

    cur.execute("SELECT id FROM provinces WHERE name = %s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        "INSERT INTO provinces (code, name, gaokao_type) VALUES (%s, %s, %s) RETURNING id",
        (code, name, gk_type),
    )
    return cur.fetchone()[0]


def get_or_create_school(cur, name):
    """获取或创建院校，返回 id"""
    cur.execute("SELECT id FROM schools WHERE name = %s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("INSERT INTO schools (name) VALUES (%s) RETURNING id", (name,))
    return cur.fetchone()[0]


def import_file(cur, file_path):
    """导入单个 Markdown 文件"""
    province_name, records = parse_score_md(file_path)
    if not records:
        print(f"  No records found in {file_path}")
        return 0

    province_id = get_or_create_province(cur, province_name)
    school_cache = {}

    imported = 0
    for rec in records:
        school_name = rec["school"]
        if school_name not in school_cache:
            school_cache[school_name] = get_or_create_school(cur, school_name)
        school_id = school_cache[school_name]

        cur.execute(
            """INSERT INTO scores (school_id, province_id, year, batch, category,
               major_name, min_score, min_rank, avg_score)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                school_id, province_id, rec["year"], rec["batch"],
                rec["category"], rec["major_name"], rec["min_score"],
                rec["min_rank"], rec["avg_score"],
            ),
        )
        imported += 1

    print(f"  {province_name}: {imported} records from {len(school_cache)} schools")
    return imported


def clear_scores(cur):
    """清空分数数据"""
    cur.execute("TRUNCATE scores, schools, provinces RESTART IDENTITY CASCADE")
    print("Cleared all data")


def show_stats(cur):
    """显示数据库统计"""
    cur.execute("SELECT COUNT(*) FROM provinces")
    n_prov = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM schools")
    n_school = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scores")
    n_scores = cur.fetchone()[0]

    print(f"\n=== 数据库统计 ===")
    print(f"省份: {n_prov}")
    print(f"院校: {n_school}")
    print(f"分数记录: {n_scores}")

    if n_scores > 0:
        cur.execute("""
            SELECT p.name, COUNT(s.id) as cnt,
                   COUNT(DISTINCT s.school_id) as schools,
                   array_agg(DISTINCT s.year ORDER BY s.year) as years
            FROM scores s JOIN provinces p ON s.province_id = p.id
            GROUP BY p.name ORDER BY cnt DESC
        """)
        print(f"\n{'省份':<8} {'记录数':>8} {'院校数':>8} {'年份':<20}")
        print("-" * 50)
        for row in cur.fetchall():
            years_str = ", ".join(str(y) for y in row[3])
            print(f"{row[0]:<8} {row[1]:>8} {row[2]:>8} {years_str:<20}")

        # 示例查询：广东 600-620 分物理类 2024
        print("\n--- 示例查询：广东 2024 物理类 590-610 分 ---")
        cur.execute("""
            SELECT sch.name, s.major_name, s.min_score, s.min_rank, s.batch
            FROM scores s
            JOIN schools sch ON s.school_id = sch.id
            JOIN provinces p ON s.province_id = p.id
            WHERE p.name = '广东'
              AND s.year = 2024
              AND s.category = '物理类'
              AND s.min_score BETWEEN 590 AND 610
            ORDER BY s.min_score DESC
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(f"  {row[0]} | {row[1][:30]:<32} | {row[2]}分 | 位次{row[3]} | {row[4]}")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="导入分数线数据到 PostgreSQL")
    parser.add_argument("--files", nargs="+", help="只导入指定文件")
    parser.add_argument("--stats", action="store_true", help="查看数据库统计")
    parser.add_argument("--reimport", action="store_true", help="清空后重新导入")
    args = parser.parse_args()

    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        if args.stats:
            show_stats(cur)
            return

        if args.reimport:
            clear_scores(cur)
            conn.commit()

        # 获取待导入文件
        if args.files:
            files = [os.path.join(KB_DIR, f) if not os.path.isabs(f) else f for f in args.files]
        else:
            files = []
            for f in sorted(os.listdir(KB_DIR)):
                if f.startswith("kb2-scores-") and f.endswith(".md") and "_part" not in f:
                    files.append(os.path.join(KB_DIR, f))

        if not files:
            print("No kb2-scores-*.md files found")
            return

        print(f"Importing {len(files)} files...\n")
        total = 0
        for fpath in files:
            fname = os.path.basename(fpath)
            print(f"[{fname}]")
            n = import_file(cur, fpath)
            total += n
            conn.commit()

        print(f"\nDone! Imported {total} records")
        show_stats(cur)

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
