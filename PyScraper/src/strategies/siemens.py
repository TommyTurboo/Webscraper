from .base import BaseStrategy

class SiemensStrategy(BaseStrategy):
    def perform_actions(self, page):
        print("  ⚙️  Running Siemens specific actions...")
        
        # 1. Cookie Banner
        # Probeer verschillende selectors voor de 'Alles accepteren' knop
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

        # 2. 'Technische gegevens' Tabblad
        # Zoek naar tabblad en klik (met force=True voor het geval er iets overheen ligt)
        try:
            tab_locator = page.get_by_text("Technische gegevens", exact=False)
            if tab_locator.count() > 0:
                print("  🖱️  Clicking 'Technische gegevens' tab...")
                tab_locator.first.click(force=True)
                self.random_delay(1500, 2500) # Wacht tot tab geladen is
        except Exception as e:
            print(f"  ⚠️  Could not click tab: {e}")

        # 3. 'Meer laden' knoppen (indien aanwezig)
        # Hier kun je in de toekomst logica toevoegen om 'Show more' knoppen in tabellen te klikken
