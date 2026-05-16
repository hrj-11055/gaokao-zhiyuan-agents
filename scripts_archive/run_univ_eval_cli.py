#!/usr/bin/env python3
"""
大学深度评估执行脚本（Gemini 版）
使用 Gemini API + 内置 Google Search 生成大学评估报告

用法:
  python3 run_univ_eval_gemini.py 广东省                    # 跑广东省所有本科院校
  python3 run_univ_eval_gemini.py 广东省 --public-only      # 只跑公办院校
  python3 run_univ_eval_gemini.py 广东省 --limit 3          # 只跑前 3 所（测试用）
  python3 run_univ_eval_gemini.py 广东省 --retry            # 重跑失败的
  python3 run_univ_eval_gemini.py 广东省 --only 中山大学 华南理工大学
  python3 run_univ_eval_gemini.py --status                  # 查看各省进度总览
  python3 run_univ_eval_gemini.py --list 广东省             # 列出该省本科院校
"""

import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional, Set

# ── 固定路径 ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "高等院校名单.csv"
PROMPT_PATH = BASE_DIR / "跑大学提示词-v2.txt"
OUTPUT_DIR = BASE_DIR / "data" / "大学评估报告"

DELAY_SECONDS = 5
TIMEOUT_SECONDS = 600  # 10 分钟，Flash 较快

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_MAX_OUTPUT_TOKENS = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "32768"))
GEMINI_API_RETRIES = int(os.environ.get("GEMINI_API_RETRIES", "2"))
GEMINI_API_RETRY_DELAY_SECONDS = float(os.environ.get("GEMINI_API_RETRY_DELAY_SECONDS", "3"))
GEMINI_QUALITY_RETRIES = int(os.environ.get("GEMINI_QUALITY_RETRIES", "1"))
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

    # 前缀指令：强调使用 Google Search 获取实时数据
    prefix = """\
## 研究执行要求

你已内置 Google Search 能力，请主动搜索以获取实时数据。
对于标记为「需搜索」的模块，你必须通过搜索获取最新数据，不得仅凭训练知识回答。
对于录取分数线、就业数据、薪酬等时效性数据，必须搜索 2023–2025 年的最新数据。

## 重要：输出要求

你必须直接输出完整的 8 个模块报告内容（Markdown 格式），不要只输出摘要。
不要说"报告已保存"或"报告已生成"，直接输出报告全文。
从"## 模块一：学术资本"开始，到"## 模块八：原始数据汇总"结束，完整输出每一个模块。
不要输出"内部评分标尺"部分。
报告正文不少于 5000 个中文字符；每个模块都要有表格、关键数据、简短分析，禁止压缩成提纲。

---

"""
    return prefix + prompt


def progress_file(province: str) -> Path:
    short = province.replace("省", "").replace("市", "").replace("自治区", "")[:6]
    return OUTPUT_DIR / f"_progress_gemini_{short}.json"


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
    """调用 Gemini API + Google Search 生成报告"""
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("未设置 GEMINI_API_KEY 环境变量")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=build_generation_config(),
    )

    if not response.text:
        raise RuntimeError("Gemini 返回空内容")

    # 附加搜索来源信息
    sources = []
    try:
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            for chunk in metadata.grounding_chunks:
                if chunk.web:
                    sources.append(f"- [{chunk.web.title}]({chunk.web.uri})")
    except Exception:
        pass

    result = response.text
    if sources:
        result += "\n\n---\n## Google 搜索来源\n\n" + "\n".join(sources)

    return result


def build_quality_repair_prompt(text: str, quality: dict, univ: dict) -> str:
    target_cjk = MIN_CJK_CHARS + 2000
    issues = format_quality_issues(quality)
    cjk_count = quality.get("stats", {}).get("中文字符数", 0)

    return f"""\
你刚才生成的《{univ['name']}》大学深度评估报告没有通过质量检查。

质检问题：{issues}
当前中文正文数：{cjk_count}
硬性目标：最终报告中文正文不少于 {MIN_CJK_CHARS} 字；本次扩写必须以 {target_cjk} 字以上为写作目标，避免再次卡在临界值。

请基于下面的上一版报告进行“扩写和修复”，直接输出一份完整替换版 Markdown 报告：

1. 必须保留并完整输出 8 个模块，从“## 模块一：学术资本”到“## 模块八：原始数据汇总”。
2. 不能只补充差异内容，不能输出修改说明，不能说“已扩写”。
3. 每个模块至少补足 2-4 段实质分析；模块二、三、五、六、七必须明显扩写。
4. 表格可以保留，但不能用表格替代正文分析；表格之外必须有足够中文段落。
5. 严禁编造无法核实的具体数字；找不到的数据继续标注 `[未检索到]` 或 `[待核实]`。
6. 不要输出“内部评分标尺”部分。

上一版报告如下：

{text}
"""


def run_one_with_retries(prompt: str) -> tuple[str, dict, int]:
    attempts = 0
    while True:
        try:
            text = run_one(prompt)
            quality = validate_report_text(text)
            return text, quality, attempts
        except Exception:
            if attempts >= GEMINI_API_RETRIES:
                raise
            attempts += 1
            if GEMINI_API_RETRY_DELAY_SECONDS > 0:
                time.sleep(GEMINI_API_RETRY_DELAY_SECONDS)


