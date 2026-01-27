import json
from pathlib import Path
import sys
import re

def extract_balanced_json(s, start_pos=0):
    """Zoek en return het eerste volledig gebalanceerde JSON-object (van { ... }) vanaf start_pos.
    Houd rekening met strings en escape-tekens."""
    i = s.find('{', start_pos)
    if i == -1:
        return None, None
    depth = 0
    in_string = False
    prev_escape = False
    for idx in range(i, len(s)):
        ch = s[idx]
        if in_string:
            if prev_escape:
                prev_escape = False
            elif ch == '\\':
                prev_escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return s[i:idx+1], (i, idx+1)
    return None, None

file_path = Path(__file__).with_name('HTML_Schneider_Automaat.txt')

try:
    raw = file_path.read_text(encoding='utf-8')
except Exception as e:
    print('Fout: kan bestand niet lezen:', e)
    sys.exit(1)

key = 'plain-all-data="'
start = raw.find(key)
if start == -1:
    print('plain-all-data attribute niet gevonden in bestand')
    sys.exit(1)
after_start = start + len(key)
end_marker = '" plain-product-id='
end = raw.find(end_marker, after_start)
if end == -1:
    print('eindmarker voor plain-all-data niet gevonden')
    sys.exit(1)

# haal de attribute-string uit raw
attr_blob = raw[after_start:end]

# herstel HTML entities (doe dit vóór extractie omdat entities in quotes kunnen zitten)
attr_blob = (attr_blob
             .replace('&quot;', '"')
             .replace('&amp;', '&')
             .replace('&lt;', '<')
             .replace('&gt;', '>')
             .strip())

print('DEBUG: full attr length =', len(attr_blob))

# probeer het JSON-object netjes te extraheren
obj_text, span = extract_balanced_json(attr_blob)
if not obj_text:
    print('Kon geen gebalanceerd JSON-object vinden in attribute.')
    # toon een korte context om het probleem te onderzoeken
    print('Context (begin):', repr(attr_blob[:1000]))
    sys.exit(1)

print('DEBUG: gevonden JSON-object lengte =', len(obj_text))

# snelle checks: einde, begin en haakjes tellen
print('Startswith {:', obj_text.startswith('{'), 'Endswith }:', obj_text.endswith('}'))
print('Open braces { =', obj_text.count('{'), '  Close braces } =', obj_text.count('}'))
print('Eerste 200 chars:', obj_text[:200])
print('Laatste 300 chars:', obj_text[-300:])

# obj_text is hier gevonden; eerst fix voor backslash + apostrof en daarna stray backslashes
obj_text = re.sub(r"(\\+)'", lambda m: m.group(1) + '\\u0027', obj_text)
obj_text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', obj_text)


# normaliseer runs van backslashes vóór een dubbele quote naar een enkele escaped quote
# (bv. \\\\"  ->  \")
obj_text = re.sub(r'\\+"', r'\\"', obj_text)

# optioneel: schrijf de fixed tekst weg voor inspectie
with open(Path(__file__).with_name('debug_obj_text_fixed.json'), 'w', encoding='utf-8') as f:
    f.write(obj_text)


def try_parse(text):
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, e

data, err = try_parse(obj_text)

# eerste parse poging
def try_parse(text):
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, e

data, err = try_parse(obj_text)
if err:
    print('Eerste parse fout:', err)
    pos = getattr(err, 'pos', None)
    if pos is not None:
        ctx_start = max(0, pos-80)
        ctx_end = pos+80
        print('Context rond fout (pos={}):'.format(pos))
        print(repr(obj_text[ctx_start:ctx_end]))

    # probeer stray backslashes te escapen (laat geldige JSON-escapes ongemoeid)
    fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', obj_text)
    print('Proberen opnieuw met gecorrigeerde backslashes...')
    data, err2 = try_parse(fixed)
    if err2:
        print('Nog steeds parse fout:', err2)
        # toon korte snippet en stop
        print('Snippet (begin 1200 chars):', fixed[:1200])
        sys.exit(1)
    else:
        print('Parse OK na backslash-fix')
        obj_text = fixed

