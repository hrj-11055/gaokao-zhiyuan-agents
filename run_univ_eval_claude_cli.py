#!/usr/bin/env python3
"""
大学深度评估执行脚本（Claude Code CLI 版）
使用 claude -p CLI + WebSearch/MiniMax MCP 搜索生成大学评估报告

必须在终端直接运行，不能在 Claude Code 会话中嵌套调用。

用法:
  python3 run_univ_eval_claude_cli.py 广东省                    # 跑广东省所有本科院校
  python3 run_univ_eval_claude_cli.py 广东省 --public-only      # 只跑公办院校
  python3 run_univ_eval_claude_cli.py 广东省 --limit 3          # 只跑前 3 所（测试用）
  python3 run_univ_eval_claude_cli.py 广东省 --retry            # 重跑失败的
  python3 run_univ_eval_claude_cli.py 广东省 --only 中山大学 华南理工大学
  python3 run_univ_eval_claude_cli.py --status                  # 查看各省进度总览
  python3 run_univ_eval_claude_cli.py --list 广东省             # 列出该省本科院校
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Set

# ── 固定路径 ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "高等院校名单.csv"
PROMPT_PATH = BASE_DIR / "跑大学提示词-v3.txt"
OUTPUT_DIR = BASE_DIR / "data" / "大学评估报告"

DELAY_SECONDS = int(os.environ.get("DELAY_SECONDS", "8"))
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "1800"))  # 30 分钟

MIN_CJK_CHARS = 2000

REQUIRED_MODULES = []

# CLI 调用配置
CLAUDE_CLI = os.environ.get("CLAUDE_CLI", "claude")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

# ── 搜索指令（注入到 prompt 前）──────────────────────
SEARCH_INSTRUCTION = """\

## 研究执行要求（严格遵守）

你必须使用搜索工具在互联网上搜索真实数据。最少执行 4 轮搜索后再撰写报告。

### 可用搜索工具

**主力搜索**: WebSearch（Anthropic 内置搜索工具）
- 直接调用即可，无需特殊参数
- 适合搜索录取分数线、学科评估、就业报告等

**辅助搜索**: mcp__MiniMax__web_search（中文区域优化）
- 当 WebSearch 结果不足时使用
- 调用参数: {"query": "搜索关键词"}

### 搜索执行计划（必须全部执行）

**第 1 轮 - 录取分数线**（优先级最高）:
- 搜索: "{大学名称} 2025 录取分数线 各省"
- 搜索: "{大学名称} 2024 录取分数线 各省"

**第 2 轮 - 学科与学术**:
- 搜索: "{大学名称} 学科评估 A类"
- 搜索: "{大学名称} 重点实验室 院士"

**第 3 轮 - 就业与深造**:
- 搜索: "{大学名称} 就业质量报告 2025"
- 搜索: "{大学名称} 毕业生薪酬 就业去向"

**第 4 轮 - 校园与风险**:
- 搜索: "{大学名称} 校园生活 宿舍 食堂 评价"
- 搜索: "{大学名称} 负面新闻 风险事件 争议"

### 数据处理规则

1. 所有数据必须标注来源
2. 搜索未找到的数据标注"未检索到"，不要编造数字
3. 无法确认的数据标注 [待核实]
4. 优先使用 2025 年数据，其次 2024 年数据

## 重要：输出要求

直接输出完整的深度研究报告（Markdown 格式），不要只输出摘要。
不要说"报告已保存"或"报告已生成"，直接输出报告全文。
从"# 大学深度评估"或第一个章节标题开始输出。
报告正文不少于 8000 个中文字符。
每个章节都要有数据表格、关键数据、分析解读，禁止压缩成提纲。

