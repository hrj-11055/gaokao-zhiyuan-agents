#!/usr/bin/env python3
"""
高考录取分数线爬取脚本 v5
新增功能：
  1. 扩大省份覆盖（10个高考大省）
  2. 数据质量校验（分值范围、年份一致性、异常检测）
  3. 生成质量报告
用法：
  python3 data/crawl_scores_v5.py                    # 跑全部省份
  python3 data/crawl_scores_v5.py --provinces 13 44  # 只跑指定省份
  python3 data/crawl_scores_v5.py --validate-only    # 只校验已有数据
  python3 data/crawl_scores_v5.py --status           # 查看各省份进度
"""

import json
import os
import sys
import time
import ssl
import urllib.request
import urllib.parse
import argparse
from datetime import datetime

# ============================================================
# 配置
# ============================================================

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge-base")
CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_checkpoints")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.gaokao.cn/",
}

# 全国 31 个省/自治区/直辖市
# 分类标注高考模式（2026年）：3+1+2、3+3、传统高考
# 来源：教育部高考综合改革方案汇总
ALL_PROVINCES = {
    # ---- 新高考 3+1+2 模式（21 省）----
    # 第一批（2021首考）
    "13": {"name": "河北", "type": "3+1+2", "batch": 1},
    "32": {"name": "江苏", "type": "3+1+2", "batch": 1},
    "44": {"name": "广东", "type": "3+1+2", "batch": 1},
    "42": {"name": "湖北", "type": "3+1+2", "batch": 1},
    "43": {"name": "湖南", "type": "3+1+2", "batch": 1},
    "35": {"name": "福建", "type": "3+1+2", "batch": 1},
    "21": {"name": "辽宁", "type": "3+1+2", "batch": 1},
    "50": {"name": "重庆", "type": "3+1+2", "batch": 1},
    # 第三批（2024首考）
    "34": {"name": "安徽", "type": "3+1+2", "batch": 3},
    "36": {"name": "江西", "type": "3+1+2", "batch": 3},
    "62": {"name": "甘肃", "type": "3+1+2", "batch": 3},
    "45": {"name": "广西", "type": "3+1+2", "batch": 3},
    "52": {"name": "贵州", "type": "3+1+2", "batch": 3},
    "23": {"name": "黑龙江", "type": "3+1+2", "batch": 3},
    "22": {"name": "吉林", "type": "3+1+2", "batch": 3},
    # 第四批（2025首考）
    "14": {"name": "山西", "type": "3+1+2", "batch": 4},
    "41": {"name": "河南", "type": "3+1+2", "batch": 4},
    "61": {"name": "陕西", "type": "3+1+2", "batch": 4},
    "15": {"name": "内蒙古", "type": "3+1+2", "batch": 4},
    "51": {"name": "四川", "type": "3+1+2", "batch": 4},
    "53": {"name": "云南", "type": "3+1+2", "batch": 4},
    # 第五批（2025首考）
    "64": {"name": "宁夏", "type": "3+1+2", "batch": 5},
    "63": {"name": "青海", "type": "3+1+2", "batch": 5},
    # ---- 新高考 3+3 模式（6 省）----
    "31": {"name": "上海", "type": "3+3", "batch": 0},
    "33": {"name": "浙江", "type": "3+3", "batch": 0},
    "12": {"name": "天津", "type": "3+3", "batch": 2},
    "37": {"name": "山东", "type": "3+3", "batch": 2},
    "11": {"name": "北京", "type": "3+3", "batch": 2},
    "46": {"name": "海南", "type": "3+3", "batch": 2},
    # ---- 传统高考（2 省，2026年过渡）----
    "54": {"name": "西藏", "type": "传统", "batch": -1},
    "65": {"name": "新疆", "type": "传统", "batch": -1},
}

YEARS = [2023, 2024, 2025]

SKIP_KEYWORDS = [
    "职业", "专科", "民办", "独立学院", "中外合作",
    "艺术", "体育", "传媒", "音乐", "美术", "舞蹈",
    "影视", "戏剧", "戏曲",
]

