# Playwright HTML Scraper

Een productieklare Python tool voor het scrapen van volledig gerenderde HTML van webpagina's met Playwright.

## 🎯 Wat doet deze tool?

- **Opent productpagina's** via Chromium (headful of headless)
- **Wacht tot de pagina volledig geladen is** (networkidle)
- **Haalt exacte HTML op** zoals in DevTools: `document.documentElement.outerHTML`
- **Schrijft per URL een eigen HTML-bestand** weg
- **Ondersteunt retries** bij timeouts of fouten
- **Flexibele CLI** met vele opties voor debug en productie

## 📋 Belangrijke opmerking

Deze tool gebruikt `document.documentElement.outerHTML`, wat de **DOM na JavaScript-rendering** oplevert. Dit kan verschillen van "View Page Source" in je browser (die de rauwe HTML toont).

## 🚀 Installatie

### 1. Maak een virtual environment (optioneel maar aanbevolen)

```bash
python -m venv .venv
```

**Activeer het:**
- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Windows (CMD): `.venv\Scripts\activate.bat`
- Linux/Mac: `source .venv/bin/activate`

### 2. Installeer dependencies

```bash
pip install -r requirements.txt
```

### 3. Installeer Playwright browsers

**Belangrijk!** Dit download de browser binaries (Chromium, etc.):

```bash
playwright install
```

Of alleen Chromium (sneller):

```bash
playwright install chromium
```

## 🎮 Gebruik

### Basis: Single URL (headful - default)

Standaard draait de scraper in **headful mode** zodat je kunt zien wat er gebeurt (handig voor debugging):

```bash
python src/scrape.py --url https://example.com/product
```

### Headless mode (voor productie/batch)

```bash
python src/scrape.py --url https://example.com/product --headless
```

### Batch scraping (meerdere URLs uit bestand)

Maak een bestand `urls.txt`:
```
https://example.com/product1
https://example.com/product2
https://example.com/product3
# Comments worden genegeerd
```

Run:
```bash
python src/scrape.py --urls urls.txt --headless
```

### Wachten op een specifieke selector

Als content dynamisch laadt, wacht dan tot een CSS selector verschijnt:

```bash
python src/scrape.py --url https://example.com --selector "#product-details"
```

### Extra wachttijd na page load

Soms heeft JavaScript extra tijd nodig:

```bash
python src/scrape.py --url https://example.com --wait 2000
```
*(wacht 2000ms = 2 seconden extra)*

### Custom output folder

```bash
python src/scrape.py --url https://example.com --out mijn_output
```

### Meer retries en langere timeout

```bash
python src/scrape.py --url https://example.com --retries 5 --timeout 120000
```

### Combinatie voorbeeld

```bash
python src/scrape.py \
  --urls producten.txt \
  --out scraped_data \
  --selector ".price-container" \
  --wait 1500 \
  --retries 3 \
  --timeout 90000 \
  --headless
```

## 🔧 CLI Opties

| Optie | Beschrijving | Default |
|-------|-------------|---------|
| `--url <url>` | Enkele URL om te scrapen | - |
| `--urls <file>` | Pad naar tekstbestand met URLs (1 per regel) | - |
| `--out <folder>` | Output map voor HTML bestanden | `output` |
| `--wait <ms>` | Extra wachttijd in milliseconden na page load | `0` |
| `--selector <css>` | CSS selector om op te wachten voor scraping | - |
| `--headful` | Draai met zichtbare browser (debug) | - |
| `--headless` | Draai zonder UI (productie/batch) | - |
| `--retries <n>` | Aantal retries bij fouten | `2` |
| `--timeout <ms>` | Page load timeout in milliseconden | `60000` |
| `--help` | Toon help met voorbeelden | - |

**Let op:** Default gedrag (zonder `--headful` of `--headless`) is **headful** voor debugging.

## 💡 Tips & Troubleshooting

### Wanneer headful vs headless?

- **Headful** (default): Gebruik tijdens ontwikkeling/debugging. Je ziet de browser en kunt problemen spotten.
- **Headless**: Gebruik voor productie/batch scraping. Sneller en gebruikt minder resources.

### Content verschijnt niet?

1. **Gebruik `--selector`** om te wachten tot een specifiek element geladen is:
   ```bash
   python src/scrape.py --url https://example.com --selector ".product-title"
   ```

2. **Verhoog `--wait`** als content traag laadt:
   ```bash
   python src/scrape.py --url https://example.com --wait 3000
   ```

3. **Verhoog `--timeout`** als de pagina traag is:
   ```bash
   python src/scrape.py --url https://example.com --timeout 120000
   ```

### Retries

Bij tijdelijke netwerkfouten probeert de tool automatisch opnieuw (default 2 retries). Verhoog dit met `--retries`:

```bash
python src/scrape.py --url https://example.com --retries 5
```

### Output bestanden

Bestanden krijgen een veilige naam gebaseerd op de URL:
- `example.com_product_123.html`
- `shop.example.com_categories_electronics.html`

### Debug mode vs Productie

**Debug:**
```bash
python src/scrape.py --url https://example.com
# Of expliciet:
python src/scrape.py --url https://example.com --headful
```

**Productie/Batch:**
```bash
python src/scrape.py --urls alle_producten.txt --headless --retries 3
```

## 📁 Projectstructuur

```
my-node-project/
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore (venv, output, etc.)
├── README.md                # Deze file
└── src/
    └── scrape.py            # Hoofdscript
```

## 🐍 Requirements

- Python 3.8+
- Playwright (automatisch geïnstalleerd via requirements.txt)

## 📝 Licentie

Open source - gebruik vrijelijk voor je projecten.

## 🆘 Support

Bij problemen:
1. Controleer of je `playwright install` hebt gedraaid
2. Probeer eerst headful mode om te zien wat er gebeurt
3. Check of de selector correct is (gebruik browser DevTools)
4. Verhoog timeout en wait tijd voor langzame sites

Happy scraping! 🎉
