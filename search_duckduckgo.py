import urllib.request
import urllib.parse
import re

def search_duckduckgo(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        # Extract snippets using regex since we might not have BeautifulSoup
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        print(f"Results for '{query}':")
        if not snippets:
            print("No snippets found.")
        
        for i, snippet in enumerate(snippets[:5]):
            clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            print(f"{i+1}. {clean_snippet}")
        print("\n")
            
    except Exception as e:
        print(f"Error searching for {query}: {e}")

if __name__ == "__main__":
    queries = [
        "江西警察学院 2024 2025 录取分数线 各省",
        "江西警察学院 就业质量报告 毕业去向 薪酬",
        "江西警察学院 学科评估 王牌专业",
        "江西警察学院 宿舍 食堂 校园生活 评价"
    ]
    for q in queries:
        search_duckduckgo(q)
