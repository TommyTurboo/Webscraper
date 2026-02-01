"""
╔════════════════════════════════════════════════════════════════╗
║  ABB JSON Extractor - Extract data from var model JavaScript  ║
╚════════════════════════════════════════════════════════════════╝

ABB embeds product data in JavaScript as:
  var model = {ProductViewModel: {...}};

This contains ALL product data including:
- ProductViewModel.Product.attributeGroups.items[] (specifications in Dutch!)
- Product metadata, dimensions, weight
- Variants, accessories, relationships
- etc.

Also extracts Schema.org data from <script type="application/ld+json">
"""
import json
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor


class ABBJSONExtractor(BaseExtractor):
    """
    Extract product data from ABB's var model JavaScript structure.
    
    ABB structure:
    1. var model = {...}; - Contains ProductViewModel with ALL data
    2. <script type="application/ld+json"> - Schema.org Product data
      The extractor automatically finds and merges both sources.
    """
    
    @property
    def extractor_type(self) -> str:
        return "abb_json"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data from ABB's JSON structures."""
        count = 0
        
        # 1. Extract JSON data (var model + LD+JSON)
        json_data = self._extract_all_json_sources(soup, spec)
        if not json_data:
            return 0
        
        # 2. Extract configuration
        extract_config = spec.get("extract", {})
        
        # 3. Extract configured fields (only what's in YAML)
        if "product_id" in extract_config:
            count += self._extract_product_id(json_data, extract_config["product_id"], kv)
        
        if "product_name" in extract_config:
            count += self._extract_product_name(json_data, extract_config["product_name"], kv)
        
        if "image" in extract_config:
            count += self._extract_image(json_data, extract_config["image"], kv)
        
        if "specifications" in extract_config:
            count += self._extract_specifications(json_data, extract_config["specifications"], kv)
        
        return count
    
    def _extract_all_json_sources(self, soup: BeautifulSoup, spec: Dict) -> Dict:
        """Extract JSON from all available sources in the HTML."""
        merged_data = {}
        html_text = str(soup)
        
        print(f"\n🔍 ABB DEBUG: Searching for JSON in HTML...")
        
        # 🎯 PRIMARY: Find var model = {...} (contains ProductViewModel with ALL data!)
        model_pattern = r'var\s+model\s*=\s*(\{.+?\});'
        model_matches = list(re.finditer(model_pattern, html_text, re.DOTALL))
        
        if model_matches:
            print(f"   🎯 Found var model = {{...}}: {len(model_matches[0].group(1)):,} chars")
            json_str = model_matches[0].group(1)
            parsed = self._parse_json(json_str)
            if parsed and isinstance(parsed, dict):
                if "ProductViewModel" in parsed:
                    pvm = parsed["ProductViewModel"]
                    product = pvm.get("Product", {})
                    attr_groups = product.get("attributeGroups", {}).get("items", [])
                    if attr_groups:
                        print(f"   ✅ Found ProductViewModel with {len(attr_groups)} attribute groups")
                merged_data = self._deep_merge(merged_data, parsed)
        
        # SECONDARY: Extract Schema.org LD+JSON data
        ld_json = soup.find_all('script', type='application/ld+json')
        if ld_json:
            for script in ld_json:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        if data.get('@type') == 'Product':
                            merged_data = self._deep_merge(merged_data, data)
                    except:
                        pass
        
        return merged_data
    
    def _parse_json(self, json_str: str) -> Optional[Dict]:
        """Parse JSON string with error handling."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try to clean common issues
            cleaned = (json_str
                      .replace('\\"', '"')
                      .replace("\\'", "'")
                      .replace('\\n', ' ')
                      .replace('\\r', '')
                      .replace('\\t', ' '))
            
            try:
                return json.loads(cleaned)
            except:
                return None
    
    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_by_path(self, data: Any, path: str) -> Any:
        """Navigate through nested dict/list using dotted path notation.
        
        Supports:
        - dict.key
        - list[0]
        - dict.list[0].key
        """
        if not path or data is None:
            return None
        
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]  # Remove empty strings
        
        current = data
        
        for part in parts:
            if part.isdigit():
                # Array index
                idx = int(part)
                if isinstance(current, list) and 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                # Dictionary key
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None
        return current
    
    def _extract_product_id(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract product ID from JSON."""
        product_id = self._get_by_path(data, config.get("path", ""))
        if product_id:
            kv["Product Info"]["Product ID"] = str(product_id)
            return 1
        return 0
    
    def _extract_product_name(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract product name from JSON."""
        name = self._get_by_path(data, config.get("path", ""))
        if name:
            kv["Product Info"]["Product Name"] = str(name)
            return 1
        return 0
    
    def _extract_image(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract product image URL from JSON."""
        image_url = self._get_by_path(data, config.get("path", ""))
        
        if image_url:
            # Handle list of images (take first)
            if isinstance(image_url, list) and len(image_url) > 0:
                image_url = image_url[0]
                if isinstance(image_url, dict):
                    image_url = image_url.get('url') or image_url.get('masterUrl')
            
            if image_url:
                kv["Product Info"]["Image URL"] = str(image_url)
                return 1
        return 0
    def _extract_specifications(self, data: Dict, config: Dict, kv: Dict) -> int:
        """
        Extract product specifications from ABB attribute groups.
        
        Searches for attributeGroups in multiple possible locations.
        """
        # Try ABB-specific paths
        abb_paths = [
            "ProductViewModel.Product.attributeGroups.items",
            "Product.attributeGroups.items",
            "attributeGroups.items"
        ]
        
        attr_groups = None
        for path in abb_paths:
            attr_groups = self._get_by_path(data, path)
            if attr_groups and isinstance(attr_groups, list):
                print(f"\n   📊 Found attribute groups at: {path}")
                print(f"      Groups: {len(attr_groups)}")
                break
        
        if attr_groups:
            return self._extract_from_attribute_groups(attr_groups, kv)
        
        return 0
    def _extract_from_attribute_groups(self, attr_groups: List[Dict], kv: Dict) -> int:
        """
        Extract specifications directly from ABB's attributeGroups structure.
        
        Also extracts PDF datasheet link from PopularDownloads group.
        
        ABB Structure:
        [
          {
            "code": "Technical",
            "description": "Technische specificaties",
            "visible": true,
            "attributes": {
              "DieTesVol": {
                "attributeName": "Diëlektrische testspanning",
                "values": [{"text": "50 / 60 Hz - 1 min 2 kV"}],
                "isInternal": false
              },
              ...
            }
          }
        ]
        """
        count = 0
        
        for group in attr_groups:
            if not isinstance(group, dict):
                continue
              # Skip invisible groups
            if not group.get("visible", True):
                continue
            
            group_desc = group.get("description", "Specifications")
            attributes = group.get("attributes", {})
            
            if not isinstance(attributes, dict):
                continue
            
            # 🎯 SPECIAL: Check for datasheet in ANY group (DatSheTecInf attribute)
            # It can be in PopularDownloads OR Certificates and Declarations
            datasheet_attr = attributes.get("DatSheTecInf", {})
            if isinstance(datasheet_attr, dict) and "Datasheet PDF" not in kv["Product Info"]:
                values = datasheet_attr.get("values", [])
                if values and isinstance(values, list) and len(values) > 0:
                    # Get first datasheet (some products have multiple)
                    first_value = values[0]
                    if isinstance(first_value, dict):
                        link = first_value.get("link", {})
                        if isinstance(link, dict):
                            doc_id = link.get("documentId")
                            if doc_id:
                                # Generate PDF download URL
                                pdf_url = f"https://search.abb.com/library/Download.aspx?DocumentID={doc_id}&LanguageCode=en&DocumentPartId=&Action=Launch"
                                kv["Product Info"]["Datasheet PDF"] = pdf_url
                                print(f"      📄 Found datasheet: {doc_id} (in {group_desc})")
                                count += 1
            
            print(f"      ├─ {group_desc}: {len(attributes)} attributes")
            
            # Extract each attribute
            for attr_code, attr_data in attributes.items():
                if not isinstance(attr_data, dict):
                    continue
                
                # Skip internal attributes
                if attr_data.get("isInternal") or attr_data.get("internal"):
                    continue
                
                # Get attribute name (in Dutch!)
                attr_name = attr_data.get("attributeName", attr_code)
                
                # Get values array
                values = attr_data.get("values", [])
                if not values:
                    continue
                
                # Extract text from values
                value_texts = []
                for val in values:
                    if isinstance(val, dict):
                        text = val.get("text", "")
                        if text:
                            value_texts.append(str(text))
                    elif isinstance(val, str):
                        value_texts.append(val)
                if value_texts:
                    # If multiple values, join with " / ", otherwise use single value
                    final_value = " / ".join(value_texts) if len(value_texts) > 1 else value_texts[0]
                    kv[group_desc][attr_name] = final_value
                    count += 1
        
        return count
