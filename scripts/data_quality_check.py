#!/usr/bin/env python3
"""
数据质量检查脚本
检测 JSON 报告中的数据漂移问题

用法：
    python3 scripts/data_quality_check.py --all
    python3 scripts/data_quality_check.py --check-empty-modules
    python3 scripts/data_quality_check.py --check-zero-scores
    python3 scripts/data_quality_check.py --check-univ-types
    python3 scripts/data_quality_check.py --check-file-mismatch
"""

import json
import glob
import os
import sys
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
MAJOR_JSON_DIR = BASE_DIR / 'data' / '专业评估报告_json_v2'
UNIV_JSON_DIR = BASE_DIR / 'data' / '大学评估报告_json_v2'
MAJOR_MD_DIR = BASE_DIR / 'data' / '专业评估报告'
UNIV_MD_DIR = BASE_DIR / 'data' / '大学评估报告'

SCHOOL_985 = {
    '清华大学', '北京大学', '中国人民大学', '北京师范大学', '北京航空航天大学',
    '北京理工大学', '中国农业大学', '中央民族大学', '南开大学', '天津大学',
    '大连理工大学', '东北大学', '吉林大学', '哈尔滨工业大学', '复旦大学',
    '同济大学', '上海交通大学', '华东师范大学', '南京大学', '东南大学',
    '浙江大学', '中国科学技术大学', '厦门大学', '山东大学', '中国海洋大学',
    '武汉大学', '华中科技大学', '湖南大学', '中南大学', '中山大学',
    '华南理工大学', '四川大学', '重庆大学', '电子科技大学', '西安交通大学',
    '西北工业大学', '西北农林科技大学', '兰州大学', '国防科技大学',
}
SCHOOL_211 = {
    '北京交通大学', '北京工业大学', '北京科技大学', '北京化工大学', '北京邮电大学',
    '北京林业大学', '北京中医药大学', '北京外国语大学', '中国传媒大学', '对外经济贸易大学',
    '中央财经大学', '中国政法大学', '华北电力大学', '天津医科大学', '河北工业大学',
    '太原理工大学', '内蒙古大学', '辽宁大学', '大连海事大学', '延边大学', '东北师范大学',
    '哈尔滨工程大学', '东北农业大学', '东北林业大学', '华东理工大学', '东华大学',
    '上海外国语大学', '上海财经大学', '上海大学', '苏州大学', '南京航空航天大学',
    '南京理工大学', '中国矿业大学', '河海大学', '江南大学', '南京农业大学', '中国药科大学',
    '南京师范大学', '安徽大学', '合肥工业大学', '福州大学', '南昌大学', '中国石油大学',
    '郑州大学', '武汉理工大学', '华中农业大学', '华中师范大学', '中南财经政法大学',
    '湖南师范大学', '华南师范大学', '广西大学', '海南大学', '四川农业大学', '西南交通大学',
    '西南大学', '西南财经大学', '云南大学', '西藏大学', '西北大学', '西安交通大学',
    '西安电子科技大学', '长安大学', '青海大学', '宁夏大学', '新疆大学', '石河子大学',
}
SCHOOL_COOPERATIVE = {
    '上海纽约大学', '昆山杜克大学', '宁波诺丁汉大学', '西交利物浦大学', '温州肯恩大学',
    '深圳北理莫斯科大学', '香港中文大学(深圳)', '北京师范大学-香港浸会大学联合国际学院',
    '广东以色列理工学院',
}


def load_json_files(directory):
    """加载目录中所有 JSON 文件"""
    files = {}
    for f in sorted(directory.glob('*.json')):
        if f.name.startswith('_'):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                files[f.name] = json.load(fh)
        except Exception as e:
            files[f.name] = {'_error': str(e)}
    return files


