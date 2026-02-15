from urllib.parse import urlparse
from .base import BaseStrategy
from .siemens import SiemensStrategy
from .phoenix import PhoenixStrategy
from .schneider import SchneiderStrategy

def get_strategy_for_url(url: str) -> BaseStrategy:
    domain = urlparse(url).netloc.lower()
    
    if "siemens" in domain:
        return SiemensStrategy()
    
    if "phoenixcontact" in domain:
        return PhoenixStrategy()

    if "se.com" in domain or "schneider-electric" in domain:
        return SchneiderStrategy()
    
    # Voeg hier later andere if-statements toe
    
    return BaseStrategy()
