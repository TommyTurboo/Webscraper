"""
╔════════════════════════════════════════════════════════════════╗
║  Datasheet Link Extractor - Find PDF datasheet links          ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from core.utils import clean_text


class DatasheetLinkExtractor(BaseExtractor):
    """
    Extract datasheet PDF links uit HTML.
    Ondersteunt meerdere strategieën:
    - CSS selectors met attribute matching
    - Text-based search (fallback)
    """
    
    @property
    def extractor_type(self) -> str:
        return "datasheet_link"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract datasheet link."""
        count = 0
        
        selectors = spec.get("selectors", [])
        if not selectors:
            return 0
        
        attribute = spec.get("attribute", "href")
        target_section = spec.get("target_section", "Downloads")
        target_key = spec.get("target_key", "Datasheet")
        base_url = spec.get("base_url", "")
        
        # Strategie 1: Probeer CSS selectors
        for selector in selectors:
            elements = soup.select(selector)
            
            for elem in elements:
                if elem.has_attr(attribute):
                    url = elem[attribute]
                    
                    # Valideer dat het een datasheet lijkt
                    if self._is_datasheet_url(url):
                        # Prepend base_url if needed
                        if base_url and not url.startswith(("http:", "https:")):
                            from urllib.parse import urljoin
                            url = urljoin(base_url, url)

                        kv[target_section][target_key] = url
                        count += 1
                        return count  # Stop na eerste match
        
        # Strategie 2: Text-based fallback
        if count == 0:
            datasheet_keywords = ["datasheet", "productfiche", "datenblatt", "fiche technique"]
            
            for link in soup.find_all("a", href=True):
                link_text = clean_text(link.get_text()).lower()
                href = link["href"]
                
                # Check of tekst datasheet keyword bevat
                if any(keyword in link_text for keyword in datasheet_keywords):
                    if self._is_datasheet_url(href):
                        # Prepend base_url if needed
                        if base_url and not href.startswith(("http:", "https:")):
                            from urllib.parse import urljoin
                            href = urljoin(base_url, href)

                        kv[target_section][target_key] = href
                        count += 1
                        return count
        
        return count
    
    def _is_datasheet_url(self, url: str) -> bool:
        """Valideer of URL naar een datasheet lijkt."""
        url_lower = url.lower()
        
        # Check op PDF extensie of datasheet in URL
        return (
            url_lower.endswith(".pdf") or
            "datasheet" in url_lower or
            "productfiche" in url_lower or
            "teddatasheet" in url_lower or
            "datenblatt" in url_lower or
            "/product/pdf/" in url_lower  # Nexans specific pattern
        )
