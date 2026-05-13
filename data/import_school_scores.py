#!/usr/bin/env python3
"""
将院校级录取分数线 CSV 导入 PostgreSQL

用法：
  python3 data/import_school_scores.py                  # 导入 school_scores_raw.csv
  python3 data/import_school_scores.py --stats           # 查看数据库统计
  python3 data/import_school_scores.py --reimport        # 清空后重新导入
  python3 data/import_school_scores.py --generate-sql    # 生成 SQL 文件（用于远程服务器）

环境变量：
  PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB
"""

import argparse
import csv
import os
import sys

try:
    import psycopg2
except ImportError:
    print("需要 psycopg2: pip3 install psycopg2-binary")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(SCRIPT_DIR, "school_scores_raw.csv")
SQL_FILE = os.path.join(SCRIPT_DIR, "_import_school_scores.sql")

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "postgres"),
    "dbname": os.environ.get("PG_DB", "gaokao"),
}


def create_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS school_scores (
            id SERIAL PRIMARY KEY,
            school_name VARCHAR(100) NOT NULL,
            school_id VARCHAR(20),
            province VARCHAR(30) NOT NULL,
            year INTEGER NOT NULL,
            type_name VARCHAR(20),
            batch_name VARCHAR(50),
            enrollment_type VARCHAR(30),
            min_score INTEGER,
            min_rank INTEGER,
            avg_score INTEGER,
            max_score INTEGER,
            is_985 BOOLEAN DEFAULT FALSE,
            is_211 BOOLEAN DEFAULT FALSE,
            nature VARCHAR(10),
            special_group VARCHAR(20),
            UNIQUE(school_name, province, year, type_name, batch_name, enrollment_type, special_group)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ss_school ON school_scores(school_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ss_province ON school_scores(province)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ss_year ON school_scores(year)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ss_type ON school_scores(type_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ss_min_score ON school_scores(min_score)")


def load_csv():
    if not os.path.exists(CSV_FILE):
        print(f"CSV not found: {CSV_FILE}")
        return []

    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from CSV")
    return rows


def import_data(cur, rows):
    sql = """
        INSERT INTO school_scores (school_name, school_id, province, year,
            type_name, batch_name, enrollment_type, min_score, min_rank,
            avg_score, max_score, is_985, is_211, nature, special_group)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (school_name, province, year, type_name, batch_name,
                     enrollment_type, special_group)
        DO UPDATE SET
            min_score = EXCLUDED.min_score,
            min_rank = EXCLUDED.min_rank,
            avg_score = EXCLUDED.avg_score,
            max_score = EXCLUDED.max_score
    """
    inserted = 0
    for row in rows:
        cur.execute(sql, (
            row["school_name"],
            row["school_id"],
            row["province"],
            int(row["year"]) if row["year"] else None,
            row["type_name"],
            row["batch_name"],
            row["enrollment_type"],
            int(row["min_score"]) if row["min_score"] and row["min_score"] != "None" else None,
            int(row["min_rank"]) if row["min_rank"] and row["min_rank"] != "None" else None,
            int(row["avg_score"]) if row["avg_score"] and row["avg_score"] != "None" else None,
            int(row["max_score"]) if row["max_score"] and row["max_score"] != "None" else None,
            row["f985"] == "True" if row.get("f985") else False,
            row["f211"] == "True" if row.get("f211") else False,
            row["nature"],
            row["special_group"],
        ))
        inserted += 1
    print(f"Imported {inserted} rows")


def generate_sql(rows):
    lines = [
        "CREATE TABLE IF NOT EXISTS school_scores (",
        "    id SERIAL PRIMARY KEY,",
        "    school_name VARCHAR(100) NOT NULL,",
        "    school_id VARCHAR(20),",
        "    province VARCHAR(30) NOT NULL,",
        "    year INTEGER NOT NULL,",
        "    type_name VARCHAR(20),",
        "    batch_name VARCHAR(50),",
        "    enrollment_type VARCHAR(30),",
        "    min_score INTEGER,",
        "    min_rank INTEGER,",
        "    avg_score INTEGER,",
        "    max_score INTEGER,",
        "    is_985 BOOLEAN DEFAULT FALSE,",
        "    is_211 BOOLEAN DEFAULT FALSE,",
        "    nature VARCHAR(10),",
        "    special_group VARCHAR(20),",
        "    UNIQUE(school_name, province, year, type_name, batch_name, enrollment_type, special_group)",
        ");",
        "",
        "CREATE INDEX IF NOT EXISTS idx_ss_school ON school_scores(school_name);",
        "CREATE INDEX IF NOT EXISTS idx_ss_province ON school_scores(province);",
        "CREATE INDEX IF NOT EXISTS idx_ss_year ON school_scores(year);",
        "CREATE INDEX IF NOT EXISTS idx_ss_type ON school_scores(type_name);",
        "CREATE INDEX IF NOT EXISTS idx_ss_min_score ON school_scores(min_score);",
        "",
        "TRUNCATE school_scores;",
        "",
    ]

    for row in rows:
        def esc(val):
            return str(val).replace("'", "''") if val and val != "None" else ""

        min_s = row["min_score"] if row["min_score"] and row["min_score"] != "None" else "NULL"
        min_r = row["min_rank"] if row["min_rank"] and row["min_rank"] != "None" else "NULL"
        avg_s = row["avg_score"] if row["avg_score"] and row["avg_score"] != "None" else "NULL"
        max_s = row["max_score"] if row["max_score"] and row["max_score"] != "None" else "NULL"
        is985 = "TRUE" if row.get("f985") == "True" else "FALSE"
        is211 = "TRUE" if row.get("f211") == "True" else "FALSE"

        lines.append(
            f"INSERT INTO school_scores (school_name, school_id, province, year, "
            f"type_name, batch_name, enrollment_type, min_score, min_rank, "
            f"avg_score, max_score, is_985, is_211, nature, special_group) VALUES ("
            f"'{esc(row['school_name'])}', '{esc(row['school_id'])}', "
            f"'{esc(row['province'])}', {row['year'] or 'NULL'}, "
            f"'{esc(row['type_name'])}', '{esc(row['batch_name'])}', "
            f"'{esc(row['enrollment_type'])}', {min_s}, {min_r}, "
            f"{avg_s}, {max_s}, {is985}, {is211}, "
            f"'{esc(row['nature'])}', '{esc(row['special_group'])}');"
        )

    with open(SQL_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated SQL: {SQL_FILE} ({len(lines)} lines)")


def show_stats(cur):
    cur.execute("SELECT COUNT(*) as cnt FROM school_scores")
    total = cur.fetchone()[0]
    print(f"Total records: {total}")

    cur.execute("SELECT COUNT(DISTINCT school_name) as cnt FROM school_scores")
    schools = cur.fetchone()[0]
    print(f"Schools: {schools}")

    cur.execute("SELECT COUNT(DISTINCT province) as cnt FROM school_scores")
    provinces = cur.fetchone()[0]
    print(f"Provinces: {provinces}")

    cur.execute("""
        SELECT year, COUNT(*) as cnt
        FROM school_scores
        GROUP BY year ORDER BY year
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} records")

    cur.execute("""
        SELECT type_name, COUNT(*) as cnt
        FROM school_scores
        GROUP BY type_name ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--reimport", action="store_true")
    parser.add_argument("--generate-sql", action="store_true")
    args = parser.parse_args()

    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    if args.stats:
        show_stats(cur)
        cur.close()
        conn.close()
        sys.exit(0)

    if args.generate_sql:
        rows = load_csv()
        if rows:
            generate_sql(rows)
        cur.close()
        conn.close()
        sys.exit(0)

    create_table(cur)

    if args.reimport:
        cur.execute("TRUNCATE school_scores")
        print("Truncated school_scores")

    rows = load_csv()
    if rows:
        import_data(cur, rows)

    show_stats(cur)
    cur.close()
    conn.close()
