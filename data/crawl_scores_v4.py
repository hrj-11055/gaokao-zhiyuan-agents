#!/usr/bin/env python3
"""高考录取分数线爬取脚本 v4 - 带限流检测和断点续传"""
import json, os, time, sys
import requests

OUTPUT_DIR = "/tmp/gaokao_scores"
CHECKPOINT_DIR = "/tmp/gaokao_scores_checkpoints"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.gaokao.cn/",
    "Accept": "application/json, text/plain, */*",
})

PROVINCES = {"13": "河北", "44": "广东"}
YEARS = [2023, 2024, 2025]
SKIP = ["职业", "专科", "民办", "独立学院", "中外合作", "艺术", "体育",
        "传媒", "音乐", "美术", "舞蹈", "影视", "戏剧", "戏曲"]

# 限流控制参数
DELAY_BETWEEN_REQUESTS = 5.0   # 正常请求间隔（秒）
DELAY_AFTER_RATELIMIT = 180    # 被限流后等待时间（秒）
MAX_RETRIES = 5                # 单次请求最大重试
PAGE_SIZE = 20                 # 每页条数（API 在 size=50 时有 bug）

def log(msg, **kwargs):
    print(msg, flush=True, **kwargs)

def get_school_list(limit=500):
    log("Fetching school list...")
    r = SESSION.get("https://static-data.gaokao.cn/www/2.0/info/linkage.json", timeout=15)
    data = r.json()
    schools = data.get("data", {}).get("school", [])
    result = []
    for s in schools:
        name = s["name"]
        if any(kw in name for kw in SKIP):
            continue
        result.append((s["school_id"], name))
        if len(result) >= limit:
            break
    log(f"Schools to process: {len(result)}")
    return result

def fetch_scores(school_id, province_id, year):
    """获取某校某省某年的专业录取分数线，带限流检测"""
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

        for retry in range(MAX_RETRIES):
            try:
                r = SESSION.get("https://api.zjzw.cn/web/api/", params=params, timeout=15)
                data = r.json()
            except Exception as e:
                log(f"  Request error: {e}, retry {retry+1}/{MAX_RETRIES}")
                time.sleep(10)
                continue

            # 检测限流（code=1069 或 message 包含 "频繁"）
            code = data.get("code", "")
            message = data.get("message", "")
            if code == "1069" or "频繁" in message:
                wait = DELAY_AFTER_RATELIMIT + retry * 30
                log(f"  RATE LIMITED! Waiting {wait}s... (retry {retry+1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue

            break
        else:
            log("  Max retries exceeded, skipping")
            return all_items

        d = data.get("data")

        # 空数据
        if not d:
            break

        # data 可能是 str（限流时的 IP 地址）
        if isinstance(d, str):
            # 如果 data 是字符串但不是 JSON，说明被限流了
            log(f"  Unexpected data type: str, content: {d[:50]}")
            time.sleep(DELAY_AFTER_RATELIMIT)
            continue

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
        time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_items

def format_md(school_name, province_name, year, items):
    if not items:
        return None

    batches = {}
    for item in items:
        batch = item.get("local_batch_name", "未知")
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
        for m in sorted(majors, key=lambda x: int(str(x["min"]).replace("-","999"))):
            name = m["spname"]
            if m["info"]:
                name += f"（{m['info']}）"
            md += f"| {name} | {m['type_name']} | {m['min']} | {m['min_section']} | {m['avg']} |\n"
        md += "\n"
    return md

def load_checkpoint(prov_name):
    """加载断点"""
    cp_file = os.path.join(CHECKPOINT_DIR, f"checkpoint-{prov_name}.json")
    if os.path.exists(cp_file):
        with open(cp_file, "r") as f:
            cp = json.load(f)
            log(f"Resuming from checkpoint: school #{cp['school_index']}, {cp['success']} records")
            return cp
    return None

def save_checkpoint(prov_name, school_index, school_total, success):
    """保存断点"""
    cp_file = os.path.join(CHECKPOINT_DIR, f"checkpoint-{prov_name}.json")
    with open(cp_file, "w") as f:
        json.dump({"school_index": school_index, "school_total": school_total, "success": success}, f)

def main():
    schools = get_school_list(limit=500)

    for prov_id, prov_name in PROVINCES.items():
        output_file = os.path.join(OUTPUT_DIR, f"kb2-scores-{prov_name}.md")
        log(f"\n{'='*50}")
        log(f"Processing: {prov_name} ({prov_id})")
        log(f"{'='*50}")

        # 检查断点
        cp = load_checkpoint(prov_name)
        start_index = cp["school_index"] if cp else 0
        if cp:
            log(f"Resuming from school #{start_index}")
        else:
            # 新文件，写 header
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# KB-2 {prov_name}省高考录取分数线数据\n\n")
                f.write(f"> 数据来源：掌上高考 | 覆盖年份：2023-2025年 | 学校数量约500所\n")
                f.write(f"> 包含各专业最低分、最低位次、平均分\n\n")

        success = cp["success"] if cp else 0

        for i in range(start_index, len(schools)):
            sid, sname = schools[i]
            for year in YEARS:
                log(f"  [{i+1}/{len(schools)}] {sname} - {year}...", end=" ")
                items = fetch_scores(sid, prov_id, year)
                if items:
                    md = format_md(sname, prov_name, year, items)
                    if md:
                        with open(output_file, "a", encoding="utf-8") as f:
                            f.write(md)
                            f.write("---\n\n")
                        success += 1
                        log(f"OK ({len(items)} majors)")
                    else:
                        log("skip (format error)")
                else:
                    log("skip (no data)")
                time.sleep(DELAY_BETWEEN_REQUESTS)

            # 每处理完一所学校，保存断点
            save_checkpoint(prov_name, i + 1, len(schools), success)

        size = os.path.getsize(output_file) / 1024
        log(f"\nDone: {prov_name} - {success} records, {size:.0f}KB")

        # 清除断点
        cp_file = os.path.join(CHECKPOINT_DIR, f"checkpoint-{prov_name}.json")
        if os.path.exists(cp_file):
            os.remove(cp_file)

    log("\nAll done!")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".md"):
            path = os.path.join(OUTPUT_DIR, f)
            log(f"  {f}: {os.path.getsize(path)/1024:.0f}KB")

if __name__ == "__main__":
    main()
