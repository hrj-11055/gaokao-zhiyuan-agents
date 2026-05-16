#!/usr/bin/env python3
"""
大学深度评估执行脚本
使用 Claude Code CLI (claude -p) + open-websearch MCP 逐个生成大学评估报告

用法:
  python3 run_univ_eval.py 广东省                    # 跑广东省所有本科院校
  python3 run_univ_eval.py 广东省 --public-only      # 只跑公办院校
  python3 run_univ_eval.py 广东省 --limit 3          # 只跑前 3 所（测试用）
  python3 run_univ_eval.py 广东省 --retry            # 重跑失败的
  python3 run_univ_eval.py 广东省 --only 中山大学 华南理工大学  # 只跑指定大学
  python3 run_univ_eval.py --status                  # 查看各省进度总览
  python3 run_univ_eval.py --list 广东省             # 列出该省本科院校
"""

import csv
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Set

# ── 固定路径 ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "高等院校名单.csv"
PROMPT_PATH = BASE_DIR / "跑大学提示词-v4.txt"
OUTPUT_DIR = BASE_DIR / "data" / "大学评估报告"

DELAY_SECONDS = 5
TIMEOUT_SECONDS = 2700  # 45 分钟，大学报告搜索量大

# ── 搜索指令 ──────────────────────────────────────────
SEARCH_INSTRUCTION = """\

## 执行要求

你必须使用搜索工具在互联网上搜索真实数据来撰写报告。
禁止读取本地项目文件，所有数据必须来自互联网搜索。
使用 mcp__open-websearch__search 搜索，engines 优先 ["duckduckgo"]，无结果换 ["baidu"]。
对有价值的搜索结果 URL，用 mcp__open-websearch__fetchWebContent 抓取全文。
找不到的数据写"未检索到"，不要编造。

直接输出完整报告全文，不要只输出摘要。

"""

# ── 省份列表（用于 --status 和参数校验）──────────────
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
            # 跳过空行
            if not row or not row[0].strip():
                continue
            # 检测省份分组行，如 "广东省（166所）"
            if "所）" in row[0] or "所)" in row[0]:
                current_province = row[0].split("（")[0].split("(")[0]
                continue
            # 跳过表头
            if row[0].strip() == "序号":
                continue

            # 只取目标省份的本科院校
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
                "code": row[2].strip(),       # 学校标识码
                "authority": row[3].strip(),   # 主管部门
                "city": row[4].strip(),        # 所在城市
                "remark": remark,              # 备注（民办/中外合作等）
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
    # 替换搜索关键词中的 [大学名称]
    prompt = prompt.replace("[大学名称]", univ["name"])
    # 替换搜索关键词中的 [城市名称]
    prompt = prompt.replace("[城市名称]", univ["city"])

    return SEARCH_INSTRUCTION + "\n---\n\n" + prompt


def progress_file(province: str) -> Path:
    # 取省份简称做文件名
    short = province.replace("省", "").replace("市", "").replace("自治区", "")[:6]
    return OUTPUT_DIR / f"_progress_{short}.json"


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
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(prompt)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--output-format", "text",
                "--dangerously-skip-permissions",
            ],
            stdin=open(tmp_path, "r", encoding="utf-8"),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd="/tmp",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
        return result.stdout
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def save_report(text: str, univ: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{univ['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def show_status():
    """显示所有省份的完成进度"""
    print("=" * 65)
    print("  大学深度评估 — 各省进度总览")
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
    """列出指定省份的本科院校"""
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
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("错误: 未找到 claude 命令，请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)

    if not PROMPT_PATH.exists():
        print(f"错误: 提示词文件不存在: {PROMPT_PATH}")
        sys.exit(1)

    template = load_template()
    univs = load_universities(province, public_only, only_names, limit)
    done = load_progress(pfile)

    if retry_mode:
        retry_list = []
        for u in univs:
            rpath = OUTPUT_DIR / f"{u['name']}.md"
            if u["name"] not in done or not rpath.exists() or rpath.stat().st_size < 2000:
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
    print(f"  {province} 大学深度评估{filter_tag}")
    done_count = len(done & {u["name"] for u in univs})
    print(f"  院校总数: {len(univs)}, 已完成: {done_count}, 待评估: {len(pending)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  调用间隔: {DELAY_SECONDS}s, 超时: {TIMEOUT_SECONDS}s")
    print("=" * 65)

    if not pending:
        print(f"所有院校已完成评估！")
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
            done.add(univ["name"])
            save_progress(pfile, done)
            ok += 1
            print(f"  ✓ 成功 -> {path.name} ({len(text)} 字)")
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
        size = f"({path.stat().st_size}B)" if path.exists() else ""
        print(f"  [{status}] {u['name']}（{u['city']}）{size}")


def match_province(arg: str) -> str:
    """模糊匹配省份名称"""
    for prov in ALL_PROVINCES:
        if prov.startswith(arg) or arg in prov:
            return prov
    # 也支持不带"省"字的简写
    for prov in ALL_PROVINCES:
        if prov.replace("省", "").replace("市", "") == arg:
            return prov
    return ""


def main():
    args = sys.argv[1:]

    if not args:
        print("用法:")
        print("  python3 run_univ_eval.py <省份> [--public-only] [--limit N] [--retry]")
        print("  python3 run_univ_eval.py <省份> --only <大学名1> <大学名2>")
        print("  python3 run_univ_eval.py --status")
        print("  python3 run_univ_eval.py --list <省份>")
        print()
        print("省份示例: 广东省, 北京, 上海, 四川")
        print()
        print("选项:")
        print("  --public-only   只跑公办院校（排除民办）")
        print("  --limit N       只跑前 N 所（测试用）")
        print("  --retry         重跑失败/过短的报告")
        print("  --only          只跑指定的大学")
        print("  --status        查看各省进度")
        print("  --list          列出该省本科院校")
        sys.exit(0)

    if args[0] == "--status":
        show_status()
        return

    if args[0] == "--list":
        if len(args) < 2:
            print("用法: python3 run_univ_eval.py --list <省份>")
            sys.exit(1)
        province = match_province(args[1])
        if not province:
            print(f"错误: 未匹配到省份 '{args[1]}'")
            print(f"可选: {', '.join(ALL_PROVINCES)}")
            sys.exit(1)
        list_universities(province)
        return

    # 解析省份参数
    province = match_province(args[0])
    if not province:
        print(f"错误: 未匹配到省份 '{args[0]}'")
        print(f"可选: {', '.join(ALL_PROVINCES)}")
        sys.exit(1)

    # 解析选项
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
