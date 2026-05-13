#!/usr/bin/env python3
"""
专业深度评估统一执行脚本
使用 Claude Code CLI (claude -p) + open-websearch MCP 逐个生成专业评估报告

用法:
  python3 run_major_eval.py 06           # 跑历史学（06）
  python3 run_major_eval.py 06 --retry   # 重跑历史学中失败的专业
  python3 run_major_eval.py 06 --only 060101 060102  # 只跑指定专业
  python3 run_major_eval.py --status     # 查看所有门类进度总览
"""

import csv
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from check_reports import MIN_CHARS as REPORT_MIN_CHARS
from check_reports import check_report

# ── 门类映射 ──────────────────────────────────────────
CATEGORY_MAP = {
    "01": "哲学", "02": "经济学", "03": "法学", "04": "教育学",
    "05": "文学", "06": "历史学", "07": "理学", "08": "工学",
    "09": "农学", "10": "医学", "11": "军事学", "12": "管理学",
    "13": "艺术学", "14": "交叉学科",
}

from typing import Optional, Set

# ── 固定路径 ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "本科专业目录_2025.csv"
PROMPT_PATH = BASE_DIR / "跑专业的提示词-v2.txt"
OUTPUT_DIR = BASE_DIR / "data" / "专业评估报告"

DELAY_SECONDS = 5
TIMEOUT_SECONDS = 1800  # 30 分钟，LLM 搜索+生成需要较长时间

# ── 搜索指令 ──────────────────────────────────────────
SEARCH_INSTRUCTION = """\

## 研究执行要求

在生成报告之前，你必须使用 open-websearch MCP 工具进行至少 4 轮网络搜索，覆盖以下数据维度：

1. **就业与薪酬数据**：搜索"[专业名称] 就业率 薪酬 起薪 2025 2024 2023"
2. **院校与排名数据**：搜索"[专业名称] 大学排名 学科评估 院校推荐"
3. **行业与产业数据**：搜索"[专业名称] 行业前景 市场规模 增长率"
4. **职业发展数据**：搜索"[专业名称] 职业路径 准入考试 通过率 深造率"

搜索策略：
- 优先使用 duckduckgo 引擎（engines: ["duckduckgo"]）
- **必须使用 searchMode: "request"**，禁止使用 playwright 或 auto 模式，避免弹出浏览器窗口
- 若 duckduckgo 返回结果不足，可尝试 bing 或 baidu 引擎
- 对有价值的搜索结果 URL，使用 fetchWebContent 抓取详细内容（同样禁止 playwright 模式）
- 若某个维度搜索无结果，可调整关键词重试一次

所有搜索获得的数据必须标注来源，无法确认的数据标注 [待核实]。

## 重要：输出要求

你必须直接输出完整的 8 个模块报告内容（Markdown 格式），不要只输出摘要。
不要说"报告已保存"或"报告已生成"，直接输出报告全文。
从"## 模块一：专业画像与总评"开始，到"模块八：原始数据支撑"结束，完整输出每一个模块。

"""
# ──────────────────────────────────────────────────────


def progress_file(category_code: str) -> Path:
    short = CATEGORY_MAP.get(category_code, category_code)
    return OUTPUT_DIR / f"_progress_{short}.json"


def load_majors(category_code: str, only_codes: Optional[Set[str]] = None):
    majors = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["学科门类代码"] != category_code:
                continue
            if only_codes and row["专业代码"] not in only_codes:
                continue
            majors.append({
                "code": row["专业代码"],
                "name": row["专业名称"],
                "category": row["学科门类"],
                "sub": row["专业类"],
            })
    return majors


def load_template():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(template, major):
    prompt = template.replace(
        "[专业编号：XXXXX    专业名称：XXX]",
        f"[专业编号：{major['code']}    专业名称：{major['name']}]",
    )
    prompt = SEARCH_INSTRUCTION + "\n---\n\n" + prompt
    prompt = prompt.replace("[专业名称]", major["name"])
    return prompt


def load_progress(pfile: Path) -> set:
    if pfile.exists():
        with open(pfile, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(pfile: Path, done: set):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=2)


def run_one(prompt):
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