def generate_with_quality_repair(prompt: str, univ: dict) -> tuple[str, dict, int]:
    text, quality, _ = run_one_with_retries(prompt)
    attempts = 0

    while not quality_allows_completion(quality) and attempts < GEMINI_QUALITY_RETRIES:
        attempts += 1
        repair_prompt = build_quality_repair_prompt(text, quality, univ)
        text, quality, _ = run_one_with_retries(repair_prompt)

    return text, quality, attempts


def build_generation_config():
    from google.genai import types

    return types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
        max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
    )


def save_report(text: str, univ: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{univ['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def count_cjk_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def validate_report_text(text: str) -> dict:
    result = {
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "stats": {
            "字符数": len(text),
            "中文字符数": count_cjk_chars(text),
            "数据表格": text.count("| ---") + text.count("|---") + text.count("|------|"),
            "搜索来源": text.count("Google 搜索来源"),
        },
    }

    cjk_count = result["stats"]["中文字符数"]
    if cjk_count < MIN_CJK_CHARS:
        result["errors"].append(f"中文正文过短: {cjk_count} 字（要求 ≥ {MIN_CJK_CHARS}）")

    missing_modules = [module for module in REQUIRED_MODULES if module not in text]
    if missing_modules:
        result["errors"].append(f"缺少模块: {', '.join(missing_modules)}")

    if "[X]" in text or "[XXX]" in text:
        result["errors"].append("存在未填充占位符")

    if result["stats"]["数据表格"] < 8:
        result["warnings"].append(f"数据表格偏少: {result['stats']['数据表格']} 个（建议 ≥ 8）")

    if "Google 搜索来源" not in text and text.count("来源") < 8:
        result["warnings"].append("搜索来源引用偏少")

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


def archive_failed_report(path: Path) -> Path:
    failed_dir = OUTPUT_DIR / "_failed_gemini"
    failed_dir.mkdir(parents=True, exist_ok=True)
    failed_path = failed_dir / path.name
    path.replace(failed_path)
    return failed_path


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
    print("  大学深度评估（Gemini 版）— 各省进度总览")
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


def run_province(
    province: str,
    public_only: bool = False,
    only_names: Optional[Set[str]] = None,
    limit: Optional[int] = None,
    retry_mode: bool = False,
):
    pfile = progress_file(province)

    # 检查 API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("错误: 未设置 GEMINI_API_KEY 环境变量")
        print("  export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    # 检查依赖
    try:
        from google import genai  # noqa: F401
    except ImportError:
        print("错误: 未安装 google-genai 包")
        print("  pip3 install google-genai")
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
    print(f"  {province} 大学深度评估{filter_tag} [Gemini {GEMINI_MODEL}]")
    done_count = len(done & {u["name"] for u in univs})
    print(f"  院校总数: {len(univs)}, 已完成: {done_count}, 待评估: {len(pending)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  调用间隔: {DELAY_SECONDS}s")
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
            text, quality, repair_attempts = generate_with_quality_repair(prompt, univ)

            if not text or len(text.strip()) < 500:
                raise RuntimeError(f"生成内容过短（{len(text.strip())}字符），可能失败")

            path = save_report(text, univ)
            quality_status = quality["status"]
            if not quality_allows_completion(quality):
                failed_path = archive_failed_report(path)
                raise RuntimeError(
                    f"质检失败 [{quality_status}]，已移至 _failed_gemini/{failed_path.name}: "
                    f"{format_quality_issues(quality)}"
                )

            done.add(univ["name"])
            save_progress(pfile, done)
            ok += 1
            stats = quality.get("stats", {})
            cjk_count = stats.get("中文字符数", "?")
            if quality_status == "WARN":
                print(f"  ⚠ 质检警告: {format_quality_issues(quality)}")
            if repair_attempts:
                print(f"  ↻ 已自动扩写修复 {repair_attempts} 次")
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
        failed_path = OUTPUT_DIR / "_failed_gemini" / f"{u['name']}.md"
        if path.exists():
            size = f"({path.stat().st_size}B)"
        elif failed_path.exists():
            size = f"(质检失败: _failed_gemini/{failed_path.name})"
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
        print("  python3 run_univ_eval_gemini.py <省份> [--public-only] [--limit N] [--retry]")
        print("  python3 run_univ_eval_gemini.py <省份> --only <大学名1> <大学名2>")
        print("  python3 run_univ_eval_gemini.py --status")
        print("  python3 run_univ_eval_gemini.py --list <省份>")
        print()
        print("环境变量:")
        print("  GEMINI_API_KEY   Google AI API Key（必需）")
        print("  GEMINI_API_RETRIES  API 瞬断重试次数（默认 2）")
        print("  GEMINI_QUALITY_RETRIES  质检失败后的自动扩写次数（默认 1）")
        print()
        print("依赖:")
        print("  pip3 install google-genai")
        sys.exit(0)

    if args[0] == "--status":
        show_status()
        return

    if args[0] == "--list":
        if len(args) < 2:
            print("用法: python3 run_univ_eval_gemini.py --list <省份>")
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
