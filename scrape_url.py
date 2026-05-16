import requests
from bs4 import BeautifulSoup
import sys
import re

def scrape(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # remove scripts and styles
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator='\n')
        # clean empty lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        print(f"--- Extracted text from {url} ---")
        for i, line in enumerate(lines):
            # Print at most 200 lines to avoid spam
            if i > 200:
                print("... [TRUNCATED] ...")
                break
            print(line)
            
    except Exception as e:
        print(f"Error scraping {url}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape(sys.argv[1])