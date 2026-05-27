#!/usr/bin/env python3
"""
Clean deep-report source files before importing them into PostgreSQL.

The script is intentionally conservative: it removes collection/prompting
artifacts and internal scoring weights while preserving decision data such as
scores, ranks, employment rates, salary ranges, sources, and caveats.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


CLEANING_VERSION = "report-source-clean-v1"

DEFAULT_TARGETS = [
    Path("data/专业评估报告_json_v2"),
    Path("data/大学评估报告_json_v2"),
]

TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
JSON_SUFFIXES = {".json"}

NOISE_LINE_PATTERNS = [
    r"^(?:搜索|研究)?数据收集完(?:成|毕)[，,。]?.*$",
    r"^已收集足够数据[，,。]?.*$",
    r"^所有研究均已完成[，,。]?.*$",
    r"^所有搜索工具均因.*?(额度|配额|网络|限制|不可用|异常).*?$",
    r"^我将基于训练数据生成报告.*?$",
    r"^以上数据主要基于训练数据.*?$",
    r"^以下是关于.*?深度.*?报告[。.]?$",
    r"^我已从多轮搜索中获得了足够的数据.*?$",
    r"^\*\*评估机构\*\*[:：].*$",
    r"^\*\*研究员\*\*[:：].*$",
    r"^\*\*报告编号\*\*[:：].*$",
    r"^\*\*研究机构\*\*[:：].*$",
    r"^\*\*首席分析师\*\*[:：].*$",
    r"^\*\*报告版本\*\*[:：].*$",
    r"^\*\*输出格式\*\*[:：]?\s*$",
    r"^输出格式[:：]?\s*$",
    r"^\*?本报告由\s*AI\s*数据分析师.*$",
    r"^>?\s*\*\*?数据透明度声明\*\*?[：:].*?(搜索工具|外部搜索工具).*$",
    r"^>?\s*\*\*?数据说明\*\*?[：:].*?(搜索工具|网络搜索工具).*?$",
]

INLINE_TAG_REPLACEMENTS = [
    (re.compile(r"`?\[直接回答\]`?"), ""),
    (re.compile(r"`?\[需搜索(?:[:：][^\]]+)?\]`?"), ""),
    (re.compile(r"`?\[数据收集完成\]`?"), ""),
    (re.compile(r"`?\[需更新\]`?"), ""),
    (re.compile(r"`?\[社区观点(?:[/／:：,，][^\]]+)?\]`?"), "（社区反馈，需核验）"),
    (re.compile(r"`?\[社区观点/待核实\]`?"), "（社区反馈，需核验）"),
]


@dataclass
class CleanStats:
    files_seen: int = 0
    files_changed: int = 0
    json_files_changed: int = 0
    text_files_changed: int = 0
    table_columns_removed: int = 0
    noise_lines_removed: int = 0
    inline_tags_removed: int = 0

    def merge(self, other: "CleanStats") -> None:
        self.files_seen += other.files_seen
        self.files_changed += other.files_changed
        self.json_files_changed += other.json_files_changed
        self.text_files_changed += other.text_files_changed
        self.table_columns_removed += other.table_columns_removed
        self.noise_lines_removed += other.noise_lines_removed
        self.inline_tags_removed += other.inline_tags_removed


def is_noise_line(line: str) -> bool:
    stripped = line.strip()
    return any(re.search(pattern, stripped) for pattern in NOISE_LINE_PATTERNS)


def split_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def clean_inline_text(text: str, stats: CleanStats) -> str:
    cleaned = text
    cleaned = re.sub(r"（\s*权重\s*\d+(?:\.\d+)?%\s*）", "", cleaned)
    cleaned = re.sub(r"\(\s*权重\s*\d+(?:\.\d+)?%\s*\)", "", cleaned)
    cleaned = cleaned.replace("AI 总评 (Executive Summary)", "顾问结论")
    cleaned = cleaned.replace("AI 总评", "顾问结论")
    cleaned = cleaned.replace("Executive Summary", "")
    cleaned = re.sub(r"`([^`\n]{1,30})`", r"\1", cleaned)

    def replace_community_tag(match: re.Match[str]) -> str:
        detail = match.group(1).strip(" \t:：,，/／-—")
        if detail in {"待核实", "需核实", "需核验"}:
            return "（社区反馈，需核验）"
        if detail == "汇总":
            return "（社区反馈汇总，需核验）"
        return f"（社区反馈，需核验；{detail}）" if detail else "（社区反馈，需核验）"

    cleaned, count = re.subn(r"`?\[社区观点([^\]\n]{0,40})\]`?", replace_community_tag, cleaned)
    stats.inline_tags_removed += count

    def replace_status_tag(match: re.Match[str]) -> str:
        label = match.group(1)
        detail = match.group(2)
        if label == "无数据":
            return f"暂无数据（{detail.strip()}）" if detail else "暂无数据"
        if label == "未检索到":
            return f"暂未检索到（{detail.strip()}）" if detail else "暂未检索到"
        if label == "部分待核实":
            return f"（部分需核验：{detail.strip()}）" if detail else "（部分需核验）"
        return f"（需核验：{detail.strip()}）" if detail else "（需核验）"

    cleaned, count = re.subn(
        r"`?\[(待核实|部分待核实|无数据|未检索到)(?:[，,、:：]?\s*([^\]]+))?\]`?",
        replace_status_tag,
        cleaned,
    )
    stats.inline_tags_removed += count

    cleaned, count = re.subn(
        r"`?\[未检索到([^\]\n。；;]*)",
        lambda match: f"暂未检索到{match.group(1).strip()}",
        cleaned,
    )
    stats.inline_tags_removed += count

    for pattern, replacement in INLINE_TAG_REPLACEMENTS:
        cleaned, count = pattern.subn(replacement, cleaned)
        stats.inline_tags_removed += count
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


def render_table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def clean_markdown_table(lines: list[str], start: int, stats: CleanStats) -> tuple[list[str], int, int]:
    table_lines: list[str] = []
    index = start
    while index < len(lines) and split_table_row(lines[index]) is not None:
        table_lines.append(lines[index])
        index += 1

    rows = [split_table_row(line) or [] for line in table_lines]
    if len(rows) < 2:
        return table_lines, index, 0

    header = rows[0]
    remove_indexes = {
        i for i, cell in enumerate(header)
        if "权重" in cell or "加权得分" in cell
    }

    cleaned_rows: list[list[str]] = []
    for row in rows:
        if any("加权总分" in cell for cell in row):
            continue
        cleaned_rows.append([
            clean_inline_text(cell, stats) for i, cell in enumerate(row)
            if i not in remove_indexes
        ])

    if len(cleaned_rows) < 2:
        return [], index, len(remove_indexes)

    rendered: list[str] = []
    for row_index, row in enumerate(cleaned_rows):
        if row_index == 1 and is_separator_row(row):
            rendered.append(render_table_row(["---"] * len(cleaned_rows[0])))
        else:
            rendered.append(render_table_row(row))

    return rendered, index, len(remove_indexes)


def clean_text(text: str) -> tuple[str, CleanStats]:
    stats = CleanStats()
    if not text:
        return "", stats

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    cleaned_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if is_noise_line(line):
            stats.noise_lines_removed += 1
            index += 1
            continue

        table_row = split_table_row(line)
        if table_row is not None:
            rendered, next_index, removed = clean_markdown_table(lines, index, stats)
            cleaned_lines.extend(rendered)
            stats.table_columns_removed += removed
            index = next_index
            continue

        cleaned = line
        before = cleaned
        cleaned = re.sub(r"^(#{1,4}\s*)维度[一二三四五六七八九十]+[：:]\s*", r"\1", cleaned)
        cleaned = clean_inline_text(cleaned, stats).rstrip()
        cleaned = re.sub(r"^\[([^\[\]]{1,40})\]$", r"\1", cleaned)
        if re.fullmatch(r"(?:\[[^\[\]\n]{1,40}\]\s*){2,}", cleaned):
            cleaned = re.sub(r"\[([^\[\]\n]+)\]", r"\1", cleaned)
        if before.strip() and not cleaned.strip():
            stats.noise_lines_removed += 1
            index += 1
            continue
        cleaned_lines.append(cleaned)
        index += 1

    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    if text.endswith("\n"):
        result += "\n"
    return result, stats


def clean_json_value(value: Any) -> tuple[Any, CleanStats]:
    stats = CleanStats()
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        cleaned_items = []
        for item in value:
            cleaned, child_stats = clean_json_value(item)
            cleaned_items.append(cleaned)
            stats.merge(child_stats)
        return cleaned_items, stats
    if isinstance(value, dict):
        cleaned_dict = {}
        for key, item in value.items():
            cleaned, child_stats = clean_json_value(item)
            cleaned_dict[key] = cleaned
            stats.merge(child_stats)
        return cleaned_dict, stats
    return value, stats


def iter_files(targets: Iterable[Path]) -> Iterable[Path]:
    for target in targets:
        if target.is_file():
            yield target
            continue
        if target.is_dir():
            for path in sorted(target.rglob("*")):
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES | JSON_SUFFIXES:
                    yield path


def clean_file(path: Path) -> tuple[str | None, CleanStats]:
    stats = CleanStats(files_seen=1)
    raw = path.read_text(encoding="utf-8")

    if path.suffix.lower() in JSON_SUFFIXES:
        data = json.loads(raw)
        cleaned_data, child_stats = clean_json_value(data)
        stats.merge(child_stats)
        if isinstance(cleaned_data, dict):
            meta = cleaned_data.setdefault("meta", {})
            if isinstance(meta, dict):
                meta["cleaning_version"] = CLEANING_VERSION
        cleaned = json.dumps(cleaned_data, ensure_ascii=False, indent=2) + "\n"
        if cleaned != raw:
            stats.files_changed = 1
            stats.json_files_changed = 1
            return cleaned, stats
        return None, stats

    if path.suffix.lower() in TEXT_SUFFIXES:
        cleaned, child_stats = clean_text(raw)
        stats.merge(child_stats)
        if cleaned != raw:
            stats.files_changed = 1
            stats.text_files_changed = 1
            return cleaned, stats

    return None, stats


def backup_file(path: Path, backup_root: Path) -> Path:
    source_path = path if not path.is_absolute() else Path(*path.parts[1:])
    backup_path = backup_root / source_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean report source Markdown/JSON files.")
    parser.add_argument("targets", nargs="*", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--apply", action="store_true", help="write cleaned files in place")
    parser.add_argument("--backup-dir", type=Path, help="backup root for --apply")
    parser.add_argument("--limit", type=int, default=0, help="limit number of files processed")
    parser.add_argument("--show-samples", type=int, default=8, help="print changed sample paths")
    args = parser.parse_args()

    backup_root = args.backup_dir
    if args.apply and backup_root is None:
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_root = Path("data/report-cleaning-backups") / stamp

    stats = CleanStats()
    changed_samples: list[Path] = []

    for index, path in enumerate(iter_files(args.targets), start=1):
        if args.limit and index > args.limit:
            break
        cleaned, file_stats = clean_file(path)
        stats.merge(file_stats)
        if cleaned is None:
            continue
        if len(changed_samples) < args.show_samples:
            changed_samples.append(path)
        if args.apply:
            assert backup_root is not None
            backup_file(path, backup_root)
            path.write_text(cleaned, encoding="utf-8")

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"mode={mode}")
    print(f"files_seen={stats.files_seen}")
    print(f"files_changed={stats.files_changed}")
    print(f"json_files_changed={stats.json_files_changed}")
    print(f"text_files_changed={stats.text_files_changed}")
    print(f"table_columns_removed={stats.table_columns_removed}")
    print(f"noise_lines_removed={stats.noise_lines_removed}")
    print(f"inline_tags_removed={stats.inline_tags_removed}")
    if args.apply and backup_root:
        print(f"backup_dir={backup_root}")
    if changed_samples:
        print("changed_samples:")
        for path in changed_samples:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
