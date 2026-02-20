from scraper import Scraper
import requests

def debug_search():
    s = Scraper()
    # Use a known image URL for testing (e.g., the Trump image user uploaded or a generic one)
    # Since I can't easily access the user's local file path in this script without them passing it,
    # I'll use a public URL of a cat or similar, or just test the text search first.
    
    print("--- Debugging Text Search (Google) ---")
    results = s.search_google("test", "reddit.com", num_results=1)
    print(f"Google Results: {len(results)}")
    
    print("\n--- Debugging Visual Search (Bing) ---")
    # Using a static image URL for testing
    test_img_url = "https://files.catbox.moe/8y8z8z.jpg" # Placeholder or previous upload if known
    
    # Manually call the Bing URL to see response
    url = f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHMP&q=imgurl:{test_img_url}"
    headers = {'User-Agent': s.ua.random}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Bing Status Code: {resp.status_code}")
        print(f"Bing Page Title: {resp.text[:500].split('<title>')[-1].split('</title>')[0] if '<title>' in resp.text else 'No Title'}")
        
        if "captcha" in resp.text.lower() or "challenge" in resp.text.lower():
            print("!!! CAPTCHA DETECTED !!!")
    except Exception as e:
        print(f"Bing Error: {e}")

if __name__ == "__main__":
    debug_search()