def check_empty_modules():
    """检查空模块"""
    print("=== 空模块检查 ===\n")

    # 专业
    major_files = load_json_files(MAJOR_JSON_DIR)
    major_empty = defaultdict(int)
    major_empty_files = defaultdict(list)
    major_total = 0

    for fname, data in major_files.items():
        if '_error' in data:
            continue
        major_total += 1
        l3 = data.get('layer3_detail', {})
        for key, val in l3.items():
            rc = val.get('raw_content', '') if isinstance(val, dict) else ''
            if len(rc) == 0:
                major_empty[key] += 1
                if len(major_empty_files[key]) < 3:
                    major_empty_files[key].append(fname)

    print(f"专业报告: {major_total} 个文件")
    if major_empty:
        for key, count in sorted(major_empty.items(), key=lambda x: -x[1]):
            pct = count / major_total * 100
            print(f"  {key}: {count}/{major_total} ({pct:.1f}%) 为空")
            if count <= 10:
                for f in major_empty_files[key]:
                    print(f"    - {f}")
    else:
        print("  无空模块")

    # 院校
    univ_files = load_json_files(UNIV_JSON_DIR)
    univ_empty_count = 0
    univ_partial_empty = 0
    univ_empty_names = []
    univ_total = 0

    for fname, data in univ_files.items():
        if '_error' in data:
            continue
        univ_total += 1
        l3 = data.get('layer3_detail', {})
        empty_count = 0
        for key, val in l3.items():
            rc = val.get('raw_content', '') if isinstance(val, dict) else ''
            if len(rc) == 0:
                empty_count += 1
        if empty_count == len(l3) and len(l3) > 0:
            univ_empty_count += 1
            name = data.get('layer1_overview', {}).get('name', fname)
            univ_empty_names.append(name)
        elif empty_count > 0:
            univ_partial_empty += 1

    print(f"\n院校报告: {univ_total} 个文件")
    print(f"  完全空（所有模块为空）: {univ_empty_count} ({univ_empty_count/univ_total*100:.1f}%)")
    print(f"  部分空: {univ_partial_empty}")
    if univ_empty_count > 0 and univ_empty_count <= 30:
        print(f"  空模块院校列表:")
        for name in sorted(univ_empty_names):
            print(f"    - {name}")

    return {
        'major': {'total': major_total, 'empty_modules': dict(major_empty)},
        'univ': {'total': univ_total, 'full_empty': univ_empty_count, 'partial_empty': univ_partial_empty},
    }


def check_zero_scores():
    """检查零分报告"""
    print("\n=== 零分报告检查 ===\n")

    # 专业
    major_files = load_json_files(MAJOR_JSON_DIR)
    major_zero = []
    for fname, data in major_files.items():
        if '_error' in data:
            continue
        score = data.get('layer1_overview', {}).get('weighted_score', 0)
        if score == 0:
            major_zero.append((fname, data.get('layer1_overview', {}).get('name', '?')))

    print(f"专业零分: {len(major_zero)}/{len(major_files)}")
    for fname, name in major_zero:
        print(f"  {fname}: {name}")

    # 院校
    univ_files = load_json_files(UNIV_JSON_DIR)
    univ_zero = []
    for fname, data in univ_files.items():
        if '_error' in data:
            continue
        score = data.get('layer1_overview', {}).get('weighted_score', 0)
        if score == 0:
            name = data.get('layer1_overview', {}).get('name', '?')
            utype = data.get('layer1_overview', {}).get('type', '?')
            univ_zero.append((fname, name, utype))

    print(f"\n院校零分: {len(univ_zero)}/{len(univ_files)}")
    # 按类型分组
    by_type = defaultdict(list)
    for fname, name, utype in univ_zero:
        by_type[utype].append(name)
    for utype, names in sorted(by_type.items()):
        print(f"  {utype}: {len(names)} 所")
        if len(names) <= 10:
            for n in names:
                print(f"    - {n}")

    return {'major_zero': len(major_zero), 'univ_zero': len(univ_zero)}


