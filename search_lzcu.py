import urllib.request
import urllib.parse
import re
import sys

def search_duckduckgo(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        print(f"Results for '{query}':")
        if not snippets:
            print("No snippets found.")
        
        for i, snippet in enumerate(snippets[:10]):
            clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            print(f"{i+1}. {clean_snippet}")
        print("\n")
            
    except Exception as e:
        print(f"Error searching for {query}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_duckduckgo(sys.argv[1])
