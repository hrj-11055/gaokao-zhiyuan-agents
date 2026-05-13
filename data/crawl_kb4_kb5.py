#!/usr/bin/env python3
"""爬取学校基本信息 + 各省批次线数据"""
import json, os, time, requests

OUTPUT_DIR = "/tmp/gaokao_kb4_kb5"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.gaokao.cn/",
})

SKIP = ["职业", "专科", "民办", "独立学院", "中外合作", "艺术", "体育",
        "传媒", "音乐", "美术", "舞蹈", "影视", "戏剧", "戏曲"]

PROVINCES = {
    "13": "河北", "44": "广东", "11": "北京", "31": "上海", "32": "江苏",
    "33": "浙江", "37": "山东", "41": "河南", "42": "湖北", "43": "湖南",
    "50": "重庆", "51": "四川", "34": "安徽", "35": "福建", "36": "江西",
    "61": "陕西", "22": "吉林", "23": "黑龙江", "21": "辽宁",
}

YEARS = [2023, 2024, 2025]


def get_school_ids(limit=500):
    """获取学校ID列表"""
    r = SESSION.get("https://static-data.gaokao.cn/www/2.0/info/linkage.json", timeout=15)
    schools = r.json().get("data", {}).get("school", [])
    result = []
    for s in schools:
        name = s["name"]
        if any(kw in name for kw in SKIP):
            continue
        result.append((s["school_id"], name))
        if len(result) >= limit:
            break
    return result


def crawl_school_info(school_id):
    """爬取单个学校基本信息"""
    url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json().get("data", r.json())
        return {
            "name": data.get("name", ""),
            "type_name": data.get("type_name", ""),       # 综合/理工/师范等
            "level_name": data.get("level_name", ""),      # 本科/专科
            "nature_name": data.get("nature_name", ""),    # 公办/民办
            "province_name": data.get("province_name", ""),# 学校所在省
            "city_name": data.get("city_name", ""),        # 学校所在城市
            "f985": str(data.get("f985", "2")),          # 985标识 "1"=是, "2"=否
            "f211": str(data.get("f211", "2")),          # 211标识 "1"=是, "2"=否
            "dual_class_name": data.get("dual_class_name", ""), # 双一流
            "school_id": str(school_id),
        }
    except:
        return None


def format_kb4(schools_info):
    """格式化学校信息为 Markdown"""
    md = "# KB-4 全国本科院校基本信息\n\n"
    md += "> 数据来源：掌上高考 | 覆盖约500所本科院校\n\n"

    # 按 985/211/普通 分组
    tier_985 = [s for s in schools_info if s["f985"] == "1"]
    tier_211 = [s for s in schools_info if s["f211"] == "1" and s["f985"] != "1"]
    tier_rest = [s for s in schools_info if s["f211"] != "1" and s["f985"] != "1"]

    md += f"## 985高校（{len(tier_985)}所）\n\n"
    md += "| 学校名称 | 类型 | 所在地 | 双一流 |\n"
    md += "|---------|------|--------|--------|\n"
    for s in sorted(tier_985, key=lambda x: x["name"]):
        md += f"| {s['name']} | {s['type_name']} | {s['province_name']}{s['city_name']} | {s['dual_class_name']} |\n"
    md += "\n"

    md += f"## 211高校（非985，{len(tier_211)}所）\n\n"
    md += "| 学校名称 | 类型 | 性质 | 所在地 | 双一流 |\n"
    md += "|---------|------|------|--------|--------|\n"
    for s in sorted(tier_211, key=lambda x: x["name"]):
        md += f"| {s['name']} | {s['type_name']} | {s['nature_name']} | {s['province_name']}{s['city_name']} | {s['dual_class_name']} |\n"
    md += "\n"

    md += f"## 其他公办本科（{len(tier_rest)}所）\n\n"
    md += "| 学校名称 | 类型 | 性质 | 所在地 |\n"
    md += "|---------|------|------|--------|\n"
    for s in sorted(tier_rest, key=lambda x: x["name"]):
        md += f"| {s['name']} | {s['type_name']} | {s['nature_name']} | {s['province_name']}{s['city_name']} |\n"
    md += "\n"

    return md


