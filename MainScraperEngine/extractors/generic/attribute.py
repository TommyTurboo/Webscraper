from bs4 import BeautifulSoup
from typing import Dict, Any
from ..base import BaseExtractor

class AttributeExtractor(BaseExtractor):
    """Extract attribute value from an element."""
    
    # Base URL mapping per vendor
    BASE_URLS = {
        'VEGA': 'https://www.vega.com',
        'Siemens': 'https://mall.industry.siemens.com'
    }
    
    @property
    def extractor_type(self) -> str:
        return 'attribute'
    
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """Extract attribute value with optional URL post-processing."""
        selector = spec.get('selector')
        attribute = spec.get('attribute', 'href')
        target_section = spec.get('target_section', 'General')
        target_key = spec.get('target_key', 'Attribute')
        post_process = spec.get('post_process')
        
        element = soup.select_one(selector)
        
        if not element or not element.has_attr(attribute):
            return 0
        
        value = element[attribute]
        
        # Post-processing: prepend base URL
        if post_process == 'prepend_base_url' and value.startswith('/'):
            # Use vendor set by scraper
            base_url = self.BASE_URLS.get(self.vendor, '')
            if base_url:
                value = f'{base_url}{value}'
            else:
                print(f'  ⚠ No base URL found for vendor: {self.vendor}')
        
        if value:
            kv[target_section][target_key] = value
            return 1
        
        return 0
