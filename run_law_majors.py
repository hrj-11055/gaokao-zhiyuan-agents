#!/usr/bin/env python3
"""
教育学类专业深度评估批量执行脚本
使用 Claude Code CLI (claude -p) + open-websearch MCP 逐个生成专业评估报告
用法: python3 run_law_majors.py
"""

import csv
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
DELAY_SECONDS = 5          # 每次调用间隔（秒）
TARGET_CATEGORIES = {"04"}  # 教育学门类
SKIP_SUBCATEGORIES = set()  # 不跳过任何专业类
RETRY_ONLY = set()  # 仅重跑指定专业代码，空集合则跑全部

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "本科专业目录_2025.csv"
PROMPT_PATH = BASE_DIR / "跑专业的提示词-v2.txt"
OUTPUT_DIR = BASE_DIR / "data" / "专业评估报告"
PROGRESS_FILE = OUTPUT_DIR / "_progress_edu.json"

# 搜索指令前缀：指示 Claude 使用 open-websearch 进行多维度数据搜索
SEARCH_INSTRUCTION = """\

## 研究执行要求

在生成报告之前，你必须使用 open-websearch MCP 工具进行至少 4 轮网络搜索，覆盖以下数据维度：

1. **就业与薪酬数据**：搜索"[专业名称] 就业率 薪酬 起薪 2025 2024 2023"
2. **院校与排名数据**：搜索"[专业名称] 大学排名 学科评估 院校推荐"
3. **行业与产业数据**：搜索"[专业名称] 行业前景 市场规模 增长率"
4. **职业发展数据**：搜索"[专业名称] 职业路径 准入考试 通过率 深造率"

搜索策略：
- 优先使用 duckduckgo 引擎（engines: ["duckduckgo"]）
- 若 duckduckgo 返回结果不足，可尝试 baidu 引擎
- 对有价值的搜索结果 URL，使用 fetchWebContent 抓取详细内容
- 若某个维度搜索无结果，可调整关键词重试一次

所有搜索获得的数据必须标注来源，无法确认的数据标注 [待核实]。

## 重要：输出要求

你必须直接输出完整的 8 个模块报告内容（Markdown 格式），不要只输出摘要。
不要说"报告已保存"或"报告已生成"，直接输出报告全文。
从"## 模块一：专业画像与总评"开始，到"模块八：原始数据支撑"结束，完整输出每一个模块。

"""
# ──────────────────────────────────────────────────────


def load_template():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_majors():
    majors = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if (row["学科门类代码"] in TARGET_CATEGORIES
                    and row["专业类代码"] not in SKIP_SUBCATEGORIES):
                if RETRY_ONLY and row["专业代码"] not in RETRY_ONLY:
                    continue
                majors.append({
                    "code": row["专业代码"],
                    "name": row["专业名称"],
                    "category": row["学科门类"],
                    "sub": row["专业类"],
                })
    return majors


def build_prompt(template, major):
    # 替换专业编号和名称
    prompt = template.replace(
        "[专业编号：XXXXX    专业名称：XXX]",
        f"[专业编号：{major['code']}    专业名称：{major['name']}]",
    )
    # 在核心指令之前插入搜索要求
    prompt = SEARCH_INSTRUCTION + "\n---\n\n" + prompt
    # 替换搜索指令中的专业名称占位符
    prompt = prompt.replace("[专业名称]", major["name"])
    return prompt


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(done):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=2)


def run_one(prompt):
    """调用 claude -p 通过临时文件传入提示词，返回生成的文本"""
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
            timeout=600,  # 10 分钟超时（含搜索时间）
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


def main():
    # 检查 claude CLI 是否可用
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("错误: 未找到 claude 命令，请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)

    # 检查提示词文件
    if not PROMPT_PATH.exists():
        print(f"错误: 提示词文件不存在: {PROMPT_PATH}")
        sys.exit(1)

    template = load_template()
    majors = load_majors()
    done = load_progress()
    pending = [m for m in majors if m["code"] not in done]

    print("=" * 60)
    print(f"  教育学门类（04）专业深度评估")
    print(f"  总专业数: {len(majors)}, 已完成: {len(done)}, 待评估: {len(pending)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  调用间隔: {DELAY_SECONDS}s")
    print("=" * 60)

    if not pending:
        print("所有教育学类专业已完成评估！")
        return

    # 打印待评估列表
    print("\n待评估专业：")
    for i, m in enumerate(pending, 1):
        status = "✓" if m["code"] in done else " "
        print(f"  [{status}] {i}. {m['code']} {m['name']}")
    print()

    ok, fail = 0, 0
    for i, major in enumerate(pending, 1):
        tag = f"{major['sub']}/{major['name']}（{major['code']}）"
        print(f"[{i}/{len(pending)}] 正在评估: {tag}", flush=True)

        try:
            prompt = build_prompt(template, major)
            text = run_one(prompt)

            # 验证输出不为空
            if not text or len(text.strip()) < 500:
                raise RuntimeError(f"生成内容过短（{len(text.strip())}字符），可能失败")

            path = save_report(text, major)
            done.add(major["code"])
            save_progress(done)
            ok += 1
            print(f"  ✓ 成功 -> {path.name} ({len(text)} 字)")
        except Exception as e:
            fail += 1
            print(f"  ✗ 失败: {e}")

        # 显示进度
        print(f"  进度: 成功 {ok}, 失败 {fail}, 剩余 {len(pending) - i}")

        if i < len(pending):
            print(f"  等待 {DELAY_SECONDS}s...")
            time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 60)
    print(f"  教育学类评估完成!")
    print(f"  成功: {ok}, 失败: {fail}, 之前完成: {len(majors) - len(pending)}")
    print(f"  总完成: {len(done)}/{len(majors)}")
    print("=" * 60)

    # 打印最终状态
    print("\n各专业完成状态：")
    for m in majors:
        status = "✓" if m["code"] in done else "✗"
        path = OUTPUT_DIR / f"{m['code']}_{m['name']}.md"
        size = f"({path.stat().st_size}B)" if path.exists() else ""
        print(f"  [{status}] {m['code']} {m['name']} {size}")


if __name__ == "__main__":
    main()
