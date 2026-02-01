# filepath: c:\Users\tomva\PlatformIO\my-node-project\MainScraperEngine\extractors\vendors\vega_pdf.py
"""
╔════════════════════════════════════════════════════════════════╗
║  VEGA PDF Extractor                                            ║
║  Extract PDF download URLs from multi-language document cards  ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor


class VegaPdfExtractor(BaseExtractor):
    """
    Extract VEGA document download URLs from product pages.
    
    HTML Pattern:
    <div class="cards">
      <div class="card">
        <h3>Productspecificatieblad</h3>  <!-- Document type -->
        <p>VEGACAP 27</p>                 <!-- Product name -->
        <ul class="languages">
          <li class="language selected" data-url="/api/sitecore/DocumentDownload/Handler?...">
            <!-- Selected language (NL) -->
          </li>
        </ul>
        <a href="..." download>Download</a>
      </div>
    </div>
    
    URL Pattern:
    https://www.vega.com/api/sitecore/DocumentDownload/Handler?
      documentContainerId=4086&languageId=5&fileExtension=pdf&...
    
    Document Types:
    - Productcatalogus (Product Catalog)
    - Productspecificatieblad (Product Specification Sheet)
    - Productinformatie (Product Information)
    - Handleiding (Manual)
    - Aanvullende handleiding (Additional Manual)
    - Beknopte handleiding (Quick Guide)
    """
    
    @property
    def extractor_type(self) -> str:
        return "vega_pdf"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """
        Extract all document download URLs from VEGA product page.
        
        Spec parameters:
        - target_section: Where to store PDF URLs (default: "Downloads")
        - base_url: Base URL for relative links (default: "https://www.vega.com")
        - cards_selector: CSS selector for cards container (default: "div.cards")
        - card_selector: CSS selector for individual cards (default: "div.card")
        """
        count = 0
        
        # Configuration
        target_section = spec.get("target_section", "Downloads")
        base_url = spec.get("base_url", "https://www.vega.com")
        cards_selector = spec.get("cards_selector", "div.cards")
        card_selector = spec.get("card_selector", "div.card")
        
        # Find the cards container
        cards_container = soup.select_one(cards_selector)
        if not cards_container:
            return 0
        
        # Find all document cards
        cards = cards_container.select(card_selector)
        
        for card in cards:
            # Extract document type from <h3>
            h3 = card.find("h3")
            if not h3:
                continue
            
            doc_type = h3.get_text(strip=True)
            if not doc_type:
                continue
            
            # Find the selected language with data-url
            selected_lang = card.select_one("li.language.selected[data-url]")
            if not selected_lang:
                continue
            
            data_url = selected_lang.get("data-url", "").strip()
            if not data_url:
                continue
            
            # Build complete URL (prepend base URL if relative)
            if data_url.startswith("/"):
                pdf_url = base_url + data_url
            elif data_url.startswith("http"):
                pdf_url = data_url
            else:
                pdf_url = base_url + "/" + data_url
            
            # Store in Downloads section with document type as key
            kv[target_section][doc_type] = pdf_url
            count += 1
        
        return count
