import time
import random
# BELANGRIJK: Gebruik een absolute import, geen '..'
from core.config import Config

class BaseStrategy:
    def execute(self, page, url):
        """Template methode: Navigeren -> Acties -> Scrollen -> Extracten"""
        print(f"  📡 Navigating to {url}")
        
        try:
            page.goto(url, wait_until='networkidle', timeout=Config.TIMEOUT_PAGE_LOAD)
        except Exception as e:
            print(f"  ⚠️  Navigation warning (might be timeout): {e}")
        
        # Helper delays
        self.random_delay()

        # ✨ NIEUW: Cookies accepteren indien aanwezig
        self.accept_cookies(page)

        # Site specifieke acties (override in child classes)
        self.perform_actions(page)
        
        # Altijd scrollen voor lazy loading
        self.random_delay() # Extra delay voor scrollen
        self.scroll_to_bottom(page)
        
        # HTML ophalen
        print("  📄 Extracting outerHTML...")
        return page.evaluate("() => document.documentElement.outerHTML")

    def perform_actions(self, page):
        """Override deze methode in subclasses voor kliks etc."""
        pass

    def accept_cookies(self, page):
        """
        Probeert automatisch cookies te accepteren via bekende selectors.
        Kan overschreven worden voor specifieke sites.
        """
        print("  🍪 Checking for cookie banners...")
        
        # Veelvoorkomende cookie accept buttons (OneTrust, Cookiebot, etc.)
        cookie_selectors = [
            "#onetrust-accept-btn-handler",                           # OneTrust
            "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll", # Cookiebot
            ".cc-btn.cc-allow",                                       # CookieConsent
            "button[data-testid='uc-accept-all-button']",             # Usercentrics
            "button.cm__btn.cm__btn--primary",                        # Custom (o.a. Siemens/Sommige shops)
            "a.cc-btn.cc-dismiss",
            "[aria-label='Accept all cookies']",
            "button:has-text('Alles accepteren')",
            "button:has-text('Agree and Close')",
            "button:has-text('Accept All')",
            "button:has-text('Alle akzeptieren')"
        ]
        
        for selector in cookie_selectors:
            try:
                # Korte timeout om niet te lang te wachten als er niets is (1s)
                if page.is_visible(selector, timeout=1000):
                    print(f"     ✓ Clicking generic cookie button: {selector}")
                    page.click(selector)
                    self.random_delay(1500, 2500) # Even wachten tot banner weg zakt/reload
                    return
            except Exception:
                continue

    def random_delay(self, min_ms=800, max_ms=2300):
        time.sleep(random.uniform(min_ms/1000, max_ms/1000))

    def scroll_to_bottom(self, page):
        print("  📜 Scrolling...")
        # Simpele 'smooth scroll' implementatie
        page.evaluate(f"""
            async () => {{
                await new Promise((resolve) => {{
                    let totalHeight = 0;
                    let distance = {Config.SCROLL_STEP};
                    let timer = setInterval(() => {{
                        let scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if(totalHeight >= scrollHeight){{
                            clearInterval(timer);
                            window.scrollTo(0, 0);
                            resolve();
                        }}
                    }}, {Config.SCROLL_DELAY});
                }});
            }}
        """)
        self.random_delay(1000, 1500)
