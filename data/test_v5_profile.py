#!/usr/bin/env python3
"""Multi-turn conversation test for Prompt v5 user profile collection."""

import json
import os
import urllib.request
import ssl

API_BASE = os.environ.get("DIFY_CHAT_API_URL", "http://8.135.37.159:8080/v1/chat-messages")
API_KEY = os.environ.get("DIFY_APP_API_KEY")
if not API_KEY:
    raise SystemExit("错误: 未设置环境变量 DIFY_APP_API_KEY")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def send_message(query, conversation_id="", user="test-v5"):
    """Send a chat message and get the full response."""
    data = json.dumps({
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": user
    }).encode("utf-8")

    req = urllib.request.Request(
        API_BASE,
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except Exception as e:
        return {"error": str(e)}


def test_profile_collection():
    """Test progressive profile collection across 4 turns."""
    user = "test-v5-profile"
    turns = [
        ("你好，我想咨询高考志愿", "R1: 应追问省份+分数+选科"),
        ("河北物理类，580分", "R2: 给具体建议+追问家庭/职业"),
        ("家里条件一般，爸爸在电力局上班，我想求稳", "R3: 利用画像给建议+追问地域/科目"),
        ("数学挺好，不太想出省", "R4: 高度个性化建议+追问风险偏好"),
    ]

    cid = ""
    print("=" * 80)
    print("Prompt v5 — 用户画像收集多轮测试")
    print("=" * 80)

    for i, (query, expected) in enumerate(turns, 1):
        print(f"\n{'='*60}")
        print(f"第 {i} 轮 | 用户输入: {query}")
        print(f"预期: {expected}")
        print("-" * 60)

        result = send_message(query, cid, user)

        if "error" in result:
            print(f"ERROR: {result['error']}")
            continue

        answer = result.get("answer", "")
        if not cid:
            cid = result.get("conversation_id", "")
            print(f"Conversation ID: {cid}")

        # Truncate long answers for display
        if len(answer) > 600:
            print(answer[:500])
            print(f"\n... (共 {len(answer)} 字，已截断)")
        else:
            print(answer)

        # Check what profile dimensions were collected
        print(f"\n[字数: {len(answer)}]")

    print(f"\n{'='*80}")
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_profile_collection()
