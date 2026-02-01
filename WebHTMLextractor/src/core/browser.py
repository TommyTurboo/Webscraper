from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from fake_useragent import UserAgent
from .config import Config

class BrowserManager:
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.ua = UserAgent()

    def start(self):
        """Start de browser instantie (één keer)."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

    def stop(self):
        """Sluit alles netjes af."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def create_context(self):
        """
        Maakt een nieuwe, schone sessie aan met een random User-Agent.
        """
        user_agent = self.ua.random
        context = self.browser.new_context(
            user_agent=user_agent,
            viewport=Config.VIEWPORT,
            locale=Config.LOCALE,
            timezone_id=Config.TIMEZONE
        )
        
        # Voeg stealth scripts toe aan de context
        return context
