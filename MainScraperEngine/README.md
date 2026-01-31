# MainScraperEngine v2.0 - Refactored Architecture

## 📁 Project Structuur

```
MainScraperEngine/
├── MSE.py                   ← CLI entry point (hoofdscript)
├── Vendor_YML.yaml          ← Alle vendor configuraties
├── __init__.py              ← Package marker
│
├── core/                    ← Core scraper logic
│   ├── __init__.py
│   ├── scraper.py           ← ConfigDrivenScraper class
│   ├── detector.py          ← Vendor detection
│   ├── config.py            ← YAML config loader
│   └── utils.py             ← Text cleaning helpers
│
├── extractors/              ← Modular extractors (hybrid approach)
│   ├── __init__.py          ← EXTRACTOR_REGISTRY
│   ├── base.py              ← Abstract BaseExtractor class
│   │
│   ├── generic/             ← Generic cross-vendor extractors
│   │   ├── __init__.py
│   │   ├── table.py         ← HTML <table> extractor
│   │   ├── dl.py            ← Definition list <dl> extractor
│   │   ├── rows.py          ← Row-based structures (VEGA, Nexans)
│   │   ├── li_split.py      ← LI split extractor (Siemens)
│   │   ├── label_value.py   ← Regex pattern extractor (fallback)
│   │   ├── datasheet.py     ← Generic datasheet link finder
│   │   ├── image.py         ← Generic image URL extractor (+ JSON-LD)
│   │   └── meta_description.py ← Meta tag extractor
│   │
│   └── vendors/             ← Vendor-specific extractors (complex cases)
│       ├── __init__.py
│       ├── schneider/
│       │   └── json_parser.py  ← Schneider JSON-in-HTML extractor
│       └── nexans/
│           └── variants.py     ← Nexans product variants extractor
│
└── vendors/                 ← (Future) Split YAML configs per vendor
    ├── siemens.yaml
    ├── phoenix.yaml
    └── ...
```

---

## 🎯 Hybrid Extractor Strategie

### **Wanneer Generic Extractor?**
✅ Gebruik generic extractor als:
- Simpele CSS selector verschillen
- Zelfde data model (key-value, table, list)
- Alleen presentatie verschilt (class names)

### **Wanneer Vendor-Specific Extractor?**
✅ Maak vendor-specific extractor als:
- Logica > 50 regels voor 1 vendor
- Unieke data structuur (Schneider JSON, Nexans variants)
- Complexe transformaties (URL constructie, data merging)
- Vendor gebruikt API i.p.v. HTML scraping

---

## 🚀 Gebruik

### **Basic Usage:**
```bash
python MSE.py                           # Default test file
python MSE.py path/to/product.html      # Scrape specific file
```

### **Programmatic Usage:**
```python
from core.scraper import scrape_file, scrape_html

# Scrape from file
result = scrape_file("product.html")

# Scrape from HTML string
result = scrape_html(html_string)

# Result structure
{
  "vendor": "Siemens",
  "kv": {
    "Section Name": {
      "Key": "Value",
      ...
    }
  },
  "stats": {
    "table": 10,
    "datasheet_link": 1,
    ...
  },
  "metadata": {
    "canonical_url": "https://...",
    "extraction_timestamp": "31/01/2026 12:00:00"
  }
}
```

---

## 📝 YAML Configuratie

### **Vendor toevoegen:**
```yaml
new_vendor:
  name: "New Vendor"
  priority: 25  # Lower = checked earlier
  
  detect:
    - selector: ".unique-class"
    - text_contains: "vendor name"
  
  specs:
    - type: "table"
      container: ".product-specs"
      tables: "table"
    
    - type: "datasheet_link"
      selectors:
        - "a[href*='datasheet']"
      target_section: "Downloads"
      target_key: "Datasheet"
```

### **Extractor Types:**

| Type | Gebruik | Generic/Vendor |
|------|---------|----------------|
| `table` | HTML tabellen | ✅ Generic |
| `dl` | Definition lists | ✅ Generic |
| `rows` | Row-based (VEGA) | ✅ Generic |
| `li_split` | LI split (Siemens) | ✅ Generic |
| `datasheet_link` | PDF datasheet finder | ✅ Generic |
| `attribute` | Image URLs | ✅ Generic |
| `meta_description` | Meta tags | ✅ Generic |
| `schneider_json` | Schneider JSON parser | ⚠️ Vendor-specific |
| `product_variants` | Nexans variants | ⚠️ Vendor-specific |

---

## 🔧 Nieuwe Extractor Toevoegen

### **1. Generic Extractor (bijv. nieuwe "gallery" type):**

