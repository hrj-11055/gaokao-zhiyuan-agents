import requests
from bs4 import BeautifulSoup
import sys
import time

def scrape_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Extract text from paragraphs
        paragraphs = soup.find_all(['p', 'div', 'span'])
        text = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        # Limit to first 3000 chars to avoid explosion
        return text[:3000]
    except Exception as e:
        return f"Error scraping {url}: {e}"

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
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
                
        # Scrape top 2 URLs for deeper context
        for u in urls_to_scrape[:2]:
            output += f"### Content from {u}\n"
            content = scrape_url(u)
            output += f"{content}\n\n"
            time.sleep(1)
            
    except Exception as e:
        output += f"Error searching: {e}\n"
    
    return output

if __name__ == "__main__":
    queries = [
        "青岛科技大学 王牌学科 A类学科 院士 国家级实验室",
        "青岛科技大学 2024 2025 录取分数线 各省 位次",
        "青岛科技大学 就业质量报告 毕业生薪酬 就业行业 深造率",
        "青岛科技大学 青岛市 产业结合 实习机会 区位优势",
        "青岛科技大学 中外合作办学 交换生 国际化",
        "青岛科技大学 校园生活 转专业政策 宿舍 食堂 评价",
        "青岛科技大学 负面新闻 专业裁撤 办学争议 风险事件"
    ]
    with open(".firecrawl/qd-tech-full-research.md", "w", encoding="utf-8") as f:
        for q in queries:
            print(f"Searching: {q}")
            res = search_ddg_lite(q)
            f.write(res)
            f.write("---\n")
            time.sleep(2)
    print("Done. Saved to .firecrawl/qd-tech-full-research.md")
