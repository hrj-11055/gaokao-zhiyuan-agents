#!/usr/bin/env python3
"""
数据导入脚本：将 JSON 报告文件导入 PostgreSQL 数据库
使用方法：python3 scripts/import_reports_to_pg.py
环境变量：
    - PG_HOST：数据库主机（默认：159.75.110.157）
    - PG_PORT：数据库端口（默认：5432）
    - PG_DATABASE：数据库名（默认：gaokao_db）
    - PG_USER：数据库用户（默认：postgres）
    - PG_PASSWORD：数据库密码（必须设置）
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import time


class ReportImporter:
    """报告数据导入器"""

    def __init__(self):
        self.pg_host = os.getenv('PG_HOST', '159.75.110.157')
        self.pg_port = os.getenv('PG_PORT', '5432')
        self.pg_database = os.getenv('PG_DATABASE', 'gaokao_db')
        self.pg_user = os.getenv('PG_USER', 'postgres')
        self.pg_password = os.getenv('PG_PASSWORD', '')

        if not self.pg_password:
            raise ValueError("PG_PASSWORD 环境变量未设置")

        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password
            )
            self.cursor = self.conn.cursor()
            print(f"✓ 已连接到数据库: {self.pg_host}:{self.pg_port}/{self.pg_database}")
        except Exception as e:
            raise Exception(f"数据库连接失败: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ 数据库连接已关闭")

    def calculate_word_count(self, data: Dict) -> int:
        """计算报告字数"""
        count = 0
        if 'layer3_detail' in data:
            for module_key, module_data in data['layer3_detail'].items():
                if isinstance(module_data, dict) and 'raw_content' in module_data:
                    count += len(module_data['raw_content'])
        if 'layer4_supplement' in data:
            if 'full_raw_content' in data['layer4_supplement']:
                count += len(data['layer4_supplement']['full_raw_content'])
        return count

    def import_major(self, code: str, data: Dict) -> bool:
        """导入单个专业报告"""
        try:
            word_count = self.calculate_word_count(data)
            layer1 = data.get('layer1_overview', {})

            self.cursor.execute("""
                INSERT INTO majors (code, name, category, data, version, source_file, word_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    data = EXCLUDED.data,
                    version = EXCLUDED.version,
                    word_count = EXCLUDED.word_count,
                    updated_at = NOW()
            """, (
                code,
                layer1.get('name', ''),
                layer1.get('category', ''),
                json.dumps(data, ensure_ascii=False),
                data.get('meta', {}).get('version', '2.0.0'),
                data.get('meta', {}).get('source_file', ''),
                word_count
            ))
            return True
        except Exception as e:
            print(f"✗ 导入专业 {code} 失败: {e}")
            return False

    def extract_province(self, data: Dict, name: str) -> str:
        """从多个来源提取省份信息"""
        import re

        # 来源1：layer1_overview.location（优先但常不完整）
        layer1 = data.get('layer1_overview', {})
        location = layer1.get('location', '')

        # 来源2：从 layer3_detail 模块一中提取（更可靠）
        l3 = data.get('layer3_detail', {})
        module1 = l3.get('module1_academic_capital', {})
        raw = module1.get('raw_content', '') if isinstance(module1, dict) else ''

        # 来源3：layer4_supplement 的 full_raw_content（兜底）
        if not raw:
            l4 = data.get('layer4_supplement', {})
            raw = l4.get('full_raw_content', '') if isinstance(l4, dict) else ''

        # 合并所有文本源
        combined = f"{location} {raw}"

        # 省份匹配（按长度降序，优先匹配"自治区"等长名称）
        province_patterns = [
            (r'((?:新疆|西藏|广西|内蒙古|宁夏))(?:维吾尔|壮族|回族)?(?:自治区)', '{g}自治区'),
            (r'((?:黑龙江|吉林|辽宁))省?', '{g}省'),
            (r'((?:河北|河南|山东|山西|湖南|湖北|广东|广西|海南|四川|贵州|云南|陕西|甘肃|青海|台湾))省?', '{g}省'),
            (r'((?:浙江|江苏|安徽|福建|江西|黑龙江))省?', '{g}省'),
            (r'北京(?:市)?', '北京市'),
            (r'上海(?:市)?', '上海市'),
            (r'天津(?:市)?', '天津市'),
            (r'重庆(?:市)?', '重庆市'),
            (r'香港(?:特别行政区)?', '香港'),
            (r'澳门(?:特别行政区)?', '澳门'),
        ]

        for pattern, fmt in province_patterns:
            match = re.search(pattern, combined)
            if match:
                if '{g}' in fmt:
                    return fmt.format(g=match.group(1))
                return fmt

        return ''

    def import_university(self, name: str, data: Dict) -> bool:
        """导入单个院校报告"""
        try:
            word_count = self.calculate_word_count(data)
            layer1 = data.get('layer1_overview', {})

            # 清理 name（移除可能的 _深度研究报告 后缀）
            clean_name = name.replace('_深度研究报告', '').strip()
            province = self.extract_province(data, clean_name)

            self.cursor.execute("""
                INSERT INTO universities (name, province, univ_type, data, version, source_file, word_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    province = EXCLUDED.province,
                    univ_type = EXCLUDED.univ_type,
                    data = EXCLUDED.data,
                    version = EXCLUDED.version,
                    word_count = EXCLUDED.word_count,
                    updated_at = NOW()
            """, (
                clean_name,
                province,
                layer1.get('type', ''),
                json.dumps(data, ensure_ascii=False),
                data.get('meta', {}).get('version', '2.0.0'),
                data.get('meta', {}).get('source_file', ''),
                word_count
            ))
            return True
        except Exception as e:
            print(f"✗ 导入院校 {name} 失败: {e}")
            return False

    def import_majors_from_dir(self, dir_path: str) -> Dict[str, int]:
        """从目录批量导入专业报告"""
        json_dir = Path(dir_path)
        results = {'success': 0, 'error': 0, 'skipped': 0}

        for json_file in sorted(json_dir.glob('*.json')):
            if json_file.name.startswith('_'):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                code = data.get('layer1_overview', {}).get('code')
                if not code:
                    code = json_file.stem

                if self.import_major(code, data):
                    results['success'] += 1
                    if results['success'] % 100 == 0:
                        self.conn.commit()  # 每100条提交一次
                        print(f"  已导入 {results['success']} 条...")
                else:
                    results['error'] += 1

            except Exception as e:
                print(f"✗ 处理文件 {json_file.name} 失败: {e}")
                results['error'] += 1

        self.conn.commit()
        return results

    def import_universities_from_dir(self, dir_path: str) -> Dict[str, int]:
        """从目录批量导入院校报告"""
        json_dir = Path(dir_path)
        results = {'success': 0, 'error': 0, 'skipped': 0}

        for json_file in sorted(json_dir.glob('*.json')):
            if json_file.name.startswith('_'):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                name = data.get('layer1_overview', {}).get('name', json_file.stem)

                if self.import_university(name, data):
                    results['success'] += 1
                    if results['success'] % 100 == 0:
                        self.conn.commit()  # 每100条提交一次
                        print(f"  已导入 {results['success']} 条...")
                else:
                    results['error'] += 1

            except Exception as e:
                print(f"✗ 处理文件 {json_file.name} 失败: {e}")
                results['error'] += 1

        self.conn.commit()
        return results

    def check_data_quality(self) -> Dict:
        """检查数据质量"""
        self.cursor.execute("SELECT * FROM check_data_quality()")
        rows = self.cursor.fetchall()

        quality_report = {}
        for row in rows:
            table_name, total, null_l1, null_l2, null_l3, empty = row
            quality_report[table_name] = {
                'total': total,
                'null_layer1': null_l1,
                'null_layer2': null_l2,
                'null_layer3': null_l3,
                'empty_content': empty
            }

        return quality_report

    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {}

        # 专业统计
        self.cursor.execute("SELECT * FROM stats_overview WHERE table_name = 'majors'")
        row = self.cursor.fetchone()
        if row:
            stats['majors'] = {
                'total': row[1],
                'green': row[2],
                'yellow': row[3],
                'red': row[4],
                'avg_score': float(row[5]) if row[5] else 0
            }

        # 院校统计
        self.cursor.execute("SELECT * FROM stats_overview WHERE table_name = 'universities'")
        row = self.cursor.fetchone()
        if row:
            stats['universities'] = {
                'total': row[1],
                'green': row[2],
                'yellow': row[3],
                'red': row[4],
                'avg_score': float(row[5]) if row[5] else 0
            }

        return stats


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='导入报告数据到 PostgreSQL')
    parser.add_argument('--majors', default='data/专业评估报告_json_v2', help='专业报告 JSON 目录')
    parser.add_argument('--universities', default='data/大学评估报告_json_v2', help='院校报告 JSON 目录')
    parser.add_argument('--skip-majors', action='store_true', help='跳过专业报告导入')
    parser.add_argument('--skip-universities', action='store_true', help='跳过院校报告导入')
    parser.add_argument('--check-only', action='store_true', help='只检查数据质量，不导入')

    args = parser.parse_args()

    importer = None
    try:
        importer = ReportImporter()
        importer.connect()

        if args.check_only:
            print("\n=== 数据质量检查 ===")
            quality = importer.check_data_quality()
            for table, data in quality.items():
                print(f"\n{table}:")
                print(f"  总记录数: {data['total']}")
                print(f"  缺失 layer1: {data['null_layer1']}")
                print(f"  缺失 layer2: {data['null_layer2']}")
                print(f"  缺失 layer3: {data['null_layer3']}")
                print(f"  空内容: {data['empty_content']}")

            stats = importer.get_stats()
            print("\n=== 统计信息 ===")
            for table, data in stats.items():
                print(f"\n{table}:")
                print(f"  总数: {data['total']}")
                print(f"  绿灯: {data['green']}, 黄灯: {data['yellow']}, 红灯: {data['red']}")
                print(f"  平均分: {data['avg_score']:.2f}")
            return

        # 导入专业报告
        if not args.skip_majors:
            print(f"\n=== 导入专业报告 ===")
            print(f"源目录: {args.majors}")
            start_time = time.time()
            major_results = importer.import_majors_from_dir(args.majors)
            elapsed = time.time() - start_time
            print(f"✓ 专业报告导入完成: {major_results['success']} 成功, {major_results['error']} 失败")
            print(f"  耗时: {elapsed:.1f} 秒")

        # 导入院校报告
        if not args.skip_universities:
            print(f"\n=== 导入院校报告 ===")
            print(f"源目录: {args.universities}")
            start_time = time.time()
            univ_results = importer.import_universities_from_dir(args.universities)
            elapsed = time.time() - start_time
            print(f"✓ 院校报告导入完成: {univ_results['success']} 成功, {univ_results['error']} 失败")
            print(f"  耗时: {elapsed:.1f} 秒")

        # 显示统计信息
        stats = importer.get_stats()
        print("\n=== 导入完成统计 ===")
        for table, data in stats.items():
            print(f"\n{table}:")
            print(f"  总数: {data['total']}")
            print(f"  绿灯: {data['green']}, 黄灯: {data['yellow']}, 红灯: {data['red']}")
            print(f"  平均分: {data['avg_score']:.2f}")

    except Exception as e:
        print(f"\n✗ 导入失败: {e}")
        return 1
    finally:
        if importer:
            importer.close()

    return 0


if __name__ == '__main__':
    exit(main())
