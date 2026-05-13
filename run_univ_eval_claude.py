#!/usr/bin/env python3
"""
大学深度评估执行脚本（Claude Code CLI 版）
使用 claude -p CLI + open-websearch MCP（request 模式，不弹浏览器）

用法:
  python3 run_univ_eval_claude.py 广东省                    # 跑广东省所有本科院校
  python3 run_univ_eval_claude.py 广东省 --public-only      # 只跑公办院校
  python3 run_univ_eval_claude.py 广东省 --limit 3          # 只跑前 3 所（测试用）
  python3 run_univ_eval_claude.py 广东省 --retry            # 重跑失败/质检不过的
  python3 run_univ_eval_claude.py 广东省 --only 中山大学 华南理工大学
  python3 run_univ_eval_claude.py --status                  # 查看各省进度总览
  python3 run_univ_eval_claude.py --list 广东省             # 列出该省本科院校
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Set

# ── 固定路径 ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "高等院校名单.csv"
PROMPT_PATH = BASE_DIR / "跑大学提示词-v3.txt"
OUTPUT_DIR = BASE_DIR / "data" / "大学评估报告"

DELAY_SECONDS = int(os.environ.get("DELAY_SECONDS", "5"))
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "2700"))  # 45 分钟
MIN_CJK_CHARS = 5000

REQUIRED_MODULES = [
    "模块一：学术资本",
    "模块二：生源竞争力",
    "模块三：毕业生价值实现",
    "模块四",
    "模块五",
    "模块六",
    "模块七",
    "模块八：原始数据汇总",
]

# ── 搜索指令（强制 request 模式，不弹浏览器）──────────
SEARCH_INSTRUCTION = """\

## 研究执行要求

本提示词定义了 7 组搜索任务（搜索组 A-G），覆盖需要实时数据验证的模块。
请使用 open-websearch MCP 工具逐一执行搜索。

### 搜索规则（严格遵守）

1. **搜索模式必须使用 `searchMode: "request"`**，严禁使用 `playwright` 或 `auto`，避免弹出浏览器窗口。
2. 优先使用 duckduckgo 引擎：`engines: ["duckduckgo"]`
3. 若 duckduckgo 返回结果不足，可用 baidu：`engines: ["baidu"]`
4. 对有价值的搜索结果 URL，使用 `fetchWebContent` 抓取详细内容（`readability: true`）
5. 若某个搜索组无结果，可调整关键词重试一次
6. **不要打开任何浏览器窗口**，所有操作必须通过 API 请求完成

### 搜索执行顺序

1. 搜索组 A（录取分数线）— 数据量最大，优先执行
2. 搜索组 C（就业质量报告）+ 搜索组 D（薪酬）— 可合并检索
3. 搜索组 B（保送生）+ 搜索组 E（校园体验）— 按需检索
4. 搜索组 F（风险点）+ 搜索组 G（品牌数据）— 最后补充

### 调用示例

搜索：使用 `search` 工具，参数示例：
```json
{"query": "中山大学 2025 录取分数线 各省", "engines": ["duckduckgo"], "searchMode": "request"}
```

抓取网页内容：使用 `fetchWebContent` 工具，参数示例：
```json
{"url": "https://example.com/page", "readability": true}
```

所有搜索获得的数据必须标注来源，无法确认的数据标注 [待核实]。

## 重要：输出要求

你必须直接输出完整的 8 个模块报告内容（Markdown 格式），不要只输出摘要。
不要说"报告已保存"或"报告已生成"，直接输出报告全文。
从"## 模块一：学术资本"开始，到"## 模块八：原始数据汇总"结束，完整输出每一个模块。
不要输出"内部评分标尺"部分。
报告正文不少于 5000 个中文字符；每个模块都要有表格、关键数据、简短分析，禁止压缩成提纲。

