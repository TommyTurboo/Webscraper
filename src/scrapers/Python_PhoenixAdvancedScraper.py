"""
╔════════════════════════════════════════════════════════════════╗
║  Universal Elektro Beveiliging - HTML Scraper (Combined)      ║
║                                                                 ║
║  Twee Modi:                                                     ║
║  1. SIMPLE  → Alleen tabellen uit Productdetails-sectie        ║
║  2. ADVANCED → Alle data (tabellen, DL, text patterns, LI)     ║
║                                                                 ║
║  Ondersteunt: Phoenix, Siemens, en andere HTML structuren      ║
╚════════════════════════════════════════════════════════════════╝
"""

from bs4 import BeautifulSoup, Tag
import json
import os
import re
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# 🎛️ CONFIGURATIE
# ═══════════════════════════════════════════════════════════════

MODE = "ADVANCED"  # Kies: "SIMPLE" of "ADVANCED"

HTML_FILE = r"C:\Users\tomva\PlatformIO\my-node-project\src\scrapers\HTML_Vega.txt"

OUTPUT_FILE_SIMPLE = "productdetails.json"
OUTPUT_FILE_ADVANCED = "phoenix_full_parsed.json"

# ═══════════════════════════════════════════════════════════════
# 📥 STAP 1: HTML INLEZEN
# ═══════════════════════════════════════════════════════════════

print(f"🔍 Checking file: {HTML_FILE}")
print(f"📁 File exists: {os.path.exists(HTML_FILE)}")

if not os.path.exists(HTML_FILE):
    raise FileNotFoundError(f"❌ HTML bestand niet gevonden: {HTML_FILE}")

