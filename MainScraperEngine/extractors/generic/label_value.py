"""
╔════════════════════════════════════════════════════════════════╗
║  Label-Value Extractor - Extract via regex patterns           ║
╚════════════════════════════════════════════════════════════════╝
"""
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from core.utils import clean_text, nearest_heading


class LabelValueExtractor(BaseExtractor):
    """Extract key-value pairs met regex patroon (generic fallback)."""
    
    @property
    def extractor_type(self) -> str:
        return "label_value"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data via regex patterns."""
        count = 0
        
        pattern = re.compile(spec.get("pattern", r"^(.{2,80}):\s*(.{1,200})$"))
        elements = spec.get("elements", ["p", "li", "div", "span"])
        
        for el in soup.find_all(elements):
            text = clean_text(el.get_text(" ", strip=True))
            match = pattern.match(text)
            
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                section = nearest_heading(el)
                
                if key and value:
                    kv[section][key] = value
                    count += 1
        
        return count
