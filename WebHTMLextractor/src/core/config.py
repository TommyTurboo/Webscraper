class Config:
    # Browser settings
    VIEWPORT = {'width': 1920, 'height': 1080}
    LOCALE = 'nl-BE'
    TIMEZONE = 'Europe/Brussels'
    
    # Timeouts (in ms)
    TIMEOUT_PAGE_LOAD = 60000
    TIMEOUT_SELECTOR = 5000
    
    # Scrape behavior
    RETRIES = 2
    SCROLL_DELAY = 100  # ms
    SCROLL_STEP = 100   # pixels
