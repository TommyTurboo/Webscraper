"""
╔════════════════════════════════════════════════════════════════╗
║  DL Extractor - Extract data uit definition lists             ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from core.utils import clean_text, nearest_heading


class DLExtractor(BaseExtractor):
    """Extract key-value pairs uit definition lists (<dl><dt><dd>)."""
    @property
    def extractor_type(self) -> str:
        return "dl"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data uit definition lists."""
        count = 0
        
        container_sel = spec.get("container", "body")
        container = soup.select_one(container_sel)
        if not container:
            container = soup  # Fallback naar hele document
        
        for dl in container.find_all("dl"):
            section = nearest_heading(dl)
            
            dt_tags = dl.find_all("dt")
            dd_tags = dl.find_all("dd")
            
            # Zip DT en DD samen
            for dt, dd in zip(dt_tags, dd_tags):
                key = clean_text(dt.get_text(" ", strip=True))
                value = clean_text(dd.get_text(" ", strip=True))
                
                if key and value:
                    kv[section][key] = value
                    count += 1
        
        return count
