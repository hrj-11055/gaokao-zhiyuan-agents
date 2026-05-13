#!/usr/bin/env python3
"""
教育学门类专业深度评估 — 单线程轮转脚本
从终端直接运行（不要在 Claude Code 会话内运行）：
    python3 run_edu_eval_v2.py

逻辑：
1. 从 CSV 筛选教育学门类(04)的 34 个专业
2. 检查 data/专业评估报告/ 中已有哪些完整报告（>=3KB）
3. 对缺失的专业，用提示词模板 + claude -p 逐个生成
4. 进度文件独立，支持断点续跑
"""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "本科专业目录_2025.csv"
PROMPT_PATH = BASE_DIR / "跑专业的提示词-v2.txt"
OUTPUT_DIR = BASE_DIR / "data" / "专业评估报告"
PROGRESS_FILE = OUTPUT_DIR / "_progress_edu_v2.json"

TARGET_CATEGORY = "04"  # 教育学
MIN_REPORT_SIZE = 3000  # 低于此大小视为不完整
TIMEOUT = 600  # 每个任务超时秒数
# ──────────────────────────────────────────────────────

OUTPUT_INSTRUCTION = """

---

## 关键执行指令

你必须严格遵守以下规则：
1. 直接将完整的评估报告内容输出到这里（stdout），包括所有模块的完整内容。
2. 不要将报告保存到任何文件。
3. 不要在报告前后添加任何总结、摘要或说明文字。
4. 输出必须以 "# 专业深度评估报告：" 开头。
"""


def load_template():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_majors():
    majors = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["学科门类代码"] == TARGET_CATEGORY:
                # 清理专业名称中的多余空格和乱码
                name = row["专业名称"].split()[0] if " " in row["专业名称"] else row["专业名称"]
                majors.append({
                    "code": row["专业代码"],
                    "name": name,
                    "category": row["学科门类"],
                    "sub": row["专业类"],
                })
    return majors


def build_prompt(template, major):
    return template.replace(
        "[专业编号：XXXXX    专业名称：XXX]",
        f"[专业编号：{major['code']}    专业名称：{major['name']}]",
    ) + OUTPUT_INSTRUCTION


def get_existing_reports():
    """扫描已存在的完整报告，返回 {专业代码: 文件路径}"""
    existing = {}
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("*.md"):
            # 文件名格式: {代码}_{名称}.md
            code = f.name.split("_")[0]
            if f.stat().st_size >= MIN_REPORT_SIZE:
                existing[code] = f
    return existing


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
    """调用 claude -p 执行单个专业评估"""
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
            timeout=TIMEOUT,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
        text = result.stdout

        # 校验完整性（只检查长度，不检查开头格式）
        if len(text.encode("utf-8")) < MIN_REPORT_SIZE:
            raise RuntimeError(f"报告过短（{len(text.encode('utf-8'))}B）")

        return text
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def save_report(text, major):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{major['code']}_{major['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def main():
    # 检查 claude CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("错误: 未找到 claude 命令，请确认 Claude Code 已安装且在 PATH 中")
        sys.exit(1)

    template = load_template()
    all_majors = load_majors()

    # 确定已完成的专业（来自进度文件 + 磁盘上的完整报告）
    existing = get_existing_reports()
    progress = load_progress()
    done = progress | set(existing.keys())

    pending = [m for m in all_majors if m["code"] not in done]

    print(f"教育学门类 | 总专业数: {len(all_majors)}")
    print(f"  磁盘完整报告: {len(existing)} | 进度文件记录: {len(progress)} | 合并去重: {len(done)}")
    print(f"  待评估: {len(pending)}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    if not pending:
        print("全部已完成，无需执行。")
        return

    # 打印待评估列表
    print("待评估专业：")
    for i, m in enumerate(pending, 1):
        print(f"  {i:2d}. {m['code']} {m['name']}")
    print("=" * 60)

    ok_count, fail_count = 0, 0

    for i, major in enumerate(pending, 1):
        tag = f"{major['category']}/{major['sub']}/{major['name']}"
        print(f"[{i}/{len(pending)}] {tag} ...", flush=True)

        try:
            text = run_one(major, template)
            path = save_report(text, major)
            done.add(major["code"])
            save_progress(done)
            ok_count += 1
            size_kb = len(text.encode("utf-8")) // 1024
            print(f"  -> {path.name} ({size_kb}KB)")
        except Exception as e:
            fail_count += 1
            print(f"  !! 失败: {e}")

    print("=" * 60)
    print(f"完成! 成功: {ok_count} | 失败: {fail_count} | 跳过: {len(all_majors) - len(pending)}")


if __name__ == "__main__":
    main()
