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

        # Site specifieke acties (override in child classes)
        self.perform_actions(page)
        
        # Altijd scrollen voor lazy loading
        self.scroll_to_bottom(page)
        
        # HTML ophalen
        print("  📄 Extracting outerHTML...")
        return page.evaluate("() => document.documentElement.outerHTML")

    def perform_actions(self, page):
        """Override deze methode in subclasses voor kliks etc."""
        pass

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