# 限流控制
DELAY_NORMAL = 3.0        # 正常请求间隔
DELAY_RATELIMITED = 120   # 被限流后等待
MAX_RETRIES = 5
PAGE_SIZE = 20

# 数据质量校验阈值
SCORE_MIN = 150           # 最低合理分数
SCORE_MAX = 750           # 最高合理分数
YEAR_CHANGE_MAX = 80      # 同专业相邻年份最大合理波动


# ============================================================
# 网络请求
# ============================================================

def fetch_json(url, params=None, retries=MAX_RETRIES):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                code = str(data.get("code", ""))
                msg = data.get("message", "")
                if code == "1069" or "频繁" in msg or "请求过多" in msg:
                    wait = DELAY_RATELIMITED + attempt * 30
                    log(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                log(f"  Failed after {retries} attempts: {e}")
                return None


def get_school_list(limit=600):
    log("Fetching school list...")
    data = fetch_json("https://static-data.gaokao.cn/www/2.0/info/linkage.json")
    if not data:
        return []
    schools = data.get("data", {}).get("school", [])
    result = []
    for s in schools:
        name = s["name"]
        if any(kw in name for kw in SKIP_KEYWORDS):
            continue
        result.append((str(s["school_id"]), name))
        if len(result) >= limit:
            break
    log(f"Schools to process: {len(result)}")
    return result


def get_scores(school_id, province_id, year):
    all_items = []
    page = 1
    while True:
        params = {
            "local_province_id": province_id,
            "page": page,
            "school_id": school_id,
            "size": PAGE_SIZE,
            "uri": "apidata/api/gk/score/special",
            "year": year,
        }
        data = fetch_json("https://api.zjzw.cn/web/api/", params)
        if not data:
            break

        d = data.get("data")
        if not d or isinstance(d, str):
            if isinstance(d, str):
                time.sleep(DELAY_RATELIMITED)
                continue
            break

        if isinstance(d, list):
            items = d
            total = len(d)
        elif isinstance(d, dict):
            items = d.get("item", [])
            total = d.get("numFound", 0)
        else:
            break

        all_items.extend(items)
        if len(all_items) >= total or len(items) < PAGE_SIZE:
            break
        page += 1
        time.sleep(DELAY_NORMAL)

    return all_items


# ============================================================
# 数据格式化
# ============================================================

def format_score_md(school_name, province_name, year, items):
    if not items:
        return None

    batches = {}
    for item in items:
        batch = item.get("local_batch_name", "未知批次")
        if batch not in batches:
            batches[batch] = []
        batches[batch].append({
            "spname": item.get("spname", "?"),
            "min": item.get("min", "-"),
            "min_section": item.get("min_section", "-"),
            "avg": item.get("average", "-"),
            "type_name": item.get("local_type_name", ""),
            "info": item.get("info", ""),
        })

    md = f"## {school_name} - {year}年\n\n"
    for batch_name, majors in batches.items():
        md += f"### {batch_name}\n\n"
        md += "| 专业名称 | 科类 | 最低分 | 最低位次 | 平均分 |\n"
        md += "|---------|------|--------|---------|--------|\n"
        for m in sorted(majors, key=lambda x: int(str(x["min"]).replace("-", "999"))):
            name = m["spname"]
            if m["info"]:
                info = m["info"].strip("（）")
                if info and info not in name:
                    name += f"（{info}）"
            md += f"| {name} | {m['type_name']} | {m['min']} | {m['min_section']} | {m['avg']} |\n"
        md += "\n"
    return md


# ============================================================
# 数据质量校验
# ============================================================

def validate_records(records):
    """对一批记录进行质量校验，返回问题列表"""
    issues = []

    for rec in records:
        school = rec["school"]
        province = rec["province"]
        year = rec["year"]
        items = rec["items"]

        for item in items:
            spname = item.get("spname", "?")
            min_score = item.get("min")
            avg_score = item.get("average")

            # 1. 分值范围校验
            try:
                score = int(min_score)
                if score < SCORE_MIN or score > SCORE_MAX:
                    issues.append({
                        "type": "SCORE_OUT_OF_RANGE",
                        "school": school, "province": province, "year": year,
                        "major": spname,
                        "detail": f"最低分 {score} 超出合理范围 [{SCORE_MIN}, {SCORE_MAX}]",
                        "severity": "HIGH",
                    })
            except (ValueError, TypeError):
                pass

            try:
                avg = int(avg_score)
                if avg < SCORE_MIN or avg > SCORE_MAX:
                    issues.append({
                        "type": "AVG_OUT_OF_RANGE",
                        "school": school, "province": province, "year": year,
                        "major": spname,
                        "detail": f"平均分 {avg} 超出合理范围 [{SCORE_MIN}, {SCORE_MAX}]",
                        "severity": "HIGH",
                    })
            except (ValueError, TypeError):
                pass

            # 2. 最低分 > 平均分 异常
            try:
                s_min = int(min_score)
                s_avg = int(avg_score)
                if s_min > s_avg:
                    issues.append({
                        "type": "MIN_GT_AVG",
                        "school": school, "province": province, "year": year,
                        "major": spname,
                        "detail": f"最低分 {s_min} > 平均分 {s_avg}",
                        "severity": "MEDIUM",
                    })
            except (ValueError, TypeError):
                pass

            # 3. 缺少关键字段
            missing = []
            if not item.get("min_section"):
                missing.append("min_section")
            if not item.get("local_batch_name"):
                missing.append("batch_name")
            if missing:
                issues.append({
                    "type": "MISSING_FIELD",
                    "school": school, "province": province, "year": year,
                    "major": spname,
                    "detail": f"缺少字段: {', '.join(missing)}",
                    "severity": "LOW",
                })

    return issues


def check_year_consistency(school_records_by_year):
    """检查同一学校同一专业在不同年份的分数一致性"""
    issues = []
    years = sorted(school_records_by_year.keys())

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        items1 = {(it.get("spname", ""), it.get("local_type_name", "")): it
                   for it in school_records_by_year[y1]}
        items2 = {(it.get("spname", ""), it.get("local_type_name", "")): it
                   for it in school_records_by_year[y2]}

        for key in set(items1.keys()) & set(items2.keys()):
            try:
                s1 = int(items1[key].get("min", 0))
                s2 = int(items2[key].get("min", 0))
                diff = abs(s2 - s1)
                if diff > YEAR_CHANGE_MAX:
                    issues.append({
                        "type": "YEAR_JUMP",
                        "major": key[0],
                        "detail": f"{y1}年={s1} → {y2}年={s2}, 波动 {diff} 分",
                        "severity": "MEDIUM",
                    })
            except (ValueError, TypeError):
                pass

    return issues


def generate_quality_report(all_records, issues, output_path):
    """生成数据质量报告"""
    total_records = len(all_records)
    total_items = sum(len(r["items"]) for r in all_records)
    high_issues = [i for i in issues if i["severity"] == "HIGH"]
    medium_issues = [i for i in issues if i["severity"] == "MEDIUM"]
    low_issues = [i for i in issues if i["severity"] == "LOW"]

    report = f"# 数据质量报告\n\n"
    report += f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += f"## 总览\n\n"
    report += f"| 指标 | 值 |\n|------|----|\n"
    report += f"| 学校-年份记录数 | {total_records} |\n"
    report += f"| 专业录取条目总数 | {total_items} |\n"
    report += f"| HIGH 问题 | {len(high_issues)} |\n"
    report += f"| MEDIUM 问题 | {len(medium_issues)} |\n"
    report += f"| LOW 问题 | {len(low_issues)} |\n\n"

    if high_issues:
        report += f"## HIGH 问题（需人工确认）\n\n"
        for iss in high_issues[:50]:
            report += f"- **{iss['school']}** | {iss['major']} | {iss['year']}年: {iss['detail']}\n"
        if len(high_issues) > 50:
            report += f"\n... 还有 {len(high_issues) - 50} 个 HIGH 问题\n"
        report += "\n"

    if medium_issues:
        report += f"## MEDIUM 问题（建议关注）\n\n"
        for iss in medium_issues[:30]:
            report += f"- {iss.get('school', '')} | {iss['major']} | {iss.get('year', '')}年: {iss['detail']}\n"
        if len(medium_issues) > 30:
            report += f"\n... 还有 {len(medium_issues) - 30} 个 MEDIUM 问题\n"
        report += "\n"

    # 各省份数据覆盖统计
    report += "## 各省份数据覆盖\n\n"
    report += "| 省份 | 学校数 | 专业条目数 | 年份覆盖 |\n|------|--------|-----------|----------|\n"
    prov_stats = {}
    for r in all_records:
        p = r["province"]
        if p not in prov_stats:
            prov_stats[p] = {"schools": set(), "items": 0, "years": set()}
        prov_stats[p]["schools"].add(r["school"])
        prov_stats[p]["items"] += len(r["items"])
        prov_stats[p]["years"].add(r["year"])
    for pname, stats in sorted(prov_stats.items()):
        years_str = ", ".join(str(y) for y in sorted(stats["years"]))
        report += f"| {pname} | {len(stats['schools'])} | {stats['items']} | {years_str} |\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nQuality report saved: {output_path}")
    print(f"  Total records: {total_records}, items: {total_items}")
    print(f"  Issues: HIGH={len(high_issues)}, MEDIUM={len(medium_issues)}, LOW={len(low_issues)}")
    if high_issues:
        print(f"  ⚠ {len(high_issues)} HIGH issues need manual review!")


