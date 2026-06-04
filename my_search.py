import urllib.request
import urllib.parse
import re
import sys
import json

def search(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        results = []
        # Find all result blocks
        blocks = re.findall(r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        for url_match, snippet in blocks[:5]:
            clean_url = urllib.parse.unquote(url_match.replace('//duckduckgo.com/l/?uddg=', '').split('&rut=')[0])
            if clean_url.startswith('http'):
                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                results.append({"url": clean_url, "snippet": clean_snippet})
                
        print(json.dumps(results, ensure_ascii=False, indent=2))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search(sys.argv[1])
