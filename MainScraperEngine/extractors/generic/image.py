"""
╔════════════════════════════════════════════════════════════════╗
║  Image Extractor - Extract product image URLs                 ║
╚════════════════════════════════════════════════════════════════╝
"""
import json
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor


class ImageExtractor(BaseExtractor):
    """
    Extract product image URLs uit HTML.
    Ondersteunt:
    - CSS selectors (multiple fallbacks)
    - JSON-LD structured data fallback
    - First/Last/All selection modes
    """
    
    @property
    def extractor_type(self) -> str:
        return "attribute"  # Legacy naam voor backwards compatibility
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract image URL(s)."""
        count = 0
        
        # Selector(s) ophalen - kan lijst of enkele string zijn
        selectors = spec.get("selectors", [])
        if not selectors:
            selectors = [spec.get("selector", "")]
        
        if isinstance(selectors, str):
            selectors = [selectors]
        
        attribute = spec.get("attribute", "src")
        target_section = spec.get("target_section", "Product Info")
        target_key = spec.get("target_key", "Image URL")
        
        # Selectie modus: "first", "last", of "all"
        take = spec.get("take", "first")
        
        # Strategie 1: CSS selectors
        for selector in selectors:
            elements = soup.select(selector)
            
            if elements:
                urls = []
                for elem in elements:
                    if elem.has_attr(attribute):
                        urls.append(elem[attribute])
                
                if urls:
                    if take == "first":
                        kv[target_section][target_key] = urls[0]
                        count = 1
                    elif take == "last":
                        kv[target_section][target_key] = urls[-1]
                        count = 1
                    elif take == "all":
                        kv[target_section][target_key] = urls
                        count = len(urls)
                    
                    return count  # Stop na eerste succesvolle selector
        
        # Strategie 2: JSON-LD fallback (alleen voor images)
        if count == 0 and spec.get("fallback_jsonld", False):
            count = self._extract_from_jsonld(soup, target_section, target_key, kv)
        
        return count
    
    def _extract_from_jsonld(self, soup: BeautifulSoup, section: str, key: str, kv: Dict) -> int:
        """Probeer image URL uit JSON-LD structured data te halen."""
        scripts = soup.find_all("script", type="application/ld+json")
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Zoek naar image veld
                image_url = self._find_image_in_json(data)
                
                if image_url:
                    kv[section][key] = image_url
                    return 1
            
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return 0
    
    def _find_image_in_json(self, data: Any) -> str:
        """Recursief zoeken naar image URL in JSON."""
        if isinstance(data, dict):
            # Direct image key
            if "image" in data:
                img = data["image"]
                if isinstance(img, str):
                    return img
                elif isinstance(img, list) and img:
                    return img[0] if isinstance(img[0], str) else img[0].get("url", "")
                elif isinstance(img, dict):
                    return img.get("url", "")
            
            # Recursief zoeken
            for value in data.values():
                result = self._find_image_in_json(value)
                if result:
                    return result
        
        elif isinstance(data, list):
            for item in data:
                result = self._find_image_in_json(item)
                if result:
                    return result
        
        return ""
