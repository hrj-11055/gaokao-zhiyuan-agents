#!/usr/bin/env python3
"""
全国本科院校录取分数线采集（院校级）
从掌上高考 API 获取每所院校在全国各省的最低录取分。

用法：
  python3 data/crawl_school_scores.py                    # 跑全部院校
  python3 data/crawl_school_scores.py --limit 10         # 只跑前 10 所（测试）
  python3 data/crawl_school_scores.py --only 清华大学 北京大学  # 只跑指定院校
  python3 data/crawl_school_scores.py --status            # 查看采集进度
  python3 data/crawl_school_scores.py --resume            # 从断点续爬
"""

import csv
import json
import os
import random
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# ============================================================
# 配置
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "school_scores_raw.csv")
CHECKPOINT_FILE = os.path.join(SCRIPT_DIR, "_checkpoints", "cp-school-scores.json")
CHECKPOINT_DIR = os.path.join(SCRIPT_DIR, "_checkpoints")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.gaokao.cn/",
}

YEARS = [2023, 2024, 2025]
PAGE_SIZE = 20
DELAY_MIN = 1.2
DELAY_MAX = 2.0
DELAY_BETWEEN_SCHOOLS = 3.0
DELAY_RATELIMITED = 120
MAX_RETRIES = 5
SAVE_EVERY = 5

SKIP_KEYWORDS = [
    "职业", "专科", "艺术", "体育", "传媒", "音乐", "美术",
    "舞蹈", "影视", "戏剧", "戏曲",
]

CSV_FIELDS = [
    "school_name", "school_id", "province", "year",
    "type_name", "batch_name", "enrollment_type",
    "min_score", "min_rank", "avg_score", "max_score",
    "f985", "f211", "nature", "special_group",
]


# ============================================================
# 网络请求
# ============================================================

def delay(lo=DELAY_MIN, hi=DELAY_MAX):
    time.sleep(random.uniform(lo, hi))


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
                    log(f"  Rate limited (attempt {attempt+1}), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                log(f"  Failed after {retries} attempts: {e}")
                return None


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ============================================================
# 学校列表
# ============================================================

def get_school_list():
    log("Fetching school list from linkage.json...")
    data = fetch_json("https://static-data.gaokao.cn/www/2.0/info/linkage.json")
    if not data:
        log("Failed to fetch school list")
        return []

    schools = data.get("data", {}).get("school", [])
    result = []
    for s in schools:
        name = s["name"]
        if any(kw in name for kw in SKIP_KEYWORDS):
            continue
        result.append({"id": str(s["school_id"]), "name": name})

    log(f"Total undergraduate schools: {len(result)}")
    return result


# ============================================================
# 采集
# ============================================================

def fetch_school_scores(school_id, year):
    all_items = []
    page = 1
    while True:
        params = {
            "school_id": school_id,
            "year": year,
            "uri": "apidata/api/gk/score/province",
            "size": PAGE_SIZE,
            "page": page,
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
        delay()

    return all_items


def parse_record(item, school_name, school_id):
    def safe_int(val):
        if val is None or val == "-" or val == "":
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    return {
        "school_name": school_name,
        "school_id": school_id,
        "province": item.get("local_province_name", ""),
        "year": item.get("year", ""),
        "type_name": item.get("local_type_name", ""),
        "batch_name": item.get("local_batch_name", ""),
        "enrollment_type": item.get("zslx_name", ""),
        "min_score": safe_int(item.get("min")),
        "min_rank": safe_int(item.get("min_section")),
        "avg_score": safe_int(item.get("average")),
        "max_score": safe_int(item.get("max")),
        "f985": item.get("f985") == 1,
        "f211": item.get("f211") == 1,
        "nature": item.get("nature_name", ""),
        "special_group": item.get("special_group", ""),
    }


# ============================================================
# 断点续爬
# ============================================================

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"completed": {}, "total_records": 0}


def save_checkpoint(cp):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)


# ============================================================
# 主流程
# ============================================================

def run_crawl(schools, resume=False):
    cp = load_checkpoint() if resume else {"completed": {}, "total_records": 0}

    file_exists = os.path.exists(OUTPUT_FILE) and resume
    fh = open(OUTPUT_FILE, "a" if resume else "w", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
    if not file_exists:
        writer.writeheader()
        fh.flush()

    completed = cp["completed"]
    total_records = cp["total_records"]
    skipped = sum(1 for s in schools if s["id"] in completed)
    if skipped:
        log(f"Skipping {skipped} already completed schools")

    start_time = time.time()
    done_count = 0

    for i, school in enumerate(schools):
        sid = school["id"]
        sname = school["name"]

        if sid in completed:
            continue

        school_records = 0
        for year in YEARS:
            items = fetch_school_scores(sid, year)
            for item in items:
                rec = parse_record(item, sname, sid)
                writer.writerow(rec)
                school_records += 1
            delay()

        fh.flush()
        completed[sid] = {"name": sname, "records": school_records}
        total_records += school_records
        done_count += 1

        elapsed = time.time() - start_time
        total_todo = len(schools) - skipped
        remaining = total_todo - done_count
        rate = done_count / elapsed if elapsed > 0 else 0
        eta = remaining / rate if rate > 0 else 0

        log(f"[{done_count}/{total_todo}] {sname} — {school_records} rec | "
            f"Total: {total_records} | ETA: {eta/60:.0f}min")

        if done_count % SAVE_EVERY == 0:
            save_checkpoint(cp)

        delay(DELAY_BETWEEN_SCHOOLS, DELAY_BETWEEN_SCHOOLS + 1)

    save_checkpoint(cp)
    fh.close()

    elapsed = time.time() - start_time
    log(f"Done! {done_count} schools, {total_records} records in {elapsed/60:.1f} min")
    log(f"Output: {OUTPUT_FILE}")


def show_status():
    cp = load_checkpoint()
    completed = cp.get("completed", {})
    total_records = cp.get("total_records", 0)
    log(f"Completed: {len(completed)} schools, {total_records} records")

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        provinces = set(r["province"] for r in rows if r["province"])
        years = set(r["year"] for r in rows if r["year"])
        types = set(r["type_name"] for r in rows if r["type_name"])
        log(f"CSV rows: {len(rows)}")
        log(f"Provinces: {len(provinces)} ({', '.join(sorted(provinces)[:10])}...)")
        log(f"Years: {sorted(years)}")
        log(f"Types: {sorted(types)}")

        if rows:
            scores = [int(r["min_score"]) for r in rows
                      if r["min_score"] and r["min_score"] != "None"]
            if scores:
                log(f"Score range: {min(scores)} - {max(scores)}")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl school-level admission scores")
    parser.add_argument("--limit", type=int, help="Only process first N schools")
    parser.add_argument("--only", nargs="+", help="Only process these school names")
    parser.add_argument("--status", action="store_true", help="Show crawl progress")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    if args.status:
        show_status()
        sys.exit(0)

    schools = get_school_list()
    if not schools:
        sys.exit(1)

    if args.only:
        schools = [s for s in schools if any(kw in s["name"] for kw in args.only)]
        log(f"Filtered to {len(schools)} schools: {[s['name'] for s in schools]}")

    if args.limit:
        schools = schools[:args.limit]

    log(f"Starting crawl for {len(schools)} schools...")
    run_crawl(schools, resume=args.resume)
