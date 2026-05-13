#!/usr/bin/env python3
"""
专业评估报告批量质检脚本
自动检查报告是否符合提示词模板的格式和内容要求
用法: python3 check_reports.py [--dir data/专业评估报告] [--min-chars 3000]
"""

import json
import re
import sys
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = BASE_DIR / "data" / "专业评估报告"
MIN_CHARS = 3000  # 报告最少字符数

# 必须包含的 8 个模块标题
REQUIRED_MODULES = [
    "模块一：专业画像与总评",
    "模块二：六维量化评估",
    "模块三：院校分档与定位",
    "模块四：横向对决台",
    "模块五：职业路径图",
    "模块六",
    "模块七",
    "模块八：原始数据支撑",
]

# 必须包含的关键结构
REQUIRED_STRUCTURES = [
    ("AI 总评", "1.1 AI 总评"),
    ("推荐标签", "综合推荐标签"),
    ("六维雷达图", "1.3 六维雷达图"),
    ("就业确定性", "就业确定性"),
    ("薪酬水平", "薪酬水平"),
    ("供需关系", "供需关系"),
    ("AI 抗风险性", "AI 抗风险性"),
    ("深造依赖度", "深造依赖度"),
    ("职业准入门槛", "职业准入门槛"),
    ("院校金字塔", "院校金字塔"),
    ("对比数据表", "对比数据表"),
    ("气质标签云", "气质标签云"),
    ("就业数据汇总", "就业数据汇总"),
]

# 合法的分类标签选项（从提示词模板提取）
VALID_LABELS = {
    "供需关系": ["严重供过于求", "供过于求", "供需平衡", "供不应求", "严重供不应求"],
    "地域依赖性": ["高度集中于特定城市", "较多集中于主要城市群", "全国分布较均匀"],
    "产业阶段": ["初创期", "成长期", "成熟期", "衰退期"],
    "增长潜力": ["高速增长(>15%)", "中速增长(5%-15%)", "低速/稳定增长(<5%)", "负增长"],
    "国家战略": ["核心关联", "强关联", "一般关联", "弱关联", "无关联"],
    "AI风险": ["极低风险", "较低风险", "中等风险", "较高风险", "极高风险"],
    "知识迭代": ["高速迭代", "中速迭代", "慢速迭代/经典稳定"],
    "技能迁移": ["极强", "较强", "一般", "较弱"],
    "深造依赖": ["极高依赖", "较高依赖", "中等依赖", "较低依赖"],
    "准入门槛": ["高壁垒(强制准入且通过率低)", "中壁垒(强制准入或行业普遍要求)", "低壁垒(无强制要求)"],
    "转行灵活": ["高灵活性", "中等灵活性", "低灵活性"],
    "路径多元": ["高度多元", "较为多元", "较为单一", "高度单一"],
    "推荐标签": ["绿灯推荐", "黄灯谨慎", "红灯预警"],
}
# ──────────────────────────────────────────────────────


