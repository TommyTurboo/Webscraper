#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to find datasheet in HTML_ABB_VMS.txt
"""
import json
import re

# Read the HTML file
html_path = 'C:/Users/tomva/PlatformIO/my-node-project/src/scrapers/HTML_ABB_VMS.txt'
print(f"Reading {html_path}...")

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

print(f"HTML file size: {len(html):,} bytes")

# Decode hex-encoded HTML
html = html.encode('utf-8').decode('unicode-escape')
print(f"Decoded HTML size: {len(html):,} bytes")

# Find var model = {...};
pattern = r'var\s+model\s*=\s*(\{.+?\});'
match = re.search(pattern, html, re.DOTALL)

if match:
    json_str = match.group(1)
    print(f"\n🎯 Found var model JSON!")
    print(f"   Size: {len(json_str):,} characters")
    
    try:
        model_data = json.loads(json_str)
        print(f"   ✅ Valid JSON")
        
        # Navigate to attribute groups
        pvm = model_data.get('ProductViewModel', {})
        product = pvm.get('Product', {})
        attr_groups = product.get('attributeGroups', {}).get('items', [])
        
        print(f"\n📊 Found {len(attr_groups)} attribute groups")
        
        # Look for datasheet-related groups
        print("\n🔍 Searching for datasheet/download groups:")
        for group in attr_groups:
            code = group.get('code', '')
            description = group.get('description', '')
            visible = group.get('visible', False)
            
            # Check if this might contain datasheet
            if any(keyword in code.lower() for keyword in ['download', 'datasheet', 'popular', 'document']):
                print(f"\n   ✅ FOUND: {code} - {description} (visible: {visible})")
                attributes = group.get('attributes', {})
                print(f"      Attributes: {list(attributes.keys())}")
                
                # Check each attribute
                for attr_key, attr_data in attributes.items():
                    attr_name = attr_data.get('attributeName', '')
                    values = attr_data.get('values', [])
                    print(f"\n      Attribute: {attr_key} = {attr_name}")
                    print(f"         Values: {len(values)}")
                    
                    if values:
                        for i, val in enumerate(values):
                            if isinstance(val, dict):
                                text = val.get('text', '')
                                link = val.get('link', {})
                                print(f"         [{i}] text: {text}")
                                if link:
                                    print(f"         [{i}] link: {link}")
            
            elif any(keyword in description.lower() for keyword in ['download', 'datasheet', 'popular', 'document']):
                print(f"\n   ✅ FOUND (description): {code} - {description} (visible: {visible})")
                attributes = group.get('attributes', {})
                print(f"      Attributes: {list(attributes.keys())}")
        
        # Also search in Certificates group
        print("\n\n🔍 Checking 'Certificates and Declarations' group:")
        for group in attr_groups:
            description = group.get('description', '')
            if 'certificate' in description.lower() or 'declaration' in description.lower():
                print(f"\n   Group: {description}")
                attributes = group.get('attributes', {})
                
                # Look for datasheet attribute
                for attr_key, attr_data in attributes.items():
                    attr_name = attr_data.get('attributeName', '')
                    if 'datasheet' in attr_name.lower() or 'data sheet' in attr_name.lower():
                        print(f"      ✅ FOUND DATASHEET ATTRIBUTE: {attr_key} = {attr_name}")
                        values = attr_data.get('values', [])
                        print(f"         Values: {values}")
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parsing failed: {e}")
else:
    print("❌ No var model found!")
