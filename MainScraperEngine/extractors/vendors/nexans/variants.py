"""
╔════════════════════════════════════════════════════════════════╗
║  Nexans Variants Extractor - Product variant lists            ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from core.utils import clean_text


class NexansVariantsExtractor(BaseExtractor):
    """
    Extract product variants uit Nexans productlijst.
    Nexans heeft een unieke structuur met variant items.
    """
    
    @property
    def extractor_type(self) -> str:
        return "product_variants"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract product variants."""
        count = 0
        
        container_sel = spec.get("container", "body")
        variant_sel = spec.get("variant_selector", "")
        fields_config = spec.get("fields", {})
        container = soup.select_one(container_sel)
        if not container:
            container = soup  # Fallback naar hele document
        
        variants = container.select(variant_sel)
        
        if not variants:
            return 0
        
        # Maak een lijst voor alle variants
        variant_list = []
        
        for variant_elem in variants:
            variant_info = {}
            
            # Extract title
            if "title" in fields_config:
                title_elem = variant_elem.select_one(fields_config["title"])
                if title_elem:
                    variant_info["title"] = clean_text(title_elem.get_text(" ", strip=True))
            
            # Extract reference
            if "ref" in fields_config:
                ref_elem = variant_elem.select_one(fields_config["ref"])
                if ref_elem:
                    variant_info["ref"] = clean_text(ref_elem.get_text(" ", strip=True))
            
            # Extract URL
            if "url" in fields_config:
                url_elem = variant_elem.select_one(fields_config["url"])
                if url_elem and url_elem.has_attr("href"):
                    variant_info["url"] = url_elem["href"]
            
            # Extract specs (nested)
            if "specs" in fields_config:
                specs_config = fields_config["specs"]
                variant_specs = {}
                
                rows = variant_elem.select(specs_config.get("rows", ""))
                for row in rows:
                    key_elem = row.select_one(specs_config.get("key", ""))
                    value_elem = row.select_one(specs_config.get("value", ""))
                    
                    if key_elem and value_elem:
                        key = clean_text(key_elem.get_text(" ", strip=True))
                        value = clean_text(value_elem.get_text(" ", strip=True))
                        
                        if key and value:
                            variant_specs[key] = value
                
                if variant_specs:
                    variant_info["specs"] = variant_specs
            
            if variant_info:
                variant_list.append(variant_info)
                count += 1
        
        # Sla alle variants op in een speciale sectie
        if variant_list:
            kv["Product Variants"]["Items"] = variant_list
        
        return count
