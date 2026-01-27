from bs4 import BeautifulSoup
import re
import json
import os

# 1) HTML inlezen - ABSOLUUT PAD
html_file = r"C:\Users\tomva\PlatformIO\my-node-project\src\scrapers\HTML_Siemens_Paaltje.txt"

print(f"🔍 Checking file: {html_file}")
print(f"📁 File exists: {os.path.exists(html_file)}")

if not os.path.exists(html_file):
    raise FileNotFoundError(f"❌ HTML bestand niet gevonden: {html_file}")

with open(html_file, "r", encoding="utf-8") as f:
    html = f.read()

print(f"✅ HTML ingelezen van: {html_file}")
print(f"📊 Grootte: {len(html):,} karakters")

# DEBUG: Zoek naar "5SY6" in de HTML om te bevestigen dat we de juiste file hebben
if "5SY6" in html:
    print("✅ '5SY6' gevonden in HTML - dit is de juiste file!")
else:
    print("⚠️ '5SY6' NIET gevonden in HTML - verkeerde file?")

# Zoek ook naar het andere artikel nummer
if "3RT2017-1HA41" in html:
    print("⚠️ '3RT2017-1HA41' gevonden - dit is NIET de 5SY6 automaat!")
else:
    print("✅ '3RT2017-1HA41' NIET gevonden - correct!")

# 2) HTML parsen naar DOM-structuur
soup = BeautifulSoup(html, "html.parser")

# 3) Alleen de relevante div selecteren
spec = soup.find(id="specifications")
if not spec:
    print("⚠️ div#specifications niet gevonden, probeer andere selector...")
    # Alternatief: zoek naar sie-ps-commercial-data component
    spec = soup.find("sie-ps-commercial-data")
    if not spec:
        # DEBUG: Laat zien welke IDs er WEL zijn
        all_ids = [tag.get('id') for tag in soup.find_all(id=True)]
        print(f"❌ Geen specifications div gevonden. Beschikbare IDs: {all_ids[:10]}")
        raise ValueError("Geen specifications div of sie-ps-commercial-data gevonden")
    else:
        print(f"✅ Gevonden: <sie-ps-commercial-data>")
else:
    print(f"✅ Gevonden: <div id='specifications'>")

# 4) Helper: rommel/artefacts wegpoetsen
def clean_text(t: str) -> str:
    if t is None:
        return ""
    t = t.replace("\xa0", " ")         # non-breaking spaces
    t = t.replace("\\n", " ")          # literal backslash-n
    # Siemens dump bevat placeholders zoals \x3C!----> (Angular/SSR comment markers)
    t = re.sub(r"\\x3C!---->", " ", t)
    t = re.sub(r"\\x3C!----&gt;", " ", t)
    t = re.sub(r"\s+", " ", t).strip()  # whitespace normaliseren
    return t

# 5) We bouwen een dict per sectie (h3 koppen)
result = {}
current_group = None

# 6) Doorloop alle elementen in document-volgorde
for el in spec.descendants:
    # 6a) Sectiekoppen detecteren (h3)
    if getattr(el, "name", None) == "h3":
        current_group = clean_text(el.get_text(" ", strip=True))
        if current_group:
            result.setdefault(current_group, {})

    # 6b) Key/value items zitten bij Siemens in <li> elementen
    if getattr(el, "name", None) == "li":
        # Skip tab-knoppen (Commercial data / Technical data)
        tab_txt = clean_text(el.get_text(" ", strip=True)).lower()
        if tab_txt in ["commercial data", "technical data"]:
            continue

        # Probeer key/value te maken door op nieuwe regels te splitsen
        parts = [clean_text(p) for p in el.get_text("\n", strip=True).split("\n")]
        parts = [p for p in parts if p and p.lower() not in ["commercial data", "technical data"]]

        # Verwacht patroon: parts[0] = key, rest = value
        if len(parts) < 2:
            continue

        key = parts[0]
        value = " ".join(parts[1:]).strip() or None

        if current_group is None:
            current_group = "(ungrouped)"
            result.setdefault(current_group, {})

        # Als dezelfde key meermaals voorkomt: maak er een lijst van
        if key in result[current_group]:
            existing = result[current_group][key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[current_group][key] = [existing, value]
        else:
            result[current_group][key] = value

# 7) Lege groepen weggooien
result = {g: kv for g, kv in result.items() if kv}

# 8) Output als JSON
print("\n✅ Parsed data:")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 9) Save to file
with open("parsed_siemens_data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\n💾 Saved to: parsed_siemens_data.json")