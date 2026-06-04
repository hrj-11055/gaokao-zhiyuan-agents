import requests
from bs4 import BeautifulSoup
import sys
import time

def scrape_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Extract text from paragraphs
        paragraphs = soup.find_all(['p', 'div', 'span', 'article', 'section'])
        text = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        # Limit to first 5000 chars to avoid explosion
        return text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {e}"

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    output = f"## Query: {query}\n\n"
    try:
        resp = requests.post(url, data=data, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.find_all('tr')
        
        urls_to_scrape = []
        for row in results:
            td = row.find('td', class_='result-snippet')
            if td:
                output += f"**Snippet:** {td.text.strip()}\n"
            a = row.find('a', class_='result-url')
            if a:
                href = a['href']
                if href.startswith('//'):
                    href = "https:" + href
                output += f"**URL:** {href}\n\n"
                urls_to_scrape.append(href)
                
        # Scrape top 3 URLs for deeper context
        for u in urls_to_scrape[:3]:
            if "baidu.com" in u or "zhihu.com" in u:
                # Basic scraping might fail on baidu/zhihu, but we try anyway
                pass
            output += f"### Content from {u}\n"
            content = scrape_url(u)
            output += f"{content}\n\n"
            time.sleep(1)
            
    except Exception as e:
        output += f"Error searching: {e}\n"
    
    return output

if __name__ == "__main__":
    queries = [
        "金华职业技术大学 王牌专业 A类 重点实验室 院士 国家级",
        "金华职业技术大学 2024 2025 录取分数线 浙江 各省 位次 提前批",
        "金华职业技术大学 毕业生 就业质量报告 深造率 专升本 薪酬",
        "金华职业技术大学 金华市 产业结合 实习 区位",
        "金华职业技术大学 中外合作办学 国际合作",
        "金华职业技术大学 宿舍 食堂 转专业 校园氛围 评价",
        "金华职业技术大学 负面 争议 专业裁撤 风险",
        "金华职业技术大学 升格 本科 专升本 情况"
    ]
    with open(".firecrawl/jinhua-full-research.md", "w", encoding="utf-8") as f:
        for q in queries:
            print(f"Searching: {q}")
            res = search_ddg_lite(q)
            f.write(res)
            f.write("---\n")
            time.sleep(2)
    print("Done. Saved to .firecrawl/jinhua-full-research.md")
