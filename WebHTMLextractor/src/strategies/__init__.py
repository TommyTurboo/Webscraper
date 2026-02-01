from urllib.parse import urlparse
from .base import BaseStrategy
from .siemens import SiemensStrategy

def get_strategy_for_url(url: str) -> BaseStrategy:
    domain = urlparse(url).netloc.lower()
    
    if "siemens" in domain:
        return SiemensStrategy()
    
    # Voeg hier later andere if-statements toe
    
    return BaseStrategy()
