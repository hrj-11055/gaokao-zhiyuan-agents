#!/usr/bin/env python3
"""
分数线数据导入 PostgreSQL (从 JSON)

用法:
  # 生成 SQL 文件
  python3 data/import_scores_json_to_pg.py --generate-sql

  # 导入到数据库（需 SSH 到服务器）
  python3 data/import_scores_json_to_pg.py --import

  # 查看统计
  python3 data/import_scores_json_to_pg.py --stats
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 配置
PROJECT_ROOT = Path(__file__).parent.parent  # 项目根目录
JSON_FILE = PROJECT_ROOT / "scores.json"
SQL_OUTPUT = PROJECT_ROOT / "_import_scores_json.sql"

# 数据库配置（服务器上）
DB_HOST = "159.75.110.157"
DB_PORT = 5432
DB_NAME = "gaokao"
DB_USER = "postgres"


def generate_sql():
    """生成 SQL 导入文件"""
    print("读取 JSON 数据...")
    with open(JSON_FILE, encoding='utf-8') as f:
        data = json.load(f)

    print(f"总记录数: {len(data):,}")

    # 生成 SQL 文件
    print("生成 SQL 文件...")
    with open(SQL_OUTPUT, 'w', encoding='utf-8') as sql:
        # 表结构
        sql.write(f"""-- 录取分数线数据表
-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 数据来源: 掌上高考 API (api.zjzw.cn)

DROP TABLE IF EXISTS scores CASCADE;