# inspecteer top-level keys en schrijf volledige JSON naar bestand voor navraag
print('TOP LEVEL KEYS:', list(data.keys()))

# sla volledige parsed JSON op zodat je het offline kunt doorzoeken
with open(Path(__file__).with_name('parsed_full.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# zoek recursief naar mogelijke productId/productCR velden
def find_keys(obj, target_keys=('productId','productCR')):
    results = []
    def _walk(o, path=''):
        if isinstance(o, dict):
            for k,v in o.items():
                p = f"{path}/{k}"
                if k in target_keys:
                    results.append((p, v))
                _walk(v, p)
        elif isinstance(o, list):
            for i,el in enumerate(o):
                _walk(el, f"{path}[{i}]")
    _walk(obj, '')
    return results

found = find_keys(data)
print('Found productId/productCR candidates:', len(found), 'matches')

# Extract productId van het hoofd product
product_id = data.get('base', {}).get('productId') or data.get('base', {}).get('productCR') or 'onbekend'
print(f'\n✅ Hoofd ProductId: {product_id}')

# Extract variants
variants = []
base_variants = data.get('base', {}).get('variants', {}).get('chars', [])
for char_group in base_variants:
    for variant in char_group.get('variants', []):
        variant_id = variant.get('productId')
        if variant_id:
            variants.append(variant_id)

print(f'✅ Aantal variants gevonden: {len(variants)}')

# Clean up specifications - verwijder HTML tags en maak platte structuur
def clean_html(text):
    """Verwijder HTML tags uit tekst."""
    if not text:
        return text
    # Vervang <br /> door newline
    text = text.replace('<br />', '\n').replace('<br>', '\n')
    # Verwijder overige HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def flatten_specifications(specs):
    """Maak een platte dictionary van specifications."""
    result = {}
    
    for table in specs.get('characteristicTables', []):
        table_name = table.get('tableName', 'Unknown')
        table_data = {}
        
        for row in table.get('rows', []):
            char_name = row.get('characteristicName', '')
            char_values = row.get('characteristicValues', [])
            
            # Combineer alle waarden
            values = []
            for val in char_values:
                label = val.get('labelText', '')
                if label:
                    label = clean_html(label)
                    values.append(label)
            
            if values:
                # Als er maar 1 waarde is, gebruik die direct
                table_data[char_name] = values[0] if len(values) == 1 else values
        
        if table_data:
            result[table_name] = table_data
    
    return result

specs = data.get('specifications', {})
cleaned_specs = flatten_specifications(specs)

# Extract beschrijving
description = specs.get('longDescSentences', [])

# Bouw finale output
output = {
    "vendor": "Schneider Electric",
    "productId": product_id,
    "variants": variants,
    "description": description,
    "specifications": cleaned_specs,
    "metadata": {
        "dataSheetTitle": data.get('dataSheetTitle'),
        "productName": cleaned_specs.get('Hoofdkenmerken', {}).get('productnaam'),
        "gamma": cleaned_specs.get('Hoofdkenmerken', {}).get('gamma'),
    }
}

# Schrijf naar file
output_file = Path(__file__).with_name('schneider_cleaned_output.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n💾 Cleaned output saved to: {output_file}')
print(f'\n📊 Summary:')
print(f'   - Product: {output["metadata"]["productName"]}')
print(f'   - ProductId: {product_id}')
print(f'   - Variants: {len(variants)}')
print(f'   - Specification tables: {len(cleaned_specs)}')

# Toon preview van eerste tabel
if cleaned_specs:
    first_table = list(cleaned_specs.keys())[0]
    print(f'\n📋 Preview - {first_table}:')
    for key, value in list(cleaned_specs[first_table].items())[:3]:
        print(f'   • {key}: {value}')
    print('   ...')