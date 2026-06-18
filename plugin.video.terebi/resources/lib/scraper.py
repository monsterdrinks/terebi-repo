import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://dlhd.pk"
CHANNELS_URL = f"{BASE_URL}/24-7-channels.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Referer": BASE_URL
}

def get_channels():
    """
    Scrapes the 24/7 channels page and returns a list of channels.
    """
    channels = []
    try:
        response = requests.get(CHANNELS_URL, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # In 24-7-channels.php, channels are usually listed as links to watch.php
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if 'watch.php?id=' in href:
                name = a_tag.get_text(strip=True)
                # Cleanup name if it has ID text inside
                name = re.sub(r'ID:\s*\d+', '', name).strip()
                
                # Make URL absolute
                if href.startswith('/'):
                    url = BASE_URL + href
                elif href.startswith('http'):
                    url = href
                else:
                    url = BASE_URL + '/' + href
                    
                # Avoid duplicates
                if not any(c['url'] == url for c in channels) and name:
                    # Guess logo filename based on API documentation behavior
                    logo_filename = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
                    logo_url = f"{BASE_URL}/logos/{logo_filename}.png"
                    
                    channels.append({
                        "name": name,
                        "url": url,
                        "id": href.split('id=')[-1],
                        "logo": logo_url
                    })
                    
        return channels
    except Exception as e:
        print(f"Error scraping channels: {e}")
        return []

import base64

def get_stream_url(watch_url):
    """
    Extracts the final .m3u8 stream URL by parsing the inner iframes.
    """
    try:
        # Step 1: Fetch the watch page (watch.php?id=...)
        response = requests.get(watch_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for the player iframe (usually points to stream-xxx.php)
        iframe = soup.find('iframe', id='playerFrame')
        if not iframe or 'src' not in iframe.attrs:
            return None
            
        iframe_src = iframe['src']
        if iframe_src.startswith('/'):
            iframe_src = BASE_URL + iframe_src
            
        # Step 2: Fetch the stream wrapper page (stream-xxx.php)
        stream_headers = HEADERS.copy()
        stream_headers["Referer"] = watch_url
        res2 = requests.get(iframe_src, headers=stream_headers)
        res2.raise_for_status()
        
        # Step 3: Find the inner iframe inside stream-xxx.php
        inner_iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', res2.text, re.IGNORECASE)
        if not inner_iframe_match:
            return None
            
        inner_src = inner_iframe_match.group(1)
        if inner_src.startswith('/'):
            inner_src = BASE_URL + inner_src
            
        # Step 4: Fetch the final inner iframe
        inner_headers = HEADERS.copy()
        inner_headers["Referer"] = iframe_src
        res3 = requests.get(inner_src, headers=inner_headers)
        res3.raise_for_status()
        
        # Step 5: Extract the base64 encoded source from window.atob('...') or similar
        atob_match = re.search(r"window\.atob\(['\"]([^'\"]+)['\"]\)", res3.text)
        if atob_match:
            encoded_m3u8 = atob_match.group(1)
            m3u8_url = base64.b64decode(encoded_m3u8).decode('utf-8')
            return m3u8_url, inner_src # Return the referer too
            
        # Fallback: look for direct source: '...'
        source_match = re.search(r"source:\s*['\"](http[^'\"]+\.m3u8[^'\"]*)['\"]", res3.text)
        if source_match:
            return source_match.group(1), inner_src
            
    except Exception as e:
        print(f"Error extracting stream URL: {e}")
        
    return None, None
