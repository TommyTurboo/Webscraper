import time
import configparser
from playwright.sync_api import Page
from .base import BaseStrategy
from core.config import Config

class PhoenixStrategy(BaseStrategy):
    def accept_cookies(self, page: Page):
        """Specifieke cookie afhandeling voor Phoenix Contact (Usercentrics)"""
        print("  🍪 Checking for Phoenix cookie banner...")
        
        try:
            # Wacht even zodat de banner zeker geladen is (Usercentrics is soms traag)
            time.sleep(2)

            # Shadow DOM aanpak voor Usercentrics (vaak zit de knop in een shadow root)
            # We zoeken naar de parent container, vaak id='usercentrics-root'
            uc_root = page.locator("#usercentrics-root")
            if uc_root.count() > 0:
                print("  Found #usercentrics-root, checking shadow DOM...")
                # In Playwright gaan locators standaard door open shadow roots heen.
                # Dus we zoeken direct naar de knop data-testid='uc-accept-all-button'
            
            # 1. Specifiek ID/TestID
            accept_btn = page.locator("button[data-testid='uc-accept-all-button']")
            if accept_btn.is_visible():
                accept_btn.click()
                print("  ✅ Clicked 'Allow All' (Usercentrics testid)")
                return

            # 2. Alternatieve selector voor de groene knop
            green_btn = page.locator(".sc-dcJsrY.hCAyXb") # Class names kunnen dynamisch zijn, riskant
            
            # 3. Tekst match (case insensitive en exact)
            # Zoek naar knoppen die 'Allow All' of 'Alles accepteren' bevatten
            possible_texts = ["Allow All", "Accept All", "Alles accepteren", "Alle akzeptieren"]
            
            for text in possible_texts:
                btn = page.get_by_role("button", name=text)
                if btn.is_visible():
                    btn.click()
                    print(f"  ✅ Clicked '{text}' button")
                    return

            # 4. Als er een shadow root is (soms bij Usercentrics)
            base_accept = super().accept_cookies(page)
            
        except Exception as e:
            print(f"  ⚠️  Cookie warning: {e}")

    def perform_actions(self, page: Page):
        print("  🕵️  Detecting Phoenix Contact specific actions...")
        
        # 1. Login Logic
        self.login(page)
        
        # 2. Setup Page Size (50 items)
        self.set_page_size(page)

        # 3. Handle Pagination & Dynamic Loading is done in execute override or here?
        # The base class 'execute' does: actions -> scroll -> return outerHTML.
        # Since we need to aggregate multiple pages, we should probably override execute 
        # or handle the aggregation here and return a modified DOM.
        # But 'perform_actions' returns nothing.
        # Strategy: We will handle the pagination/aggregation INSIDE perform_actions 
        # by manipulating the DOM of the *current* page (Page 1) to append items from next pages.
        # BUT: Navigating to page 2 destroys page 1's DOM state in the browser.
        # So we can't easily stay on Page 1 and "bring in" Page 2.
        # We must override `execute` to control the full flow and return the final string.

    def execute(self, page: Page, url: str):
        """Override execute to handle multi-page scraping and merging."""
        print(f"  📡 Navigating to {url}")
        
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=Config.TIMEOUT_PAGE_LOAD)
        except Exception as e:
            print(f"  ⚠️  Navigation warning: {e}")

        # Basic setup we will use a wait here to make sure cookies load
        time.sleep(2)
        self.accept_cookies(page)
        self.login(page)
        
        # Check if we were redirected away from the product page (e.g. to profile dashboard)
        if page.url != url:
            print(f"  🔙 Redirected to {page.url}, going back to product list/page...")
            page.goto(url, wait_until='domcontentloaded', timeout=Config.TIMEOUT_PAGE_LOAD)
            time.sleep(2)

        # DETECTIE: Is dit een Lijst of een Product Detail Pagina?
        # Lijsten hebben meestal de id #se-result of dropdowns voor pagina grootte
        is_list_page = page.locator("#se-result").count() > 0
        
        if is_list_page:
            print("  📋 Detected LIST page mode.")
            return self.execute_list_mode(page)
        else:
            print("  📦 Detected PRODUCT DETAIL page mode.")
            return self.execute_detail_mode(page)

    def execute_detail_mode(self, page: Page):
        """Handelt enkele productpagina's af."""
        # Scrollen om alles te laden (specificaties, footer, etc)
        self.scroll_to_bottom(page)
        time.sleep(3)

        # Probeer ook hier Shadow DOM prijzen vrij te maken (zit vaak in de header/sidebar)
        self.fix_shadow_prices(page)
        
        # Return full HTML
        return page.evaluate("() => document.documentElement.outerHTML")

    def fix_shadow_prices(self, page: Page):
        """Helper om shadow dom prijzen te fixen (Code duplicatie voorkomen)"""
        # --- SMART PRICE CHECK ---
        max_retries = 3
        for attempt in range(max_retries):
            price_status = page.evaluate("""() => {
                const prices = document.querySelectorAll('sh-product-price');
                if (prices.length === 0) return { found: false, filled: 0 };
                
                let filled = 0;
                prices.forEach(el => {
                    if (el.shadowRoot && el.shadowRoot.textContent.trim().length > 0) {
                        filled++;
                    }
                });
                return { found: true, total: prices.length, filled: filled };
            }""")
            
            if not price_status['found']:
                # Op detailpagina's is de prijs soms niet in een <sh-product-price> maar elders,
                # of er is gewoon geen prijs component. We loggen het en gaan door.
                # print("  ⚠️ No price components found (might be normal for detail page).")
                break 
            elif price_status['filled'] == 0:
                print(f"  ⏳ Attempt {attempt+1}/{max_retries}: Prices components found but empty. Waiting...")
                time.sleep(5)
            else:
                print(f"  ✅ Prices detected ({price_status['filled']}/{price_status['total']} items).")
                break
        
        # Extractie
        page.evaluate("""() => {
            const targets = document.querySelectorAll('sh-product-price, sh-product-availability');
            targets.forEach(el => {
                if (el.shadowRoot) {
                    el.innerHTML = el.shadowRoot.innerHTML;
                }
            });
        }""")

    def execute_list_mode(self, page: Page):
        """Oude logica voor lijsten scraping"""
        # Set size to 50
        self.set_page_size(page)
        self.scroll_to_bottom(page) # Load prices for page 1
        
        # Initialize scraping variables
        collected_product_html = []
        current_page_num = 1
        
        # Sla EERST de basis van de pagina op (header, footer, styles)
        # We halen de resultaten-container leeg zodat we een schone template hebben
        print("  📸 Capturing page skeleton...")
        page_skeleton = page.evaluate("""() => {
             // Clone document om niet destructief te zijn
             const clone = document.documentElement.cloneNode(true);
             const resultContainer = clone.querySelector('#se-result');
             if (resultContainer) {
                 resultContainer.innerHTML = '<!-- PRODUCTS_PLACEHOLDER -->';
             }
             return clone.outerHTML;
        }""")

        while True:
            print(f"  📄 Processing list page {current_page_num}...")
            
            # Wait for dynamic prices (scroll)
            self.scroll_to_bottom(page)
            time.sleep(2) # Korter wachten, 5s is veel

            # Fix shadow prices
            self.fix_shadow_prices(page)
            
            # 1. HUIDIGE pagina content opslaan (Alleen de innerHTML van de grid)
            page_content = page.evaluate("""() => {
                const container = document.querySelector('#se-result');
                if (!container) return null;
                
                // Verwijder paginatie uit de snapshot anders komt die TIG keer voor
                const clone = container.cloneNode(true);
                clone.querySelectorAll('.se-pagination').forEach(e => e.remove());
                
                return clone.innerHTML;
            }""")
            
            if page_content:
                collected_product_html.append(page_content)
                print(f"     -> Content captured for page {current_page_num} ({len(page_content)} bytes)")

            # 2. Zoeken naar VOLGENDE pagina knop
            next_page_link = page.locator(f"a[data-se-page-number='{current_page_num + 1}']").first
            
            if next_page_link.count() > 0 and next_page_link.is_visible():
                print("  ➡️  Clicking next page...")
                try:
                    next_page_link.click()
                    # Wait for next page specific element
                    try:
                        page.wait_for_selector(f"a.se-active[data-se-page-number='{current_page_num + 1}']", timeout=10000)
                    except:
                        print("     ⚠️ Timeout waiting for pagination update, assuming loaded...")
                        time.sleep(3)
                        
                    current_page_num += 1
                except Exception as e:
                    print(f"  ⚠️  Pagination click failed: {e}")
                    break
            else:
                print("  ⏹️  No next page found, stopping pagination.")
                break

        print(f"  📦 Assembling {len(collected_product_html)} pages of data in Python...")
        
        # We plakken alles aan elkaar in Python, NIET in de browser
        all_products_html = "\n<!-- PAGE BREAK -->\n".join(collected_product_html)
        
        # Injecteer de producten in de skeleton
        full_html = page_skeleton.replace('<!-- PRODUCTS_PLACEHOLDER -->', all_products_html)
        
        return full_html

    def login(self, page: Page):
        print("  🔑 Performing Login...")
        
        # Read credentials
        config = configparser.ConfigParser()
        config.read(Config.SECRETS_PATH)
        
        if 'phoenix' not in config:
            print("  ⚠️  No [phoenix] section in credentials.ini")
            return
            
        email = config['phoenix'].get('email')
        password = config['phoenix'].get('password')
        
        # 1. Click Login Link
        try:
            # <span id="cu-login"> <a ...>
            login_link = page.locator("#cu-login a")
            
            # Check of we al ingelogd zijn
            logout_btn = page.locator("#cu-logout")
            if (logout_btn.is_visible()):
                print("  Already logged in (Logout button visible)")
                return

            if login_link.is_visible():
                login_link.click()
                print("  Clicked Login Link")
                page.wait_for_load_state("networkidle")
            else:
                print("  Login link not found (already logged in?)")
        except Exception as e:
            print(f"  Login link logic error: {e}")

        # 2. Email Step
        # User XPath: //*[@id="form20"]/div[1]/div[3]/div[1]/div[2]
        # This looks like a Div. I'll click it, then try to type.
        try:
            email_field = page.locator('xpath=//*[@id="form20"]/div[1]/div[3]/div[1]/div[2]')
            
            # Wacht op zichtbaarheid
            email_field.wait_for(state="visible", timeout=5000)
            
            # Als er al tekst staat, probeer die te wissen (Select All + Backspace)
            # Omdat het een DIV/wrapper is, werkt .clear() of .fill() misschien niet direct op de wrapper.
            # We proberen te klikken en met keyboard commands alles te selecteren.
            email_field.click()
            time.sleep(0.5)
            # Forceer focus en selecteer alles
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            time.sleep(0.5)

            # Nu schoon invullen
            page.keyboard.type(email, delay=50) # Type blindly if focused
            print("  Entered Email")
            
            # 3. Click Next
            next_btn = page.get_by_role("button", name="Next")
            if not next_btn.is_visible():
                next_btn = page.get_by_text("Next", exact=True)
            
            next_btn.click()
            print("  Clicked Next")
            time.sleep(2) # Wait for animation/step
            
            # 4. Password Step
            # //*[@id="input64"]
            page.locator('xpath=//*[@id="input64"]').fill(password)
            print("  Entered Password")
            
            # 5. Click Verify
            verify_btn = page.get_by_role("button", name="Verify")
            if not verify_btn.is_visible():
                verify_btn = page.get_by_text("Verify", exact=True)
                
            verify_btn.click()
            print("  Clicked Verify")
            
            # BELANGRIJK: Wacht tot de OAuth sequence klaar is.
            # We wachten tot de URL verandert naar iets dat NIET de login-server is,
            # of tot we expliciet op de 'myphoenixcontact' of productpagina zijn.
            print("  ⏳ Waiting for login redirects to complete...")
            try:
                # Wacht tot URL niet meer start met de login server
                # Of wacht expliciet op 'myphoenixcontact' of de target URL
                page.wait_for_url(lambda u: "login.phoenixcontact.com" not in u, timeout=30000)
                
                # Wacht nog heel even tot de nieuwe pagina 'rustig' is
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2) 
            except Exception as e:
                print(f"  ⚠️ Wait for redirect time-out (continuing anyway): {e}")

            # CHECK: Na login redirect naar profielpagina?
            current_url = page.url
            print(f"  Current URL after login: {current_url}")
            
            # De daadwerkelijke navigatie terug gebeurt in execute()
            
        except Exception as e:
            print(f"  ⚠️ Login failed or skipped: {e}")

    def set_page_size(self, page: Page):
        print("  📏 Setting page size to 50...")
        try:
            # Open Dropdown - gebruik .first om strict mode te fixen
            page.locator(".edd-head").first.click()
            time.sleep(0.5)
            
            # Select 50 - gebruik .first
            option_50 = page.locator('.edd-option[title="50"]').first
            if option_50.is_visible():
                option_50.click()
                print("  Selected 50 items")
                # Wait for HTMX swap
                time.sleep(3)
            else:
                print("  Option '50' not found")
        except Exception as e:
            print(f"  ⚠️ Error setting page size: {e}")