def check_univ_types():
    """检查院校类型分类准确性"""
    print("\n=== 院校类型验证 ===\n")

    univ_files = load_json_files(UNIV_JSON_DIR)
    issues = []

    # 已知类型的院校验证
    known_types = {}
    for s in SCHOOL_985:
        known_types[s] = '985'
    for s in SCHOOL_211:
        if s not in known_types:
            known_types[s] = '211'
    for s in SCHOOL_COOPERATIVE:
        known_types[s] = '中外合作办学'

    for fname, data in univ_files.items():
        if '_error' in data:
            continue
        name = data.get('layer1_overview', {}).get('name', '')
        actual_type = data.get('layer1_overview', {}).get('type', '')
        if name in known_types:
            expected = known_types[name]
            if actual_type != expected:
                issues.append(f"  {name}: expected={expected}, actual={actual_type}")

    if issues:
        print("类型不匹配:")
        for i in issues:
            print(i)
    else:
        print("所有已知院校类型正确")

    # 统计各类型数量
    type_counts = defaultdict(int)
    for fname, data in univ_files.items():
        if '_error' in data:
            continue
        t = data.get('layer1_overview', {}).get('type', 'unknown')
        type_counts[t] += 1
    print("\n类型分布:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    return {'issues': len(issues), 'type_counts': dict(type_counts)}


def check_file_mismatch():
    """检查 MD 和 JSON 文件数量是否一致"""
    print("\n=== 文件数量对比 ===\n")

    major_md = set(f.stem for f in MAJOR_MD_DIR.glob('*.md') if not f.name.startswith('_'))
    major_json = set(f.stem for f in MAJOR_JSON_DIR.glob('*.json') if not f.name.startswith('_'))
    univ_md = set(f.stem for f in UNIV_MD_DIR.glob('*.md') if not f.name.startswith('_'))
    univ_json = set(f.stem for f in UNIV_JSON_DIR.glob('*.json') if not f.name.startswith('_'))

    print(f"专业: MD={len(major_md)}, JSON={len(major_json)}")
    md_only = major_md - major_json
    json_only = major_json - major_md
    if md_only:
        print(f"  仅 MD: {len(md_only)} 个")
        for f in sorted(md_only)[:5]:
            print(f"    - {f}")
    if json_only:
        print(f"  仅 JSON: {len(json_only)} 个")
        for f in sorted(json_only)[:5]:
            print(f"    - {f}")
    if not md_only and not json_only:
        print("  完全匹配")

    print(f"\n院校: MD={len(univ_md)}, JSON={len(univ_json)}")
    md_only = univ_md - univ_json
    json_only = univ_json - univ_md
    if md_only:
        print(f"  仅 MD: {len(md_only)} 个")
        for f in sorted(md_only)[:5]:
            print(f"    - {f}")
    if json_only:
        print(f"  仅 JSON: {len(json_only)} 个")
        for f in sorted(json_only)[:5]:
            print(f"    - {f}")
    if not md_only and not json_only:
        print("  完全匹配")

    # 检查缺失的知名院校
    print("\n已知院校缺失检查:")
    missing = []
    for name in ['宁波诺丁汉大学', '西交利物浦大学', '昆山杜克大学', '深圳北理莫斯科大学']:
        found = any(name in f for f in univ_json)
        if not found:
            missing.append(name)
            print(f"  缺失: {name}")
    if not missing:
        print("  无缺失")

    return {'missing_univ': missing}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='数据质量检查')
    parser.add_argument('--all', action='store_true', help='运行所有检查')
    parser.add_argument('--check-empty-modules', action='store_true')
    parser.add_argument('--check-zero-scores', action='store_true')
    parser.add_argument('--check-univ-types', action='store_true')
    parser.add_argument('--check-file-mismatch', action='store_true')
    args = parser.parse_args()

    if not any([args.all, args.check_empty_modules, args.check_zero_scores,
                args.check_univ_types, args.check_file_mismatch]):
        args.all = True

    if args.all or args.check_file_mismatch:
        check_file_mismatch()
    if args.all or args.check_empty_modules:
        check_empty_modules()
    if args.all or args.check_zero_scores:
        check_zero_scores()
    if args.all or args.check_univ_types:
        check_univ_types()


if __name__ == '__main__':
    main()
