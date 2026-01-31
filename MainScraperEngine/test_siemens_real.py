#!/usr/bin/env python3
"""Quick test met echt Siemens bestand."""

import sys
from core.scraper import scrape_file

# Test met ECHT Siemens bestand (heeft sie-ps-technical-data elements)
html_file = r"c:\Users\tomva\PlatformIO\my-node-project\output\sieportal.siemens.com_nl-be_products-services_detail_3RA2908-1A.html"

print(f"Testing: {html_file}\n")

result = scrape_file(html_file)

print(f"\n=== RESULT ===")
print(f"Vendor: {result['vendor']}")
print(f"Stats: {result['stats']}")
print(f"Sections: {list(result['kv'].keys())}")

# Show first section
if result['kv']:
    first_section = list(result['kv'].keys())[0]
    items = result['kv'][first_section]
    print(f"\nFirst section '{first_section}' has {len(items)} items:")
    for i, (k, v) in enumerate(items.items()):
        if i >= 5:
            print("  ...")
            break
        print(f"  - {k}: {v[:50]}...")
