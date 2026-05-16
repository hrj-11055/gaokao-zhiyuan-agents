import urllib.request
import urllib.parse
import re
import sys

def search_baidu(query):
    url = 'https://www.baidu.com/s?wd=' + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        
        # Simple extraction of text content from search results
        snippets = re.findall(r'<div class="c-abstract.*?>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
        if not snippets:
            # try another pattern
            snippets = re.findall(r'<span class="content-right_8Zs40.*?>(.*?)</span>', html, re.IGNORECASE | re.DOTALL)
            
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
        search_baidu(sys.argv[1])
