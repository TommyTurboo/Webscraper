#!/usr/bin/env python3
"""
Quick test script to verify refactored MSE works.
Tests all critical imports and basic functionality.
"""

print("=" * 60)
print("  MSE v2.0 - Refactor Verification Test")
print("=" * 60)
print()

# Test 1: Core imports
print("✓ Test 1: Core imports...")
try:
    from core.utils import clean_text, nearest_heading
    from core.detector import detect_vendor
    from core.config import load_configs
    from core.scraper import ConfigDrivenScraper, scrape_html, scrape_file
    print("  ✅ All core imports successful")
except ImportError as e:
    print(f"  ❌ FAILED: {e}")
    exit(1)

# Test 2: Extractor imports
print("\n✓ Test 2: Extractor imports...")
try:
    from extractors import EXTRACTOR_REGISTRY
    print(f"  ✅ Registry loaded with {len(EXTRACTOR_REGISTRY)} extractors")
    print(f"     Types: {', '.join(list(EXTRACTOR_REGISTRY.keys())[:5])}...")
except ImportError as e:
    print(f"  ❌ FAILED: {e}")
    exit(1)

# Test 3: Config loading
print("\n✓ Test 3: Config loading...")
try:
    configs = load_configs()
    vendors = list(configs.keys())
    print(f"  ✅ Loaded {len(vendors)} vendors: {', '.join(vendors)}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    exit(1)

# Test 4: Vendor detection
print("\n✓ Test 4: Vendor detection...")
try:
    from bs4 import BeautifulSoup
    
    # Test Siemens detection
    html_siemens = '<html><body><sie-ps-technical-data></sie-ps-technical-data></body></html>'
    soup = BeautifulSoup(html_siemens, 'html.parser')
    vendor = detect_vendor(soup, configs)
    print(f"  ✅ Siemens HTML detected as: {vendor}")
    
    # Test generic fallback
    html_generic = '<html><body><table><tr><td>Test</td></tr></table></body></html>'
    soup_generic = BeautifulSoup(html_generic, 'html.parser')
    vendor_generic = detect_vendor(soup_generic, configs)
    print(f"  ✅ Generic HTML detected as: {vendor_generic}")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    exit(1)

# Test 5: Basic scrape
print("\n✓ Test 5: Basic scrape test...")
try:
    test_html = '''
    <html>
        <head>
            <meta name="description" content="Test product description">
            <link rel="canonical" href="https://example.com/product/123">
        </head>
        <body>
            <table>
                <tr><td>Voltage</td><td>230V</td></tr>
                <tr><td>Current</td><td>16A</td></tr>
            </table>
        </body>
    </html>
    '''
    
    result = scrape_html(test_html)
    
    assert result['vendor'] == 'Generic', "Should detect as Generic"
    assert 'kv' in result, "Should have kv section"
    assert 'stats' in result, "Should have stats"
    assert 'metadata' in result, "Should have metadata"
    assert 'canonical_url' in result['metadata'], "Should have canonical URL"
    assert result['metadata']['canonical_url'] == 'https://example.com/product/123'
    assert 'extraction_timestamp' in result['metadata'], "Should have timestamp"
    
    print(f"  ✅ Basic scrape successful!")
    print(f"     - Vendor: {result['vendor']}")
    print(f"     - Sections: {len(result['kv'])}")
    print(f"     - Stats: {result['stats']}")
    print(f"     - URL: {result['metadata']['canonical_url']}")
    
except AssertionError as e:
    print(f"  ❌ ASSERTION FAILED: {e}")
    exit(1)
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: Extractor instantiation
print("\n✓ Test 6: Extractor instantiation...")
try:
    from extractors.generic.table import TableExtractor
    from extractors.generic.datasheet import DatasheetLinkExtractor
    from extractors.vendors.schneider import SchneiderJSONExtractor
    
    table_ext = TableExtractor()
    datasheet_ext = DatasheetLinkExtractor()
    schneider_ext = SchneiderJSONExtractor()
    
    print(f"  ✅ Extractors instantiated:")
    print(f"     - TableExtractor: {table_ext.extractor_type}")
    print(f"     - DatasheetLinkExtractor: {datasheet_ext.extractor_type}")
    print(f"     - SchneiderJSONExtractor: {schneider_ext.extractor_type}")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    exit(1)

# All tests passed!
print("\n" + "=" * 60)
print("  🎉 ALL TESTS PASSED! Refactor verification successful! 🎉")
print("=" * 60)
print()
print("Next steps:")
print("  1. Run: python MSE.py")
print("  2. Test with real vendor HTML files")
print("  3. Verify all 5 vendors work correctly")
print()