def save_report(text, major):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{major['code']}_{major['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def quality_allows_completion(result: dict) -> bool:
    """Only PASS/WARN reports can be marked complete."""
    return result.get("status") in {"PASS", "WARN"}


def format_quality_issues(result: dict) -> str:
    issues = []
    issues.extend(result.get("errors", []))
    issues.extend(result.get("warnings", []))
    return "；".join(issues) if issues else "无"


def validate_generated_report(path: Path) -> dict:
    return check_report(path, min_chars=REPORT_MIN_CHARS)


def archive_failed_report(path: Path) -> Path:
    failed_dir = OUTPUT_DIR / "_failed"
    failed_dir.mkdir(parents=True, exist_ok=True)
    failed_path = failed_dir / path.name
    path.replace(failed_path)
    return failed_path


def show_status():
    """显示所有门类的完成进度"""
    print("=" * 60)
    print("  专业深度评估 — 全门类进度总览")
    print("=" * 60)
    for code, name in CATEGORY_MAP.items():
        pfile = progress_file(code)
        done = load_progress(pfile) if pfile.exists() else set()
        # 统计该门类专业总数
        total = 0
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row["学科门类代码"] == code:
                    total += 1
        if total == 0:
            continue
        pct = len(done) / total * 100 if total else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        status = "✓ 完成" if len(done) == total else f"{len(done)}/{total}"
        print(f"  {code} {name:　<4s} [{bar}] {status} ({pct:.0f}%)")
    print("=" * 60)


def run_category(category_code: str, only_codes: Optional[Set[str]] = None, retry_mode: bool = False):
    cat_name = CATEGORY_MAP.get(category_code, "未知")
    pfile = progress_file(category_code)

    # 检查 claude CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("错误: 未找到 claude 命令，请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)

    if not PROMPT_PATH.exists():
        print(f"错误: 提示词文件不存在: {PROMPT_PATH}")
        sys.exit(1)

    template = load_template()
    majors = load_majors(category_code, only_codes)
    done = load_progress(pfile)

    if retry_mode:
        # 重试模式：找出有报告文件但内容过短、或没有报告文件的专业
        retry_list = []
        for m in majors:
            rpath = OUTPUT_DIR / f"{m['code']}_{m['name']}.md"
            if m["code"] not in done or not rpath.exists() or rpath.stat().st_size < 1000:
                retry_list.append(m)
        pending = retry_list
    else:
        pending = [m for m in majors if m["code"] not in done]

    print("=" * 60)
    print(f"  {cat_name}门类（{category_code}）专业深度评估")
    print(f"  总专业数: {len(majors)}, 已完成: {len(done)}, 待评估: {len(pending)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  调用间隔: {DELAY_SECONDS}s")
    print("=" * 60)

    if not pending:
        print(f"所有{cat_name}类专业已完成评估！")
        return

    print("\n待评估专业：")
    for i, m in enumerate(pending, 1):
        print(f"  [ ] {i}. {m['code']} {m['name']}")
    print()

    ok, fail = 0, 0
    for i, major in enumerate(pending, 1):
        tag = f"{major['sub']}/{major['name']}（{major['code']}）"
        print(f"[{i}/{len(pending)}] 正在评估: {tag}", flush=True)

        try:
            prompt = build_prompt(template, major)
            text = run_one(prompt)

            if not text or len(text.strip()) < 500:
                raise RuntimeError(f"生成内容过短（{len(text.strip())}字符），可能失败")

            path = save_report(text, major)
            quality = validate_generated_report(path)
            quality_status = quality["status"]
            if not quality_allows_completion(quality):
                failed_path = archive_failed_report(path)
                raise RuntimeError(
                    f"质检失败 [{quality_status}]，已移至 _failed/{failed_path.name}: "
                    f"{format_quality_issues(quality)}"
                )

            done.add(major["code"])
            save_progress(pfile, done)
            ok += 1
            if quality_status == "WARN":
                print(f"  ⚠ 质检警告: {format_quality_issues(quality)}")
            print(f"  ✓ 成功 -> {path.name} ({len(text)} 字, 质检 {quality_status})")
        except Exception as e:
            fail += 1
            print(f"  ✗ 失败: {e}")

        print(f"  进度: 成功 {ok}, 失败 {fail}, 剩余 {len(pending) - i}")

        if i < len(pending):
            print(f"  等待 {DELAY_SECONDS}s...")
            time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 60)
    print(f"  {cat_name}门类评估完成!")
    print(f"  成功: {ok}, 失败: {fail}, 之前完成: {len(majors) - len(pending)}")
    print(f"  总完成: {len(done)}/{len(majors)}")
    print("=" * 60)

    print("\n各专业完成状态：")
    for m in majors:
        status = "✓" if m["code"] in done else "✗"
        path = OUTPUT_DIR / f"{m['code']}_{m['name']}.md"
        failed_path = OUTPUT_DIR / "_failed" / f"{m['code']}_{m['name']}.md"
        if path.exists():
            size = f"({path.stat().st_size}B)"
        elif failed_path.exists():
            size = f"(质检失败: _failed/{failed_path.name})"
        else:
            size = ""
        print(f"  [{status}] {m['code']} {m['name']} {size}")


def main():
    args = sys.argv[1:]

    if not args:
        print("用法: python3 run_major_eval.py <门类代码> [--retry] [--only 代码1 代码2 ...]")
        print("      python3 run_major_eval.py --status")
        print()
        print("门类代码:")
        for code, name in CATEGORY_MAP.items():
            print(f"  {code}  {name}")
        sys.exit(0)

    if args[0] == "--status":
        show_status()
        return

    category_code = args[0]
    if category_code not in CATEGORY_MAP:
        print(f"错误: 未知门类代码 '{category_code}'")
        sys.exit(1)

    retry_mode = "--retry" in args
    only_codes = None
    if "--only" in args:
        idx = args.index("--only")
        only_codes = set(args[idx + 1:])

    run_category(category_code, only_codes, retry_mode)


if __name__ == "__main__":
    main()