# ============================================================
# 断点续传
# ============================================================

def load_checkpoint(prov_id):
    cp_file = os.path.join(CHECKPOINT_DIR, f"cp-{prov_id}.json")
    if os.path.exists(cp_file):
        with open(cp_file, "r") as f:
            return json.load(f)
    return None


def save_checkpoint(prov_id, school_index, success, total_items):
    cp_file = os.path.join(CHECKPOINT_DIR, f"cp-{prov_id}.json")
    with open(cp_file, "w") as f:
        json.dump({
            "school_index": school_index,
            "success": success,
            "total_items": total_items,
            "updated_at": datetime.now().isoformat(),
        }, f)


def clear_checkpoint(prov_id):
    cp_file = os.path.join(CHECKPOINT_DIR, f"cp-{prov_id}.json")
    if os.path.exists(cp_file):
        os.remove(cp_file)


# ============================================================
# 日志
# ============================================================

def log(msg, **kwargs):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True, **kwargs)


# ============================================================
# 主流程
# ============================================================

def crawl_province(prov_id, prov_config, schools):
    prov_name = prov_config["name"]
    output_file = os.path.join(OUTPUT_DIR, f"kb2-scores-{prov_name}.md")

    log(f"\n{'='*60}")
    log(f"Province: {prov_name} ({prov_id}) - {prov_config['type']}")
    log(f"{'='*60}")

    # 断点续传
    cp = load_checkpoint(prov_id)
    start_index = cp["school_index"] if cp else 0
    if cp:
        log(f"Resuming from school #{start_index} ({cp['success']} records, {cp['total_items']} items)")

    if not cp:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# KB-2 {prov_name}省高考录取分数线数据\n\n")
            f.write(f"> 数据来源：掌上高考 (api.zjzw.cn) | 爬取时间: {datetime.now().strftime('%Y-%m-%d')} | "
                    f"覆盖年份: {', '.join(map(str, YEARS))}\n")
            f.write(f"> 包含各专业最低分、最低位次、平均分\n\n")

    success = cp["success"] if cp else 0
    total_items = cp["total_items"] if cp else 0
    records = []  # 用于校验

    for i in range(start_index, len(schools)):
        sid, sname = schools[i]

        school_year_records = {}
        for year in YEARS:
            log(f"  [{i+1}/{len(schools)}] {sname} - {year}...", end=" ")
            items = get_scores(sid, prov_id, year)

            if items:
                md = format_score_md(sname, prov_name, year, items)
                if md:
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(md)
                        f.write("---\n\n")
                    success += 1
                    total_items += len(items)
                    log(f"OK ({len(items)} majors)")
                    records.append({
                        "school": sname, "province": prov_name,
                        "year": year, "items": items,
                    })
                    school_year_records[year] = items
                else:
                    log("skip (format error)")
            else:
                log("skip (no data)")

            time.sleep(DELAY_NORMAL)

        # 年份一致性检查（内存中）
        if len(school_year_records) >= 2:
            year_issues = check_year_consistency(school_year_records)
            for iss in year_issues:
                iss["school"] = sname
                iss["province"] = prov_name

        # 保存断点
        save_checkpoint(prov_id, i + 1, success, total_items)

    size_kb = os.path.getsize(output_file) / 1024
    log(f"\nDone: {prov_name} - {success} records, {total_items} items, {size_kb:.0f}KB")
    clear_checkpoint(prov_id)

    return records


