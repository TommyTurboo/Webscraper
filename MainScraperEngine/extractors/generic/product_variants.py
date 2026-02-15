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
            if "item_reference" in fields_config:
                ref_elem = variant_elem.select_one(fields_config["item_reference"])
                if ref_elem:
                    variant_info["item_reference"] = clean_text(ref_elem.get_text(" ", strip=True))
            elif "ref" in fields_config:
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
                price_selector = fields_config["list_price"]
                price_elem = variant_elem.select_one(price_selector)
                
                # Fallback check for shadow DOM templates
                if not price_elem:
                    for tmpl in variant_elem.find_all('template'):
                        # Check inside template content
                        # Since BS4 parses template content as child tags usually:
                        found = tmpl.select_one(price_selector)
                        if found:
                            price_elem = found
                            break

                if price_elem:
                    # Remove potential noise like "/" or "per Piece" from text
                    text = clean_text(price_elem.get_text(" ", strip=True))
                    # Remove trailing separator if present (e.g. "9.058,00 EUR /")
                    if text.endswith("/"):
                        text = text[:-1].strip()
                    variant_info["list_price"] = text

            # Extract Your Price
            if "your_price" in fields_config:
                price_selector = fields_config["your_price"]
                # 1. Try direct selection (works if no shadow, or if parsed flat)
                price_elem = variant_elem.select_one(price_selector)
                
                # 2. Fallback check for shadow DOM templates
                if not price_elem:
                    # Check ALL 'sh-product-price' elements or just look for ANY template
                    # Looking specifically inside sh-product-price might be safer if we knew
                    # But generic search in templates is fine.
                    
                    for tmpl in variant_elem.find_all('template'):
                        # Try select_one directly on the template tag
                        found = tmpl.select_one(price_selector)
                        if found:
                            price_elem = found
                            break
                        
                        # If not found, try parsing the template content as HTML string
                        if tmpl.string:
                            try:
                                template_soup = BeautifulSoup(tmpl.string, 'html.parser')
                                found = template_soup.select_one(price_selector)
                                if found:
                                    price_elem = found
                                    break
                            except Exception:
                                pass
                
                if price_elem:
                    # ✨ NEW FIX: Handle price format "304,17" -> "304.17" or standard currency cleaning
                    raw_price = clean_text(price_elem.get_text(" ", strip=True))
                    # If empty, maybe it was hidden?
                    if raw_price:
                         variant_info["your_price"] = raw_price
                    else:
                        # Sometimes text is in data attribute or value
                        pass

            # ✨ NEW: Extract Availability
            if "availability" in fields_config:
                avail_elem = variant_elem.select_one(fields_config["availability"])
                if avail_elem:
                    variant_info["availability"] = clean_text(avail_elem.get_text(" ", strip=True))

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
