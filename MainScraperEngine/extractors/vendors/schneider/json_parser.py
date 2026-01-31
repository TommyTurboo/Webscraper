"""
╔════════════════════════════════════════════════════════════════╗
║  Schneider JSON Extractor - Complex JSON-in-HTML extraction   ║
╚════════════════════════════════════════════════════════════════╝
"""
import json
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor


class SchneiderJSONExtractor(BaseExtractor):
    """
    Extract data uit Schneider Electric's JSON-in-HTML-attribute structuur.
    
    Schneider slaat alle data op in een `plain-all-data` attribuut als JSON string.
    Dit is te complex voor generic extractors.
    """
    
    @property
    def extractor_type(self) -> str:
        return "schneider_json"
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract data uit Schneider's JSON structure."""
        count = 0
        
        # 1. Vind het element met de JSON data
        json_selector = spec.get("json_selector", "[plain-all-data]")
        json_attr = spec.get("json_attribute", "plain-all-data")
        
        elem = soup.select_one(json_selector)
        if not elem or not elem.has_attr(json_attr):
            return 0
        
        # 2. Extract en parse JSON
        raw_json = elem[json_attr]
        data = self._parse_schneider_json(raw_json)
        
        if not data:
            return 0
        
        # 3. Extract configuratie
        extract_config = spec.get("extract", {})
        
        # 3a. Extract Product ID
        if "product_id" in extract_config:
            count += self._extract_product_id(data, extract_config["product_id"], kv)
        
        # 3b. Extract Variants
        if "variants" in extract_config:
            count += self._extract_variants(data, extract_config["variants"], kv)
        
        # 3c. Extract Specifications
        if "specifications" in extract_config:
            count += self._extract_specifications(data, extract_config["specifications"], kv)
        
        # 3d. Extract Description
        if "description" in extract_config:
            count += self._extract_description(data, extract_config["description"], kv)
        
        # 3e. Extract Metadata
        if "metadata" in extract_config:
            count += self._extract_metadata(data, extract_config["metadata"], kv)
        
        return count
    
    def _parse_schneider_json(self, raw_json: str) -> Dict:
        """Parse Schneider's messy JSON with HTML entities."""
        # Fix HTML entities
        raw_json = (raw_json
                   .replace('&quot;', '"')
                   .replace('&amp;', '&')
                   .replace('&lt;', '<')
                   .replace('&gt;', '>'))
        
        # Fix stray backslashes
        raw_json = re.sub(r"(\\+)'", lambda m: m.group(1) + '\\u0027', raw_json)
        raw_json = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw_json)
        raw_json = re.sub(r'\\+"', r'\\"', raw_json)
        
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {}
    
    def _get_by_path(self, data: Any, path: str) -> Any:
        """Navigate door nested dict/list met dotted path."""
        if not path:
            return None
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _extract_product_id(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract product ID met fallback."""
        primary = self._get_by_path(data, config.get("path", ""))
        fallback = self._get_by_path(data, config.get("fallback_path", ""))
        
        product_id = primary or fallback
        if product_id:
            kv["Product Info"]["Product ID"] = product_id
            return 1
        return 0
    
    def _extract_variants(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract product variants."""
        variants_data = self._get_by_path(data, config.get("path", ""))
        if not isinstance(variants_data, list):
            return 0
        
        count = 0
        variant_list = []
        fields = config.get("extract_fields", [])
        
        for variant in variants_data:
            variant_info = {}
            for field in fields:
                if field in variant:
                    variant_info[field] = variant[field]
            
            if variant_info:
                variant_list.append(variant_info)
                count += 1
        
        if variant_list:
            kv["Variants"]["Available"] = variant_list
        
        return count
    
    def _extract_specifications(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract specification tables."""
        tables = self._get_by_path(data, config.get("path", ""))
        if not isinstance(tables, list):
            return 0
        
        count = 0
        table_name_key = config.get("table_name_key", "tableName")
        rows_key = config.get("rows_key", "rows")
        char_name_key = config.get("char_name_key", "characteristicName")
        char_values_key = config.get("char_values_key", "characteristicValues")
        label_key = config.get("label_key", "labelText")
        
        for table in tables:
            section = table.get(table_name_key, "Specifications")
            rows = table.get(rows_key, [])
            
            for row in rows:
                key = row.get(char_name_key, "")
                values = row.get(char_values_key, [])
                
                if values and isinstance(values, list):
                    value = values[0].get(label_key, "") if values else ""
                    
                    if key and value:
                        kv[section][key] = self._clean_html(value)
                        count += 1
        
        return count
    
    def _extract_description(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract long description."""
        desc_data = self._get_by_path(data, config.get("path", ""))
        
        if isinstance(desc_data, list):
            description = " ".join(str(s) for s in desc_data if s)
        elif isinstance(desc_data, str):
            description = desc_data
        else:
            return 0
        
        if description:
            kv["Product Info"]["Description"] = self._clean_html(description)
            return 1
        return 0
    
    def _extract_metadata(self, data: Dict, config: Dict, kv: Dict) -> int:
        """Extract metadata fields."""
        count = 0
        
        for key, path in config.items():
            value = self._get_by_path(data, path) if isinstance(path, str) else None
            
            if value:
                kv["Metadata"][key] = value
                count += 1
        
        return count
    
    def _clean_html(self, text: str) -> str:
        """Verwijder HTML tags uit tekst."""
        if not text:
            return ""
        
        # Vervang <br /> door newline
        text = text.replace('<br />', '\n').replace('<br>', '\n')
        # Verwijder overige HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