**Stap 1:** Maak `extractors/generic/gallery.py`:
```python
from typing import Dict, Any
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor

class GalleryExtractor(BaseExtractor):
    @property
    def extractor_type(self) -> str:
        return "gallery"
    
    def extract(self, soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        # Implementation...
        pass
```

**Stap 2:** Voeg toe aan `extractors/generic/__init__.py`:
```python
from extractors.generic.gallery import GalleryExtractor

__all__ = [
    # ...existing...
    "GalleryExtractor",
]
```

**Stap 3:** Registreer in `extractors/__init__.py`:
```python
EXTRACTOR_REGISTRY = {
    # ...existing...
    "gallery": GalleryExtractor,
}
```

**Stap 4:** Gebruik in YAML:
```yaml
siemens:
  specs:
    - type: "gallery"
      selector: ".product-gallery"
      target_section: "Images"
```

---

### **2. Vendor-Specific Extractor (bijv. Phoenix PDF parser):**

**Stap 1:** Maak folder `extractors/vendors/phoenix/`

**Stap 2:** Maak `extractors/vendors/phoenix/__init__.py`:
```python
from extractors.vendors.phoenix.pdf_parser import PhoenixPDFExtractor

__all__ = ["PhoenixPDFExtractor"]
```

**Stap 3:** Maak `extractors/vendors/phoenix/pdf_parser.py`:
```python
from extractors.base import BaseExtractor

class PhoenixPDFExtractor(BaseExtractor):
    @property
    def extractor_type(self) -> str:
        return "phoenix_pdf"
    
    def extract(self, soup, spec, kv):
        # Complex Phoenix-specific logic...
        pass
```

**Stap 4:** Registreer in `extractors/__init__.py`:
```python
from extractors.vendors.phoenix import PhoenixPDFExtractor

EXTRACTOR_REGISTRY = {
    # ...
    "phoenix_pdf": PhoenixPDFExtractor,
}
```

---

## 🐛 Debugging

### **Test specific extractor:**
```python
from extractors.generic.datasheet import DatasheetLinkExtractor
from bs4 import BeautifulSoup

html = "<html>...</html>"
soup = BeautifulSoup(html, "html.parser")
kv = {}

extractor = DatasheetLinkExtractor()
count = extractor.extract(soup, {"selectors": ["a[href*='.pdf']"]}, kv)

print(f"Extracted {count} items: {kv}")
```

### **Test vendor detection:**
```python
from core.detector import detect_vendor
from core.config import load_configs
from bs4 import BeautifulSoup

configs = load_configs()
soup = BeautifulSoup(html, "html.parser")
vendor = detect_vendor(soup, configs)

print(f"Detected: {vendor}")
```

---

## 📊 Refactor Wins

| Metric | Old MSE.py | New (Refactored) |
|--------|-----------|------------------|
| **Lines of code** | 965 | ~50 (CLI) + modules |
| **Extractors** | Monolithic class | 12 modular files |
| **Testability** | Hard | Easy (isolated units) |
| **Maintainability** | ⚠️ Medium | ✅ High |
| **Extensibility** | ⚠️ Medium | ✅ High |

---

## 🔄 Migration from v1.0

### **Code Changes:**
**Old:**
```python
from MSE import scrape_html
result = scrape_html(html)
```

**New:**
```python
from core.scraper import scrape_html
result = scrape_html(html)  # Same API!
```

### **YAML:**
No changes needed! `Vendor_YML.yaml` is fully compatible.

---

## 📚 Next Steps

- [ ] Split `Vendor_YML.yaml` into separate files per vendor (`vendors/siemens.yaml`, etc.)
- [ ] Add unit tests per extractor (`tests/test_datasheet.py`, etc.)
- [ ] Create abstract `VendorExtractor` base class for complex vendors
- [ ] Add logging system (vendor detection, extractor performance)
- [ ] Implement caching for repeated scrapes

---

## 🎓 Architecture Philosophy

**"Start Generic, Specialize When Needed"**

1. **First:** Try to solve with generic extractors
2. **If 3+ fallbacks needed:** Consider vendor-specific
3. **If > 100 lines:** Definitely vendor-specific
4. **Keep YAML simple:** Complex logic → Python extractor

This keeps the codebase **DRY** while allowing **vendor expertise** where needed.

---

## 🤝 Contributing

Nieuwe vendor toevoegen:
1. Voeg detection rules toe aan `Vendor_YML.yaml`
2. Probeer eerst generic extractors
3. Maak vendor-specific extractor als nodig
4. Update deze README

---

## 📄 License

[Your License Here]

---

**Happy Scraping! 🚀**
