"""
╔════════════════════════════════════════════════════════════════╗
║  Product Variants Extractor - Generic list extractor          ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from core.utils import clean_text


class ProductVariantsExtractor(BaseExtractor):
    """
    Extract product variants from a list of items using selectors.
    Generic extractor for product lists, configured via YAML.
    """
    
    @property
    def extractor_type(self) -> str:
        return "product_variants"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract product variants."""
        count = 0
        
        container_sel = spec.get("container", "body")
        variant_sel = spec.get("variant_selector", "")
        base_url = spec.get("base_url", "")
        fields_config = spec.get("fields", {})
        
        container = soup.select_one(container_sel)
        if not container:
            container = soup  # Fallback to the entire document
        
        variants = container.select(variant_sel)
        
        if not variants:
            return 0
        
        # Create a list for all variants
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
                    url_val = url_elem["href"]
                    if base_url and not url_val.startswith(("http:", "https:")):
                         url_val = urljoin(base_url, url_val)
                    variant_info["url"] = url_val
            
            # Extract Description
            if "description" in fields_config:
                desc_elem = variant_elem.select_one(fields_config["description"])
                if desc_elem:
                    variant_info["description"] = clean_text(desc_elem.get_text(" ", strip=True))

            # Extract Image
            if "image" in fields_config:
                img_elem = variant_elem.select_one(fields_config["image"])
                if img_elem and img_elem.has_attr("src"):
                    variant_info["image"] = img_elem["src"]

            # Extract List Price
            if "list_price" in fields_config:
                price_elem = variant_elem.select_one(fields_config["list_price"])
                if price_elem:
                    # Remove potential noise like "/" or "per Piece" from text
                    text = clean_text(price_elem.get_text(" ", strip=True))
                    # Remove trailing separator if present (e.g. "9.058,00 EUR /")
                    if text.endswith("/"):
                        text = text[:-1].strip()
                    variant_info["list_price"] = text

            # Extract Your Price
            if "your_price" in fields_config:
                price_elem = variant_elem.select_one(fields_config["your_price"])
                if price_elem:
                    variant_info["your_price"] = clean_text(price_elem.get_text(" ", strip=True))

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
        
        # Save all variants in a special section
        if variant_list:
            kv["Product Variants"]["Items"] = variant_list
        
        return count
