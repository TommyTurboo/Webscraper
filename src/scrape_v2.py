#!/usr/bin/env python3
"""
Playwright HTML Scraper (Enhanced Anti-Detection Version)
----------------------------------------------------------
Scrapes complete rendered HTML from product pages using Playwright (sync API).
Features:
- Playwright Stealth (anti-bot detection)
- Random delays (human behavior simulation)
- User-Agent rotation
- Cookie banner handling
- Click automation for tabs/buttons
"""

import argparse
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
from fake_useragent import UserAgent


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape rendered HTML from URLs using Playwright (Anti-Bot Enhanced)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single URL in headful mode
  python src/scrape_v2.py --url https://example.com/product --headful

  # Siemens with tab click
  python src/scrape_v2.py --url "https://sieportal.siemens.com/..." --click "Technische gegevens" --headful

  # Batch URLs from file (headless, stealthy)
  python src/scrape_v2.py --urls urls.txt --headless --wait 3000
        """
    )
      # URL input
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument('--url', help='Single URL to scrape')
    url_group.add_argument('--urls', help='Path to text file with URLs (one per line)')
    
    # Output settings
    parser.add_argument('--out', default='output', help='Output folder (default: output)')
    
    # Wait settings
    parser.add_argument('--wait', type=int, default=0, help='Extra wait time in ms after page load (default: 0)')
    parser.add_argument('--selector', help='CSS selector to wait for before scraping')
    parser.add_argument('--click', help='CSS selector or text to click before scraping (e.g., tab button)')
    
    # Browser mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--headful', action='store_true', help='Run in headful mode (visible browser)')
    mode_group.add_argument('--headless', action='store_true', help='Run in headless mode (no UI)')
    
    # Retry settings
    parser.add_argument('--retries', type=int, default=2, help='Number of retries on failure (default: 2)')
    parser.add_argument('--timeout', type=int, default=60000, help='Page load timeout in ms (default: 60000)')
    
    args = parser.parse_args()
    
    # Handle headless/headful logic
    if args.headless and args.headful:
        print("⚠️  WARNING: Both --headless and --headful specified. Using --headless.")
        args.is_headless = True
    elif args.headless:
        args.is_headless = True
    elif args.headful:
        args.is_headless = False
    else:
        # Default: headful for debugging
        args.is_headless = False
    
    return args


def safe_filename_from_url(url: str) -> str:
    """
    Generate a safe filename from a URL.
    Uses domain + path, sanitized for filesystem.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/')
    
    # Combine domain and path
    if path:
        filename = f"{domain}_{path}"
    else:
        filename = domain
    
    # Replace invalid characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length (keep extension space)
    max_len = 200
    if len(filename) > max_len:
        filename = filename[:max_len]
    
    # Remove trailing underscores/dots
    filename = filename.rstrip('_.')
    
    return f"{filename}.html"


def read_urls_from_file(filepath: str) -> List[str]:
    """Read URLs from a text file (one per line), skipping empty lines and comments."""
    urls = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls.append(line)
        return urls
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Failed to read file {filepath}: {e}")
        sys.exit(1)


