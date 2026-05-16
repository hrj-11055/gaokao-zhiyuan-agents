import requests
from bs4 import BeautifulSoup

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.post(url, data=data, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.find_all('tr')
        print(f"Results for: {query}")
        for row in results:
            td = row.find('td', class_='result-snippet')
            if td:
                print("Snippet:", td.text.strip())
            a = row.find('a', class_='result-url')
            if a:
                print("Title:", a.text.strip())
                print("URL:", a['href'])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    search_ddg_lite("青岛科技大学 第五轮学科评估")
