"""
╔════════════════════════════════════════════════════════════════╗
║  Table Extractor - Extract data uit HTML tables               ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractors.base import BaseExtractor
from core.utils import clean_text, nearest_heading  # Direct import - geen __init__


class TableExtractor(BaseExtractor):
    """Extract key-value pairs uit HTML tabellen."""
    
    @property
    def extractor_type(self) -> str:
        return "table"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data uit HTML tables."""
        count = 0
        
        container_sel = spec.get("container", "body")
        tables_sel = spec.get("tables", "table")
        
        container = soup.select_one(container_sel)
        if not container:
            container = soup  # Fallback naar hele document
        
        tables = container.select(tables_sel)
        
        for table in tables:
            count += self._extract_table(table, spec, kv)
        
        return count
    
    def _extract_table(self, table, spec: Dict, kv: Dict) -> int:
        """Extract single table."""
        count = 0
        section = nearest_heading(table)
        
        extract_mode = spec.get("extract_mode", "auto")
        key_col = spec.get("key_column", 0)
        val_col = spec.get("value_column", 1)
        skip_class = spec.get("skip_rows_with_class")
        
        for row in table.find_all("tr"):
            # Skip header rows
            if skip_class and row.get("class") and skip_class in row.get("class"):
                continue
            
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            
            # Extract key en value
            if key_col < len(cells) and val_col < len(cells):
                key = clean_text(cells[key_col].get_text(" ", strip=True))
                value = clean_text(cells[val_col].get_text(" ", strip=True))
                
                if key and value:
                    kv[section][key] = value
                    count += 1
        
        return count
