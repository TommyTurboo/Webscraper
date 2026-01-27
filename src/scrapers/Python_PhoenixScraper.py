from bs4 import BeautifulSoup
import json
import os

# 1) HTML inlezen - ABSOLUUT PAD
html_file = r"C:\Users\tomva\PlatformIO\my-node-project\src\scrapers\ElektroBev_Phoenix.txt"

print(f"🔍 Checking file: {html_file}")
print(f"📁 File exists: {os.path.exists(html_file)}")

if not os.path.exists(html_file):
    raise FileNotFoundError(f"❌ HTML bestand niet gevonden: {html_file}")

with open(html_file, "r", encoding="utf-8") as f:
    html = f.read()

print(f"✅ HTML ingelezen van: {html_file}")
print(f"📊 Grootte: {len(html):,} karakters")

# 2) HTML parsen naar DOM-structuur
soup = BeautifulSoup(html, "html.parser")

# 3) Zoek de 'Productdetails' sectie (h2 of h3)
hdr = soup.find(
    lambda t: t.name in ['h2', 'h3'] and
    'productdetails' in t.get_text(strip=True).lower()
)

if not hdr:
    print("⚠️ 'Productdetails' header niet gevonden")
    # DEBUG: Laat zien welke headers er WEL zijn
    all_headers = [f"<{h.name}>{h.get_text(strip=True)[:50]}" for h in soup.find_all(['h2', 'h3', 'h4'])[:10]]
    print(f"❌ Geen productdetails gevonden. Beschikbare headers: {all_headers}")
    raise ValueError("Geen 'Productdetails' sectie gevonden")
else:
    print(f"✅ Gevonden: <{hdr.name}> met tekst '{hdr.get_text(strip=True)}'")

# Neem het bovenliggende element (daar zitten alle tabellen meestal in)
section = hdr.find_parent()

# 4) Helper: dichtstbijzijnde titel boven een tabel vinden
def find_nearest_title(elem):
    """Loop achteruit door HTML en vind eerste heading."""
    for prev in elem.find_all_previous():
        if prev.name in ['h2', 'h3', 'h4', 'button']:
            txt = prev.get_text(strip=True)
            if txt:
                return txt
    return 'Unknown'

# 5) Alle tabellen binnen deze sectie ophalen
tables = section.find_all('table') if section else []
print(f"📊 Gevonden: {len(tables)} tabel(len)")

# 6) We bouwen een dict per sectietitel
result = {}

# 7) Loop door elke tabel
for idx, tbl in enumerate(tables, 1):
    # Zoek bijhorende sectietitel
    title = find_nearest_title(tbl)
    print(f"  Tabel {idx}: '{title}'")
    
    rows = []
    
    # Loop door alle <tr> rijen
    for tr in tbl.find_all('tr'):
        # Verzamel alle cellen (td/th) en strip whitespace
        cells = [c.get_text(strip=True) for c in tr.find_all(['td', 'th'])]
        
        # Bewaar alleen rijen met minstens 1 veld
        if len(cells) >= 1:
            rows.append(cells)
    
    # Voeg toe aan result onder correcte titel
    result.setdefault(title, []).append(rows)

# 8) Output als JSON
print("\n✅ Parsed data:")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 9) Save to file
with open("productdetails.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\n💾 Saved to: productdetails.json")