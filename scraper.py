import requests
from bs4 import BeautifulSoup
import easyocr
from fake_useragent import UserAgent
import urllib.parse
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class Scraper:
    def __init__(self, api_key=None, rapidapi_key=None):
        self.ua = UserAgent()
        self.api_key = api_key
        self.rapidapi_key = rapidapi_key
        # Initialize EasyOCR
        self.reader = easyocr.Reader(['en'], gpu=True) 
        self.session = requests.Session()
        
        # Initialize Selenium (always needed for fallbacks or other engines)
        print("Initializing Browser Driver...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument(f"user-agent={self.ua.random}")
        chrome_options.page_load_strategy = 'eager'
        
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Selenium: {e}")
            self.driver = None

    # ... (existing methods) ...

    def search_rapidapi_reverse_image(self, image_url):
        """
        Uses RapidAPI 'reverse-image-search1' for visual matches.
        """
        if not self.rapidapi_key: return []
        
        print(f"Querying RapidAPI (Reverse Image) with URL: {image_url}")
        try:
            url = "https://reverse-image-search1.p.rapidapi.com/reverse-image-search"
            querystring = {"url": image_url, "limit": "10", "safe_search": "off"}
            headers = {
                "x-rapidapi-host": "reverse-image-search1.p.rapidapi.com",
                "x-rapidapi-key": self.rapidapi_key
            }
            
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()
            
            candidates = []
            # The API response structure varies, assuming standard list of results
            # Based on typical RapidAPI reverse image responses:
            if 'data' in data:
                for item in data['data']:
                    link = item.get('url') or item.get('page_url')
                    title = item.get('title')
                    thumb = item.get('thumbnail_url') or item.get('preview_url')
                    if link:
                        candidates.append({
                            'url': link, 
                            'title': title, 
                            'platform': 'Web', 
                            'user': 'Unknown',
                            'thumbnail': thumb
                        })
            
            print(f"Found {len(candidates)} matches via RapidAPI Reverse Image.")
            return candidates
        except Exception as e:
            print(f"RapidAPI Reverse Image Error: {e}")
            return []

    def get_page_source_rapidapi(self, url):
        """
        Uses RapidAPI 'bypass-cloudflare-api' to get page source of protected sites.
        """
        if not self.rapidapi_key: return None
        
        print(f"Fetching source via RapidAPI (Cloudflare Bypass): {url}")
        try:
            api_url = "https://bypass-cloudflare-api.p.rapidapi.com/get_page_source"
            querystring = {"url": url}
            headers = {
                "x-rapidapi-host": "bypass-cloudflare-api.p.rapidapi.com",
                "x-rapidapi-key": self.rapidapi_key,
                "Content-Type": "application/json"
            }
            
            # The user example was POST with data '{}' but also had query params. 
            # Usually GET is enough for page source, but let's follow the POST pattern if needed.
            # The user example: POST ... url in query param ... data '{}'
            
            response = requests.post(api_url, headers=headers, params=querystring, json={})
            
            if response.status_code == 200:
                data = response.json()
                # The API usually returns content in a field like 'content' or 'result'
                return data.get('result') or data.get('content') or response.text
            return None
        except Exception as e:
            print(f"RapidAPI Cloudflare Bypass Error: {e}")
            return None

    def get_metadata(self, url):
        """Extracts metadata using requests, Selenium, or RapidAPI."""
        metadata = {'url': url, 'date': None, 'user': 'Unknown', 'platform': 'Web', 'title': ''}
        
        # Helper to parse HTML
        def parse_html(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            if soup.title: metadata['title'] = soup.title.string.strip()
            
            date_meta = soup.find('meta', property='article:published_time') or \
                        soup.find('meta', property='og:published_time') or \
                        soup.find('meta', attrs={'name': 'date'}) or \
                        soup.find('time')
                        
            if date_meta:
                content = date_meta.get('content') or date_meta.get('datetime')
                if content:
                    try:
                        import dateutil.parser
                        dt = dateutil.parser.parse(content)
                        metadata['date'] = dt.timestamp()
                    except:
                        pass
        
        try:
            headers = {'User-Agent': self.ua.random}
            
            # 1. Try Standard Requests
            try:
                if "reddit.com" in url:
                    metadata['platform'] = 'Reddit'
                    json_url = url.rstrip('/') + ".json"
                    resp = self.session.get(json_url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        post = data[0]['data']['children'][0]['data']
                        metadata['date'] = post.get('created_utc')
                        metadata['user'] = post.get('author')
                        metadata['title'] = post.get('title')
                        return metadata
                
                resp = self.session.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    parse_html(resp.text)
                    return metadata
            except:
                pass # Fallback to next method

            # 2. Try RapidAPI Cloudflare Bypass (if requests failed/blocked)
            if self.rapidapi_key:
                source = self.get_page_source_rapidapi(url)
                if source:
                    parse_html(source)
                    return metadata

            # 3. Fallback to Selenium (if initialized)
            if self.driver:
                self.driver.get(url)
                parse_html(self.driver.page_source)

        except Exception as e:
            print(f"Metadata Error {url}: {e}")
            
        return metadata

    def hybrid_search(self, image_path):
        candidates = []
        
        # 1. OCR Search
        text = self.extract_text(image_path)
        if text:
            # DuckDuckGo (Must be included as per user request)
            print("Searching DuckDuckGo (Text)...")
            candidates.extend(self.search_ddg(text, "reddit.com"))
            candidates.extend(self.search_ddg(text, "pinterest.com"))
            
            if self.api_key:
                # Use SerpApi for Text
                candidates.extend(self.search_serpapi_text(text, "reddit.com"))
                candidates.extend(self.search_serpapi_text(text, "pinterest.com"))
            else:
                # Fallback Selenium Google
                g_res = self.search_google_selenium(text, "reddit.com")
                candidates.extend(g_res)
                p_res = self.search_google_selenium(text, "pinterest.com")
                candidates.extend(p_res)
            
        # 2. Visual Search
        image_url = self.upload_image(image_path)
        if image_url:
            # RapidAPI Reverse Image (New)
            if self.rapidapi_key:
                candidates.extend(self.search_rapidapi_reverse_image(image_url))

            # SerpApi
            if self.api_key:
                print("Using SerpApi for Visual Search...")
                candidates.extend(self.search_serpapi(image_url))
                candidates.extend(self.search_serpapi_visual_engines(image_url, "bing_reverse_image_search"))
                candidates.extend(self.search_serpapi_visual_engines(image_url, "yandex_images"))
            else:
                # Fallback Selenium
                print("Using Selenium for Visual Search...")
                candidates.extend(self.search_google_lens_selenium(image_url))
                candidates.extend(self.search_bing_selenium(image_url))
                candidates.extend(self.search_yandex_selenium(image_url))
        
        # 3. Filter & Enrich
        unique = {c['url']: c for c in candidates}.values()
        enriched = []
        
        allowed_domains = ["reddit.com", "pinterest.com"]
        
        for c in unique:
            # Strict Filtering
            if not any(d in c['url'] for d in allowed_domains):
                continue

            # If it's a manual check item, keep it
            if c.get('manual_check'):
                enriched.append(c)
                continue
                
            meta = self.get_metadata(c['url'])
            
            c['date'] = meta.get('date')
            if meta.get('user') and meta.get('user') != 'Unknown':
                c['user'] = meta.get('user')
            c['platform'] = meta.get('platform')
            
            if meta.get('title'):
                c['title'] = meta['title']
                
            enriched.append(c)
            
        return enriched
        print("Initializing Browser Driver...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument(f"user-agent={self.ua.random}")
        chrome_options.page_load_strategy = 'eager'
        
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Selenium: {e}")
            self.driver = None

    # ... (rest of methods) ...

    def search_serpapi(self, image_url):
        """
        Uses SerpApi to get Google Lens results.
        Reliable and detailed.
        """
        if not self.api_key:
            return []
            
        print(f"Querying SerpApi (Google Lens) with URL: {image_url}")
        try:
            from serpapi import GoogleSearch
            
            params = {
                "engine": "google_lens",
                "url": image_url,
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            candidates = []
            
            # Parse "Visual matches"
            if "visual_matches" in results:
                for match in results["visual_matches"]:
                    link = match.get("link")
                    title = match.get("title")
                    source = match.get("source")
                    thumb = match.get("thumbnail")
                    
                    if link and any(x in link for x in ["reddit.com", "pinterest.com", "twitter.com", "instagram.com", "facebook.com"]):
                         candidates.append({
                             'url': link,
                             'title': title,
                             'user': source, 
                             'platform': 'Web',
                             'thumbnail': thumb # Capture thumbnail
                         })
                         
            print(f"Found {len(candidates)} matches via SerpApi.")
            return candidates
            
        except Exception as e:
            print(f"SerpApi Error: {e}")
            return []

    def search_serpapi_text(self, query, site):
        """
        Uses SerpApi (Google Search) for text queries.
        Targeting specific sites (Reddit/Pinterest).
        """
        if not self.api_key or not query:
            return []
            
        print(f"Querying SerpApi (Text) for '{query}' on {site}...")
        try:
            from serpapi import GoogleSearch
            
            params = {
                "engine": "google",
                "q": f"site:{site} {query}",
                "api_key": self.api_key,
                "num": 20 # Request more results
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            candidates = []
            if "organic_results" in results:
                for res in results["organic_results"]:
                    link = res.get("link")
                    title = res.get("title")
                    
                    if link:
                        candidates.append({
                            'url': link,
                            'title': title,
                            'platform': 'Web',
                            'user': 'Unknown'
                        })
            
            print(f"Found {len(candidates)} text matches via SerpApi for {site}.")
            return candidates
        except Exception as e:
            print(f"SerpApi Text Error: {e}")
            return []

    def search_serpapi_visual_engines(self, image_url, engine="bing_images"):
        """
        Uses SerpApi for other visual engines (Bing, Yandex).
        """
        if not self.api_key:
            return []
            
        print(f"Querying SerpApi ({engine}) with URL...")
        try:
            from serpapi import GoogleSearch
            
            params = {
                "engine": engine,
                "url": image_url, 
                "api_key": self.api_key
            }
            
            # Adjust param based on engine
            if engine == "bing_reverse_image_search":
                params["image_url"] = image_url
                del params["url"]
            elif engine == "yandex_images":
                params["url"] = image_url
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            candidates = []
            
            # Parse Bing
            if engine == "bing_reverse_image_search" and "image_results" in results:
                for match in results["image_results"]:
                    link = match.get("link") or match.get("source_url") 
                    title = match.get("title")
                    thumb = match.get("thumbnail")
                    if link: candidates.append({'url': link, 'title': title, 'thumbnail': thumb})

            # Parse Yandex
            elif engine == "yandex_images" and "visual_matches" in results:
                 for match in results["visual_matches"]:
                    link = match.get("link")
                    title = match.get("title")
                    thumb = match.get("thumbnail")
                    if link: candidates.append({'url': link, 'title': title, 'thumbnail': thumb})
            
            # Generic fallback
            if not candidates and "images_results" in results:
                 for match in results["images_results"]:
                    link = match.get("link")
                    title = match.get("title")
                    thumb = match.get("thumbnail")
                    if link: candidates.append({'url': link, 'title': title, 'thumbnail': thumb})

            print(f"Found {len(candidates)} matches via SerpApi ({engine}).")
            return candidates
            
        except Exception as e:
            print(f"SerpApi {engine} Error: {e}")
            return []

    # ... (rest of existing methods) ...

    def hybrid_search(self, image_path):
        candidates = []
        
        # 1. OCR (Selenium Google + DDG Fallback)
        text = self.extract_text(image_path)
        if text:
            # Google
            g_res = self.search_google_selenium(text, "reddit.com")
            if not g_res:
                print("Google failed, trying DuckDuckGo...")
                g_res = self.search_ddg(text, "reddit.com")
            candidates.extend(g_res)
            
            # Pinterest
            p_res = self.search_google_selenium(text, "pinterest.com")
            if not p_res:
                p_res = self.search_ddg(text, "pinterest.com")
            candidates.extend(p_res)
            
        # 2. Visual Search
        image_url = self.upload_image(image_path)
        if image_url:
            # Priority: SerpApi
            if self.api_key:
                print("Using SerpApi for Visual Search...")
                candidates.extend(self.search_serpapi(image_url))
            else:
                # Fallback: Selenium Scrapers
                print("Using Selenium for Visual Search (No API Key)...")
                candidates.extend(self.search_google_lens_selenium(image_url))
                candidates.extend(self.search_bing_selenium(image_url))
                candidates.extend(self.search_yandex_selenium(image_url))
        
        # 3. Enrich
        unique = {c['url']: c for c in candidates}.values()
        enriched = []
        for c in unique:
            # If it's a manual check item, skip metadata extraction or handle gracefully
            if c.get('manual_check'):
                enriched.append(c)
                continue
                
            meta = self.get_metadata(c['url'])
            
            # Merge metadata into the original candidate dict to preserve existing keys (like title, manual_check)
            # We prioritize metadata values if they exist, otherwise keep original
            c['date'] = meta.get('date')
            if meta.get('user') and meta.get('user') != 'Unknown':
                c['user'] = meta.get('user')
            c['platform'] = meta.get('platform')
            
            # Only overwrite title if metadata has a better one
            if meta.get('title'):
                c['title'] = meta['title']
                
            enriched.append(c)
            
        return enriched

    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

    def extract_text(self, image_path):
        """Extracts text from an image using EasyOCR."""
        print(f"Extracting text from {image_path}...")
        try:
            result = self.reader.readtext(image_path, detail=0)
            text = " ".join(result)
            print(f"Extracted text: {text}")
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def upload_image(self, image_path):
        """
        Uploads image to Catbox.moe to get a public URL for reverse search.
        """
        print(f"Uploading {image_path} to Catbox...")
        try:
            files = {'fileToUpload': open(image_path, 'rb')}
            data = {'reqtype': 'fileupload'}
            response = requests.post('https://catbox.moe/user/api.php', files=files, data=data)
            if response.status_code == 200:
                url = response.text
                print(f"Uploaded: {url}")
                return url
            return None
        except Exception as e:
            print(f"Upload Error: {e}")
            return None

    def search_ddg(self, query, site_filter=None):
        """Searches DuckDuckGo (Text) - often easier to scrape."""
        if not self.driver: return []
        
        search_query = query
        if site_filter:
            search_query += f" site:{site_filter}"
            
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(search_query)}"
        print(f"Selenium DDG Search: {search_query}")
        
        try:
            self.driver.get(url)
            time.sleep(5) # Increased wait
            
            # Debug: Save HTML
            with open("debug_ddg.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            results = []
            elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
            if not elements:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "div.result")
            if not elements:
                # Try generic links in main content
                elements = self.driver.find_elements(By.XPATH, "//div[@id='links']//a[@data-testid='result-title-a']")
                
            for el in elements:
                try:
                    # Handle different element types
                    if el.tag_name == 'a':
                        link_el = el
                    else:
                        link_el = el.find_element(By.TAG_NAME, "a")
                        
                    href = link_el.get_attribute("href")
                    title = link_el.text
                    if href and href.startswith("http"):
                        results.append({'url': href, 'title': title})
                except:
                    continue
            
            if not results:
                 results.append({'url': url, 'title': 'Manual Check: DuckDuckGo Results', 'manual_check': True})
                 
            return results
        except Exception as e:
            print(f"Selenium DDG Error: {e}")
            return [{'url': url, 'title': 'Manual Check: DuckDuckGo (Error)', 'manual_check': True}]

    def search_google_selenium(self, query, site_filter=None):
        """Searches Google using Selenium."""
        if not self.driver: return []
        
        search_query = query
        if site_filter:
            search_query += f" site:{site_filter}"
            
        url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        print(f"Selenium Google Search: {search_query}")
        
        try:
            self.driver.get(url)
            # Check for consent button
            try:
                consent_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Agree')]")
                if consent_btns:
                    consent_btns[0].click()
                    time.sleep(1)
            except:
                pass
            
            time.sleep(3)
            
            # Debug: Save HTML
            with open("debug_google.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            results = []
            elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
            if not elements:
                elements = self.driver.find_elements(By.XPATH, "//div[@data-header-feature]")
                
            for el in elements:
                try:
                    link_el = el.find_element(By.TAG_NAME, "a")
                    href = link_el.get_attribute("href")
                    try:
                        title = el.find_element(By.TAG_NAME, "h3").text
                    except:
                        title = href
                        
                    if href and href.startswith("http"):
                        results.append({'url': href, 'title': title})
                except:
                    continue
            
            if not results:
                 results.append({'url': url, 'title': 'Manual Check: Google Results', 'manual_check': True})
                 
            return results
        except Exception as e:
            print(f"Selenium Google Error: {e}")
            return [{'url': url, 'title': 'Manual Check: Google (Error)', 'manual_check': True}]

    def search_google_lens_selenium(self, image_url):
        """
        Scrapes Google Lens results directly.
        This is what the user expects to see.
        """
        if not self.driver: return []
        
        # Google Lens Upload URL
        url = f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote(image_url)}"
        print(f"Selenium Google Lens Search: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5) # Wait for initial load
            
            # Scroll down to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Debug: Save HTML
            with open("debug_lens.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            results = []
            
            # Google Lens selectors are messy and dynamic.
            # We look for 'a' tags that link to external sites.
            # Usually inside a grid.
            
            # Try to find the "Visual matches" grid
            # Common class for result container might be 'G0pjOe' or similar, but it changes.
            # We will look for all links that have a title and are external.
            
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if not href: continue
                
                # Filter for relevant social media/content sites
                if any(x in href for x in ["reddit.com", "pinterest.com", "twitter.com", "instagram.com", "facebook.com", "tiktok.com"]):
                    # Try to get title from inside the link or the link text
                    title = link.text
                    if not title:
                        # Try finding a header inside
                        try:
                            title = link.find_element(By.CSS_SELECTOR, "div.UAiK1e").text # Common title class
                        except:
                            title = href
                    
                    if not any(r['url'] == href for r in results):
                        results.append({'url': href, 'title': title})
            
            print(f"Found {len(results)} matches via Google Lens.")
            return results

        except Exception as e:
            print(f"Selenium Lens Error: {e}")
            return []

    def search_bing_selenium(self, image_url):
        """Reverse image search on Bing using Selenium."""
        if not self.driver: return []
        
        url = f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHMP&q=imgurl:{urllib.parse.quote(image_url)}"
        print(f"Selenium Bing Search: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Debug: Save HTML
            with open("debug_bing.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            results = []
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and any(x in href for x in ["reddit.com", "pinterest.com", "twitter.com", "instagram.com"]):
                    title = link.text or href
                    if not any(r['url'] == href for r in results):
                        results.append({'url': href, 'title': title})
            
            if not results:
                 results.append({'url': url, 'title': 'Manual Check: Bing Visual Search', 'manual_check': True})

            return results
        except Exception as e:
            print(f"Selenium Bing Error: {e}")
            return [{'url': url, 'title': 'Manual Check: Bing (Error)', 'manual_check': True}]

    def search_yandex_selenium(self, image_url):
        """Reverse image search on Yandex using Selenium."""
        if not self.driver: return []
        
        url = f"https://yandex.com/images/search?rpt=imageview&url={urllib.parse.quote(image_url)}"
        print(f"Selenium Yandex Search: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Debug: Save HTML
            with open("debug_yandex.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            results = []
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and any(x in href for x in ["reddit.com", "pinterest.com", "twitter.com", "instagram.com"]):
                    title = link.text or "Yandex Result"
                    if not any(r['url'] == href for r in results):
                        results.append({'url': href, 'title': title})
            
            if not results:
                 results.append({'url': url, 'title': 'Manual Check: Yandex Visual Search', 'manual_check': True})

            return results
        except Exception as e:
            print(f"Selenium Yandex Error: {e}")
            return [{'url': url, 'title': 'Manual Check: Yandex (Error)', 'manual_check': True}]

    def search_rapidapi_reverse_image(self, image_url):
        """
        Uses RapidAPI 'reverse-image-search1' for visual matches.
        """
        if not self.rapidapi_key: return []
        
        print(f"Querying RapidAPI (Reverse Image) with URL: {image_url}")
        try:
            url = "https://reverse-image-search1.p.rapidapi.com/reverse-image-search"
            querystring = {"url": image_url, "limit": "10", "safe_search": "off"}
            headers = {
                "x-rapidapi-host": "reverse-image-search1.p.rapidapi.com",
                "x-rapidapi-key": self.rapidapi_key
            }
            
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()
            
            candidates = []
            # The API response structure varies, assuming standard list of results
            # Based on typical RapidAPI reverse image responses:
            if 'data' in data:
                for item in data['data']:
                    link = item.get('url') or item.get('page_url')
                    title = item.get('title')
                    if link:
                        candidates.append({'url': link, 'title': title, 'platform': 'Web', 'user': 'Unknown'})
            
            print(f"Found {len(candidates)} matches via RapidAPI Reverse Image.")
            return candidates
        except Exception as e:
            print(f"RapidAPI Reverse Image Error: {e}")
            return []

    def get_page_source_rapidapi(self, url):
        """
        Uses RapidAPI 'bypass-cloudflare-api' to get page source of protected sites.
        """
        if not self.rapidapi_key: return None
        
        print(f"Fetching source via RapidAPI (Cloudflare Bypass): {url}")
        try:
            api_url = "https://bypass-cloudflare-api.p.rapidapi.com/get_page_source"
            querystring = {"url": url}
            headers = {
                "x-rapidapi-host": "bypass-cloudflare-api.p.rapidapi.com",
                "x-rapidapi-key": self.rapidapi_key,
                "Content-Type": "application/json"
            }
            
            # The user example was POST with data '{}' but also had query params. 
            # Usually GET is enough for page source, but let's follow the POST pattern if needed.
            # The user example: POST ... url in query param ... data '{}'
            
            response = requests.post(api_url, headers=headers, params=querystring, json={})
            
            if response.status_code == 200:
                data = response.json()
                # The API usually returns content in a field like 'content' or 'result'
                return data.get('result') or data.get('content') or response.text
            return None
        except Exception as e:
            print(f"RapidAPI Cloudflare Bypass Error: {e}")
            return None

    def get_metadata(self, url):
        """Extracts metadata using requests, Selenium, or RapidAPI."""
        metadata = {'url': url, 'date': None, 'user': 'Unknown', 'platform': 'Web', 'title': ''}
        
        # Helper to parse HTML
        def parse_html(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            if soup.title: metadata['title'] = soup.title.string.strip()
            
            date_meta = soup.find('meta', property='article:published_time') or \
                        soup.find('meta', property='og:published_time') or \
                        soup.find('meta', attrs={'name': 'date'}) or \
                        soup.find('time')
                        
            if date_meta:
                content = date_meta.get('content') or date_meta.get('datetime')
                if content:
                    try:
                        import dateutil.parser
                        dt = dateutil.parser.parse(content)
                        metadata['date'] = dt.timestamp()
                    except:
                        pass
        
        try:
            headers = {'User-Agent': self.ua.random}
            
            # 1. Try Standard Requests
            try:
                if "reddit.com" in url:
                    metadata['platform'] = 'Reddit'
                    json_url = url.rstrip('/') + ".json"
                    resp = self.session.get(json_url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        post = data[0]['data']['children'][0]['data']
                        metadata['date'] = post.get('created_utc')
                        metadata['user'] = post.get('author')
                        metadata['title'] = post.get('title')
                        return metadata
                
                resp = self.session.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    parse_html(resp.text)
                    return metadata
            except:
                pass # Fallback to next method

            # 2. Try RapidAPI Cloudflare Bypass (if requests failed/blocked)
            if self.rapidapi_key:
                source = self.get_page_source_rapidapi(url)
                if source:
                    parse_html(source)
                    return metadata

            # 3. Fallback to Selenium (if initialized)
            if self.driver:
                self.driver.get(url)
                parse_html(self.driver.page_source)

        except Exception as e:
            print(f"Metadata Error {url}: {e}")
            
        return metadata

    def hybrid_search(self, image_path):
        candidates = []
        
        # 1. OCR Search
        text = self.extract_text(image_path)
        if text:
            # DuckDuckGo (Must be included as per user request)
            print("Searching DuckDuckGo (Text)...")
            candidates.extend(self.search_ddg(text, "reddit.com"))
            candidates.extend(self.search_ddg(text, "pinterest.com"))
            
            if self.api_key:
                # Use SerpApi for Text
                candidates.extend(self.search_serpapi_text(text, "reddit.com"))
                candidates.extend(self.search_serpapi_text(text, "pinterest.com"))
            else:
                # Fallback Selenium Google
                g_res = self.search_google_selenium(text, "reddit.com")
                candidates.extend(g_res)
                p_res = self.search_google_selenium(text, "pinterest.com")
                candidates.extend(p_res)
            
        # 2. Visual Search
        image_url = self.upload_image(image_path)
        if image_url:
            # RapidAPI Reverse Image (New)
            if self.rapidapi_key:
                candidates.extend(self.search_rapidapi_reverse_image(image_url))

            # SerpApi
            if self.api_key:
                print("Using SerpApi for Visual Search...")
                candidates.extend(self.search_serpapi(image_url))
                candidates.extend(self.search_serpapi_visual_engines(image_url, "bing_reverse_image_search"))
                candidates.extend(self.search_serpapi_visual_engines(image_url, "yandex_images"))
            else:
                # Fallback Selenium
                print("Using Selenium for Visual Search...")
                candidates.extend(self.search_google_lens_selenium(image_url))
                candidates.extend(self.search_bing_selenium(image_url))
                candidates.extend(self.search_yandex_selenium(image_url))
        
        # 3. Filter & Enrich
        unique = {c['url']: c for c in candidates}.values()
        enriched = []
        
        allowed_domains = ["reddit.com", "pinterest.com"]
        
        for c in unique:
            # Strict Filtering
            if not any(d in c['url'] for d in allowed_domains):
                continue

            # If it's a manual check item, keep it
            if c.get('manual_check'):
                enriched.append(c)
                continue
                
            meta = self.get_metadata(c['url'])
            
            c['date'] = meta.get('date')
            if meta.get('user') and meta.get('user') != 'Unknown':
                c['user'] = meta.get('user')
            c['platform'] = meta.get('platform')
            
            if meta.get('title'):
                c['title'] = meta['title']
                
            enriched.append(c)
            
        return enriched
