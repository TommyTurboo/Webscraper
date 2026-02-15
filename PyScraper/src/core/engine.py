import os
import time
from .browser import BrowserManager
from strategies import get_strategy_for_url
from utils.file_ops import read_urls, ensure_dir, save_html
from playwright_stealth import Stealth

class ScrapeEngine:
    def __init__(self, input_file, output_dir, headless):
        self.input_file = input_file
        self.output_dir = output_dir
        self.headless = headless
        self.browser_manager = BrowserManager(headless)

    def run(self):
        urls = read_urls(self.input_file)
        print(f"🚀 Starting scrape for {len(urls)} URLs...")
        ensure_dir(self.output_dir)

        self.browser_manager.start()
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Processing: {url}")
                self._process_url(url)
        finally:
            self.browser_manager.stop()
            print("\n🏁 All done.")

    def _process_url(self, url):
        # 1. Bepaal strategie
        strategy = get_strategy_for_url(url)
        print(f"  🧠 Strategy: {strategy.__class__.__name__}")

        # 2. Maak sessie
        context = self.browser_manager.create_context()
        page = context.new_page()
        
        # Activeer stealth
        # stealth = Stealth()
        # stealth.use_sync(page)

        try:
            # 3. Voer strategie uit
            html_content = strategy.execute(page, url)
            
            if html_content:
                # 4. Opslaan
                save_html(self.output_dir, url, html_content)
                print("  ✅ Saved.")
            else:
                print("  ❌ Failed (No HTML returned).")

        except Exception as e:
            print(f"  ⚠️  Error: {e}")
        finally:
            # 5. Opruimen sessie
            page.close()
            context.close()
