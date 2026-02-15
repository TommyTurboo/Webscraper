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
        
        # Extra argumenten om detectie te verminderen
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--start-maximized',
            '--disable-infobars',
            '--exclude-switches=enable-automation',
            '--use-fake-ui-for-media-stream',
        ]

        # Pad voor persistent profile
        user_data_path = Config.BASE_DIR / "browser_profile"

        print(f"  📂 Using persistent profile at: {user_data_path}")

        # Persistent context start NIET via .launch() maar via .launch_persistent_context()
        try:
           self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_path),
                channel="msedge", # Of "chrome"
                headless=self.headless,
                args=browser_args,
                viewport=None, # Laat browser zelf bepalen (fullscreen)
                
                # Belangrijk: zet automation flags ui
                ignore_default_args=["--enable-automation"],
                
                # GEEN fake user-agent gebruiken bij echte browser!
                # user_agent=self.ua.random 
            )
           
        except Exception as e:
            print(f"  ⚠️  Failed to launch persistent context: {e}")
            # Fallback (kan nog steeds falen als geblokkeerd)
            self.browser = self.playwright.chromium.launch(args=browser_args, headless=self.headless)

    def stop(self):
        """Sluit alles netjes af."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def create_context(self):
        """
        Bij persistent context IS de browser al de context.
        We geven dus gewoon self.browser terug (wat eigenlijk een Context object is).
        """
        # Als we persistent runnen, is self.browser eigenlijk de Context
        # Stealth settings toepassen kan nog steeds
        
        context = self.browser
        
        # Probeer stealth script toe te voegen als het nog niet bestaat
        # try:
        #     context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # except:
        #     pass
            
        return context
