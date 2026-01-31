"""
╔════════════════════════════════════════════════════════════════╗
║  Rows Extractor - Extract data uit row-based structures       ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from core.utils import clean_text, nearest_heading


class RowsExtractor(BaseExtractor):
    """Extract key-value pairs uit row-gebaseerde structuren (VEGA, Nexans)."""
    
    @property
    def extractor_type(self) -> str:
        return "rows"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data uit row-based structures."""
        count = 0
        
        rows_selector = spec.get("rows", "")
        key_selector = spec.get("key", "")
        value_selector = spec.get("value", "")
        multiple_values = spec.get("multiple_values", False)
        remove_noise = spec.get("remove_noise", [])
        
        # Vind alle rows
        rows = soup.select(rows_selector)
        
        for row in rows:
            section = nearest_heading(row)
            
            # Extract key
            key_elem = row.select_one(key_selector)
            if not key_elem:
                continue
            
            key = clean_text(key_elem.get_text(" ", strip=True))
            if not key:
                continue
            
            # Remove noise elements
            for noise_sel in remove_noise:
                for noise in row.select(noise_sel):
                    noise.decompose()
            
            # Extract value(s)
            if multiple_values:
                value_elems = row.select(value_selector)
                values = [clean_text(v.get_text(" ", strip=True)) for v in value_elems]
                values = [v for v in values if v]
                value = " | ".join(values) if values else ""
            else:
                value_elem = row.select_one(value_selector)
                value = clean_text(value_elem.get_text(" ", strip=True)) if value_elem else ""
            
            if value:
                kv[section][key] = value
                count += 1
        
        return count
