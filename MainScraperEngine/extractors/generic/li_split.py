"""
╔════════════════════════════════════════════════════════════════╗
║  LI Split Extractor - Extract uit LI items (Siemens style)    ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup, Tag
from extractors.base import BaseExtractor
from core.utils import clean_text


class LiSplitExtractor(BaseExtractor):
    """Extract key-value pairs uit LI elementen door te splitsen op newline."""
    
    @property
    def extractor_type(self) -> str:
        return "li_split"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data uit LI elements met split strategie."""
        count = 0
        
        container_sel = spec.get("container", "body")
        section_headers = spec.get("section_headers", ["h3", "h4"])
        items_sel = spec.get("items", "li")
        split_on = spec.get("split_on", "\n")
        skip_texts = set(t.lower() for t in spec.get("skip_texts", []))
        min_parts = spec.get("min_parts", 2)
          # Vind container
        container = soup.select_one(container_sel)
        if not container:
            container = soup  # Fallback naar hele document
        
        current_section = "Unknown"
        
        # Loop door alle descendants
        for el in container.descendants:
            if not isinstance(el, Tag):
                continue
            
            # Update section als we een header tegenkomen
            if el.name in section_headers:
                section_text = clean_text(el.get_text(" ", strip=True))
                if section_text and section_text.lower() not in skip_texts:
                    current_section = section_text
            
            # Extract LI items
            elif el.name == items_sel.strip().replace("li", ""):  # Simpele check
                text = el.get_text(split_on, strip=True)
                parts = [clean_text(p) for p in text.split(split_on)]
                parts = [p for p in parts if p]
                
                if len(parts) >= min_parts:
                    key = parts[0]
                    value = " ".join(parts[1:])
                    
                    if key and value:
                        kv[current_section][key] = value
                        count += 1
        
        return count
