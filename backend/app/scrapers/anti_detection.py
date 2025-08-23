# scrapers/anti_detection.py
import random
import asyncio
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

class AntiDetectionScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.proxies = self.load_proxies()
        self.current_proxy_index = 0
        
    def load_proxies(self):
        """Load residential proxies from file"""
        with open('proxies/proxy_list.txt', 'r') as f:
            proxies = [line.strip() for line in f.readlines()]
        return proxies
    
    def get_random_user_agent(self):
        """Get random desktop user agent"""
        desktop_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(desktop_agents)
    
    def get_next_proxy(self):
        """Rotate to next proxy"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    async def create_stealth_browser(self):
        """Create browser with anti-detection measures"""
        playwright = await async_playwright().start()
        
        # Browser launch options
        launch_options = {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        }
        
        # Add proxy if available
        proxy = self.get_next_proxy()
        if proxy:
            launch_options['proxy'] = {
                'server': proxy.split('@')[1] if '@' in proxy else proxy,
                'username': proxy.split('@')[0].split(':')[0] if '@' in proxy else None,
                'password': proxy.split('@')[0].split(':')[1] if '@' in proxy else None
            }
        
        browser = await playwright.chromium.launch(**launch_options)
        context = await browser.new_context(
            user_agent=self.get_random_user_agent(),
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        
        return browser, context
    
    async def random_delay(self, min_seconds=2, max_seconds=5):
        """Random delay between requests"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def human_like_scroll(self, page):
        """Simulate human scrolling behavior"""
        for _ in range(random.randint(2, 4)):
            await page.evaluate('window.scrollBy(0, Math.random() * 500 + 300)')
            await asyncio.sleep(random.uniform(0.5, 1.5))
