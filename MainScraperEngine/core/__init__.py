"""Core scraper functionality."""

# Lege __init__ om circular imports te vermijden
# Import direct vanuit submodules:
#   from core.utils import clean_text
#   from core.scraper import ConfigDrivenScraper
#   etc.

__all__ = [
    "clean_text",
    "nearest_heading",
    "detect_vendor",
    "load_configs",
    "ConfigDrivenScraper",
    "scrape_html",
    "scrape_file",
]