CREATE TABLE scores (
    id BIGSERIAL PRIMARY KEY,
    year INT NOT NULL,
    province_id VARCHAR(2) NOT NULL,
    province_name VARCHAR(20) NOT NULL,
    school_id VARCHAR(20),
    school_name VARCHAR(100) NOT NULL,
    major_id VARCHAR(20),
    major_name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    batch VARCHAR(50),
    min_score INT,
    min_rank INT,
    avg_score INT,
    is_985 BOOLEAN DEFAULT FALSE,
    is_211 BOOLEAN DEFAULT FALSE,
    is_double_first BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_scores_province_score ON scores(province_id, category, min_score);
CREATE INDEX idx_scores_school_province ON scores(school_id, province_id);
CREATE INDEX idx_scores_year_province ON scores(year, province_id);
CREATE INDEX idx_scores_major_name ON scores USING GIN(to_tsvector('simple', major_name));

-- 分析表
ANALYZE scores;

""")

        # 批量插入
        batch_size = 5000
        total = len(data)

        for i in range(0, total, batch_size):
            batch = data[i:i + batch_size]
            sql.write(f"-- Batch {i // batch_size + 1} (记录 {i + 1}-{min(i + batch_size, total)})\n")
            sql.write("INSERT INTO scores (")
            sql.write("year, province_id, province_name, school_id, school_name, ")
            sql.write("major_name, category, batch, min_score, min_rank, avg_score, ")
            sql.write("is_985, is_211, is_double_first) VALUES\n")

            values = []
            for record in batch:
                values.append(
                    f"({record['year']}, "
                    f"'{record.get('province_id', '')}', "
                    f"'{record['province_name']}', "
                    f"'{record.get('school_id', '')}', "
                    f"{_escape(record['school_name'])}, "
                    f"{_escape(record['major_name'])}, "
                    f"{_escape(record.get('category', '综合'))}, "
                    f"{_escape(record.get('batch', '本科批'))}, "
                    f"{record.get('min_score') or 'NULL'}, "
                    f"{record.get('min_rank') or 'NULL'}, "
                    f"{record.get('avg_score') or 'NULL'}, "
                    f"{str(record.get('is_985', False)).lower()}, "
                    f"{str(record.get('is_211', False)).lower()}, "
                    f"{str(record.get('is_double_first', False)).lower()})"
                )

            sql.write(',\n'.join(values))
            sql.write(';\n\n')

            if (i + batch_size) % 50000 == 0:
                print(f"  已处理: {min(i + batch_size, total):,} / {total:,}")

        # 统计查询
        sql.write("""
-- 统计信息
SELECT '总记录数' as metric, COUNT(*) as count FROM scores
UNION ALL
SELECT '学校数量', COUNT(DISTINCT school_name) FROM scores
UNION ALL
SELECT '年份覆盖', COUNT(DISTINCT year) FROM scores
UNION ALL
SELECT '省份覆盖', COUNT(DISTINCT province_id) FROM scores
UNION ALL
SELECT '2023年', COUNT(*) FROM scores WHERE year = 2023
UNION ALL
SELECT '2024年', COUNT(*) FROM scores WHERE year = 2024
UNION ALL
SELECT '2025年', COUNT(*) FROM scores WHERE year = 2025;

-- 示例查询: 广东物理类600分匹配
SELECT school_name, major_name, min_score
FROM scores
WHERE province_id = '44' AND category = '物理类' AND min_score IS NOT NULL
ORDER BY min_score DESC
LIMIT 10;
""")

    print(f"SQL 文件已生成: {SQL_OUTPUT}")
    print(f"文件大小: {SQL_OUTPUT.stat().st_size / 1024 / 1024:.1f} MB")


def _escape(s):
    """转义 SQL 字符串"""
    if s is None:
        return 'NULL'
    s = str(s).replace("'", "''")
    return f"'{s}'"


def show_stats():
    """显示数据统计"""
    print("读取 JSON 数据...")
    with open(JSON_FILE, encoding='utf-8') as f:
        data = json.load(f)

    print("\n" + "="*60)
    print("数据统计")
    print("="*60)

    print(f"\n总记录数: {len(data):,}")

    # 按年份统计
    years = defaultdict(int)
    for r in data:
        years[r['year']] += 1

    print("\n按年份:")
    for year in sorted(years):
        print(f"  {year}: {years[year]:,} 条")

    # 按省份统计
    provinces = defaultdict(int)
    for r in data:
        provinces[r['province_name']] += 1

    print(f"\n按省份 (共 {len(provinces)} 个):")
    for prov, count in sorted(provinces.items(), key=lambda x: -x[1])[:10]:
        print(f"  {prov}: {count:,} 条")

    # 按科类统计
    categories = defaultdict(int)
    for r in data:
        cat = r.get('category', '综合')
        categories[cat] += 1

    print(f"\n按科类 (共 {len(categories)} 个):")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {count:,} 条")


def do_import():
    """导入到服务器数据库（通过 SSH）"""
    import subprocess

    sql_file = SQL_OUTPUT
    if not sql_file.exists():
        print(f"SQL 文件不存在: {sql_file}")
        print("请先运行: python3 data/import_scores_json_to_pg.py --generate-sql")
        return False

    print("上传 SQL 文件到服务器...")

    # 上传文件
    upload_cmd = [
        "scp", str(sql_file),
        f"ubuntu@{DB_HOST}:/tmp/scores_json.sql"
    ]

    result = subprocess.run(upload_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"上传失败: {result.stderr}")
        return False

    print("文件已上传，执行导入...")

    # 通过 SSH 执行导入
    import_cmd = f"ssh ubuntu@{DB_HOST} 'psql -h localhost -U postgres -d gaokao -f /tmp/scores_json.sql'"

    result = subprocess.run(import_cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("导入成功！")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return True
    else:
        print(f"导入失败: {result.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description='分数线数据导入 PostgreSQL')
    parser.add_argument('--generate-sql', action='store_true', help='生成 SQL 文件')
    parser.add_argument('--do-import', action='store_true', help='导入到服务器数据库')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.generate_sql:
        generate_sql()
    elif args.do_import:
        do_import()
    else:
        # 默认生成 SQL
        generate_sql()
        print("\n提示: 使用以下命令导入到数据库:")
        print(f"  psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} -f {SQL_OUTPUT}")
        print(f"  或: python3 data/import_scores_json_to_pg.py --do-import")

    return 0


if __name__ == '__main__':
    sys.exit(main())
