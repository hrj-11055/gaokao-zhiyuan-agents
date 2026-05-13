#!/usr/bin/env python3
"""
高考录取分数线爬取脚本
数据源：掌上高考 api.zjzw.cn
爬取范围：河北(13) + 广东(44), 2023-2025年
输出：Dify 知识库格式的 Markdown 文件
"""

import json
import os
import time
import urllib.request
import urllib.parse
import ssl

# 跳过SSL验证
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = "https://api.zjzw.cn/web/api/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

# 省份配置
PROVINCES = {
    "13": {"name": "河北", "types": {"物理类": "1", "历史类": "2"}},
    "44": {"name": "广东", "types": {"物理类": "1", "历史类": "2"}},
}

YEARS = [2023, 2024, 2025]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "knowledge-base")

# 重点院校列表（本科一批主要院校，约300所）
PRIORITY_SCHOOL_KEYWORDS = ["大学", "学院"]  # 后续过滤


def fetch_json(url, params=None, retries=3):
    """发起HTTP请求获取JSON数据"""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # 检查是否被限流
                if isinstance(data, dict) and "请求过多" in str(data):
                    print(f"  Rate limited, waiting 10s...")
                    time.sleep(10)
                    continue
                return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                print(f"  Failed after {retries} attempts: {e}")
                return None


def get_school_list():
    """获取全部学校列表"""
    print("Fetching school list...")
    data = fetch_json("https://static-data.gaokao.cn/www/2.0/info/linkage.json")
    if not data:
        return {}

    schools = data.get("data", {}).get("school", [])
    result = {}
    for s in schools:
        sid = s["school_id"]
        name = s["name"]
        result[sid] = name

    print(f"  Total schools: {len(result)}")
    return result


