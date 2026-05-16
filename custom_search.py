import urllib.request
import urllib.parse
import re
import json
from bs4 import BeautifulSoup
import sys
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        response = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        html = response.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000] # return first 5000 chars
    except Exception as e:
        return f"Error fetching {url}: {e}"

def search_duckduckgo_lite(query):
    print(f"Searching for: {query}")
    url = 'https://html.duckduckgo.com/html/'
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    try:
        response = urllib.request.urlopen(req, timeout=10, context=ctx)
        html = response.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        for a in soup.select('.result__url'):
            link = a.get('href')
            if link and not link.startswith('//'):
                # Sometimes duckduckgo links are absolute
                if link.startswith('/l/?'):
                    # Extract the actual URL
                    m = re.search(r'uddg=([^&]+)', link)
                    if m:
                        actual_url = urllib.parse.unquote(m.group(1))
                        results.append(actual_url)
                else:
                    results.append(link)
                    
        print(f"Found {len(results)} links")
        
        snippets = soup.select('.result__snippet')
        
        all_text = ""
        for i, snippet in enumerate(snippets[:3]):
            all_text += f"\nSnippet {i+1}:\n" + snippet.get_text(strip=True) + "\n"
            if i < len(results):
                all_text += f"\nContent from {results[i]}:\n"
                all_text += fetch_url(results[i]) + "\n"
                
        return all_text
    except Exception as e:
        print(f"Error in search: {e}")
        return ""

if __name__ == "__main__":
    query = sys.argv[1]
    res = search_duckduckgo_lite(query)
    with open(f".firecrawl/custom_search_{hash(query)}.txt", "w", encoding='utf-8') as f:
        f.write(res)
    print(f"Done for {query}")
