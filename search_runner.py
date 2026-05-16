import custom_search
import os

queries = {
    "jn_academic.txt": "济南大学 第五轮学科评估 A类 B类 C类 王牌专业 重点实验室 院士",
    "jn_admission.txt": "济南大学 2024 2023 录取分数线 山东 浙江 河南 广东 位次趋势",
    "jn_employment.txt": "济南大学 2024 2023 毕业生就业质量报告 深造率 考研率 薪酬 去向",
    "jn_industry.txt": "济南大学 产业合作 济南市 经济格局 实习就业 优势学科耦合",
    "jn_international.txt": "济南大学 国际合作办学 交换生 中外合作 泉城学院 国际化",
    "jn_campus.txt": "济南大学 转专业政策 宿舍条件 食堂 学术氛围 贴吧 评价",
    "jn_risks.txt": "济南大学 负面新闻 争议 避坑 专业裁撤 缺点"
}

os.makedirs(".firecrawl", exist_ok=True)

for filename, query in queries.items():
    print(f"Running query for {filename}: {query}")
    try:
        res = custom_search.search_duckduckgo_lite(query)
        with open(f".firecrawl/{filename}", "w", encoding='utf-8') as f:
            f.write(res)
    except Exception as e:
        print(f"Error for {filename}: {e}")

print("All searches completed.")
