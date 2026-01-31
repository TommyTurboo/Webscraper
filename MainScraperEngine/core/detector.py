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
    
    Args:
        soup: BeautifulSoup object van de HTML
        configs: Dictionary met alle vendor configuraties
    
    Returns:
        str: Vendor key (bijv. "siemens", "phoenix") of "generic"
    """
    
    for vendor_key, config in configs.items():
        if vendor_key == "generic":
            continue  # Skip generic, is fallback
        
        detect_rules = config.get("detect", [])
        
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
