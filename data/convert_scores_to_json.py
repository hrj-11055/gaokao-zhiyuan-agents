#!/usr/bin/env python3
"""
录取分数线数据转换脚本
将 kb2-scores-*.md 文件转换为 JSON 格式

用法:
  python3 data/convert_scores_to_json.py                    # 转换全部文件
  python3 data/convert_scores_to_json.py --validate        # 只验证数据
  python3 data/convert_scores_to_json.py --stats           # 查看统计信息
  python3 data/convert_scores_to_json.py --output scores.json
"""

import re
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 配置
INPUT_DIR = Path(__file__).parent / "knowledge-base"
OUTPUT_DIR = Path(__file__).parent
PROVINCE_MAP = {
    "河北": "13", "江苏": "32", "广东": "44", "湖北": "42", "湖南": "43",
    "福建": "35", "辽宁": "21", "重庆": "50", "安徽": "34", "江西": "36",
    "甘肃": "62", "广西": "45", "贵州": "52", "黑龙江": "23", "吉林": "22",
    "山西": "14", "河南": "41", "陕西": "61", "内蒙古": "15", "四川": "51",
    "云南": "53", "宁夏": "64", "青海": "63", "上海": "31", "浙江": "33",
    "天津": "12", "山东": "37", "北京": "11", "海南": "46", "西藏": "54",
    "新疆": "65",
}

SCHOOL_LEVELS = {
    "清华": "985", "北大": "985", "浙江大学": "985", "复旦大学": "985",
    "上海交大": "985", "中科大": "985", "南京大学": "985", "西安交大": "985",
    "哈尔滨工业大学": "985", "中山大学": "985", "武汉大学": "985",
    "华中科技": "985", "四川大学": "985", "中国人民大学": "985",
    "南开": "985", "山东大学": "985", "厦门大学": "985", "同济": "985",
    "东南大学": "985", "天津大学": "985", "华南理工": "985",
    # 211
    "暨南大学": "211", "华南师范大学": "211", "武汉理工": "211",
}


