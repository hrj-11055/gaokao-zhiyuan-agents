import urllib.request
import urllib.parse
import re
import sys

def search(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        links = re.findall(r'<a class="result__url" href="([^"]+)">', html)
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        for i, (link, snippet) in enumerate(zip(links[:5], snippets[:5])):
            link = urllib.parse.unquote(link)
            if 'uddg=' in link:
                link = link.split('uddg=')[1].split('&')[0]
            clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            print(f"URL: {link}")
            print(f"Snippet: {clean_snippet}\n")
    except Exception as e:
        print(f"Error: {e}")

search(sys.argv[1])