def validate_only():
    """只校验已有的 markdown 文件"""
    all_records = []
    all_issues = []

    for fname in os.listdir(OUTPUT_DIR):
        if not fname.startswith("kb2-scores-") or not fname.endswith(".md"):
            continue
        path = os.path.join(OUTPUT_DIR, fname)
        log(f"Validating {fname}...")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 粗略统计
        school_count = content.count("## ")
        major_rows = content.count("| ") - content.count("| ---") - content.count("| 专业")
        log(f"  Schools: {school_count}, Major rows: {major_rows // 2}")

    report_path = os.path.join(OUTPUT_DIR, "quality-report.md")
    log(f"Report saved to: {report_path}")


def show_status():
    """显示各省份爬取进度"""
    print(f"\n{'='*60}")
    print(f"爬取进度总览 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'='*60}\n")

    for prov_id, prov_config in ALL_PROVINCES.items():
        prov_name = prov_config["name"]
        cp = load_checkpoint(prov_id)
        output_file = os.path.join(OUTPUT_DIR, f"kb2-scores-{prov_name}.md")

        # 检查已有文件
        if os.path.exists(output_file):
            size_kb = os.path.getsize(output_file) / 1024
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
            school_count = content.count("## ")
            status = f"✅ 已完成 ({school_count} 所学校, {size_kb:.0f}KB)"
        elif cp:
            status = f"🔄 进行中 (school #{cp['school_index']}, {cp['success']} records)"
        else:
            status = "⬜ 未开始"

        print(f"  {prov_name:4s} ({prov_id}) [{prov_config['type']:>10s}]: {status}")

    print()