def check_report(filepath: Path, min_chars: int = MIN_CHARS) -> dict:
    """检查单份报告，返回质检结果"""
    result = {
        "file": filepath.name,
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        result["status"] = "FAIL"
        result["errors"].append(f"文件读取失败: {e}")
        return result

    char_count = len(text)
    result["stats"]["字符数"] = char_count

    # ── 1. 基础长度检查 ──
    if char_count < min_chars:
        result["errors"].append(f"内容过短: {char_count} 字符（要求 ≥ {min_chars}）")
    else:
        result["stats"]["字符评级"] = "充足" if char_count >= 5000 else ("一般" if char_count >= 4000 else "偏短")

    # ── 2. 模块完整性检查 ──
    missing_modules = []
    for module in REQUIRED_MODULES:
        if module not in text:
            missing_modules.append(module)
    if missing_modules:
        result["errors"].append(f"缺少模块: {', '.join(missing_modules)}")

    # ── 3. 关键结构检查 ──
    missing_structures = []
    for name, keyword in REQUIRED_STRUCTURES:
        if keyword not in text:
            missing_structures.append(name)
    if missing_structures:
        result["errors"].append(f"缺少结构: {', '.join(missing_structures)}")

    # ── 4. 数据表格检查 ──
    table_count = text.count("| ---") + text.count("| --- |") + text.count("|------|")
    result["stats"]["数据表格"] = table_count
    if table_count < 5:
        result["warnings"].append(f"数据表格偏少: {table_count} 个（建议 ≥ 5）")

    # ── 5. 未填充占位符检查 ──
    placeholders = re.findall(r'\[X+\]', text)
    unfilled_sources = re.findall(r'\[来源\]', text)
    if placeholders:
        result["errors"].append(f"存在未填充占位符 {len(placeholders)} 处: {placeholders[:5]}")
    if unfilled_sources:
        result["warnings"].append(f"存在未填充的 [来源] 标记 {len(unfilled_sources)} 处")

    # ── 6. [待核实] 标记统计 ──
    verify_count = text.count("[待核实]")
    result["stats"]["待核实标记"] = verify_count
    if verify_count > 15:
        result["warnings"].append(f"待核实标记过多: {verify_count} 处（可能数据可信度低）")

    # ── 7. 数据来源引用检查 ──
    source_patterns = re.findall(r'来源[：:][^\n]+', text)
    data_sources = re.findall(r'麦可思|职友集|国家统计局|教育部|软科|前瞻|艾瑞|国知局|知识产权局', text)
    result["stats"]["来源引用数"] = len(source_patterns)
    result["stats"]["引用的数据源"] = list(set(data_sources))
    if len(source_patterns) < 3:
        result["warnings"].append(f"数据来源引用偏少: {len(source_patterns)} 处")

    # ── 8. 分类标签合规性检查 ──
    # 检查是否使用了非标准标签（粗略检查）
    label_issues = []
    for category, valid in VALID_LABELS.items():
        # 在报告中搜索该维度的值
        pass  # 标签合规性需要更复杂的解析，这里跳过

    # ── 9. 加权总分检查 ──
    score_match = re.search(r'加权总分.*?(\d\.\d+)', text)
    if score_match:
        score = float(score_match.group(1))
        result["stats"]["加权总分"] = score
        if score < 1.0 or score > 5.0:
            result["warnings"].append(f"加权总分异常: {score}（应在 1.0-5.0 范围）")
    else:
        result["warnings"].append("未找到加权总分")

    # ── 10. 院校分档检查 ──
    if "S 档" not in text:
        result["warnings"].append("院校分档可能不完整（缺少 S 档）")

    # ── 最终判定 ──
    if result["errors"]:
        result["status"] = "FAIL"
    elif len(result["warnings"]) >= 3:
        result["status"] = "WARN"
    else:
        result["status"] = "PASS"

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="专业评估报告批量质检")
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="报告目录")
    parser.add_argument("--min-chars", type=int, default=MIN_CHARS, help="最少字符数")
    parser.add_argument("--category", default=None, help="仅检查指定门类代码，如 03")
    args = parser.parse_args()

    report_dir = Path(args.dir)
    min_chars = args.min_chars

    # 收集报告文件
    files = sorted(report_dir.glob("*.md"))
    files = [f for f in files if not f.name.startswith("_")]

    # 按门类过滤
    if args.category:
        files = [f for f in files if f.name.startswith(args.category)]

    if not files:
        print("未找到报告文件")
        sys.exit(1)

    print("=" * 70)
    print(f"  专业评估报告质检 | 目录: {report_dir.name} | 文件数: {len(files)}")
    print("=" * 70)

    results = []
    for f in files:
        results.append(check_report(f, min_chars))

    # ── 汇总输出 ──
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    # 逐份输出
    for r in results:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[r["status"]]
        name = r["file"].replace(".md", "")
        char = r["stats"].get("字符数", "?")
        tables = r["stats"].get("数据表格", "?")
        score = r["stats"].get("加权总分", "?")

        print(f"\n{icon} {name}")
        print(f"   字符: {char} | 表格: {tables} | 总分: {score}")

        for e in r["errors"]:
            print(f"   ❌ {e}")
        for w in r["warnings"]:
            print(f"   ⚠️  {w}")

    # 汇总统计
    print("\n" + "=" * 70)
    print(f"  质检结果: ✅ 通过 {pass_count} | ⚠️ 警告 {warn_count} | ❌ 失败 {fail_count}")
    print("=" * 70)

    # 失败报告列表
    failed = [r for r in results if r["status"] == "FAIL"]
    if failed:
        print("\n需要重跑的报告：")
        for r in failed:
            print(f"  {r['file']}")
            for e in r["errors"]:
                print(f"    - {e}")

    # 警告报告列表
    warned = [r for r in results if r["status"] == "WARN"]
    if warned:
        print(f"\n有警告的报告（{len(warned)} 份）：")
        for r in warned:
            print(f"  {r['file']}")
            for w in r["warnings"]:
                print(f"    - {w}")

    # 总分分布
    scores = [r["stats"]["加权总分"] for r in results if "加权总分" in r["stats"]]
    if scores:
        print(f"\n加权总分分布:")
        print(f"  平均: {sum(scores)/len(scores):.2f}")
        print(f"  最高: {max(scores):.2f}")
        print(f"  最低: {min(scores):.2f}")
        green = sum(1 for s in scores if s >= 4.0)
        yellow = sum(1 for s in scores if 3.0 <= s < 4.0)
        red = sum(1 for s in scores if s < 3.0)
        print(f"  🟢 绿灯(≥4.0): {green} | 🟡 黄灯(3.0-3.9): {yellow} | 🔴 红灯(<3.0): {red}")

    # 字符数分布
    chars = [r["stats"]["字符数"] for r in results]
    print(f"\n字符数分布:")
    print(f"  平均: {sum(chars)//len(chars):,} | 最大: {max(chars):,} | 最小: {min(chars):,}")


if __name__ == "__main__":
    main()
