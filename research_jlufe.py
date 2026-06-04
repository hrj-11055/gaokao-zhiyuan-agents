import requests
from bs4 import BeautifulSoup
import sys
import time

def scrape_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
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
        for u in urls_to_scrape[:3]:
            output += f"### Content from {u}\n"
            content = scrape_url(u)
            output += f"{content}\n\n"
            time.sleep(1)
            
    except Exception as e:
        output += f"Error searching: {e}\n"
    
    return output

if __name__ == "__main__":
    queries = [
        "吉林财经大学 优势学科 A类学科 第五轮 王牌专业",
        "吉林财经大学 2024 2025 录取分数线 各省 位次",
        "吉林财经大学 2024 届毕业生就业质量 深造率 去向 薪酬",
        "吉林财经大学 长春市 区位优势 产业结合 经济发展",
        "吉林财经大学 中外合作办学 国际合作项目 交换生",
        "吉林财经大学 校园生活 食堂 宿舍环境 转专业政策",
        "吉林财经大学 评价 负面事件 坑 吐槽",
        "吉林财经大学 院士 国家级实验室 科研平台"
    ]
    with open(".firecrawl/jlufe-full-research.md", "w", encoding="utf-8") as f:
        for q in queries:
            print(f"Searching: {q}")
            res = search_ddg_lite(q)
            f.write(res)
            f.write("---\n")
            time.sleep(2)
    print("Done.")
