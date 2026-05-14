#!/usr/bin/env python3
"""Run the 30-question acceptance set through gaokao-proxy blocking chat."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEST_SET_PATH = BASE_DIR / "test-runs" / "30q-test-set.md"
RAW_RESULTS_PATH = BASE_DIR / "test-runs" / "30q-raw-results.json"
SUMMARY_PATH = BASE_DIR / "test-runs" / "30q-results.md"
DEFAULT_API_URL = "http://47.113.125.147/api/chat"


def load_questions(path: Path) -> list[dict]:
    questions = []
    row_re = re.compile(r"^\|\s*(Q\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = row_re.match(line.strip())
        if not match:
            continue
        qid, category, question, check = [part.strip() for part in match.groups()]
        questions.append({
            "id": qid,
            "category": category,
            "question": question,
            "check": check,
        })
    return questions


def post_chat(api_url: str, token: str, question: dict, timeout: int) -> dict:
    payload = {
        "query": question["question"],
        "user": f"test-user-{question['id'].lower()}",
        "inputs": {},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["x-proxy-token"] = token

    request = urllib.request.Request(api_url, data=body, headers=headers, method="POST")
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        elapsed_ms = round((time.time() - started) * 1000)
        data = json.loads(raw)
        return {
            "status": "ok",
            "http_status": response.status,
            "answer": data.get("answer", ""),
            "conversation_id": data.get("conversation_id", ""),
            "elapsed_ms": elapsed_ms,
            "answer_length": len(data.get("answer", "")),
        }


def write_summary(results: list[dict], path: Path) -> None:
    ok_count = sum(1 for item in results if item["status"] == "ok")
    lines = [
        "# 30 题测试结果",
        "",
        f"- 总题数：{len(results)}",
        f"- 接口成功：{ok_count}/{len(results)}",
        "- 人工评分：待填写",
        "",
        "| ID | 类别 | 状态 | 耗时(ms) | 回答字数 | 人工评分 | 问题记录 |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for item in results:
        lines.append(
            f"| {item['id']} | {item['category']} | {item['status']} | "
            f"{item.get('elapsed_ms', '')} | {item.get('answer_length', '')} |  |  |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_outputs(results: list[dict], raw_path: Path, summary_path: Path) -> None:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(results, summary_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=os.environ.get("GAOKAO_TEST_API_URL", DEFAULT_API_URL))
    parser.add_argument("--token", default=os.environ.get("PROXY_API_TOKEN", ""))
    parser.add_argument("--input", type=Path, default=TEST_SET_PATH)
    parser.add_argument("--output", type=Path, default=RAW_RESULTS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--sleep", type=float, default=float(os.environ.get("GAOKAO_TEST_SLEEP", "3")))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("GAOKAO_TEST_TIMEOUT", "90")))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only", nargs="*", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    all_questions = load_questions(args.input)
    questions = all_questions
    if args.only:
        only_ids = {item.upper() for item in args.only}
        questions = [item for item in questions if item["id"] in only_ids]
    if args.limit:
        questions = questions[:args.limit]
    if not questions:
        raise SystemExit(f"没有从 {args.input} 读取到测试题")

    if args.dry_run:
        print(f"Loaded {len(questions)} questions from {args.input}", flush=True)
        for item in questions:
            print(f"{item['id']} [{item['category']}] {item['question']}", flush=True)
        return 0

    results = []
    if args.only and args.output.exists():
        try:
            results = json.loads(args.output.read_text(encoding="utf-8"))
        except Exception:
            results = []
    result_index = {item.get("id"): index for index, item in enumerate(results)}

    for index, question in enumerate(questions, 1):
        print(f"[{index}/{len(questions)}] {question['id']} {question['question']}", flush=True)
        result = {**question}
        try:
            result.update(post_chat(args.api_url, args.token, question, args.timeout))
            print(f"  OK {result['elapsed_ms']}ms, {result['answer_length']} chars", flush=True)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            result.update({
                "status": "error",
                "http_status": exc.code,
                "answer": body[:500],
            })
            print(f"  HTTP {exc.code}", flush=True)
        except Exception as exc:
            result.update({
                "status": "error",
                "answer": str(exc),
            })
            print(f"  ERROR {exc}", flush=True)
        if result["id"] in result_index:
            results[result_index[result["id"]]] = result
        else:
            result_index[result["id"]] = len(results)
            results.append(result)
        results.sort(key=lambda item: next(
            (index for index, question in enumerate(all_questions) if question["id"] == item.get("id")),
            999,
        ))
        save_outputs(results, args.output, args.summary)
        if index < len(questions) and args.sleep > 0:
            time.sleep(args.sleep)

    ok_count = sum(1 for item in results if item["status"] == "ok")
    print(f"\nSaved raw results to {args.output}", flush=True)
    print(f"Saved summary scaffold to {args.summary}", flush=True)
    print(f"Success: {ok_count}/{len(results)}", flush=True)
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
