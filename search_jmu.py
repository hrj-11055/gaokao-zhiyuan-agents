import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import sys
import time
import re

def search_baidu(query):
    url = 'https://www.baidu.com/s?wd=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        results = soup.find_all('div', class_='result')
        output = f"## Results for '{query}'\n\n"
        
        for r in results:
            title = r.find('h3')
            title_text = title.text.strip() if title else 'No title'
            abstract = r.find('div', class_='c-abstract') or r.find('div', class_='content-right_8Zs40') or r.find('div', class_='c-row')
            abstract_text = abstract.text.strip() if abstract else r.text.strip()
            abstract_text = re.sub(r'\s+', ' ', abstract_text)
            output += f"**{title_text}**\n{abstract_text}\n\n"
            
        return output
    except Exception as e:
        return f"Error: {e}\n"

def search_duckduckgo(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        output = f"## DuckDuckGo Results for '{query}'\n\n"
        for i, snippet in enumerate(snippets[:10]):
            clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            clean_snippet = re.sub(r'\s+', ' ', clean_snippet)
            output += f"{i+1}. {clean_snippet}\n"
        return output + "\n"
    except Exception as e:
        return f"Error: {e}\n"

queries = [
    "吉林医药学院 学科评估 王牌专业 重点学科 硕士点",
    "吉林医药学院 2024 2025 录取分数线 各省 位次",
    "吉林医药学院 2024 就业质量报告 毕业生去向 薪酬 升学率",
    "吉林医药学院 保送生 特殊招生 2025",
    "吉林市 医药产业 经济 实习 吉林医药学院",
    "吉林医药学院 国际合作 交流项目 中外合作办学",
    "吉林医药学院 宿舍 食堂 环境 转专业 校园生活",
    "吉林医药学院 负面新闻 风险 坑 争议 评价",
    "吉林医药学院 临床医学 药学 专业评估"
]

with open("tmp_jmu_research.md", "w", encoding="utf-8") as f:
    for q in queries:
        print(f"Searching {q}...")
        f.write(search_baidu(q))
        time.sleep(1)
        f.write(search_duckduckgo(q))
        time.sleep(1)
