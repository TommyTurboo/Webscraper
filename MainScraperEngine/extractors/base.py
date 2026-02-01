"""
╔════════════════════════════════════════════════════════════════╗
║  Base Extractor - Abstract Base Class                         ║
║  Alle extractors erven van deze class                         ║
╚════════════════════════════════════════════════════════════════╝
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from bs4 import BeautifulSoup


class BaseExtractor(ABC):
    """Abstract base class voor alle extractors."""
    
    def __init__(self):
        self.vendor = None  # Will be set by scraper
    
    @abstractmethod
    def extract(self, soup: BeautifulSoup, spec: Dict[str, Any], kv: Dict) -> int:
        """
        Extract data uit HTML en voeg toe aan kv dict.
        
        Args:
            soup: BeautifulSoup object van de HTML
            spec: YAML configuratie voor deze extractor
            kv: Key-value dictionary om resultaten in op te slaan
        
        Returns:
            int: Aantal geëxtraheerde items
        """
        pass
    
    @property
    @abstractmethod
    def extractor_type(self) -> str:
        """Return de type naam van deze extractor (voor stats)."""
        pass
