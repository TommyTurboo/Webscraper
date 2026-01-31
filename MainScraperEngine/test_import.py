#!/usr/bin/env python3
import sys
sys.path.insert(0, '..')

try:
    from MainScraperEngine.extractors.generic.table import TableExtractor
    print("✅ TableExtractor imported successfully")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
