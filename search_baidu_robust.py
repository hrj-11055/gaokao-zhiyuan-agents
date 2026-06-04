import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import sys
import time

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
        
        # Get text from search results
        results = soup.find_all('div', class_='result')
        output = f"## Results for '{query}'\n\n"
        
        for r in results:
            title = r.find('h3')
            title_text = title.text.strip() if title else 'No title'
            abstract = r.find('div', class_='c-abstract') or r.find('div', class_='content-right_8Zs40') or r.find('div', class_='c-row')
            abstract_text = abstract.text.strip() if abstract else r.text.strip()
            # Clean up newlines and excessive spaces
            import re
            abstract_text = re.sub(r'\s+', ' ', abstract_text)
            
            output += f"**{title_text}**\n{abstract_text}\n\n"
            
        return output
    except Exception as e:
        return f"Error: {e}\n"

queries = [
    "金华职业技术大学 2024 2025 录取分数线 各省 位次",
    "金华职业技术大学 就业质量报告 深造率 专升本 薪酬",
    "金华职业技术大学 产业结合 区位优势",
    "金华职业技术大学 中外合作办学",
    "金华职业技术大学 宿舍 食堂 评价",
    "金华职业技术大学 升格职业本科"
]

with open(".firecrawl/jinhua_baidu.md", "w", encoding="utf-8") as f:
    for q in queries:
        print(f"Searching {q}...")
        f.write(search_baidu(q))
        time.sleep(1)