class ScoreDataParser:
    """分数线数据解析器"""

    def __init__(self):
        self.records = []
        self.errors = []
        self.warnings = []
        self._stats = defaultdict(int)

    def parse_file(self, filepath):
        """解析单个 Markdown 文件"""
        filename = filepath.name
        # 从文件名提取省份: kb2-scores-广东.md -> 广东
        match = re.search(r'kb2-scores-(.+?)\.md', filename)
        if not match:
            self.errors.append(f"无法从文件名提取省份: {filename}")
            return []

        province_name = match.group(1)
        province_id = PROVINCE_MAP.get(province_name, "")

        content = filepath.read_text(encoding='utf-8')
        lines = content.split('\n')

        records = []
        current_school = None
        current_year = None
        current_batch = None
        in_table = False

        for line in lines:
            line = line.strip()

            # 匹配学校标题: ## 清华大学 - 2023年
            school_match = re.match(r'##\s+(.+?)\s*-\s*(\d{4})年', line)
            if school_match:
                current_school = school_match.group(1).strip()
                current_year = int(school_match.group(2))
                current_batch = None
                in_table = False
                continue

            # 匹配批次: ### 本科批
            batch_match = re.match(r'###\s+(.+)', line)
            if batch_match:
                current_batch = batch_match.group(1).strip()
                in_table = False
                continue

            # 检测表格开始
            if line.startswith('| 专业名称 |'):
                in_table = True
                continue

            # 跳过表格分隔行
            if in_table and line.startswith('|--'):
                continue

            # 解析表格行
            if in_table and line.startswith('|') and current_school and current_year:
                record = self._parse_table_row(
                    line, province_name, province_id,
                    current_school, current_year, current_batch
                )
                if record:
                    records.append(record)

        self._stats['parsed_files'] += 1
        self._stats['parsed_records'] += len(records)
        return records

    def _parse_table_row(self, line, province_name, province_id, school_name, year, batch):
        """解析表格行"""
        # 移除首尾的 | 并分割
        parts = [p.strip() for p in line.strip('|').split('|')]
        if len(parts) < 5:
            return None

        major_name = parts[0]
        category = parts[1]  # 科类: 物理类/历史类
        min_score_str = parts[2]
        min_rank_str = parts[3]
        avg_score_str = parts[4]

        # 清理专业名称（去掉括号内的补充信息）
        major_clean = re.sub(r'（.*', '', major_name).strip()
        major_clean = re.sub(r'\(.*', '', major_clean).strip()

        # 解析分数
        min_score = self._parse_number(min_score_str)
        min_rank = self._parse_number(min_rank_str)
        avg_score = self._parse_number(avg_score_str)

        # 确定科类
        if not category or category == '-':
            # 从专业名称推断
            if any(x in major_name for x in ['计算机', '电子信息', '自动化', '机械', '电气']):
                category = '物理类'
            else:
                category = '综合'

        # 确定学校层次
        school_level = self._get_school_level(school_name)

        return {
            'year': year,
            'province_id': province_id,
            'province_name': province_name,
            'school_id': self._generate_school_id(school_name),
            'school_name': school_name,
            'major_name': major_clean,
            'major_name_full': major_name,  # 保留完整信息
            'category': category,
            'batch': batch or '本科批',
            'min_score': min_score,
            'min_rank': min_rank,
            'avg_score': avg_score,
            'is_985': school_level == '985',
            'is_211': school_level in ['985', '211'],
            'is_double_first': school_level in ['985', '211'],  # 简化处理
        }

    def _parse_number(self, s):
        """解析数字，返回 None 如果不是有效数字"""
        if not s or s == '-' or s == '':
            return None
        try:
            return int(s)
        except ValueError:
            return None

    def _generate_school_id(self, school_name):
        """生成学校ID（简化版，实际应该从源数据获取）"""
        # 使用哈希生成简单的ID
        return str(abs(hash(school_name)))[:10]

    def _get_school_level(self, school_name):
        """确定学校层次"""
        for name, level in SCHOOL_LEVELS.items():
            if name in school_name:
                return level
        return '普通本科'

    def convert_all(self, input_dir=None, output_file=None):
        """转换所有文件"""
        if input_dir is None:
            input_dir = INPUT_DIR

        input_path = Path(input_dir)
        all_records = []

        # 查找所有 kb2-scores-*.md 文件
        md_files = sorted(input_path.glob('kb2-scores-*.md'))

        if not md_files:
            self.errors.append(f"在 {input_path} 中未找到 kb2-scores-*.md 文件")
            return []

        print(f"找到 {len(md_files)} 个文件")

        for filepath in md_files:
            print(f"处理: {filepath.name}...", end=' ')
            records = self.parse_file(filepath)
            print(f"OK ({len(records)} 条记录)")
            all_records.extend(records)

        # 去重：保留相同 key 的第一条记录
        all_records = self._deduplicate(all_records)

        # 过滤异常分数
        all_records = self._filter_abnormal(all_records)

        self.records = all_records

        # 输出 JSON
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(
                json.dumps(all_records, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"\n已输出到: {output_path}")

        return all_records

    def _deduplicate(self, records):
        """去重：保留相同 key 的第一条记录"""
        seen = set()
        deduped = []

        for record in records:
            key = (record['school_name'], record['major_name'],
                   record['province_name'], record['year'],
                   record['category'], record['batch'])
            if key not in seen:
                seen.add(key)
                deduped.append(record)
            else:
                self._stats['duplicates_removed'] += 1

        removed = len(records) - len(deduped)
        if removed > 0:
            print(f"  去重: 移除 {removed} 条重复记录")

        return deduped

    def _filter_abnormal(self, records):
        """过滤明显异常的记录"""
        filtered = []
        removed = 0

        for record in records:
            score = record.get('min_score')
            # 过滤明显错误分数 (< 50 或 > 800)
            # 体育/艺术类可能 < 120 或 > 750（综合分）
            if score is not None and (score < 50 or score > 800):
                removed += 1
                continue
            filtered.append(record)

        if removed > 0:
            print(f"  过滤: 移除 {removed} 条异常分数记录")

        return filtered

    def validate(self):
        """验证数据质量"""
        if not self.records:
            return False

        issues = []

        # 1. 检查必填字段
        required_fields = ['year', 'province_name', 'school_name', 'major_name']
        for i, record in enumerate(self.records):
            for field in required_fields:
                if not record.get(field):
                    issues.append(f"记录 {i}: 缺少必填字段 {field}")

        # 2. 检查数据范围 (支持专科 200-750)
        for i, record in enumerate(self.records):
            score = record.get('min_score')
            if score is not None:
                if not (200 <= score <= 750):
                    issues.append(f"记录 {i}: 分数异常 {score} ({record['school_name']} {record['major_name']})")

        # 3. 检查年份覆盖
        years = set(r.get('year') for r in self.records if r.get('year'))
        if years != {2023, 2024, 2025}:
            issues.append(f"年份覆盖不完整: {years}")

        # 4. 检查省份覆盖
        provinces = set(r.get('province_name') for r in self.records if r.get('province_name'))
        if len(provinces) < 30:
            issues.append(f"省份数量不足: {len(provinces)}/31")

        self.errors.extend(issues)

        # 输出报告
        print("\n" + "="*60)
        print("验证报告")
        print("="*60)
        print(f"总记录数: {len(self.records)}")
        print(f"年份覆盖: {sorted(years)}")
        print(f"省份覆盖: {len(provinces)} 个")
        print(f"学校数量: {len(set(r['school_name'] for r in self.records))}")
        print(f"问题数: {len(issues)}")

        if issues:
            print(f"\n发现问题:")
            for issue in issues[:20]:  # 只显示前20个
                print(f"  - {issue}")
            if len(issues) > 20:
                print(f"  ... 还有 {len(issues)-20} 个问题")

        return len(issues) == 0

    def stats(self):
        """输出统计信息"""
        if not self.records:
            print("没有数据可统计")
            return

        print("\n" + "="*60)
        print("数据统计")
        print("="*60)

        years = defaultdict(int)
        provinces = defaultdict(int)
        categories = defaultdict(int)

        for r in self.records:
            years[r['year']] += 1
            provinces[r['province_name']] += 1
            categories[r['category']] += 1

        print(f"\n总记录数: {len(self.records)}")
        print(f"\n按年份:")
        for year in sorted(years):
            print(f"  {year}: {years[year]:,} 条")

        print(f"\n按省份 (前10):")
        for prov, count in sorted(provinces.items(), key=lambda x: -x[1])[:10]:
            print(f"  {prov}: {count:,} 条")

        print(f"\n按科类:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count:,} 条")

        print(f"\n学校数量: {len(set(r['school_name'] for r in self.records)):,}")
        print(f"专业数量: {len(set(r['major_name'] for r in self.records)):,}")


def main():
    parser = argparse.ArgumentParser(description='转换分数线数据')
    parser.add_argument('--input', default=None, help='输入目录')
    parser.add_argument('--output', default='scores.json', help='输出JSON文件')
    parser.add_argument('--validate', action='store_true', help='只验证数据')
    parser.add_argument('--stats', action='store_true', help='只显示统计')

    args = parser.parse_args()

    converter = ScoreDataParser()

    if args.stats or args.validate:
        # 先转换以便验证
        converter.convert_all()
        if args.stats:
            converter.stats()
        if args.validate:
            success = converter.validate()
            return 0 if success else 1
    else:
        converter.convert_all(output_file=args.output)
        converter.validate()
        converter.stats()

    return 0


if __name__ == '__main__':
    sys.exit(main())
