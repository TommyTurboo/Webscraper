from .base import BaseStrategy
from core.config import Config

class SiemensStrategy(BaseStrategy):
    def execute(self, page, url):
        # 1. Navigeer
        print(f"  📡 Navigating to {url}")
        try:
            page.goto(url, wait_until='networkidle', timeout=Config.TIMEOUT_PAGE_LOAD)
        except Exception as e:
            print(f"  ⚠️  Navigation warning: {e}")
        
        self.random_delay()
        self._accept_cookies(page)

        # 2. Login indien nodig
        self._login(page)
        
        # 3. Bepaal paginatype
        # We kijken of de 'Lijst weergave' controls aanwezig zijn.
        is_variant_page = page.locator('label[for="listView"]').count() > 0 or \
                          page.locator('input#listView').count() > 0

        if is_variant_page:
            return self._execute_variant_strategy(page)
        else:
            return self._execute_product_strategy(page)

    def _execute_variant_strategy(self, page):
        """Logica voor productvarianten (load more loop)"""
        print("  🧩 Type Detected: Product Variants Page")
        
        self._set_list_view(page)
        self._load_all_variants(page)
        
        # Gebruik de snelle jump voor extractie (variant lijsten zijn te lang voor slow scroll)
        self._quick_scroll_bottom(page)
        
        print("  📄 Extracting Variants HTML...")
        return page.content()

    def _execute_product_strategy(self, page):
        """Logica voor enkel product (Commercieel + Technische Tab extractie)"""
        print("  🧩 Type Detected: Single Product Page (Multi-Tab)")
        
        # --- Deel 1: Commerciële data ---
        print("  📸 Processing Step 1: Commercial Tab...")
        # Gebruik de standaard 'langzame' scroll van BaseStrategy voor lazy loading
        self.scroll_to_bottom(page) 
        html_commercial = page.content()
        
        # --- Deel 2: Technische data ---
        # Probeer naar tweede tab te gaan
        if self._click_tech_tab(page):
            print("  📸 Processing Step 2: Technical Tab...")
            # Wederom scrollen op de nieuwe pagina
            self.scroll_to_bottom(page)
            html_tech = page.content()
            
            print("  ➕ Concatenating HTML outputs (Commercial + Technical)...")
            
            # BELANGRIJK: We injecteren de content van de 2e pagina IN de body van de 1e pagina.
            # Simpelweg erachter plakken zorgt voor ongeldige HTML (dubbele <html/body> tags)
            # waardoor parsers (zoals BeautifulSoup) het tweede deel volledig negeren.
            import re
            
            tech_content = html_tech
            tech_body_match = re.search(r'<body[^>]*>(.*?)</body>', html_tech, re.DOTALL | re.IGNORECASE)
            if tech_body_match:
                tech_content = tech_body_match.group(1)
            
            separator = "\n\n<!-- ============================================= -->\n" \
                        "<!-- === APPENDED DATA: TECHNISCHE GEGEVENS TAB === -->\n" \
                        "<!-- ============================================= -->\n\n"
            
            # Injecteer voor de sluitende body tag van de commerciële HTML
            if "</body>" in html_commercial:
                final_html = html_commercial.replace("</body>", separator + tech_content + "\n</body>")
                return final_html
            else:
                # Fallback als er geen body tag is
                return html_commercial + separator + tech_content
        
        return html_commercial

    def _login(self, page):
        """Voert de login procedure uit indien niet ingelogd."""
        import configparser
        import os

        # Check of we moeten inloggen. We gebruiken de specifieke XPath van de knop.
        login_button_selector = 'xpath=//*[@id="headerLoginButton"]'
        
        try:
             # We wachten heel even (max 5s) tot de knop verschijnt, voor het geval de header traag laadt
             page.wait_for_selector(login_button_selector, state='visible', timeout=5000)
        except:
             # Timeout = knop niet gevonden
             print(f"  ℹ️  Already logged in or login button not found (checked {login_button_selector}).")
             return

        print("  🔑 Initiating login sequence...")
        
        # Laad credentials
        config = configparser.ConfigParser()
        if not os.path.exists(Config.SECRETS_PATH):
             print(f"  ⚠️  Secrets file not found at {Config.SECRETS_PATH}")
             return
            
        config.read(Config.SECRETS_PATH)
        if 'siemens' not in config:
             print("  ⚠️  No [siemens] section in secrets file")
             return

        email = config['siemens'].get('email')
        password = config['siemens'].get('password')
        
        if not email or not password:
             print("  ⚠️  Email or password not found in secrets file")
             return

        try:
             # 1. Klik op login knop in header
             # Selector van gebruiker: //*[@id="headerLoginButton"]
             login_btn = page.locator('xpath=//*[@id="headerLoginButton"]').first
             if login_btn.is_visible():
                  print("  👆 Clicking header login button...")
                  login_btn.click()
                  self.random_delay(2000, 3000)
             
             # 2. Vul Username in
             # Selector van gebruiker: //*[@id="username"]
             print("  ✍️  Entering username...")
             page.fill('xpath=//*[@id="username"]', email)
             self.random_delay(500, 1000)
             
             # 3. Klik Continue (Submit Username)
             # Zoek button op basis van class of tekst, aangezien ID dynamisch/lang kan zijn, 
             # maar 'button[type="submit"]' is vaak veilig als het de enige is.
             print("  👆 Clicking Continue...")
             page.click('button[type="submit"]')
             
             # Wacht tot password veld zichtbaar is (Login flow is vaak multi-step)
             print("  ⏳ Waiting for password field...")
             page.wait_for_selector('input#password', state='visible', timeout=10000)
             self.random_delay(1000, 2000)
             
             # 4. Vul Password in
             # Selector van gebruiker: input#password (uit HTML snippet)
             print("  ✍️  Entering password...")
             page.fill('input#password', password)
             self.random_delay(500, 1000)
             
             # 5. Submit Password
             # Vaak is de 'Sign On' knop ook een submit button
             print("  👆 Clicking Sign On...")
             page.click('button[type="submit"]')
             
             page.wait_for_load_state('networkidle')
             print("  ✅ Login submitted")
             self.random_delay(3000, 5000)
             
        except Exception as e:
             print(f"  ❌ Login failed: {e}")

    #From here: Helper Functions
    
    def _accept_cookies(self, page):
        cookie_selectors = [
            'button[data-testid="uc-accept-all-button"]',
            '#usercentrics-root button[data-testid="uc-accept-all-button"]'
        ]
        for sel in cookie_selectors:
            if page.locator(sel).is_visible():
                try:
                    print("  🍪 Accepting cookies...")
                    page.click(sel)
                    self.random_delay()
                    break
                except:
                    pass

    def _set_list_view(self, page):
        print("  👀 Checking View State...")
        try:
            self.random_delay(1000, 1500)
            list_view_label = page.locator('label[for="listView"]')
            is_active = page.locator('input#listView').is_checked()
            
            if is_active:
                 print("  ℹ️  List View is already active.")
            elif list_view_label.count() > 0:
                print("  📋 Switching to List View...")
                list_view_label.first.scroll_into_view_if_needed()
                self.random_delay(500)
                list_view_label.click(force=True)
                self.random_delay(2000, 3000)
            else:
                fallback = page.get_by_title("Lijst weergave")
                if fallback.count() > 0:
                    fallback.click(force=True)
                    self.random_delay(2000, 3000)
        except Exception as e:
            print(f"  ⚠️  Could not switch to List View: {e}")

    def _load_all_variants(self, page):
        print("  🔄 Starting Infinite Scroll Loop...")
        load_more_selector = "button.infinite-pagination__load-more-btn"
        
        while True:
            button = page.locator(load_more_selector)
            if button.is_visible():
                try:
                    print("  👇 Clicking 'Meer laden'...")
                    button.scroll_into_view_if_needed()
                    self.random_delay(500, 1000)
                    button.click()
                    self.random_delay(2000, 3000) 
                except Exception as e:
                    print(f"  ⚠️  Error clicking 'Meer laden': {e}")
                    break
            else:
                print("  ✅ All variants loaded.")
                break

    def _click_tech_tab(self, page):
        print("  🖱️  Looking for 'Technische gegevens' tab...")
        try:
            # Soms staat er 'Technische gegevens', soms 'Technical data'
            tab_locator = page.locator("li").filter(has_text="Technische gegevens")
            if tab_locator.count() == 0:
                 tab_locator = page.locator("li").filter(has_text="Technical data")
            
            if tab_locator.count() > 0:
                print("  👇 Clicking Tech Tab...")
                tab_locator.first.click(force=True)
                self.random_delay(3000, 4000) # Goede delay voor laden nieuwe content
                return True
            else:
                print("  ⚠️  Tab 'Technische gegevens' not found.")
        except Exception as e:
            print(f"  ⚠️  Error clicking tab: {e}")
        return False

    def _quick_scroll_bottom(self, page):
        """Snelle scroll voor lange lijsten."""
        print("  ⚡ Fast-Scrolling to bottom...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.random_delay(1500, 2500)
        page.evaluate("window.scrollTo(0, 0)")

    # Opmerking: perform_actions is niet meer nodig omdat we execute() overriden.