"""

# ── 省份列表 ──────────────────────────────────────────
ALL_PROVINCES = [
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
    "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
    "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
    "海南省", "重庆市", "四川省", "贵州省", "云南省",
    "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
    "新疆维吾尔自治区",
]


def load_universities(
    province: str,
    public_only: bool = False,
    only_names: Optional[Set[str]] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """从 CSV 读取指定省份的本科院校列表"""
    univs = []
    current_province = ""

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row or not row[0].strip():
                continue
            if "所）" in row[0] or "所)" in row[0]:
                current_province = row[0].split("（")[0].split("(")[0]
                continue
            if row[0].strip() == "序号":
                continue

            if not current_province.startswith(province):
                continue
            if len(row) < 6 or row[5].strip() != "本科":
                continue

            name = row[1].strip()
            remark = row[6].strip() if len(row) > 6 else ""

            if public_only and "民办" in remark:
                continue
            if only_names and name not in only_names:
                continue

            univs.append({
                "name": name,
                "code": row[2].strip(),
                "authority": row[3].strip(),
                "city": row[4].strip(),
                "remark": remark,
            })

    if limit:
        univs = univs[:limit]
    return univs


def load_template():
    if not PROMPT_PATH.exists():
        # fallback to v2
        fallback = BASE_DIR / "跑大学提示词-v2.txt"
        if not fallback.exists():
            print(f"错误: 提示词文件不存在: {PROMPT_PATH}")
            sys.exit(1)
        print(f"提示: 未找到 v3 提示词，使用 {fallback.name}")
        with open(fallback, "r", encoding="utf-8") as f:
            return f.read()
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(template: str, univ: dict) -> str:
    prompt = template.replace(
        "[大学名称：XXX]",
        f"[大学名称：{univ['name']}]",
    )
    prompt = prompt.replace(
        '[专业1、专业2 等，无则填"无特定关注"]',
        "[无特定关注]",
    )
    prompt = prompt.replace("[大学名称]", univ["name"])
    prompt = prompt.replace("[城市名称]", univ["city"])

    return SEARCH_INSTRUCTION + "\n---\n\n" + prompt


def progress_file(province: str) -> Path:
    short = province.replace("省", "").replace("市", "").replace("自治区", "")[:6]
    return OUTPUT_DIR / f"_progress_claude_{short}.json"


def load_progress(pfile: Path) -> set:
    if pfile.exists():
        with open(pfile, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(pfile: Path, done: set):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=2)


def run_one(prompt: str) -> str:
    """调用 claude -p CLI 生成报告"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(prompt)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["claude", "-p", "--output-format", "text", "--dangerously-skip-permissions"],
            stdin=open(tmp_path, "r", encoding="utf-8"),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
        return result.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def run_one_with_retry(prompt: str, max_retries: int = 2) -> tuple[str, int]:
    """带重试的生成"""
    attempts = 0
    while True:
        try:
            text = run_one(prompt)
            return text, attempts
        except Exception:
            if attempts >= max_retries:
                raise
            attempts += 1
            print(f"    重试第 {attempts} 次...", flush=True)
            time.sleep(DELAY_SECONDS)


def generate_and_validate(prompt: str) -> tuple[str, dict]:
    """生成报告 + 质检"""
    text, _ = run_one_with_retry(prompt)
    quality = validate_report_text(text)
    return text, quality


# ── 质检 ──────────────────────────────────────────────

def count_cjk_chars(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text))


def validate_report_text(text: str) -> dict:
    result = {
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "stats": {
            "字符数": len(text),
            "中文字符数": count_cjk_chars(text),
            "数据表格": text.count("| ---") + text.count("|---") + text.count("|------|"),
        },
    }

    cjk_count = result["stats"]["中文字符数"]
    if cjk_count < MIN_CJK_CHARS:
        result["errors"].append(f"中文正文过短: {cjk_count} 字（要求 ≥ {MIN_CJK_CHARS}）")

    missing_modules = [m for m in REQUIRED_MODULES if m not in text]
    if missing_modules:
        result["errors"].append(f"缺少模块: {', '.join(missing_modules)}")

    if "[X]" in text or "[XXX]" in text:
        result["errors"].append("存在未填充占位符")

    if result["stats"]["数据表格"] < 8:
        result["warnings"].append(f"数据表格偏少: {result['stats']['数据表格']} 个（建议 ≥ 8）")

    if result["errors"]:
        result["status"] = "FAIL"
    elif len(result["warnings"]) >= 3:
        result["status"] = "WARN"

    return result


def quality_allows_completion(result: dict) -> bool:
    return result.get("status") in {"PASS", "WARN"}


def format_quality_issues(result: dict) -> str:
    issues = result.get("errors", []) + result.get("warnings", [])
    return "；".join(issues) if issues else "无"


