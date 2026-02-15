"""
╔════════════════════════════════════════════════════════════════╗
║  Vendor Detection - Detecteert welke vendor de HTML is        ║
╚════════════════════════════════════════════════════════════════╝
"""
from typing import Dict, Optional
from bs4 import BeautifulSoup


def detect_vendor(soup: BeautifulSoup, configs: Dict) -> Optional[str]:
    """
    Detecteer welke vendor bij deze HTML hoort.
    
    Detection priority:
    1. Canonical URL (most reliable!)
    2. Configured detection rules
    3. Generic fallback
    
    Args:
        soup: BeautifulSoup object van de HTML
        configs: Dictionary met alle vendor configuraties
    
    Returns:
        str: Vendor key (bijv. "siemens", "phoenix") of "generic"
    """
    
    # 🎯 PRIORITY 1: Check canonical URL first (most reliable!)
    canonical_link = soup.find("link", rel="canonical")
    if canonical_link and canonical_link.has_attr("href"):
        canonical_url = canonical_link["href"].lower()
        
        # Domain mapping voor vendors
        url_vendor_map = {
            "new.abb.com": "abb",
            "abb.com": "abb",
            "phoenixcontact.com": "phoenix",
            "new.schneider-electric.com": "schneider",
            "se.com": "schneider",
            "siemens.com": "siemens",
            "mall.industry.siemens.com": "siemens",
            "sieportal.siemens.com": "siemens",
            "vega.com": "vega",
            "nexans.": "nexans",  # nexans.nl, nexans.com, etc.
        }
        
        for domain, vendor in url_vendor_map.items():
            if domain in canonical_url:
                return vendor
    
    # PRIORITY 2: Fallback to configured detection rules
    # Sort by priority (lower number = higher priority)
    sorted_vendors = sorted(
        [(k, v) for k, v in configs.items() if k != "generic"],
        key=lambda x: x[1].get("priority", 999)
    )
    
    for vendor_key, config in sorted_vendors:
        detect_rules = config.get("detect") or []
        
        for rule in detect_rules:
            matched = False
            
            # Type 1: ID selector
            if "id" in rule:
                matched = soup.find(id=rule["id"]) is not None
            
            # Type 2: CSS selector
            elif "selector" in rule:
                matched = len(soup.select(rule["selector"])) > 0
            
            # Type 3: Class contains
            elif "class_contains" in rule:
                search_class = rule["class_contains"]
                matched = soup.find(
                    class_=lambda c: c and search_class in c if c else False
                ) is not None
            
            # Type 4: Text contains
            elif "text_contains" in rule:
                page_text = soup.get_text().lower()
                matched = rule["text_contains"].lower() in page_text
            
            if matched:
                return vendor_key
    
    return "generic"  # Fallback
