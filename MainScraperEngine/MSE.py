#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════╗
║  MSE - Main Scraper Engine                                    ║
║  Configuration-Driven HTML Scraper - Refactored v2.0          ║
╚════════════════════════════════════════════════════════════════╝
"""
import os
import sys
import json

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from core.scraper import scrape_file


def main():
    """CLI interface voor de scraper."""
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Configuration-Driven HTML Scraper v2.0                        ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
      # Default test file of CLI argument
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        html_file = r"C:\Users\tomva\PlatformIO\my-node-project\secrets-backup\HTML_SIE_DISCON_MAIN_SERIES.html"
    print(f"📄 Input: {html_file}")
    
    if not os.path.exists(html_file):
        print(f"❌ Bestand niet gevonden: {html_file}")
        sys.exit(1)
    
    print("🔄 Loading HTML...")
    
    # Scrape
    try:
        result = scrape_file(html_file)
    except Exception as e:
        print(f"❌ ERROR during scraping: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Output
    print(f"\n✅ Scraping voltooid!")
    print(f"   - Vendor: {result['vendor']}")
    print(f"   - Secties: {len(result['kv'])}")
    print(f"   - Stats: {result['stats']}")

    # Metadata info
    metadata = result.get("metadata", {})
    if "canonical_url" in metadata:
        print(f"   - URL: {metadata['canonical_url']}")    
        print(f"   - Extractie: {metadata.get('extraction_timestamp', 'Unknown')}")
    
    # Save to JSON in MainScraperEngine directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "config_scraped_output.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Preview
    print("\n📋 Preview (eerste 3 secties):")
    for i, (section, items) in enumerate(result["kv"].items()):
        if i >= 3:
            print("   ...")
            break
        print(f"   📁 {section}: {len(items)} items")
        for j, (key, value) in enumerate(items.items()):
            if j >= 2:
                print(f"      ...")
                break
            val_preview = str(value)[:50] + "..." if len(str(value)) > 50 else value
            print(f"      • {key}: {val_preview}")


if __name__ == "__main__":
    main()
