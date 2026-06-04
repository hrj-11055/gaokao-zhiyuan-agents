import custom_search
import os

queries = {
    "im_academic.txt": "内蒙古财经大学 第五轮学科评估 A类 王牌专业 重点实验室",
    "im_admission.txt": "内蒙古财经大学 2024 2023 录取分数线 各省 位次趋势 竞争程度",
    "im_employment.txt": "内蒙古财经大学 2024 2023 毕业生就业质量年度报告 深造率 薪酬 去向",
    "im_industry.txt": "内蒙古财经大学 产业合作 呼和浩特市 经济格局 实习就业 优势学科",
    "im_international.txt": "内蒙古财经大学 国际合作办学 交换生 中外合作 留学生",
    "im_campus.txt": "内蒙古财经大学 转专业政策 宿舍条件 食堂 学术氛围 评价 传统",
    "im_risks.txt": "内蒙古财经大学 负面新闻 争议 避坑 专业裁撤 地理劣势"
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