def crawl_batch_scores(province_id, year):
    """爬取某省某年的院校投档线（含批次线信息）"""
    all_items = []
    page = 1
    while True:
        params = {
            'local_province_id': province_id,
            'page': page,
            'size': 20,
            'uri': 'apidata/api/gk/score/province',
            'year': year,
        }
        try:
            r = SESSION.get("https://api.zjzw.cn/web/api/", params=params, timeout=15)
            data = r.json()
        except:
            break

        if data.get("code") == "1069":
            print("  RATE LIMITED, waiting...")
            time.sleep(120)
            continue

        d = data.get("data")
        if not d:
            break
        if isinstance(d, dict):
            items = d.get("item", [])
            total = d.get("numFound", 0)
        elif isinstance(d, list):
            items = d
            total = len(d)
        else:
            break

        all_items.extend(items)
        if len(all_items) >= total or len(items) < 20:
            break
        page += 1
        time.sleep(3)

    return all_items


def format_kb5(province_name, year, items):
    """格式化批次线/投档线数据"""
    if not items:
        return None

    # 过滤掉专科/职业院校数据，只保留本科
    VOCATIONAL_SKIP = ["职业", "专科"]
    filtered = []
    for item in items:
        name = item.get("name", "")
        batch = item.get("local_batch_name", "")
        # 过滤专科批次和职业院校
        if "专科" in batch:
            continue
        if any(kw in name for kw in VOCATIONAL_SKIP):
            continue
        filtered.append(item)

    if not filtered:
        return None

    md = f"## {province_name}省 - {year}年\n\n"

    md += "### 各院校投档线\n\n"
    md += "| 学校名称 | 科类 | 批次 | 最低分 | 最低位次 | 性质 | 985/211 |\n"
    md += "|---------|------|------|--------|---------|------|--------|\n"
    for item in sorted(filtered, key=lambda x: int(str(x.get("min","9999")).replace("-","9999"))):
        name = item.get("name", "?")
        tname = item.get("local_type_name", "-")
        batch = item.get("local_batch_name", "-")
        min_s = item.get("min", "-")
        min_sec = item.get("min_section", "-")
        nature = item.get("nature_name", "-")
        tag = ""
        f985 = item.get("f985")
        f211 = item.get("f211")
        # f985/f211 可能是 int(1/0) 或 str("1"/"2")
        if f985 == 1 or f985 == "1":
            tag = "985"
        elif f211 == 1 or f211 == "1":
            tag = "211"
        md += f"| {name} | {tname} | {batch} | {min_s} | {min_sec} | {nature} | {tag} |\n"
    md += "\n"

    return md


def main():
    # ===== Part 1: 爬学校信息 (KB-4) =====
    print("=" * 50)
    print("Part 1: 爬取学校基本信息 (KB-4)")
    print("=" * 50)

    schools = get_school_ids(500)
    print(f"学校列表: {len(schools)} 所")

    schools_info = []
    for i, (sid, sname) in enumerate(schools):
        if i % 50 == 0:
            print(f"  [{i+1}/{len(schools)}] {sname}...")
        info = crawl_school_info(sid)
        if info and info["name"]:
            schools_info.append(info)
        time.sleep(0.5)

    md = format_kb4(schools_info)
    kb4_file = os.path.join(OUTPUT_DIR, "kb4-school-info.md")
    with open(kb4_file, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nKB-4 完成: {len(schools_info)} 所学校, {os.path.getsize(kb4_file)/1024:.0f}KB")

    # ===== Part 2: 爬批次线/投档线 (KB-5) =====
    print(f"\n{'='*50}")
    print("Part 2: 爬取批次线/投档线 (KB-5)")
    print("=" * 50)

    kb5_file = os.path.join(OUTPUT_DIR, "kb5-batch-scores.md")
    with open(kb5_file, "w", encoding="utf-8") as f:
        f.write("# KB-5 各省院校投档线数据\n\n")
        f.write("> 数据来源：掌上高考 | 覆盖省份：河北、广东等 | 2023-2025年\n\n")

    total_records = 0
    for prov_id, prov_name in PROVINCES.items():
        for year in YEARS:
            print(f"  {prov_name} {year}...", end=" ", flush=True)
            items = crawl_batch_scores(prov_id, year)
            if items:
                md = format_kb5(prov_name, year, items)
                if md:
                    with open(kb5_file, "a", encoding="utf-8") as f:
                        f.write(md)
                        f.write("---\n\n")
                    total_records += len(items)
                    print(f"OK ({len(items)} records)")
                else:
                    print("skip (format error)")
            else:
                print("skip (no data)")
            time.sleep(5)

    print(f"\nKB-5 完成: {total_records} 条记录, {os.path.getsize(kb5_file)/1024:.0f}KB")
    print(f"\n输出文件:")
    for f in os.listdir(OUTPUT_DIR):
        path = os.path.join(OUTPUT_DIR, f)
        print(f"  {f}: {os.path.getsize(path)/1024:.0f}KB")


if __name__ == "__main__":
    main()
