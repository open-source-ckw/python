# search_url = f"https://duckduckgo.com/?ia=web&assist=true&kp=-1&kz=1&kav=1&q=!assist+{urllib.parse.quote(sq)}"

import requests
from bs4 import BeautifulSoup
import urllib.parse
import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_web(sq: str) -> dict:
    try:
        # Search DuckDuckGo directly
        #search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(sq)}"
        #search_url = f"https://duckduckgo.com/?ia=web&assist=true&kp=-1&q=!assist+{urllib.parse.quote(sq)}"
        #search_url = f"https://www.hotbot.com/chat/?q={urllib.parse.quote(sq)}"
        search_url = f"https://www.startpage.com/do/search?query={urllib.parse.quote(sq)}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text from search results
        results = []
        for result in soup.find_all('div', class_='result'):
            text = result.get_text(strip=True)
            if text:
                results.append(text)
        
        # Join all results
        full_text = ' '.join(results)
        
        return {
            "status": "success",
            "content": full_text,
            "word_count": len(full_text.split())
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

print(search_web("news update for today"))