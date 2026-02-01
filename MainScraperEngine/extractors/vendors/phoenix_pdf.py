"""
╔════════════════════════════════════════════════════════════════╗
║  Phoenix Contact PDF Extractor                                 ║
║  Generate PDF datasheet download URL from article number       ║
╚════════════════════════════════════════════════════════════════╝
"""
import base64
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor


class PhoenixPdfExtractor(BaseExtractor):
    """
    Generate Phoenix Contact PDF download URL.
    
    URL Pattern:
    https://www.phoenixcontact.com/product/pdf/api/v1/{BASE64_ARTICLE_ID}?_realm=be&_locale=nl-BE&blocks=commercial-data%2Ctechnical-data%2Cdrawings%2Capprovals%2Cclassifications%2Cenvironmental-compliance-data%2Call-accessories&action=DOWNLOAD
    
    Example:
    - Article: 2905743 → Base64: MjkwNTc0Mw
    - URL: https://www.phoenixcontact.com/product/pdf/api/v1/MjkwNTc0Mw?...
    """
    
    @property
    def extractor_type(self) -> str:
        return "phoenix_pdf"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """
        Extract article number and generate PDF download URL.
        
        Spec parameters:
        - article_key: Key name in kv where article number is stored (default: "Artikelnummer")
        - article_section: Section name where article number is stored (default: "Productdetails")
        - target_section: Where to store PDF URL (default: "Downloads")
        - target_key: Key name for PDF URL (default: "PDF Datasheet")
        - realm: Region code (default: "be")
        - locale: Language code (default: "nl-BE")
        """
        count = 0
        
        # Configuration
        article_key = spec.get("article_key", "Artikelnummer")
        article_section = spec.get("article_section", "Productdetails")
        target_section = spec.get("target_section", "Downloads")
        target_key = spec.get("target_key", "PDF Datasheet")
        realm = spec.get("realm", "be")
        locale = spec.get("locale", "nl-BE")
        
        # Try to get article number from already extracted data
        article_number = None
        if article_section in kv and article_key in kv[article_section]:
            article_number = kv[article_section][article_key]
        
        # If not found, try to extract from canonical URL as fallback
        if not article_number:
            article_number = self._extract_from_canonical_url(soup)
        
        if not article_number:
            return 0
        
        # Generate PDF URL
        pdf_url = self._generate_pdf_url(article_number, realm, locale)
        
        if pdf_url:
            kv[target_section][target_key] = pdf_url
            count = 1
        
        return count
    
    def _extract_from_canonical_url(self, soup: BeautifulSoup) -> str:
        """
        Extract article number from canonical URL as fallback.
        Example: https://www.phoenixcontact.com/nl-be/producten/....-2905743
        """
        link = soup.find("link", rel="canonical")
        if link and link.has_attr("href"):
            url = link["href"]
            # Article number is typically the last part after the last dash
            parts = url.rstrip('/').split('-')
            if parts:
                potential_article = parts[-1]
                # Validate it's numeric
                if potential_article.isdigit():
                    return potential_article
        return None
    
    def _generate_pdf_url(self, article_number: str, realm: str, locale: str) -> str:
        """
        Generate Phoenix Contact PDF download URL.
        
        Args:
            article_number: Article ID (e.g., "2905743")
            realm: Region code (e.g., "be", "de", "nl")
            locale: Language code (e.g., "nl-BE", "de-DE")
        
        Returns:
            Complete PDF download URL
        """
        # Base64 encode the article number
        encoded_id = base64.b64encode(article_number.encode()).decode()
        
        # Build URL with all standard blocks
        blocks = [
            "commercial-data",
            "technical-data",
            "drawings",
            "approvals",
            "classifications",
            "environmental-compliance-data",
            "all-accessories"
        ]
        blocks_param = "%2C".join(blocks)
        
        pdf_url = (
            f"https://www.phoenixcontact.com/product/pdf/api/v1/{encoded_id}"
            f"?_realm={realm}&_locale={locale}"
            f"&blocks={blocks_param}"
            f"&action=DOWNLOAD"
        )
        
        return pdf_url