def get_school_info(school_id):
    """获取学校详细信息（985/211等）"""
    data = fetch_json(f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json")
    if not data:
        return {}
    d = data.get("data", data)
    return {
        "name": d.get("name", ""),
        "type_name": d.get("type_name", ""),  # 985, 211 等
        "level_name": d.get("level_name", ""),  # 本科/专科
        "nature_name": d.get("nature_name", ""),  # 公办/民办
        "province_name": d.get("province_name", ""),
    }


def get_school_scores(school_id, province_id, year, page=1, size=50):
    """获取某学校某省某年的专业录取分数线"""
    params = {
        "local_province_id": province_id,
        "page": page,
        "school_id": school_id,
        "size": str(size),
        "uri": "apidata/api/gk/score/special",
        "year": year,
    }
    return fetch_json(BASE_URL, params)


def get_all_scores_for_school(school_id, province_id, year):
    """获取某学校某省某年的全部专业分数线（分页）"""
    all_items = []
    page = 1

    while True:
        data = get_school_scores(school_id, province_id, year, page=page, size=50)
        if not data:
            break

        d = data.get("data", {})

        # Handle both dict and list response formats
        if isinstance(d, list):
            items = d
            total = len(d)
        elif isinstance(d, dict):
            items = d.get("item", [])
            total = d.get("numFound", 0)
        else:
            break

        all_items.extend(items)
        if len(all_items) >= total or len(items) < 50:
            break

        page += 1
        time.sleep(0.5)

    return all_items


def filter_undergraduate_schools(school_list):
    """过滤出本科院校（排除职业、专科等），MVP阶段限制500所"""
    filtered = {}
    skip_keywords = ["职业", "专科", "民办", "独立学院", "中外合作",
                     "艺术", "体育", "传媒", "音乐", "美术", "舞蹈",
                     "影视", "戏剧", "戏曲"]

    for sid, name in school_list.items():
        skip = False
        for kw in skip_keywords:
            if kw in name:
                skip = True
                break
        if not skip:
            filtered[sid] = name

    # MVP: limit to 500 schools
    if len(filtered) > 500:
        filtered = dict(list(filtered.items())[:500])

    return filtered


def format_score_entry(school_name, province_name, year, items, school_info):
    """将分数线数据格式化为知识库Markdown"""
    if not items:
        return None

    # 按批次和科类分组
    batches = {}
    for item in items:
        batch = item.get("local_batch_name", "未知批次")
        spname = item.get("spname", "未知专业")
        min_score = item.get("min", "-")
        min_section = item.get("min_section", "-")
        avg_score = item.get("average", "-")
        dual_class = item.get("dual_class_name", "")
        info = item.get("info", "")

        if batch not in batches:
            batches[batch] = []

        batches[batch].append({
            "spname": spname,
            "min": min_score,
            "min_section": min_section,
            "avg": avg_score,
            "dual_class": dual_class,
            "info": info,
        })

    # 构建 Markdown
    tags = []
    if school_info.get("type_name"):
        tags.append(school_info["type_name"])
    if school_info.get("nature_name"):
        tags.append(school_info["nature_name"])

    md = f"# {school_name} - {province_name} {year}年录取分数线\n\n"
    md += f"## 基本信息\n"
    md += f"- 学校：{school_name}\n"
    md += f"- 省份：{province_name}\n"
    md += f"- 年份：{year}年\n"
    if tags:
        md += f"- 标签：{'、'.join(tags)}\n"
    if school_info.get("province_name"):
        md += f"- 学校所在省份：{school_info['province_name']}\n"
    md += f"\n"

    md += f"## 各专业录取分数线\n\n"

    for batch_name, majors in batches.items():
        md += f"### {batch_name}\n\n"
        md += f"| 专业名称 | 最低分 | 最低位次 | 平均分 | 备注 |\n"
        md += f"|---------|--------|---------|--------|------|\n"

        for m in sorted(majors, key=lambda x: int(x["min"]) if str(x["min"]).isdigit() else 999):
            name = m["spname"]
            if m["info"]:
                name += f"（{m['info']}）"
            md += f"| {name} | {m['min']} | {m['min_section']} | {m['avg']} | {m['dual_class']} |\n"
        md += "\n"

    return md


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 获取学校列表
    school_list = get_school_list()
    undergrad_schools = filter_undergraduate_schools(school_list)
    print(f"Undergraduate schools: {len(undergrad_schools)}")

    # Step 2: 批量爬取数据
    for prov_id, prov_config in PROVINCES.items():
        prov_name = prov_config["name"]
        print(f"\n{'='*60}")
        print(f"Processing province: {prov_name} ({prov_id})")
        print(f"{'='*60}")

        all_results = []
        school_count = 0
        success_count = 0

        for sid, sname in undergrad_schools.items():
            school_count += 1

            for year in YEARS:
                print(f"  [{school_count}/{len(undergrad_schools)}] {sname} - {year}...", end="", flush=True)

                # 获取分数线
                items = get_all_scores_for_school(sid, prov_id, year)

                if items and len(items) > 0:
                    # 获取学校信息（用于标签）
                    school_info = {}
                    if success_count < 50:  # 只获取前50所学校的信息，减少请求
                        school_info = get_school_info(sid) or {}
                        time.sleep(0.3)

                    md = format_score_entry(sname, prov_name, year, items, school_info)
                    if md:
                        all_results.append(md)
                        success_count += 1
                        print(f" OK ({len(items)} majors)")
                else:
                    print(f" skip (no data)")

                # 控制请求频率
                time.sleep(0.8)

        # Step 3: 保存文件
        output_file = os.path.join(OUTPUT_DIR, f"kb2-scores-{prov_name}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# KB-2 {prov_name}省高考录取分数线数据\n\n")
            f.write(f"> 数据来源：掌上高考 | 覆盖年份：{', '.join(map(str, YEARS))} | 学校数量：{success_count}所\n")
            f.write(f"> 包含各专业最低分、最低位次、平均分\n\n")

            for i, result in enumerate(all_results):
                f.write(result)
                if i < len(all_results) - 1:
                    f.write("\n---\n\n")

        size_kb = os.path.getsize(output_file) / 1024
        print(f"\nSaved: {output_file} ({size_kb:.0f}KB, {len(all_results)} records)")

    print("\nAll done!")


if __name__ == "__main__":
    main()
