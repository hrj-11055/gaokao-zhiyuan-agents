#!/usr/bin/env python3
"""
教育学门类专业深度评估 — 并行执行脚本
使用 Claude Code CLI (claude -p) + MCP 网络搜索，并行生成专业评估报告
用法: python3 run_edu_eval.py [并发数]
默认并发数: 2
"""

import csv
import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "本科专业目录_2025.csv"
PROMPT_PATH = BASE_DIR / "跑专业的提示词-v2.txt"
OUTPUT_DIR = BASE_DIR / "data" / "专业评估报告"
PROGRESS_FILE = OUTPUT_DIR / "_progress_edu.json"

TARGET_CATEGORY = "04"  # 教育学
MAX_WORKERS = 2  # 默认并发数
# ──────────────────────────────────────────────────────


def load_template():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_majors():
    majors = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["学科门类代码"] == TARGET_CATEGORY:
                majors.append({
                    "code": row["专业代码"],
                    "name": row["专业名称"],
                    "category": row["学科门类"],
                    "sub": row["专业类"],
                })
    return majors


OUTPUT_INSTRUCTION = """

---

## 关键执行指令

你必须严格遵守以下规则：
1. 直接将完整的评估报告内容输出到这里（stdout），包括所有模块的完整内容。
2. 不要将报告保存到任何文件。
3. 不要在报告前后添加任何总结、摘要或说明文字。
4. 输出必须以 "# 专业深度评估报告：" 开头。
"""


def build_prompt(template, major):
    return template.replace(
        "[专业编号：XXXXX    专业名称：XXX]",
        f"[专业编号：{major['code']}    专业名称：{major['name']}]",
    ) + OUTPUT_INSTRUCTION


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(done):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=2)


def run_one(major, template):
    """调用 claude -p 执行单个专业评估，带 MCP 网络搜索"""
    prompt = build_prompt(template, major)

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
            timeout=600,  # 10 分钟超时
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


def worker(major, template):
    """单个任务：执行评估 → 校验完整性 → 保存报告 → 返回结果"""
    tag = f"{major['category']}/{major['sub']}/{major['name']}"
    try:
        text = run_one(major, template)
        # 校验：完整报告应大于 3KB，且以标题开头
        if len(text.encode("utf-8")) < 3000:
            raise RuntimeError(f"报告过短（{len(text.encode('utf-8'))}B），可能只是摘要")
        if not text.strip().startswith("#"):
            # 去掉前面可能的空行后再检查
            if not text.lstrip().startswith("#"):
                raise RuntimeError("报告格式异常，未以 Markdown 标题开头")
        path = save_report(text, major)
        return {"ok": True, "major": major, "file": path.name, "tag": tag}
    except Exception as e:
        return {"ok": False, "major": major, "error": str(e), "tag": tag}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else MAX_WORKERS

    # 检查 claude CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("错误: 未找到 claude 命令，请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)

    template = load_template()
    majors = load_majors()
    done = load_progress()
    pending = [m for m in majors if m["code"] not in done]

    print(f"教育学门类 | 总专业数: {len(majors)} | 已完成: {len(done)} | 待评估: {len(pending)}")
    print(f"并发数: {workers} | 输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    if not pending:
        print("全部已完成，无需执行。")
        return

    ok_count, fail_count = 0, 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        # 提交所有任务
        futures = {pool.submit(worker, m, template): m for m in pending}

        for i, future in enumerate(as_completed(futures), 1):
            res = future.result()
            major = res["major"]

            if res["ok"]:
                ok_count += 1
                done.add(major["code"])
                save_progress(done)
                print(f"  ✅ [{i}/{len(pending)}] {res['tag']} → {res['file']}")
            else:
                fail_count += 1
                print(f"  ❌ [{i}/{len(pending)}] {res['tag']} 失败: {res['error']}")

    print("=" * 60)
    print(f"完成! 成功: {ok_count} | 失败: {fail_count} | 跳过: {len(majors) - len(pending)}")


if __name__ == "__main__":
    main()
