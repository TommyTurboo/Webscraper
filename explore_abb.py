import json
import re

with open('C:/Users/tomva/PlatformIO/my-node-project/src/scrapers/HTML_ABB.txt', 'r', encoding='utf-8') as f:
    html = f.read()

# Decode hex
html = html.encode('utf-8').decode('unicode-escape')

# Find var model
match = re.search(r'var\s+model\s*=\s*(\{.+?\});', html, re.DOTALL)
if match:
    model = json.loads(match.group(1))
    pvm = model.get('ProductViewModel', {})
    product = pvm.get('Product', {})
    
    print('Product keys:')
    for key in product.keys():
        val = product[key]
        if isinstance(val, dict):
            print(f'  {key}: dict with {len(val)} keys')
            if 'items' in val:
                num_items = len(val['items'])
                print(f'    -> has "items": {num_items} items')
                if num_items > 0 and key.lower() == 'attributegroups':
                    print(f'    *** FOUND ATTRIBUTE GROUPS! ***')
                    first_group = val['items'][0]
                    print(f'    First group keys: {list(first_group.keys())}')
                    print(f'    First group description: {first_group.get("description")}')
        elif isinstance(val, list):
            print(f'  {key}: list with {len(val)} items')
        else:
            val_str = str(val)[:80]
            print(f'  {key}: {val_str}')
