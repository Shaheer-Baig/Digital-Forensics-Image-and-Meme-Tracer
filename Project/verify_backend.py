from scraper import Scraper
import time

def test_scraper():
    print("Testing Selenium Scraper...")
    try:
        s = Scraper()
        
        # Test Text Search (Google)
        print("\n1. Testing Google Search (Selenium)...")
        results = s.search_google_selenium("python programming", "reddit.com")
        print(f"   Found {len(results)} results.")
        if results:
            print(f"   Sample: {results[0]['title']} - {results[0]['url']}")
            
        # Test Visual Search (Bing)
        print("\n2. Testing Visual Search (Bing Selenium)...")
        # Use a known image URL
        test_url = "https://files.catbox.moe/8y8z8z.jpg" 
        results = s.search_bing_selenium(test_url)
        print(f"   Found {len(results)} results.")
        if results:
            print(f"   Sample: {results[0]['title']} - {results[0]['url']}")
            
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_scraper()