def save_report(text: str, univ: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{univ['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def archive_failed_report(path: Path) -> Path:
    failed_dir = OUTPUT_DIR / "_failed_claude"
    failed_dir.mkdir(parents=True, exist_ok=True)
    failed_path = failed_dir / path.name
    path.replace(failed_path)
    return failed_path


# ── 展示 ──────────────────────────────────────────────

def show_status():
    print("=" * 65)
    print("  大学深度评估（Claude CLI 版）— 各省进度总览")
    print("=" * 65)

    total_all, done_all = 0, 0
    for prov in ALL_PROVINCES:
        pfile = progress_file(prov)
        done = load_progress(pfile) if pfile.exists() else set()
        univs = load_universities(prov)
        total = len(univs)
        if total == 0:
            continue
        total_all += total
        done_count = len(done & {u["name"] for u in univs})
        done_all += done_count
        pct = done_count / total * 100 if total else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        status = "✓ 完成" if done_count == total else f"{done_count}/{total}"
        print(f"  {prov:　<6s} [{bar}] {status} ({pct:.0f}%)")

    pct_all = done_all / total_all * 100 if total_all else 0
    print("=" * 65)
    print(f"  全国总计: {done_all}/{total_all} ({pct_all:.1f}%)")
    print("=" * 65)


def list_universities(province: str):
    univs = load_universities(province)
    if not univs:
        print(f"未找到 {province} 的本科院校")
        return

    print(f"\n{province} 本科院校（共 {len(univs)} 所）")
    print("-" * 55)
    public = [u for u in univs if "民办" not in u["remark"] and "中外" not in u["remark"]]
    private = [u for u in univs if "民办" in u["remark"]]
    joint = [u for u in univs if "中外" in u["remark"]]

    if public:
        print(f"\n  公办（{len(public)} 所）：")
        for u in public:
            print(f"    {u['name']}（{u['city']}）")
    if private:
        print(f"\n  民办（{len(private)} 所）：")
        for u in private:
            print(f"    {u['name']}（{u['city']}）")
    if joint:
        print(f"\n  中外/港澳合作（{len(joint)} 所）：")
        for u in joint:
            print(f"    {u['name']}（{u['city']}）")
    print()


# ── 主流程 ────────────────────────────────────────────

def run_province(
    province: str,
    public_only: bool = False,
    only_names: Optional[Set[str]] = None,
    limit: Optional[int] = None,
    retry_mode: bool = False,
):
    pfile = progress_file(province)

    # 检查 claude CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("错误: 未找到 claude 命令，请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)

    template = load_template()
    univs = load_universities(province, public_only, only_names, limit)
    done = load_progress(pfile)

    if retry_mode:
        retry_list = []
        for u in univs:
            rpath = OUTPUT_DIR / f"{u['name']}.md"
            if (
                u["name"] not in done
                or not rpath.exists()
                or rpath.stat().st_size < 2000
            ):
                retry_list.append(u)
        pending = retry_list
    else:
        pending = [u for u in univs if u["name"] not in done]

    filter_tag = ""
    if public_only:
        filter_tag += "（仅公办）"
    if limit:
        filter_tag += f"（前 {limit} 所）"

    print("=" * 65)
    print(f"  {province} 大学深度评估{filter_tag} [Claude CLI]")
    done_count = len(done & {u["name"] for u in univs})
    print(f"  院校总数: {len(univs)}, 已完成: {done_count}, 待评估: {len(pending)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  调用间隔: {DELAY_SECONDS}s, 超时: {TIMEOUT_SECONDS}s")
    print(f"  提示词: {PROMPT_PATH.name}")
    print(f"  搜索模式: request（不弹浏览器）")
    print("=" * 65)

    if not pending:
        print("所有院校已完成评估！")
        return

    print(f"\n待评估院校：")
    for i, u in enumerate(pending, 1):
        tag = f" [{u['remark']}]" if u["remark"] else ""
        print(f"  [ ] {i}. {u['name']}（{u['city']}）{tag}")
    print()

    ok, fail = 0, 0
    for i, univ in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] 正在评估: {univ['name']}（{univ['city']}）", flush=True)

        try:
            prompt = build_prompt(template, univ)
            text, quality = generate_and_validate(prompt)

            if not text or len(text.strip()) < 500:
                raise RuntimeError(f"生成内容过短（{len(text.strip())}字符），可能失败")

            path = save_report(text, univ)
            quality_status = quality["status"]

            if not quality_allows_completion(quality):
                # 质检失败但仍保存报告，移到 _failed_claude 目录
                failed_path = archive_failed_report(path)
                fail += 1
                print(f"  ✗ 质检失败 [{quality_status}]: {format_quality_issues(quality)}")
                print(f"    报告已移至 _failed_claude/{failed_path.name}")
            else:
                done.add(univ["name"])
                save_progress(pfile, done)
                ok += 1
                stats = quality.get("stats", {})
                cjk_count = stats.get("中文字符数", "?")
                if quality_status == "WARN":
                    print(f"  ⚠ 质检警告: {format_quality_issues(quality)}")
                print(f"  ✓ 成功 -> {path.name} ({cjk_count} 中文字, {len(text)} 字符, 质检 {quality_status})")
        except Exception as e:
            fail += 1
            print(f"  ✗ 失败: {e}")

        print(f"  进度: 成功 {ok}, 失败 {fail}, 剩余 {len(pending) - i}")

        if i < len(pending):
            print(f"  等待 {DELAY_SECONDS}s...")
            time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 65)
    print(f"  {province} 评估完成!")
    print(f"  成功: {ok}, 失败: {fail}, 之前完成: {len(univs) - len(pending)}")
    done_in_scope = len(done & {u["name"] for u in univs})
    print(f"  总完成: {done_in_scope}/{len(univs)}")
    print("=" * 65)

    print("\n各院校完成状态：")
    for u in univs:
        status = "✓" if u["name"] in done else "✗"
        path = OUTPUT_DIR / f"{u['name']}.md"
        failed_path = OUTPUT_DIR / "_failed_claude" / f"{u['name']}.md"
        if path.exists():
            size = f"({path.stat().st_size}B)"
        elif failed_path.exists():
            size = f"(质检失败: _failed_claude/{failed_path.name})"
        else:
            size = ""
        print(f"  [{status}] {u['name']}（{u['city']}）{size}")


def match_province(arg: str) -> str:
    for prov in ALL_PROVINCES:
        if prov.startswith(arg) or arg in prov:
            return prov
    for prov in ALL_PROVINCES:
        if prov.replace("省", "").replace("市", "") == arg:
            return prov
    return ""


def main():
    args = sys.argv[1:]

    if not args:
        print("用法:")
        print("  python3 run_univ_eval_claude.py <省份> [--public-only] [--limit N] [--retry]")
        print("  python3 run_univ_eval_claude.py <省份> --only <大学名1> <大学名2>")
        print("  python3 run_univ_eval_claude.py --status")
        print("  python3 run_univ_eval_claude.py --list <省份>")
        print()
        print("省份示例: 广东省, 北京, 上海, 四川")
        print()
        print("选项:")
        print("  --public-only   只跑公办院校（排除民办）")
        print("  --limit N       只跑前 N 所（测试用）")
        print("  --retry         重跑失败/质检不过的报告")
        print("  --only          只跑指定的大学")
        print("  --status        查看各省进度")
        print("  --list          列出该省本科院校")
        print()
        print("特点:")
        print("  - 使用 claude -p CLI + open-websearch MCP")
        print("  - 搜索模式: request（不弹浏览器）")
        print("  - 自动质检 + 扩写修复")
        print("  - 进度文件: _progress_claude_*.json")
        sys.exit(0)

    if args[0] == "--status":
        show_status()
        return

    if args[0] == "--list":
        if len(args) < 2:
            print("用法: python3 run_univ_eval_claude.py --list <省份>")
            sys.exit(1)
        province = match_province(args[1])
        if not province:
            print(f"错误: 未匹配到省份 '{args[1]}'")
            print(f"可选: {', '.join(ALL_PROVINCES)}")
            sys.exit(1)
        list_universities(province)
        return

    province = match_province(args[0])
    if not province:
        print(f"错误: 未匹配到省份 '{args[0]}'")
        print(f"可选: {', '.join(ALL_PROVINCES)}")
        sys.exit(1)

    public_only = "--public-only" in args
    retry_mode = "--retry" in args
    limit = None
    only_names = None

    if "--limit" in args:
        idx = args.index("--limit")
        try:
            limit = int(args[idx + 1])
        except (IndexError, ValueError):
            print("错误: --limit 需要一个数字参数")
            sys.exit(1)

    if "--only" in args:
        idx = args.index("--only")
        only_names = set(args[idx + 1:])

    run_province(province, public_only, only_names, limit, retry_mode)


if __name__ == "__main__":
    main()
