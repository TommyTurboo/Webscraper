import json
import re

# Read HTML
html = open('C:/Users/tomva/PlatformIO/my-node-project/src/scrapers/HTML_ABB_VMS.txt', 'r', encoding='utf-8').read()
html = html.encode('utf-8').decode('unicode-escape')

# Find var model
m = re.search(r'var\s+model\s*=\s*(\{.+?\});', html, re.DOTALL)
if not m:
    print("No var model found!")
    exit(1)

model = json.loads(m.group(1))
pvm = model.get('ProductViewModel', {})
prod = pvm.get('Product', {})
groups = prod.get('attributeGroups', {}).get('items', [])

print(f"\n🔍 Found {len(groups)} attribute groups:\n")

for i, g in enumerate(groups):
    code = g.get('code', 'N/A')
    desc = g.get('description', 'N/A')
    visible = g.get('visible', False)
    attrs = g.get('attributes', {})
    
    print(f"{i}: {code}")
    print(f"   Description: {desc}")
    print(f"   Visible: {visible}")
    print(f"   Attributes: {len(attrs)}")
    
    # Check for datasheet
    if 'download' in desc.lower() or code == 'PopularDownloads':
        print(f"   ⭐ THIS IS THE DOWNLOADS GROUP!")
        datasheet = attrs.get('DatSheTecInf', {})
        print(f"   DatSheTecInf: {datasheet}")
    print()