def ensure_dir(directory: str) -> None:
    """Ensure directory exists, create if necessary."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def random_delay(min_ms: int = 800, max_ms: int = 2300) -> None:
    """
    Sleep for a random duration to simulate human behavior.
    Default range: 0.8 to 2.3 seconds
    """
    delay_sec = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
    time.sleep(delay_sec)


def get_random_user_agent() -> str:
    """
    Generate a random but realistic User-Agent string.
    Falls back to a safe default if generation fails.
    """
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        # Fallback to a realistic default
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def scrape_one_url(
    url: str,
    output_dir: str,
    is_headless: bool,
    wait_ms: int,
    selector: Optional[str],
    click_target: Optional[str],
    retries: int,
    timeout: int
) -> bool:
    """
    Scrape a single URL with retries.
    Returns True on success, False on failure.
    """
    attempt = 0
    last_error = None
    
    while attempt <= retries:
        try:
            if attempt > 0:
                print(f"  🔄 Retry {attempt}/{retries}...")
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=is_headless)
                  # Generate random User-Agent for this session
                user_agent = get_random_user_agent()
                
                # Create context with realistic settings
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1366, 'height': 768},
                    locale='nl-BE',  # Match Belgian locale for Siemens
                    timezone_id='Europe/Brussels'  # Match timezone
                )
                
                page = context.new_page()
                
                # Apply stealth mode to avoid bot detection
                stealth_obj = Stealth()
                stealth_obj.use_sync(page)
                
                try:
                    # Navigate to URL
                    print(f"  📡 Loading: {url}")
                    page.goto(url, wait_until='networkidle', timeout=timeout)
                    
                    # Try to close cookie banner if present
                    try:
                        cookie_selectors = [
                            'button[data-testid="uc-accept-all-button"]',
                            'button:has-text("Accepteren")',
                            'button:has-text("Accept")',
                            '#usercentrics-root button',
                        ]
                        for cookie_sel in cookie_selectors:
                            try:
                                page.click(cookie_sel, timeout=2000)
                                print(f"  🍪 Cookie banner closed")
                                random_delay(400, 800)  # Short random pause
                                break
                            except:
                                continue
                    except:
                        pass
                    
                    # Click element if specified (e.g., to switch tabs)
                    if click_target:
                        print(f"  🖱️  Clicking: {click_target}")
                        try:
                            # Try as CSS selector first
                            if click_target.startswith('.') or click_target.startswith('#') or click_target.startswith('['):
                                page.click(click_target, timeout=10000)
                            else:
                                # Try as text content with force click to bypass overlays
                                page.get_by_text(click_target, exact=False).first.click(timeout=10000, force=True)
                            
                            # Wait for content to load after click with random delay
                            random_delay(800, 1500)
                        except Exception as e:
                            print(f"  ⚠️  Could not click '{click_target}': {e}")
                      # Wait for selector if specified
                    if selector:
                        print(f"  ⏳ Waiting for selector: {selector}")
                        page.wait_for_selector(selector, timeout=30000)
                    
                    # Scroll down to trigger lazy loading
                    print(f"  📜 Scrolling to load lazy content...")
                    page.evaluate("""
                        async () => {
                            await new Promise((resolve) => {
                                let totalHeight = 0;
                                let distance = 100;
                                let scrollDelay = 100;
                                
                                let timer = setInterval(() => {
                                    let scrollHeight = document.body.scrollHeight;
                                    window.scrollBy(0, distance);
                                    totalHeight += distance;
                                    
                                    if(totalHeight >= scrollHeight){
                                        clearInterval(timer);
                                        // Scroll back to top
                                        window.scrollTo(0, 0);
                                        resolve();
                                    }
                                }, scrollDelay);
                            });
                        }
                    """)
                    
                    # Extra wait after scrolling to ensure content is loaded
                    random_delay(1000, 1500)
                      # Extra wait if specified
                    if wait_ms > 0:
                        print(f"  ⏳ Extra wait: {wait_ms}ms")
                        time.sleep(wait_ms / 1000.0)
                      # Get the complete rendered HTML
                    print(f"  📄 Extracting HTML...")
                    html = page.evaluate("() => document.documentElement.outerHTML")
                    
                    # Generate safe filename
                    filename = safe_filename_from_url(url)
                    html_path = os.path.join(output_dir, filename)
                    
                    # Save HTML file
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"  ✅ Saved HTML: {html_path}")
                    
                    return True
                    
                finally:
                    # Cleanup
                    page.close()
                    context.close()
                    browser.close()
        
        except PlaywrightTimeoutError as e:
            last_error = f"Timeout: {e}"
            print(f"  ⚠️  Timeout error: {e}")
            attempt += 1
            
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            print(f"  ⚠️  Error: {e}")
            attempt += 1
    
    # All retries failed
    print(f"  ❌ FAILED after {retries + 1} attempts: {last_error}")
    return False


def main():
    """Main entry point."""
    args = parse_args()
      # Banner
    print("=" * 70)
    print("Playwright HTML Scraper (Anti-Bot Enhanced)")
    print("=" * 70)
      # Show mode
    mode = "HEADLESS" if args.is_headless else "HEADFUL"
    print(f"🔧 Mode: {mode}")
    print(f"📁 Output: {args.out}")
    print(f"🔁 Retries: {args.retries}")
    print(f"⏱️  Timeout: {args.timeout}ms")
    if args.wait > 0:
        print(f"⏳ Extra wait: {args.wait}ms")
    if args.selector:
        print(f"🎯 Selector: {args.selector}")
    if args.click:
        print(f"🖱️  Click target: {args.click}")
    print("✨ Anti-Bot Features: Stealth Mode + Random Delays + UA Rotation")
    print("=" * 70)
    
    # Ensure output directory exists
    ensure_dir(args.out)
    
    # Get list of URLs
    if args.url:
        urls = [args.url]
    else:
        urls = read_urls_from_file(args.urls)
    
    print(f"\n📋 Total URLs to scrape: {len(urls)}\n")
    
    # Scrape each URL
    success_count = 0
    fail_count = 0
    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] Processing: {url}")
        
        success = scrape_one_url(
            url=url,
            output_dir=args.out,
            is_headless=args.is_headless,
            wait_ms=args.wait,
            selector=args.selector,
            click_target=args.click,
            retries=args.retries,
            timeout=args.timeout
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📁 Output folder: {args.out}")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
