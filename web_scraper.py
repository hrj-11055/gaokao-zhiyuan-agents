import requests
from bs4 import BeautifulSoup
import sys
import re

def search_bing(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.find_all('li', class_='b_algo')
        print(f"--- Search Results for: {query} ---")
        for res in results[:5]:
            title_tag = res.find('h2')
            if not title_tag:
                continue
            title = title_tag.text
            link = title_tag.find('a')['href'] if title_tag.find('a') else ''
            snippet_tag = res.find('div', class_='b_caption') or res.find('div', class_='b_snippet') or res.find('p')
            snippet = snippet_tag.text if snippet_tag else ''
            print(f"Title: {title}")
            print(f"Link: {link}")
            print(f"Snippet: {snippet}\n")
    except Exception as e:
        print(f"Error searching Bing: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_bing(sys.argv[1])
