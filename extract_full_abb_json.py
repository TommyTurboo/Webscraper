#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract the full 1.6 MB JSON from ABB HTML file
"""
import json
import re
import sys

print("Starting extraction...", file=sys.stderr)

# Read the HTML file
html_path = 'C:/Users/tomva/PlatformIO/my-node-project/src/scrapers/HTML_ABB.txt'
print(f"Reading {html_path}...", file=sys.stderr)

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

print(f"📄 HTML file size: {len(html):,} bytes", file=sys.stderr)

# Decode hex-encoded HTML
html = html.encode('utf-8').decode('unicode-escape')
print(f"✅ Decoded HTML size: {len(html):,} bytes", file=sys.stderr)

# Find var model = {...};
pattern = r'var\s+model\s*=\s*(\{.+?\});'
print("Searching for var model...", file=sys.stderr)
match = re.search(pattern, html, re.DOTALL)

if match:
    json_str = match.group(1)
    print(f"\n🎯 Found var model JSON!", file=sys.stderr)
    print(f"   Size: {len(json_str):,} characters", file=sys.stderr)
    
    # Parse JSON to validate
    try:
        model_data = json.loads(json_str)
        print(f"   ✅ Valid JSON", file=sys.stderr)
        print(f"   Top-level keys: {list(model_data.keys())}", file=sys.stderr)
        
        # Save the FULL JSON (pretty-printed)
        output_file = 'C:/Users/tomva/PlatformIO/my-node-project/MainScraperEngine/ABB_FULL_MODEL_1.6MB.json'
        print(f"Writing to {output_file}...", file=sys.stderr)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved full 1.6 MB JSON to:", file=sys.stderr)
        print(f"   {output_file}", file=sys.stderr)
        print(f"\n📊 Statistics:", file=sys.stderr)
        print(f"   - ProductViewModel keys: {len(model_data.get('ProductViewModel', {}))}", file=sys.stderr)
        
        pvm = model_data.get('ProductViewModel', {})
        product = pvm.get('Product', {})
        attr_groups = product.get('attributeGroups', {}).get('items', [])
        print(f"   - Attribute groups: {len(attr_groups)}", file=sys.stderr)
        
        total_attrs = sum(len(g.get('attributes', {})) for g in attr_groups)
        print(f"   - Total attributes: {total_attrs}", file=sys.stderr)
        
        print("\n✅ DONE!", file=sys.stderr)
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parsing failed: {e}", file=sys.stderr)
        sys.exit(1)
else:
    print("❌ No var model found!", file=sys.stderr)
    sys.exit(1)