with open(HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

print(f"✅ HTML ingelezen van: {HTML_FILE}")
print(f"📊 Grootte: {len(html):,} karakters")
print(f"⚙️  Modus: {MODE}\n")

# ═══════════════════════════════════════════════════════════════
# 🔧 STAP 2: HTML PARSEN
# ═══════════════════════════════════════════════════════════════

soup = BeautifulSoup(html, "html.parser")

# ═══════════════════════════════════════════════════════════════
# 🛠️ HELPER FUNCTIES (voor beide modi)
# ═══════════════════════════════════════════════════════════════

def clean_text(x: str) -> str:
    """Verwijder overtollige whitespace en normaliseer tekst."""
    if x is None:
        return ""
    # Siemens-specifieke cleaning
    x = x.replace("\xa0", " ")         # non-breaking spaces
    x = x.replace("\\n", " ")          # literal backslash-n
    x = re.sub(r"\\x3C!---->", " ", x)  # Angular/SSR comment markers
    x = re.sub(r"\\x3C!----&gt;", " ", x)
    return re.sub(r"\s+", " ", x).strip()


def nearest_heading(elem: Tag) -> str:
    """Zoek de meest nabije heading boven dit element (h1-h6)."""
    for prev in elem.find_all_previous():
        if isinstance(prev, Tag) and prev.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            t = clean_text(prev.get_text(" ", strip=True))
            if t:
                return t
    return "Unknown"


def find_nearest_title(elem):
    """
    Loop achteruit door HTML en vind eerste heading of button.
    (Voor SIMPLE modus - compatibel met oude code)
    """
    for prev in elem.find_all_previous():
        if prev.name in ['h2', 'h3', 'h4', 'button']:
            txt = prev.get_text(strip=True)
            if txt:
                return txt
    return 'Unknown'


# ═══════════════════════════════════════════════════════════════
# 🏭 VENDOR DETECTIE
# ═══════════════════════════════════════════════════════════════

def detect_vendor(soup):
    """Detecteer of dit Siemens of Phoenix HTML is."""
    # Siemens markers
    if soup.find("sie-ps-commercial-data") or soup.find(id="specifications"):
        return "SIEMENS"
    # Phoenix markers
    if soup.find(lambda t: t.name in ['h2', 'h3'] and 'productdetails' in t.get_text().lower()):
        return "PHOENIX"
    return "UNKNOWN"

vendor = detect_vendor(soup)
print(f"🏭 Detected vendor: {vendor}\n")


# ═══════════════════════════════════════════════════════════════
# 📊 MODUS 1: SIMPLE - Alleen Productdetails Tabellen
# ═══════════════════════════════════════════════════════════════

if MODE == "SIMPLE":
    print("🔹 Running SIMPLE mode (Productdetails tables only)\n")
    
    # Zoek de 'Productdetails' sectie
    hdr = soup.find(
        lambda t: t.name in ['h2', 'h3'] and
        'productdetails' in t.get_text(strip=True).lower()
    )
    
    if not hdr:
        all_headers = [f"<{h.name}>{h.get_text(strip=True)[:50]}" 
                      for h in soup.find_all(['h2', 'h3', 'h4'])[:10]]
        print(f"❌ Geen productdetails gevonden. Beschikbare headers: {all_headers}")
        raise ValueError("Geen 'Productdetails' sectie gevonden")
    else:
        print(f"✅ Gevonden: <{hdr.name}> met tekst '{hdr.get_text(strip=True)}'")
    
    # Neem het bovenliggende element
    section = hdr.find_parent()
    
    # Alle tabellen binnen deze sectie
    tables = section.find_all('table') if section else []
    print(f"📊 Gevonden: {len(tables)} tabel(len)\n")
    
    # Bouw result dict
    result = {}
    
    for idx, tbl in enumerate(tables, 1):
        title = find_nearest_title(tbl)
        print(f"  Tabel {idx}: '{title}'")
        
        rows = []
        for tr in tbl.find_all('tr'):
            cells = [c.get_text(strip=True) for c in tr.find_all(['td', 'th'])]
            if len(cells) >= 1:
                rows.append(cells)
        
        result.setdefault(title, []).append(rows)
    
    # Output
    print("\n✅ Parsed data:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    with open(OUTPUT_FILE_SIMPLE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved to: {OUTPUT_FILE_SIMPLE}")


# ═══════════════════════════════════════════════════════════════
# 📊 MODUS 2: ADVANCED - Multi-Strategy Scraping
# ═══════════════════════════════════════════════════════════════

elif MODE == "ADVANCED":
    print("🔸 Running ADVANCED mode (multi-strategy extraction)\n")
    
    # --- Helper voor key-value pairs ---
    def add_kv(bucket: dict, section: str, key: str, value: str):
        """Voeg key-value toe aan bucket, behoud duplicates."""
        key = clean_text(key)
        value = clean_text(value)
        if not key or not value:
            return
        bucket[section].setdefault(key, [])
        if value not in bucket[section][key]:
            bucket[section][key].append(value)
    
    # --- STRATEGIE 1: Key-Value uit <dl> tags ---
    print("🔹 Strategie 1: Extracting <dl> definition lists...")
    kv = defaultdict(dict)
    
    for dl in soup.find_all("dl"):
        section = nearest_heading(dl)
        dts = dl.find_all("dt")
        for dt in dts:
            dd = dt.find_next_sibling("dd")
            if dd:
                add_kv(kv, section, dt.get_text(" ", strip=True), dd.get_text(" ", strip=True))
    
    print(f"   ✅ Gevonden: {len(kv)} secties met DL-data")
    
    # --- STRATEGIE 2: Tabellen (full + 2-koloms als KV) ---
    print("🔹 Strategie 2: Extracting tables...")
    tables_data = []
    
    for tbl in soup.find_all("table"):
        section = nearest_heading(tbl)
        rows = []
        for tr in tbl.find_all("tr"):
            cells = [clean_text(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            cells = [c for c in cells if c]  # Verwijder lege cellen
            if not cells:
                continue
            rows.append(cells)
            
            # Heuristiek: 2 cellen = key/value
            if len(cells) == 2:
                add_kv(kv, section, cells[0], cells[1])
        
        if rows:
            tables_data.append({"section": section, "rows": rows})
    
    print(f"   ✅ Gevonden: {len(tables_data)} tabellen")
    
    # --- STRATEGIE 2.5: Div-based "tabellen" (Nexans/VEGA/Phoenix karakteristieken) ---
    print("🔹 Strategie 2.5: Extracting DIV-based characteristic rows...")
    div_table_count = 0
    
    # PATROON 1: Nexans - list-characteristics__row
    nexans_rows = soup.find_all("div", class_=lambda c: c and "list-characteristics__row" in c if c else False)
    
    for row in nexans_rows:
        inner_row = row.find("div", class_="row")
        if not inner_row:
            continue
        
        cells = inner_row.find_all("div", class_=lambda c: c and ("cell-6" in c or "cell-t-6" in c or "cell-m-6" in c) if c else False)
        
        if len(cells) >= 2:
            key_span = cells[0].find("span", class_=lambda c: c and "list-characteristics__title" in c if c else False)
            val_span = cells[1].find("span", class_=lambda c: c and "list-characteristics__desc" in c if c else False)
            
            if key_span and val_span:
                section = nearest_heading(row)
                key = clean_text(key_span.get_text(" ", strip=True))
                value = clean_text(val_span.get_text(" ", strip=True))
                
                if key and value:
                    add_kv(kv, section, key, value)
                    div_table_count += 1
    
    # PATROON 2: VEGA - characteristic + characteristic-title
    vega_chars = soup.find_all("div", class_=lambda c: c and "characteristic" in c and "characteristic-" not in c if c else False)
    
    for char in vega_chars:
        # Zoek de row binnen de characteristic
        inner_row = char.find("div", class_="row")
        if not inner_row:
            continue
        
        # Zoek key (characteristic-title)
        key_div = inner_row.find("div", class_=lambda c: c and "characteristic-title" in c if c else False)
        if not key_div:
            continue
        
        # Zoek value container (de tweede col div)
        value_container = inner_row.find("div", class_=lambda c: c and ("col-xs-12" in c or "col-sm-8" in c) if c else False)
        if not value_container or value_container == key_div:
            # Vind de ANDERE col div (niet de key div)
            all_cols = inner_row.find_all("div", class_=lambda c: c and "col-" in c if c else False)
            value_container = None
            for col in all_cols:
                if col != key_div:
                    value_container = col
                    break
        
        if not value_container:
            continue
        
        # Zoek characteristic-value items (kunnen meerdere zijn!)
        value_items = value_container.find_all("li", class_=lambda c: c and "characteristic-value" in c if c else False)
        
        if value_items:
            section = nearest_heading(char)
            key = clean_text(key_div.get_text(" ", strip=True))
            
            # Als er meerdere values zijn, voeg ze allemaal toe
            for val_li in value_items:
                # Verwijder unit-choices spans (de [Meter - Foot] knoppen)
                for unit_span in val_li.find_all("span", class_=lambda c: c and "unit-choices" in c if c else False):
                    unit_span.decompose()
                
                value = clean_text(val_li.get_text(" ", strip=True))
                
                if key and value:
                    add_kv(kv, section, key, value)
                    div_table_count += 1
    
    print(f"   ✅ Gevonden: {div_table_count} DIV-based karakteristieken")
    
    # --- STRATEGIE 3: "Label: Waarde" patronen ---
    print("🔹 Strategie 3: Extracting 'Label: Value' patterns...")
    label_value_regex = re.compile(r"^([^:]{2,80}):\s*(.{1,200})$")
    
    candidates = soup.find_all(["p", "li", "div", "span"])
    pattern_count = 0
    
    for el in candidates:
        txt = clean_text(el.get_text(" ", strip=True))
        if not txt or len(txt) > 260:
            continue
        m = label_value_regex.match(txt)
        if m:
            section = nearest_heading(el)
            add_kv(kv, section, m.group(1), m.group(2))
            pattern_count += 1
    
    print(f"   ✅ Gevonden: {pattern_count} label:waarde patronen")
    
    # --- STRATEGIE 4: Fallback - Alle tekst per heading ---
    print("🔹 Strategie 4: Collecting fallback text per heading...")
    sections_text = defaultdict(list)
    
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    for h in headings:
        title = clean_text(h.get_text(" ", strip=True))
        if not title:
            continue
        
        texts = []
        for sib in h.next_siblings:
            if isinstance(sib, Tag) and sib.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            if isinstance(sib, Tag):
                if sib.name in ["script", "style", "noscript"]:
                    continue
                t = clean_text(sib.get_text(" ", strip=True))
                if t:
                    texts.append(t)
        
        if texts:
            sections_text[title].append(" ".join(texts))
    
    print(f"   ✅ Verzameld: {len(sections_text)} text secties")
    
    # --- STRATEGIE 5: Siemens <li> patronen ---
    print("🔹 Strategie 5: Extracting Siemens-style <li> elements...")
    
    # Blacklist van teksten die we willen negeren
    SKIP_LI_TEXTS = {
        "commercial data", 
        "technical data", 
        "productdetails",
        "downloads",
        "accessories",
        "related products",
        "support",
        "contact",
        "service"
    }

    # Zoek eerst de specifications container (zoals de Siemens scraper doet)
    spec_container = soup.find(id="specifications")
    if not spec_container:
        spec_container = soup.find("sie-ps-commercial-data")

    if spec_container and vendor == "SIEMENS":
        current_group = None
        li_count = 0
        
        # Gebruik descendants iterator (zoals originele Siemens scraper)
        for el in spec_container.descendants:
            # Detecteer section headings
            if getattr(el, "name", None) in ["h3", "h4"]:
                current_group = clean_text(el.get_text(" ", strip=True))
                continue
            
            # Parse LI elements
            if getattr(el, "name", None) == "li":
                li_text_lower = clean_text(el.get_text(" ", strip=True)).lower()
                if li_text_lower in SKIP_LI_TEXTS:
                    continue
                
                if el.find(['ul', 'ol']):
                    continue
                
                parts = [clean_text(p) for p in el.get_text("\n", strip=True).split("\n")]
                parts = [p for p in parts if p and p.lower() not in SKIP_LI_TEXTS]
                
                if len(parts) >= 2 and current_group:
                    key = parts[0]
                    value = " ".join(parts[1:])
                    
                    if len(key) <= 100:
                        add_kv(kv, current_group, key, value)
                        li_count += 1
        
        print(f"   ✅ Gevonden: {li_count} Siemens LI pairs")
    else:
        # Fallback voor non-Siemens of als container niet gevonden
        li_count = 0
        for li in soup.find_all("li"):
            li_text_lower = clean_text(li.get_text(" ", strip=True)).lower()
            if li_text_lower in SKIP_LI_TEXTS:
                continue
            
            if li.find(['ul', 'ol']):
                continue
            
            parts = [clean_text(p) for p in li.get_text("\n", strip=True).split("\n")]
            parts = [p for p in parts if p and p.lower() not in SKIP_LI_TEXTS]
            
            if len(parts) >= 2:
                section = nearest_heading(li)
                key = parts[0]
                value = " ".join(parts[1:])
                
                if len(key) <= 100:
                    add_kv(kv, section, key, value)
                    li_count += 1
        
        print(f"   ✅ Gevonden: {li_count} fallback LI pairs")
    
    # --- Output samenstellen ---
    result = {
        "vendor": vendor,
        "kv": kv,                    # section -> key -> [values]
        "tables": tables_data,       # Full table data
        "sections_text": sections_text  # Fallback text per heading
    }
    
    # Converteer defaultdict naar normale dict (voor JSON)
    def to_dict(obj):
        if isinstance(obj, defaultdict):
            obj = dict(obj)
        if isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        return obj
    
    result = to_dict(result)
    
    # Output
    print("✅ Parsed data (summary):")
    print(f"   - Vendor: {vendor}")
    print(f"   - KV pairs: {len(result['kv'])} secties")
    print(f"   - Tables: {len(result['tables'])} tabellen")
    print(f"   - Text sections: {len(result['sections_text'])} secties\n")
    
    with open(OUTPUT_FILE_ADVANCED, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to: {OUTPUT_FILE_ADVANCED}")

else:
    raise ValueError(f"❌ Ongeldige MODE: '{MODE}'. Kies 'SIMPLE' of 'ADVANCED'")

print("\n🎉 Scraping voltooid!")