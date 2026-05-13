import os
from volcenginesdkarkruntime import Ark

# 配置信息
# 建议通过环境变量设置 ARK_API_KEY
# export ARK_API_KEY="b38b2f1e-0477-4472-9c01-d6cc58c0cfdd"
api_key = os.environ.get("ARK_API_KEY", "b38b2f1e-0477-4472-9c01-d6cc58c0cfdd")
endpoint_id = "ep-20260512182636-8kq8g"

def test_deepseek_v3():
    print(f"--- 正在调用火山引擎 DeepSeek V3 (Endpoint: {endpoint_id}) ---")
    
    client = Ark(api_key=api_key)

    try:
        # 非流式调用（方便直接看结果）
        completion = client.chat.completions.create(
            model=endpoint_id,
            messages=[
                {"role": "system", "content": "你是一个高考志愿填报专家。"},
                {"role": "user", "content": "请简述计算机科学与技术专业的就业前景，字数控制在 100 字以内。"},
            ],
        )
        
        print("\n[AI 回复]:")
        print(completion.choices[0].message.content)
        
        print("\n[用量统计]:")
        print(f"Prompt Tokens: {completion.usage.prompt_tokens}")
        print(f"Completion Tokens: {completion.usage.completion_tokens}")
        print(f"Total Tokens: {completion.usage.total_tokens}")
        
        print("\n✅ 调用成功！现在你可以去火山引擎控制台查看账单详情并申请合同了。")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")

if __name__ == "__main__":
    test_deepseek_v3()
