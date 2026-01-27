# Scraper Instructies - JSON Output

## Stap 1: Bereid je URLs voor

Maak een `.txt` bestand met de URLs die je wilt scrapen. Bijvoorbeeld `test_urls.txt`:

```txt
https://example.com
https://www.wikipedia.org
https://www.github.com
# Je kunt commentaarlijnen toevoegen met #
https://stackoverflow.com
```

## Stap 2: Run de scraper met JSON output

### Optie A: HTML + JSON genereren
```bash
python src/scrape_v2.py --urls test_urls.txt --json --headless
```

Dit genereert voor elke URL:
- Een `.html` bestand met de volledige pagina
- Een `.json` bestand met metadata en de HTML content

### Optie B: Alleen JSON genereren (geen HTML bestanden)
```bash
python src/scrape_v2.py --urls test_urls.txt --json-only --headless
```

Dit genereert alleen `.json` bestanden (bespaart schijfruimte).

### Optie C: Alleen HTML genereren (standaard gedrag)
```bash
python src/scrape_v2.py --urls test_urls.txt --headless
```

## Stap 3: Bekijk de resultaten

De output wordt standaard opgeslagen in de `output/` folder:

```
output/
├── example.com.html
├── example.com.json
├── www.wikipedia.org.html
├── www.wikipedia.org.json
└── ...
```

## JSON Structuur

Elk JSON bestand bevat:
```json
{
  "url": "https://example.com",
  "scraped_at": "2026-01-27T14:30:00.123456",
  "metadata": {
    "title": "Example Domain",
    "url": "https://example.com",
    "final_url": "https://example.com/",
    "description": "Example Domain description",
    "keywords": null,
    "og_title": null,
    "og_description": null
  },
  "html": "<html>...</html>",
  "html_length": 12345,
  "success": true
}
```

## Extra opties

### Headful modus (zie de browser)
```bash
python src/scrape_v2.py --urls test_urls.txt --json --headful
```

### Met extra wachttijd
```bash
python src/scrape_v2.py --urls test_urls.txt --json --wait 3000 --headless
```

### Met click actie (bijvoorbeeld voor tabs)
```bash
python src/scrape_v2.py --urls test_urls.txt --json --click "Technische gegevens" --headless
```

### Aangepaste output folder
```bash
python src/scrape_v2.py --urls test_urls.txt --json --out mijn_output --headless
```

## Testvoorbeeld

1. Open een terminal in de project folder
2. Run het test commando:
```bash
python src/scrape_v2.py --urls test_urls.txt --json-only --headless --wait 1000
```

3. Bekijk de resultaten in de `output/` folder

## Troubleshooting

Als je errors krijgt over ontbrekende packages:
```bash
pip install -r requirements.txt
```

Als Playwright browsers nog niet geïnstalleerd zijn:
```bash
playwright install chromium
```
