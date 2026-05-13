import os
import time
from volcenginesdkarkruntime import Ark

# 配置信息
api_key = os.environ.get("ARK_API_KEY", "b38b2f1e-0477-4472-9c01-d6cc58c0cfdd")
endpoint_id = "ep-20260512182636-8kq8g"

# 5 个不同级别的系统角色 (System Roles)
SYSTEM_ROLES = [
    "你是一个通用的 AI 助手。",
    "你是一个专业的教育咨询师，擅长学业规划。",
    "你是一个高考志愿填报专家，精通各大学录取分数线和专业前景。",
    "你是一个职业规划师，擅长根据专业分析未来的行业趋势和薪酬发展。",
    "你是一个资深的升学战略专家，能从宏观经济、行业周期和个人特质三个维度提供深度咨询。"
]

# 4 个不同复杂度的用户提示词 (User Prompts)
USER_PROMPTS = [
    # Level 1: 简单事实查询
    "计算机科学与技术专业主要学什么课程？",
    
    # Level 2: 关联性分析
    "对比一下软件工程和人工智能专业在就业方向上的核心差异。",
    
    # Level 3: 场景化建议
    "一个理科男生，分数在省排名 5000 左右，对数学感兴趣但不想学纯数学，请推荐 3 个专业并说明理由。",
    
    # Level 4: 深度战略规划
    "结合未来 10 年 AI 技术对就业市场的冲击，请分析现在报考『电子信息工程』专业的长期风险与收益，并给出一个跨学科的学习路径建议。"
]

def run_evaluation():
    client = Ark(api_key=api_key)
    results = []

    print(f"开始执行 20 次模型测评 (Endpoint: {endpoint_id})...\n")

    for s_idx, system_content in enumerate(SYSTEM_ROLES):
        for u_idx, user_content in enumerate(USER_PROMPTS):
            case_num = s_idx * len(USER_PROMPTS) + u_idx + 1
            print(f"[{case_num}/20] 测试中: 系统角色 {s_idx+1} | 提示词复杂度 {u_idx+1}...")
            
            try:
                start_time = time.time()
                completion = client.chat.completions.create(
                    model=endpoint_id,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.7
                )
                duration = time.time() - start_time
                
                # 记录结果摘要
                results.append({
                    "case": case_num,
                    "system_level": s_idx + 1,
                    "prompt_level": u_idx + 1,
                    "tokens": completion.usage.total_tokens,
                    "duration": f"{duration:.2f}s",
                    "preview": completion.choices[0].message.content[:50].replace("\n", " ") + "..."
                })
                
                # 适当间隔，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"   ✗ Case {case_num} 失败: {e}")

    # 打印简要报告
    print("\n" + "="*80)
    print(f"{'编号':<6} | {'角色':<6} | {'难度':<6} | {'Tokens':<8} | {'耗时':<8} | {'回答预览'}")
    print("-" * 80)
    for r in results:
        print(f"{r['case']:<8} | {r['system_level']:<8} | {r['prompt_level']:<8} | {r['tokens']:<10} | {r['duration']:<10} | {r['preview']}")
    print("="*80)
    print(f"\n测评完成！总计成功 {len(results)}/20 次。")
    print("真实用量已产生，你可以在 15 分钟后去火山引擎控制台下载合同和查阅账单。")

if __name__ == "__main__":
    run_evaluation()
