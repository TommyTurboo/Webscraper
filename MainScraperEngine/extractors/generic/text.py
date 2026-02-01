from bs4 import BeautifulSoup
from typing import Dict, Any
from ..base import BaseExtractor

class TextExtractor(BaseExtractor):
    """Extract plain text from an element."""
    
    @property
    def extractor_type(self) -> str:
        """Return the extractor type."""
        return "text"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract text from a selector and clean whitespace."""
        selector = spec.get("selector")
        target_section = spec.get("target_section", "General")
        target_key = spec.get("target_key", "Text")
        
        element = soup.select_one(selector)
        
        if not element:
            return 0
        
        # Get text and clean ALL whitespace/newlines
        text = element.get_text(separator=" ", strip=True)
        
        # Clean up text:
        import re
        # 1. Replace actual newlines/tabs with space
        text = re.sub(r'[\n\r\t]+', ' ', text)
        # 2. Remove literal \n, \r, \t escape sequences (as text, not characters)
        text = text.replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ')
        # 3. Replace multiple spaces with single space
        text = re.sub(r'\s{2,}', ' ', text)
        # 4. Final trim
        text = text.strip()
        
        if text:
            kv[target_section][target_key] = text
            return 1
        
        return 0
