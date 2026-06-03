#!/usr/bin/env python3
"""批量跑 20 题测试，保存回答到文件"""
import os
import requests, json, time

API_URL = os.environ.get("DIFY_CHAT_API_URL", "http://159.75.110.157/v1/chat-messages")
API_KEY = os.environ.get("DIFY_APP_API_KEY")
if not API_KEY:
    raise SystemExit("错误: 未设置环境变量 DIFY_APP_API_KEY")

QUESTIONS = [
    # 第一组：追问触发
    ("Q1", "你好，我想咨询高考志愿"),
    ("Q2", "我考了580分，能上什么学校？"),
    ("Q3", "计算机专业怎么样？"),
    ("Q4", "推荐几个好就业的专业"),
    # 第二组：核心场景
    ("Q5", "我是河北物理类考生，考了620分，能冲哪些211？"),
    ("Q6", "广东历史类，560分，想学法学，有哪些学校推荐？"),
    ("Q7", "河北物理类530分，家庭条件一般，想找一个好就业的专业"),
    ("Q8", "广东物理类480分，刚过本科线，怎么填报最稳？"),
    # 第三组：专业咨询
    ("Q9", "人工智能和计算机科学有什么区别？哪个更推荐？"),
    ("Q10", "电气工程及其自动化这个专业就业方向是什么？"),
    ("Q11", "土木工程现在还能报吗？听说行业不行了"),
    ("Q12", "张雪峰老师怎么看新闻传播专业？"),
    # 第四组：学校对比
    ("Q13", "燕山大学和河北工业大学哪个好？我河北物理类570分"),
    ("Q14", "深圳大学和广东工业大学，广东物理类560分选哪个？"),
    ("Q15", "省内大学和省外同档次大学怎么选？"),
    # 第五组：边界情况
    ("Q16", "我家孩子今年高考，但是我什么都不懂，你能从头教我吗？"),
    ("Q17", "中外合作办学值得去吗？一年学费好几万"),
    ("Q18", "我是复读生，今年考得还不如去年，要不要再复读？"),
    ("Q19", "考研和直接就业，哪个更划算？报志愿的时候要不要考虑这个？"),
    ("Q20", "张老师，你觉得学医怎么样？临床医学分数那么高值得冲吗？"),
]

OUTPUT_FILE = "/tmp/gaokao_test_results.json"

results = []
for qid, question in QUESTIONS:
    print(f"Testing {qid}: {question[:30]}...")
    try:
        r = requests.post(API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": {},
                "query": question,
                "response_mode": "blocking",
                "user": f"test-user-{qid}",
            },
            timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            answer = data.get("answer", "")
            conv_id = data.get("conversation_id", "")
            results.append({
                "id": qid,
                "question": question,
                "answer": answer,
                "conversation_id": conv_id,
                "answer_length": len(answer),
                "status": "ok"
            })
            print(f"  OK ({len(answer)}字)")
        else:
            results.append({
                "id": qid,
                "question": question,
                "answer": f"ERROR: {r.status_code} {r.text[:200]}",
                "status": "error"
            })
            print(f"  ERROR: {r.status_code}")
    except Exception as e:
        results.append({
            "id": qid,
            "question": question,
            "answer": f"EXCEPTION: {e}",
            "status": "error"
        })
        print(f"  EXCEPTION: {e}")

    time.sleep(3)  # avoid rate limiting

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nDone! {len(results)} questions tested. Results saved to {OUTPUT_FILE}")
ok_count = sum(1 for r in results if r["status"] == "ok")
print(f"Success: {ok_count}/{len(results)}")
