import urllib.request
import urllib.parse
import re
import sys
import json

def search_duckduckgo(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        # Regex to find result links and titles
        # This is a basic regex for DuckDuckGo HTML results
        pattern = re.compile(r'<a class="result__url" href="([^"]+)">(.*?)</a>', re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(html)
        
        snippet_pattern = re.compile(r'<a class="result__snippet[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        snippets = snippet_pattern.findall(html)
        
        results = []
        for i in range(min(len(matches), 5)):
            url = urllib.parse.unquote(matches[i][0]).replace('//duckduckgo.com/l/?uddg=', '').split('&rut=')[0]
            title = re.sub(r'<[^>]+>', '', matches[i][1]).strip()
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
            results.append({
                "url": url,
                "title": title,
                "snippet": snippet
            })
            
        print(json.dumps(results, ensure_ascii=False, indent=2))
            
    except Exception as e:
        print(f"Error searching for {query}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        search_duckduckgo(query)
    else:
        print("Usage: python search_duckduckgo_urls.py '<query>'")
