import time
from playwright.sync_api import Page
from .base import BaseStrategy
from core.config import Config

class SchneiderStrategy(BaseStrategy):
    """
    Strategie voor Schneider Electric (se.com).
    Ondersteunt zowel productlijst-pagina's (Ranges) als detailpagina's.
    """

    def accept_cookies(self, page: Page):
        print("  🍪 Checking for Schneider cookie banner...")
        try:
            # Wacht even op de banner
            time.sleep(2)
            
            # Schneider heeft vaak een Shadow DOM banner of een 'Onetrust' banner
            # 1. Probeer generieke teksten
            possible_texts = ["Accept All", "Alles accepteren", "Akkoord", "Allow all cookies"]
            
            for text in possible_texts:
                # Zoek naar knoppen die deze tekst bevatten
                # We gebruiken een brede selector omdat IDs vaak veranderen
                btn = page.get_by_role("button", name=text)
                if btn.count() > 0 and btn.is_visible():
                    print(f"  ✅ Found cookie button with text '{text}'")
                    btn.click()
                    return

            # 2. Specifieke selector voor OneTrust (indien aanwezig)
            onetrust_btn = page.locator("#onetrust-accept-btn-handler")
            if onetrust_btn.count() > 0 and onetrust_btn.is_visible():
                print("  ✅ Clicked OneTrust accept button")
                onetrust_btn.click()
                return

        except Exception as e:
            print(f"  ⚠️ Cookie handling warning: {e}")

    def execute(self, page: Page, url: str):
        print(f"  📡 Navigating to {url}")
        
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=Config.TIMEOUT_PAGE_LOAD)
        except Exception as e:
            print(f"  ⚠️ Navigation warning: {e}")

        # Wacht op initiële load
        time.sleep(3)
        self.accept_cookies(page)

        # DETECTIE: Is dit een Lijst (Range) of Detail pagina?
        # A) Check op URL patroon
        if "/product-range/" in page.url or "parent-subcategory-id" in page.url:
            print("  📋 Detected LIST/RANGE page mode (based on URL).")
            return self.execute_list_mode(page)
            
        # B) Check op aanwezigheid van specifieke elementen (fallback)
        # We zoeken naar de list/grid switch buttons
        # Playwright gaat automatisch door open Shadow DOMs heen
        list_switch = page.locator(".button-list, [title='Lijst']")
        
        if list_switch.count() > 0:
            print("  📋 Detected LIST/RANGE page mode (based on elements).")
            return self.execute_list_mode(page)
        else:
            print("  📦 Detected PRODUCT DETAIL page mode.")
            return self.execute_detail_mode(page)

    def execute_detail_mode(self, page: Page):
        """Handelt enkele productpagina's af."""
        print("  ⬇️ Scrolling for lazy loading...")
        self.scroll_to_bottom(page)
        
        # Smart wait voor prijzen (vaak dynamisch geladen)
        self.smart_price_wait(page)
        
        # Expand Shadow DOM voor opslaan
        self.expand_shadow_dom(page)
        
        # Return full HTML
        return page.evaluate("() => document.documentElement.outerHTML")

    def execute_list_mode(self, page: Page):
        """Handelt multi-page lijsten af."""
        
        # 1. Schakel naar ListView (indien nog niet actief)
        try:
            # Zoek de knop met class 'button-list' of title 'Lijst'
            # Playwright locators boren automatisch door Shadow DOM
            list_btn = page.locator(".button-list, button[title='Lijst']").first
            
            if list_btn.is_visible():
                classes = list_btn.get_attribute("class") or ""
                if "active" not in classes:
                    print("  🔲 Switching to List View...")
                    list_btn.click()
                    time.sleep(2) 
                else:
                    print("  ✅ List View already active.")
        except Exception as e:
            print(f"  ⚠️ Could not switch to List View: {e}")

        collected_html_parts = []
        current_page_num = 1
        
        while True:
            print(f"  📄 Processing list page {current_page_num}...")
            
            self.scroll_to_bottom(page)
            self.smart_price_wait(page)
            
            # NIEUWE METHODE: Non-destructive read
            # We veranderen de pagina NIET, we lezen alleen uit.
            print("  📸 Snapshotting page content (Memory only)...")
            
            # DEBUG: Print de IDs die we nu zien om te checken of we werkelijk nieuwe data hebben
            debug_ids = page.evaluate("""() => {
                const w = document.querySelector('product-cards-wrapper');
                return w ? w.getAttribute('product-ids') : 'No wrapper found';
            }""")
            if debug_ids and len(debug_ids) > 50:
                print(f"     👀 Current IDs start: {debug_ids[:50]}...")
            else:
                print(f"     👀 Current IDs: {debug_ids}")

            # MOD: Geef door of dit de eerste pagina is
            is_first_page = (current_page_num == 1)
            page_content = self.get_snapshot_html(page, is_first_page)
            
            # CRUCIAL FIX: HTML Concatenation Logic
            # Parsers stoppen vaak na </html>. We moeten zorgen dat we 1 lange valide body maken.
            if is_first_page:
                # Strip closing tags van page 1
                page_content = page_content.replace('</body>', '').replace('</html>', '')
            
            collected_html_parts.append(page_content)
            print(f"     -> Content captured ({len(page_content)} bytes)")

            # Zoek VOLGENDE knop 
            # ... rest van de paginatie code blijft hetzelfde
            next_btn = page.locator("se-icon[title='Volgende'], se-icon[title='Next'], se-icon[arial-label='Volgende'], se-icon[aria-label='Volgende']").first
            
            # Debug info
            print(f"     -> Checking for next button (Found: {next_btn.count()})")
            
            if next_btn.count() > 0:
                # Capture huidige state VOOR de klik (voor vergelijking)
                previous_state_hash = page.evaluate("""() => {
                    const w = document.querySelector('product-cards-wrapper');
                    return w ? w.getAttribute('product-ids') : document.body.innerText.substring(0, 200);
                }""")

                # ... (rest van click logic blijft grotendeels gelijk, maar we halen expand_shadow_dom weg) ->
                
                try:
                    next_btn.scroll_into_view_if_needed()
                except:
                    pass

                is_visible = next_btn.is_visible()
                if not is_visible:
                     print("  ⚠️ Button reports not visible, trying to force click anyway...")
                
                # Check disabled...
                is_disabled = page.evaluate("""(icon) => {
                       // ... (zelfde check als voorheen) ...
                       if (icon.hasAttribute('disabled')) return true;
                       if (icon.classList.contains('disabled')) return true;
                       if (icon.shadowRoot) {
                            const internalBtn = icon.shadowRoot.querySelector('button');
                            if (internalBtn && (internalBtn.disabled || internalBtn.classList.contains('disabled'))) return true;
                       }
                       const parentBtn = icon.closest('button');
                       if (parentBtn && (parentBtn.disabled || parentBtn.classList.contains('disabled'))) return true;
                       return false;
                }""", next_btn.element_handle())
                    
                if is_disabled:
                        print("  ⏹️ Next button is disabled. End of list.")
                        break
                        
                print("  ➡️ Clicking next page...")
                try:
                        next_btn.click(force=True)
                        print("  ⏳ Waiting for content update...")
                        
                        # Wacht tot het product-ids attribuut verandert
                        try:
                            updated = False
                            for _ in range(20): # 10 sec
                                time.sleep(0.5)
                                current_state_hash = page.evaluate("""() => {
                                    const w = document.querySelector('product-cards-wrapper');
                                    return w ? w.getAttribute('product-ids') : document.body.innerText.substring(0, 200);
                                }""")
                                
                                if current_state_hash != previous_state_hash:
                                    print("  ✅ Content update detected.")
                                    updated = True
                                    break
                            
                            if not updated:
                                print("  ⚠️ Warning: Content did not appear to change after click.")
                                
                        except Exception as wait_err:
                            print(f"  ⚠️ Content wait error: {wait_err}")

                        current_page_num += 1
                        
                except Exception as e:
                        print(f"  ⚠️ Pagination click error: {e}")
                        break
            else:
                print("  ⏹️ No next page button found.")
                break

        print(f"  📦 Assembling {len(collected_html_parts)} pages of data...")
        
        # Voeg handmatig de sluit-tags toe die we eerder hebben gestript
        full_html = "".join(collected_html_parts) + "</body></html>"
        return full_html

    def get_snapshot_html(self, page: Page, is_first_page: bool = False):
        """
        Genereert een string representatie van de DOM inclusief expanded shadow roots.
        Flattened de structuur voor makkelijkere parsing.
        
        Args:
            is_first_page: Als True, pakken we de hele <html> tag om <head> (canonical) mee te hebben.
                           Als False, pakken we alleen de content wrapper.
        """
        return page.evaluate("""(is_first) => {
            const MAX_DEPTH = 15;
            
            function serializeNode(node, depth) {
                if (depth > MAX_DEPTH) return '';
                
                if (node.nodeType === Node.TEXT_NODE) {
                     return node.nodeValue;
                }
                
                if (node.nodeType === Node.ELEMENT_NODE) {
                    const tagName = node.tagName.toLowerCase();
                    
                    let html = `<${tagName}`;
                    if (node.attributes) {
                        for (let i = 0; i < node.attributes.length; i++) {
                             const attr = node.attributes[i];
                             html += ` ${attr.name}="${attr.value.replace(/"/g, '&quot;')}"`;
                        }
                    }
                    html += ` data-depth="${depth}"`; // Debug info
                    html += '>';
                    
                    let childrenHtml = '';
                    
                    // 1. Shadow DOM content (PRIORITEIT)
                    if (node.shadowRoot) {
                        childrenHtml += '<div class="scraped-shadow-root" style="border: 1px dashed red; margin: 5px; padding: 5px;">';
                        childrenHtml += `<!-- START SHADOW ROOT of ${tagName} -->`;
                        
                        // FIX: We moeten zeker weten dat we children ophalen
                        const shadowChildren = Array.from(node.shadowRoot.childNodes);
                         childrenHtml += `<!-- Found ${shadowChildren.length} shadow children -->`;

                        shadowChildren.forEach(child => {
                            childrenHtml += serializeNode(child, depth + 1);
                        });
                        
                        childrenHtml += `<!-- END SHADOW ROOT of ${tagName} -->`;
                        childrenHtml += '</div>';
                    }
                    
                    // 2. Light DOM children
                    if (node.childNodes.length > 0) {
                        Array.from(node.childNodes).forEach(child => {
                             childrenHtml += serializeNode(child, depth + 1);
                        });
                    }
                    
                    html += childrenHtml;
                    html += `</${tagName}>`;
                    return html;
                }
                
                return '';
            }

            // We moeten de 'product-cards-wrapper' vinden, OOK als die in een shadow root zit.
            // document.querySelector kan niet in shadow roots kijken.
            // We gebruiken een brute-force searcher.
            
            function findElementDeep(root, selector) {
                if (root.matches && root.matches(selector)) return root;
                if (root.shadowRoot) {
                    const found = findElementDeep(root.shadowRoot, selector);
                    if (found) return found;
                }
                
                const children = root.children || root.childNodes; // childNodes voor shadowRoot
                for (let i = 0; i < children.length; i++) {
                    const el = children[i];
                    if (el.nodeType === 1) { // ELEMENT_NODE
                        const found = findElementDeep(el, selector);
                        if (found) return found;
                         // Check shadow root of child
                        if (el.shadowRoot) {
                             const shadowFound = findElementDeep(el.shadowRoot, selector);
                             if (shadowFound) return shadowFound;
                        }
                    }
                }
                return null;
            }

            // LOGICA: Eerste pagina -> Hele site (voor metadata)
            //         Vervolg paginas -> Alleen content
            
            if (is_first) {
                 const logComment = `<!-- SNAPSHOT INFO: Full Page (incl HEAD) -->`;
                 return logComment + serializeNode(document.documentElement, 0);
            }
            
            // Vervolg pagina's: Alleen nieuwe content
            let target = findElementDeep(document.body, 'product-cards-wrapper');
            
            if (!target) {
                // Fallback naar de lijst container
                target = findElementDeep(document.body, '.range-products-tab__products-list');
                if (!target) target = document.body;
            }
            
            // Log voor debugging
            const logComment = `<!-- SNAPSHOT INFO: Target found: ${target.tagName} IDs: ${target.getAttribute('product-ids')} -->`;
            
            return logComment + serializeNode(target, 0);
        }""", is_first_page)

    def expand_shadow_dom(self, page: Page):
        pass

    def smart_price_wait(self, page: Page):
        """Wacht tot prijzen zichtbaar zijn en fixt Shadow DOM indien nodig."""
        login_selectors = [
            "a[href*='login']", 
            "button[data-testid*='login']",
            ".login-link",
            "text=Log in", 
            "text=Aanmelden", 
            "text=Se connecter"
        ]
        
        is_guest = False
        for selector in login_selectors:
            if page.locator(selector).first.is_visible():
                is_guest = True
                break
        
        if is_guest:
             print("  👤 Guest detected (Login button visible): Skipping smart price wait.")
             return

        max_retries = 3
        print("  💰 Checking for prices...")
        
        for attempt in range(max_retries):
            found_prices = page.evaluate("""() => {
                const prices = document.querySelectorAll('.price, .product-price, pes-product-price');
                if (prices.length === 0) return false;
                
                for (let p of prices) {
                    if (p.textContent.trim().length > 0) return true;
                    if (p.shadowRoot && p.shadowRoot.textContent.trim().length > 0) return true;
                }
                return false;
            }""")
            
            if found_prices:
                print("  ✅ Prices detected.")
                break
            else:
                print(f"  ⏳ Attempt {attempt+1}/{max_retries}: Waiting for prices...")
                time.sleep(4)

        page.evaluate("""() => {
            const targets = document.querySelectorAll('*');
            targets.forEach(el => {
                if (el.tagName.startsWith('SE-') || el.tagName.startsWith('PES-')) {
                    if (el.shadowRoot) {
                        try {
                             if(!el.innerText && el.shadowRoot.innerText) {
                                el.setAttribute('data-scraped-content', el.shadowRoot.innerText);
                             }
                        } catch(e) {}
                    }
                }
            });
        }""")