"""


def get_existing_reports() -> set:
    """读取已存在的报告文件名"""
    existing = set()
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("*.md"):
            existing.add(f.stem)
    return existing


def load_universities(
    province: str,
    public_only: bool = False,
    only_names: Optional[Set[str]] = None,
    limit: Optional[int] = None,
    existing: Optional[set] = None,
) -> list[dict]:
    """从 CSV 读取指定省份的本科院校列表"""
    if existing is None:
        existing = set()

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
            if name in existing:
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
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(template: str, univ: dict, focus_majors: str = "无特定关注") -> str:
    prompt = template.replace(
        "[大学名称：XXX]",
        f"[大学名称：{univ['name']}]",
    )
    prompt = prompt.replace(
        '[专业1、专业2 等，无则填"无特定关注"]',
        f"[{focus_majors}]",
    )
    prompt = prompt.replace("[大学名称]", univ["name"])
    prompt = prompt.replace("[城市名称]", univ["city"])

    search_block = SEARCH_INSTRUCTION.replace("{大学名称}", univ["name"])

    return search_block + "\n---\n\n" + prompt


def progress_file(province: str) -> Path:
    short = province.replace("省", "").replace("市", "").replace("自治区", "")[:6]
    return OUTPUT_DIR / f"_progress_claude_cli_{short}.json"


def load_progress(pfile: Path, existing: Optional[set] = None) -> set:
    done = set()
    if pfile.exists():
        with open(pfile, "r", encoding="utf-8") as f:
            try:
                done = set(json.load(f))
            except json.JSONDecodeError:
                pass
    
    if existing:
        # 同步磁盘上已存在的报告到进度文件
        done.update(existing)
    return done


def save_progress(pfile: Path, done: set):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # 只保存字符串列表
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump(sorted(list(done)), f, ensure_ascii=False, indent=2)


def run_one(prompt: str) -> str:
    """调用 claude -p CLI 生成报告"""
    cmd = [
        CLAUDE_CLI, "-p",
        "--output-format", "text",
        "--dangerously-skip-permissions",
        "--model", CLAUDE_MODEL,
    ]

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        stderr_msg = result.stderr.strip() if result.stderr else f"exit code {result.returncode}"
        raise RuntimeError(f"claude CLI 失败: {stderr_msg}")

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("claude CLI 返回空内容")

    return output


def save_report(text: str, univ: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{univ['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


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
            "数据表格": len(re.findall(r'\|[\s\-:]+\|[\s\-:|]+', text)),
        },
    }

    cjk_count = result["stats"]["中文字符数"]
    if cjk_count < MIN_CJK_CHARS:
        result["errors"].append(f"中文正文过短: {cjk_count} 字（要求 >= {MIN_CJK_CHARS}）")

    if "[X]" in text or "[XXX]" in text or "[大学名称：XXX]" in text:
        result["errors"].append("存在未填充占位符")

    if result["stats"]["数据表格"] < 3:
        result["warnings"].append(f"数据表格偏少: {result['stats']['数据表格']} 个")

    if result["errors"]:
        result["status"] = "FAIL"
    elif len(result["warnings"]) >= 3:
        result["status"] = "WARN"

    return result


def validate_generated_report(path: Path) -> dict:
    try:
        return validate_report_text(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"status": "FAIL", "errors": [f"文件读取失败: {e}"], "warnings": [], "stats": {}}


def quality_allows_completion(result: dict) -> bool:
    return result.get("status") in {"PASS", "WARN"}


def format_quality_issues(result: dict) -> str:
    issues = []
    issues.extend(result.get("errors", []))
    issues.extend(result.get("warnings", []))
    return "；".join(issues) if issues else "无"


ALL_PROVINCES = [
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
    "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
    "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
    "海南省", "重庆市", "四川省", "贵州省", "云南省",
    "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
    "新疆维吾尔自治区",
]


def show_status():
    print("=" * 65)
    print("  大学深度评估（Claude CLI 版）— 各省进度总览")
    print("=" * 65)

    existing = get_existing_reports()
    total_all, done_all = 0, 0
    for prov in ALL_PROVINCES:
        pfile = progress_file(prov)
        univs = load_universities(prov)
        total = len(univs)
        if total == 0:
            continue
        
        # 统计该省已完成的院校（存在报告文件 或 在进度文件中）
        univ_names = {u["name"] for u in univs}
        done_in_pfile = load_progress(pfile)
        done_count = len((done_in_pfile | existing) & univ_names)
        
        total_all += total
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
        subprocess.run(
            [CLAUDE_CLI, "--version"],
            capture_output=True,
            timeout=10,
        )
    except FileNotFoundError:
        print(f"错误: 找不到 {CLAUDE_CLI} 命令")
        print("  请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)
    except Exception as e:
        print(f"警告: 无法检查 claude CLI 版本: {e}")

    if not PROMPT_PATH.exists():
        print(f"错误: 提示词文件不存在: {PROMPT_PATH}")
        sys.exit(1)

    template = load_template()
    existing = get_existing_reports()
    univs = load_universities(province, public_only, only_names, limit, existing)
    
    # 加载进度并同步磁盘上已有的报告
    done = load_progress(pfile, existing)
    save_progress(pfile, done)

    if retry_mode:
        retry_list = []
        for u in univs:
            rpath = OUTPUT_DIR / f"{u['name']}.md"
            if (
                u["name"] not in done
                or not rpath.exists()
                or rpath.stat().st_size < 2000
                or not quality_allows_completion(validate_generated_report(rpath))
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
    print(f"  {province} 大学深度评估{filter_tag} [Claude CLI {CLAUDE_MODEL}]")
    done_count = len(done & {u["name"] for u in univs})
    print(f"  院校总数: {len(univs)}, 已完成: {done_count}, 待评估: {len(pending)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  调用间隔: {DELAY_SECONDS}s, 超时: {TIMEOUT_SECONDS}s")
    print(f"  提示词: {PROMPT_PATH.name}")
    print(f"  搜索工具: WebSearch + MiniMax")
    print("=" * 65)

    if not pending:
        print(f"\n所有院校已完成评估！")
        return

    print(f"\n待评估院校：")
    for i, u in enumerate(pending, 1):
        tag = ""
        if u["remark"]:
            tag = f" [{u['remark']}]"
        print(f"  [ ] {i}. {u['name']}（{u['city']}）{tag}")
    print()

    ok, fail = 0, 0
    for i, univ in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] 正在评估: {univ['name']}（{univ['city']}）", flush=True)

        try:
            prompt = build_prompt(template, univ)
            text = run_one(prompt)

            if not text or len(text.strip()) < 500:
                raise RuntimeError(f"生成内容过短（{len(text.strip())}字符），可能失败")

            path = save_report(text, univ)
            quality = validate_report_text(text)

            if not quality_allows_completion(quality):
                raise RuntimeError(
                    f"质检未通过 [{quality['status']}]: {format_quality_issues(quality)}"
                )

            done.add(univ["name"])
            save_progress(pfile, done)
            ok += 1
            stats = quality.get("stats", {})
            cjk_count = stats.get("中文字符数", "?")
            quality_status = quality["status"]
            if quality_status == "WARN":
                print(f"  ⚠ 质检警告: {format_quality_issues(quality)}")
            print(f"  ✓ 成功 -> {path.name} ({cjk_count} 中文字, 质检 {quality_status})")

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
        if path.exists():
            size = f"({path.stat().st_size // 1024}KB)"
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
        print("  python3 run_univ_eval_claude_cli.py <省份> [--public-only] [--limit N] [--retry]")
        print("  python3 run_univ_eval_claude_cli.py <省份> --only <大学名1> <大学名2>")
        print("  python3 run_univ_eval_claude_cli.py --status")
        print("  python3 run_univ_eval_claude_cli.py --list <省份>")
        print()
        print("环境变量:")
        print("  CLAUDE_CLI       claude 命令路径（默认: claude）")
        print("  CLAUDE_MODEL     模型名称（默认: claude-sonnet-4-6）")
        print("  TIMEOUT_SECONDS  每所院校超时（默认: 1800）")
        print("  DELAY_SECONDS    调用间隔（默认: 8）")
        print()
        print("依赖:")
        print("  Claude Code CLI（claude 命令）")
        sys.exit(0)

    if args[0] == "--status":
        show_status()
        return

    if args[0] == "--list":
        if len(args) < 2:
            print("用法: python3 run_univ_eval_claude_cli.py --list <省份>")
            sys.exit(1)
        province = match_province(args[1])
        if not province:
            print(f"错误: 未匹配到省份 '{args[1]}'")
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
