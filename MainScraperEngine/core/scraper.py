"""
╔════════════════════════════════════════════════════════════════╗
║  Config-Driven Scraper - Main orchestrator class              ║
╚════════════════════════════════════════════════════════════════╝
"""
from bs4 import BeautifulSoup
from collections import defaultdict
from typing import Dict, Any, Optional
from datetime import datetime
import html

from core.config import load_configs
from core.detector import detect_vendor
from extractors import EXTRACTOR_REGISTRY


class ConfigDrivenScraper:
    """
    Configuration-driven HTML scraper.
    
    Gebruik:
        scraper = ConfigDrivenScraper(html)
        result = scraper.scrape()
    """
    
    def __init__(self, html: str):
        # First, try to unescape the HTML if it's escaped
        self.html = self._unescape_if_needed(html)
        self.soup = BeautifulSoup(self.html, "html.parser")
        self.configs = load_configs()
        self.vendor = None
        self.stats = defaultdict(int)
        self.extraction_timestamp = datetime.now()
    
    def _unescape_if_needed(self, html_content: str) -> str:
        """
        Check if HTML is escaped and unescape it if needed.
        ABB HTML files are often saved with hex-encoded characters (\\x3C instead of <).
        """
        # Check for hex-encoded HTML (\\x3C instead of <)
        if '\\x3C' in html_content[:1000] or '\\x3E' in html_content[:1000]:
            print("🔧 Detected hex-encoded HTML - decoding...")
            # Decode hex escapes
            decoded = html_content.encode('utf-8').decode('unicode-escape')
            script_count_before = html_content.count('<script')
            script_count_after = decoded.count('<script')
            print(f"   <script tags: {script_count_before} → {script_count_after}")
            return decoded
        
        # Check if the HTML is escaped by looking for common escaped tags
        elif '&lt;' in html_content[:1000]:
            print("🔧 Detected HTML entity-escaped HTML - unescaping...")
            unescaped = html.unescape(html_content)
            script_count_before = html_content.count('<script')
            script_count_after = unescaped.count('<script')
            print(f"   <script tags: {script_count_before} → {script_count_after}")
            return unescaped
        
        else:
            # Still check for script tags even if not obviously escaped
            script_count = html_content.count('<script')
            print(f"ℹ️  HTML appears unescaped ({script_count} <script tags found)")
            return html_content

    def scrape(self) -> Dict[str, Any]:
        """Main scraping method."""
        
        # 1. Detecteer vendor
        self.vendor = detect_vendor(self.soup, self.configs)
        vendor_config = self.configs.get(self.vendor, self.configs.get("generic", {}))
        
        print(f"🏭 Detected vendor: {vendor_config.get('name', self.vendor)}")
        
        # 2. Initialiseer result
        kv = defaultdict(dict)
          # 3. Run alle spec extractors voor deze vendor
        specs = vendor_config.get("specs", [])
        for spec in specs:
            spec_type = spec.get("type")
            extractor_class = EXTRACTOR_REGISTRY.get(spec_type)
            
            if extractor_class:
                try:
                    extractor = extractor_class()
                    # ✨ Pass vendor name to extractor
                    extractor.vendor = vendor_config.get('name', self.vendor)
                    count = extractor.extract(self.soup, spec, kv)
                    
                    if count > 0:
                        # Update stats met extractor type
                        stat_key = extractor.extractor_type
                        self.stats[stat_key] += count
                        print(f"  ✓ {spec_type}: {count} items")
                    else:
                        print(f"  ○ {spec_type}: 0 items (no match)")
                
                except Exception as e:
                    print(f"  ✗ {spec_type} failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ⚠ Unknown extractor type: {spec_type}")
        
        # 4. Cleanup en flatten
        result = self._cleanup(kv, vendor_config)

        # 5. Voeg metadata toe
        result["metadata"] = self._build_metadata()
        
        return result
    
    def _extract_canonical_url(self) -> Optional[str]:
        """Extract canonical URL uit HTML."""
        link = self.soup.find("link", rel="canonical")
        if link and link.has_attr("href"):
            return link["href"]
        return None

    def _build_metadata(self) -> Dict[str, str]:
        """
        Bouw metadata sectie met alleen:
        - Canonical URL
        - Extraction timestamp (dd/mm/yyyy HH:MM:SS)
        """
        metadata = {}
        
        # 1. Canonical URL
        canonical_url = self._extract_canonical_url()
        if canonical_url:
            metadata["canonical_url"] = canonical_url
        
        # 2. Extraction timestamp (Europees formaat)
        metadata["extraction_timestamp"] = self.extraction_timestamp.strftime("%d/%m/%Y %H:%M:%S")
        
        return metadata
    
    def _cleanup(self, kv: Dict, config: Dict) -> Dict:
        """Post-processing: cleanup en normalize."""
        
        # Convert defaultdict to regular dict
        cleaned_kv = {}
        
        for section, items in kv.items():
            if not items:
                continue
            
            cleaned_kv[section] = {}
            
            for key, value in items.items():
                # Skip lege values
                if value is None or value == "":
                    continue
                
                cleaned_kv[section][key] = value
        
        return {
            "vendor": config.get("name", self.vendor),
            "kv": cleaned_kv,
            "stats": dict(self.stats)
        }


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def scrape_html(html: str) -> Dict[str, Any]:
    """Convenience function om HTML te scrapen."""
    scraper = ConfigDrivenScraper(html)
    return scraper.scrape()


def scrape_file(filepath: str) -> Dict[str, Any]:
    """Convenience function om een HTML bestand te scrapen."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    
    scraper = ConfigDrivenScraper(html)
    return scraper.scrape()
