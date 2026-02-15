import os
from pathlib import Path

class Config:
    # Paths
    # PyScraper root (assuming config.py is in src/core/)
    BASE_DIR = Path(__file__).parent.parent.parent

    # Browser settings
    VIEWPORT = {'width': 1920, 'height': 1080}
    LOCALE = 'en-BE'
    TIMEZONE = 'Europe/Brussels'
    
    # Timeouts (in ms)
    TIMEOUT_PAGE_LOAD = 60000
    TIMEOUT_SELECTOR = 5000
    
    # Scrape behavior
    RETRIES = 2
    SCROLL_DELAY = 100  # ms
    SCROLL_STEP = 100   # pixels

    # Secrets
    SECRETS_PATH = "c:\\Users\\tomva\\PlatformIO\\my-node-project\\secrets\\credentials.ini"