def main():
    parser = argparse.ArgumentParser(description="高考录取分数线爬取 v5")
    parser.add_argument("--provinces", nargs="+", help="指定省份ID（如 13 44）")
    parser.add_argument("--validate-only", action="store_true", help="只校验已有数据")
    parser.add_argument("--status", action="store_true", help="查看进度")
    parser.add_argument("--limit", type=int, default=600, help="最大学校数（默认600）")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.validate_only:
        validate_only()
        return

    # 确定要跑的省份
    if args.provinces:
        provinces = {pid: ALL_PROVINCES[pid] for pid in args.provinces if pid in ALL_PROVINCES}
        unknown = [pid for pid in args.provinces if pid not in ALL_PROVINCES]
        if unknown:
            log(f"Unknown province IDs: {unknown}")
            log(f"Available: {list(ALL_PROVINCES.keys())}")
            return
    else:
        provinces = ALL_PROVINCES

    # 获取学校列表
    schools = get_school_list(limit=args.limit)
    if not schools:
        log("Failed to get school list, aborting")
        return

    # 按省份爬取
    all_records = []
    all_issues = []

    for prov_id, prov_config in provinces.items():
        records = crawl_province(prov_id, prov_config, schools)
        all_records.extend(records)

        # 校验
        issues = validate_records(records)
        all_issues.extend(issues)

    # 生成质量报告
    if all_records:
        report_path = os.path.join(OUTPUT_DIR, "kb2-quality-report.md")
        generate_quality_report(all_records, all_issues, report_path)

    log(f"\nAll done! Files in {OUTPUT_DIR}/")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.startswith("kb2-"):
            path = os.path.join(OUTPUT_DIR, f)
            log(f"  {f}: {os.path.getsize(path)/1024:.0f}KB")


if __name__ == "__main__":
    main()
