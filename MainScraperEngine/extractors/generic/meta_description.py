"""
╔════════════════════════════════════════════════════════════════╗
║  Meta Description Extractor - Extract from meta tags          ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor


class MetaDescriptionExtractor(BaseExtractor):
    """Extract description uit HTML <meta> tags."""
    
    @property
    def extractor_type(self) -> str:
        return "meta_description"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract meta description."""
        count = 0
        
        selector = spec.get("selector", "meta[name='description']")
        attribute = spec.get("attribute", "content")
        target_section = spec.get("target_section", "General")
        target_key = spec.get("target_key", "Description")
        
        elem = soup.select_one(selector)
        if elem and elem.has_attr(attribute):
            description = elem[attribute].strip()
            if description:
                kv[target_section][target_key] = description
                count = 1
        
        return count
