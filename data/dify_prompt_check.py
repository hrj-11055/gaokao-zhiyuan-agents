#!/usr/bin/env python3
"""Run focused Dify prompt checks and grade the answer quality."""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT / "gaokao-proxy" / ".env"
DEFAULT_OUTPUT = Path("/tmp/gaokao_dify_prompt_check.json")

TEST_PROMPTS = [
    {
        "id": "prompt-1",
        "query": "我广东省 580 分可以上华南农业大学吗？",
        "school": "华南农业大学",
        "aliases": ["华南农业大学", "华农", "华南农"],
        "score": "580",
        "province": "广东",
    }
]


def load_dotenv(path=DEFAULT_ENV_FILE):
    """Load simple KEY=VALUE pairs without overriding existing environment."""
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def chat_api_url():
    url = os.environ.get("DIFY_CHAT_API_URL") or os.environ.get("DIFY_API_URL")
    if not url:
        raise SystemExit("错误: 未设置 DIFY_CHAT_API_URL 或 DIFY_API_URL")
    return url.rstrip("/") if url.endswith("/v1/chat-messages") else f"{url.rstrip('/')}/v1/chat-messages"


def app_api_key():
    key = os.environ.get("DIFY_APP_API_KEY") or os.environ.get("DIFY_API_KEY")
    if not key:
        raise SystemExit("错误: 未设置 DIFY_APP_API_KEY 或 DIFY_API_KEY")
    return key


def call_dify(query, user, conversation_id="", timeout=90):
    data = json.dumps({
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": user,
    }, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        chat_api_url(),
        data=data,
        headers={
            "Authorization": f"Bearer {app_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    started_at = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)
            payload["_http_status"] = response.status
            payload["_elapsed_seconds"] = round(time.monotonic() - started_at, 2)
            return payload
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "error": f"HTTP {exc.code}",
            "body": body[:500],
            "_http_status": exc.code,
            "_elapsed_seconds": round(time.monotonic() - started_at, 2),
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "_elapsed_seconds": round(time.monotonic() - started_at, 2),
        }


def contains_any(text, terms):
    return any(term in text for term in terms)


def has_uncertainty_guard(text):
    return contains_any(text, [
        "不一定",
        "不能说",
        "不能保证",
        "不保证",
        "要看",
        "得看",
        "取决于",
        "还得看",
        "需要看",
        "没办法给你准话",
        "没法给你准话",
        "不敢给你准话",
        "不是稳上",
        "不是稳的",
        "不能闭着眼睛",
        "不能闭眼",
        "建议核",
        "以官方",
    ])


def is_locally_negated(text, index):
    prefix = text[max(0, index - 8):index]
    return contains_any(prefix, ["不", "别", "没", "无", "非"])


def is_overconfident(text):
    overconfident_terms = [
        "肯定能上",
        "一定能上",
        "百分百",
        "必上",
        "稳上",
        "放心报",
        "闭眼报",
    ]
    for term in overconfident_terms:
        start = 0
        while True:
            index = text.find(term, start)
            if index == -1:
                break
            if not is_locally_negated(text, index):
                return True
            start = index + len(term)
    return False


def has_preliminary_conclusion(text):
    return contains_any(text, [
        "结论",
        "可以",
        "能上",
        "机会",
        "概率",
        "冲",
        "稳",
        "保",
        "风险",
        "不建议",
    ])


def evaluate_answer(prompt, answer):
    text = answer.strip()
    failures = []
    warnings = []

    if not text:
        failures.append("empty_answer")
    if len(text) < 80:
        failures.append("too_short")
    if "<think>" in text or "</think>" in text:
        failures.append("think_leaked")
    if not contains_any(text, prompt["aliases"]):
        failures.append("missing_school")
    if prompt["score"] not in text:
        failures.append("missing_score")
    if prompt["province"] not in text:
        failures.append("missing_province")
    if not contains_any(text, ["物理", "历史", "选科", "科类", "位次", "排位", "排名", "专业组"]):
        failures.append("missing_candidate_dimension")
    if not has_uncertainty_guard(text):
        failures.append("missing_uncertainty_guard")
    if not has_preliminary_conclusion(text):
        failures.append("missing_preliminary_conclusion")
    if not contains_any(text, ["冲", "稳", "保", "专业", "调剂", "考试院", "官网", "志愿"]):
        failures.append("missing_actionable_advice")
    if is_overconfident(text):
        failures.append("overconfident")
    if not contains_any(text, ["2024", "2025", "往年", "近年", "历年", "数据"]):
        warnings.append("missing_data_timeframe")
    if len(text) > 900:
        warnings.append("too_long")

    return {
        "status": "fail" if failures else "warning" if warnings else "pass",
        "failures": failures,
        "warnings": warnings,
        "answer_length": len(text),
    }


def run_checks(output_path=DEFAULT_OUTPUT, prompt_id=None, user_prefix="dify-compat"):
    load_dotenv()
    prompts = [prompt for prompt in TEST_PROMPTS if not prompt_id or prompt["id"] == prompt_id]
    if not prompts:
        raise SystemExit(f"错误: 未找到测试 prompt: {prompt_id}")

    results = []
    for prompt in prompts:
        user = f"{user_prefix}-{prompt['id']}"
        response = call_dify(prompt["query"], user=user)
        answer = response.get("answer", "")
        evaluation = evaluate_answer(prompt, answer) if answer else {
            "status": "fail",
            "failures": ["api_error"],
            "warnings": [],
            "answer_length": 0,
        }
        results.append({
            "id": prompt["id"],
            "query": prompt["query"],
            "http_status": response.get("_http_status"),
            "elapsed_seconds": response.get("_elapsed_seconds"),
            "conversation_id": response.get("conversation_id", ""),
            "answer": answer,
            "evaluation": evaluation,
            "api_error": response.get("error"),
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run focused Dify prompt compatibility checks")
    parser.add_argument("--prompt-id", help="Only run one prompt id, e.g. prompt-1")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON output path")
    args = parser.parse_args(argv)

    results = run_checks(output_path=args.output, prompt_id=args.prompt_id)
    for result in results:
        evaluation = result["evaluation"]
        print(f"{result['id']}: {evaluation['status']} ({evaluation['answer_length']}字)")
        if result.get("api_error"):
            print(f"  API error: {result['api_error']}")
        if evaluation["failures"]:
            print(f"  failures: {', '.join(evaluation['failures'])}")
        if evaluation["warnings"]:
            print(f"  warnings: {', '.join(evaluation['warnings'])}")
        if result.get("answer"):
            print(f"  answer: {result['answer'][:300]}")
    print(f"结果已保存: {args.output}")

    return 1 if any(item["evaluation"]["status"] == "fail" for item in results) else 0


if __name__ == "__main__":
    sys.exit(main())
