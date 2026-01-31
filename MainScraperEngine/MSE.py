"""
╔════════════════════════════════════════════════════════════════╗
║  Configuration-Driven HTML Scraper                             ║
║                                                                 ║
║  Scrapt product data op basis van YAML configuraties.          ║
║  Nieuwe vendors toevoegen = alleen YAML aanpassen!             ║
╚════════════════════════════════════════════════════════════════╝
"""

import os
import re
import json
import yaml
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from collections import defaultdict
from typing import Optional, Dict, List, Any
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATIE LADEN
# ═══════════════════════════════════════════════════════════════

CONFIG_FILE = Path(__file__).parent / "Vendor_YML.yaml"

def load_configs() -> Dict:
    """Laad vendor configuraties uit YAML."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"❌ Config bestand niet gevonden: {CONFIG_FILE}")
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        configs = yaml.safe_load(f)
    
    # Sorteer op prioriteit (lager = eerder proberen)
    sorted_configs = dict(sorted(
        configs.items(), 
        key=lambda x: x[1].get("priority", 100)
    ))
    
    return sorted_configs


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIES
# ═══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Normaliseer tekst - verwijder tabs, newlines, extra spaties."""
    if text is None:
        return ""
    
    # Vervang escaped characters
    text = text.replace("\\t", " ")           # tabs
    text = text.replace("\\n", " ")           # newlines
    text = text.replace("\t", " ")            # real tabs
    text = text.replace("\n", " ")            # real newlines
    text = text.replace("\r", " ")            # carriage returns
    text = text.replace("\xa0", " ")          # non-breaking spaces
    
    # Verwijder Angular/HTML markers
    text = re.sub(r"\\x3C!---->", " ", text)
    text = re.sub(r"\\x3C!----&gt;", " ", text)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    
    # Normaliseer alle whitespace naar enkele spaties
    text = re.sub(r"\s+", " ", text)
    
    # Trim aan begin en eind
    return text.strip()


def nearest_heading(elem: Tag, levels: List[str] = None) -> str:
    """Zoek de meest nabije heading boven dit element."""
    if levels is None:
        levels = ["h1", "h2", "h3", "h4", "h5", "h6"]
    
    for prev in elem.find_all_previous():
        if isinstance(prev, Tag) and prev.name in levels:
            t = clean_text(prev.get_text(" ", strip=True))
            if t:
                return t
    return "Unknown"


# ═══════════════════════════════════════════════════════════════
# VENDOR DETECTIE
# ═══════════════════════════════════════════════════════════════

def detect_vendor(soup: BeautifulSoup, configs: Dict) -> Optional[str]:
    """Detecteer welke vendor bij deze HTML hoort."""
    
    for vendor_key, config in configs.items():
        if vendor_key == "generic":
            continue  # Skip generic, is fallback
        
        detect_rules = config.get("detect", [])
        
        for rule in detect_rules:
            matched = False
            
            # Type 1: ID selector
            if "id" in rule:
                matched = soup.find(id=rule["id"]) is not None
            
            # Type 2: CSS selector
            elif "selector" in rule:
                matched = len(soup.select(rule["selector"])) > 0
            
            # Type 3: Class contains
            elif "class_contains" in rule:
                search_class = rule["class_contains"]
                matched = soup.find(
                    class_=lambda c: c and search_class in c if c else False
                ) is not None
            
            # Type 4: Text contains
            elif "text_contains" in rule:
                page_text = soup.get_text().lower()
                matched = rule["text_contains"].lower() in page_text
            
            if matched:
                return vendor_key
    
    return "generic"  # Fallback


# ═══════════════════════════════════════════════════════════════
# EXTRACTORS - Één per spec type
# ═══════════════════════════════════════════════════════════════

class Extractors:
    """Collectie van extractor methodes per spec type."""
    
    @staticmethod
    def extract_rows(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """Extract key-value pairs uit row-gebaseerde structuren."""
        count = 0
        
        rows_selector = spec.get("rows", "")
        key_selector = spec.get("key", "")
        value_selector = spec.get("value", "")
        multiple_values = spec.get("multiple_values", False)
        remove_noise = spec.get("remove_noise", [])
        
        # Vind alle rows
        rows = soup.select(rows_selector)
        
        for row in rows:
            # Verwijder noise elementen
            for noise_sel in remove_noise:
                for noise_elem in row.select(noise_sel):
                    noise_elem.decompose()
            
            # Vind key
            key_elem = row.select_one(key_selector)
            if not key_elem:
                continue
            
            key = clean_text(key_elem.get_text(" ", strip=True))
            if not key:
                continue
            
            # Vind section
            section = nearest_heading(row)
            
            # Vind value(s)
            if multiple_values:
                value_elems = row.select(value_selector)
                for val_elem in value_elems:
                    value = clean_text(val_elem.get_text(" ", strip=True))
                    if value:
                        kv[section].setdefault(key, [])
                        if value not in kv[section][key]:
                            kv[section][key].append(value)
                        count += 1
            else:
                val_elem = row.select_one(value_selector)
                if val_elem:
                    value = clean_text(val_elem.get_text(" ", strip=True))
                    if value:
                        kv[section].setdefault(key, [])
                        if value not in kv[section][key]:
                            kv[section][key].append(value)
                        count += 1
        
        return count
    
    @staticmethod
    def extract_li_split(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """Extract key-value pairs uit LI elementen (Siemens stijl)."""
        count = 0
        
        container_sel = spec.get("container", "body")
        section_headers = spec.get("section_headers", ["h3", "h4"])
        items_sel = spec.get("items", "li")
        split_on = spec.get("split_on", "\n")
        skip_texts = set(t.lower() for t in spec.get("skip_texts", []))
        min_parts = spec.get("min_parts", 2)
        
        # Vind container
        container = soup.select_one(container_sel)
        if not container:
            return 0
        
        current_section = "Unknown"
        
        # Loop door alle descendants
        for el in container.descendants:
            if not isinstance(el, Tag):
                continue
            
            # Detecteer section headers
            if el.name in section_headers:
                section_text = clean_text(el.get_text(" ", strip=True))
                if section_text and section_text.lower() not in skip_texts:
                    current_section = section_text
                continue
            
            # Process LI items
            if el.name == "li" or (items_sel != "li" and el.select_one(items_sel)):
                li_text = clean_text(el.get_text(" ", strip=True)).lower()
                if li_text in skip_texts:
                    continue
                
                # Skip als LI nested lists bevat (navigatie)
                if el.find(["ul", "ol"]):
                    continue
                
                # Split op newlines
                parts = [clean_text(p) for p in el.get_text("\n", strip=True).split(split_on)]
                parts = [p for p in parts if p and p.lower() not in skip_texts]
                
                if len(parts) >= min_parts:
                    key = parts[0]
                    value = " ".join(parts[1:])
                    
                    if len(key) <= 100:  # Key niet te lang
                        kv[current_section].setdefault(key, [])
                        if value not in kv[current_section][key]:
                            kv[current_section][key].append(value)
                        count += 1
        
        return count
    
    @staticmethod
    def extract_table(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """Extract key-value pairs uit HTML tabellen."""
        count = 0
        
        container_sel = spec.get("container", "body")
        tables_sel = spec.get("tables", "table")
        
        container = soup.select_one(container_sel)
        if not container:
            container = soup
        
        tables = container.select(tables_sel)
        
        for table in tables:
            section = nearest_heading(table)
            
            for tr in table.find_all("tr"):
                cells = [clean_text(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
                cells = [c for c in cells if c]
                
                # 2 cellen = key-value
                if len(cells) == 2:
                    key, value = cells
                    kv[section].setdefault(key, [])
                    if value not in kv[section][key]:
                        kv[section][key].append(value)
                    count += 1
        
        return count
    
    @staticmethod
    def extract_dl(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """Extract key-value pairs uit definition lists."""
        count = 0
        
        container_sel = spec.get("container", "body")
        container = soup.select_one(container_sel)
        if not container:
            container = soup
        
        for dl in container.find_all("dl"):
            section = nearest_heading(dl)
            
            for dt in dl.find_all("dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    key = clean_text(dt.get_text(" ", strip=True))
                    value = clean_text(dd.get_text(" ", strip=True))
                    
                    if key and value:
                        kv[section].setdefault(key, [])
                        if value not in kv[section][key]:
                            kv[section][key].append(value)
                        count += 1
        
        return count
    
    @staticmethod
    def extract_label_value(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """Extract key-value pairs met regex patroon."""
        count = 0
        
        pattern = re.compile(spec.get("pattern", r"^(.{2,80}):\s*(.{1,200})$"))
        elements = spec.get("elements", ["p", "li", "div", "span"])
        
        for el in soup.find_all(elements):
            text = clean_text(el.get_text(" ", strip=True))
            if not text or len(text) > 300:
                continue
            
            match = pattern.match(text)
            if match:
                section = nearest_heading(el)
                key = match.group(1)
                value = match.group(2)
                
                kv[section].setdefault(key, [])
                if value not in kv[section][key]:
                    kv[section][key].append(value)
                count += 1
        
        return count

    @staticmethod
    def extract_product_variants(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """Extract product variants uit Nexans productlijst."""
        count = 0
        
        container_sel = spec.get("container", "body")
        variant_sel = spec.get("variant_selector", "")
        fields_config = spec.get("fields", {})
        
        container = soup.select_one(container_sel)
        if not container:
            container = soup
        
        variants = container.select(variant_sel)
        
        if not variants:
            return 0
        
        # Maak een lijst voor alle variants
        variant_list = []
        
        for variant_elem in variants:
            variant_data = {}
            
            # Extract title
            if "title" in fields_config:
                title_elem = variant_elem.select_one(fields_config["title"])
                if title_elem:
                    variant_data["title"] = clean_text(title_elem.get_text())  # ← FIX
            
            # Extract reference number
            if "ref" in fields_config:
                ref_elem = variant_elem.select_one(fields_config["ref"])
                if ref_elem:
                    ref_text = clean_text(ref_elem.get_text())  # ← FIX
                    # Extract alleen het nummer uit "Nexans ref. 10514199"
                    ref_match = re.search(r'\d+', ref_text)
                    if ref_match:
                        variant_data["reference"] = ref_match.group()
            
            # Extract URL
            if "url" in fields_config:
                url_elem = variant_elem.select_one(fields_config["url"])
                if url_elem and url_elem.has_attr("href"):
                    variant_data["url"] = url_elem["href"]
            
            # Extract specs (key-value pairs)
            if "specs" in fields_config:
                specs_config = fields_config["specs"]
                rows_sel = specs_config.get("rows", "")
                key_sel = specs_config.get("key", "")
                
                variant_data["specs"] = {}
                
                for row in variant_elem.select(rows_sel):
                    key_elem = row.select_one(key_sel)
                    if not key_elem:
                        continue
                    
                    key = clean_text(key_elem.get_text())  # ← FIX
                    key = key.rstrip(":")
                    
                    # Voor value: neem de hele row text en haal de key eruit
                    full_text = clean_text(row.get_text())  # ← FIX
                    key_text = clean_text(key_elem.get_text())  # ← FIX
                    value = full_text.replace(key_text, "", 1).strip()
                    
                    if key and value:
                        variant_data["specs"][key] = value
            
            # Voeg variant toe als er data is
            if variant_data:
                variant_list.append(variant_data)
                count += 1
        
        # Sla alle variants op in een speciale sectie
        if variant_list:
            kv["Product Variants"]["variants"] = variant_list
        
        return count

    @staticmethod
    def extract_schneider_json(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """
        Extract data uit Schneider Electric's JSON-in-HTML-attribute structuur.
        
        Schneider slaat alle data op in een `plain-all-data` attribuut als JSON string.
        """
        count = 0
        
        # 1. Vind het element met de JSON data
        json_selector = spec.get("json_selector", "[plain-all-data]")
        json_attr = spec.get("json_attribute", "plain-all-data")
        
        elem = soup.select_one(json_selector)
        if not elem or not elem.has_attr(json_attr):
            print("   ⚠️  Schneider JSON attribuut niet gevonden")
            return 0
        
        # 2. Extract en parse JSON
        raw_json = elem[json_attr]
        
        # Fix HTML entities
        raw_json = (raw_json
                   .replace('&quot;', '"')
                   .replace('&amp;', '&')
                   .replace('&lt;', '<')
                   .replace('&gt;', '>'))
        
        # Fix stray backslashes
        raw_json = re.sub(r"(\\+)'", lambda m: m.group(1) + '\\u0027', raw_json)
        raw_json = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw_json)
        raw_json = re.sub(r'\\+"', r'\\"', raw_json)
        
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parse error: {e}")
            return 0
        
        # 3. Extract configuratie
        extract_config = spec.get("extract", {})
        
        # 3a. Extract Product ID
        if "product_id" in extract_config:
            product_id = Extractors._extract_json_path(
                data, 
                extract_config["product_id"].get("path"),
                extract_config["product_id"].get("fallback_path")
            )
            if product_id:
                # ✅ FIX: Sla op als string, niet als list
                kv["Product Info"]["Product ID"] = str(product_id)
                count += 1
        
        # 3b. Extract Variants
        if "variants" in extract_config:
            variant_config = extract_config["variants"]
            variants_data = Extractors._get_by_path(data, variant_config.get("path", ""))
            
            if variants_data:
                variant_ids = []
                extract_fields = variant_config.get("extract_fields", ["productId"])
                
                for char_group in variants_data:
                    for variant in char_group.get("variants", []):
                        variant_info = {}
                        for field in extract_fields:
                            if field in variant:
                                variant_info[field] = variant[field]
                        if variant_info:
                            variant_ids.append(variant_info)
                
                if variant_ids:
                    kv["Product Variants"]["variants"] = variant_ids
                    count += len(variant_ids)
        
        # 3c. Extract Specifications (characteristicTables)
        if "specifications" in extract_config:
            spec_config = extract_config["specifications"]
            tables = Extractors._get_by_path(data, spec_config.get("path", ""))
            
            if tables:
                table_name_key = spec_config.get("table_name_key", "tableName")
                rows_key = spec_config.get("rows_key", "rows")
                char_name_key = spec_config.get("char_name_key", "characteristicName")
                char_values_key = spec_config.get("char_values_key", "characteristicValues")
                label_key = spec_config.get("label_key", "labelText")
                
                for table in tables:
                    table_name = table.get(table_name_key, "Unknown")
                    
                    for row in table.get(rows_key, []):
                        char_name = row.get(char_name_key, "")
                        char_values = row.get(char_values_key, [])
                        
                        # Combineer alle waarden
                        values = []
                        for val in char_values:
                            label = val.get(label_key, "")
                            if label:
                                # ✅ FIX: Clean HTML en behoud als string
                                label = Extractors._clean_html(str(label))
                                values.append(label)
                        
                        if char_name and values:
                            # ✅ FIX: Als 1 waarde → string, anders → list van strings
                            final_value = values[0] if len(values) == 1 else values
                            kv[table_name][char_name] = final_value
                            count += 1
        
        # 3d. Extract Description
        if "description" in extract_config:
            desc_path = extract_config["description"].get("path", "")
            description = Extractors._get_by_path(data, desc_path)
            
            if description and isinstance(description, list):
                # ✅ FIX: Description is al een list van strings
                kv["Product Description"]["description"] = description
                count += 1
        
        # 3e. Extract Metadata
        if "metadata" in extract_config:
            for meta_key, meta_path in extract_config["metadata"].items():
                meta_value = Extractors._get_by_path(data, meta_path)
                if meta_value:
                    # ✅ FIX: Behoud originele type (string, list, dict)
                    kv["Metadata"][meta_key] = meta_value
                    count += 1
        
        return count
    
    @staticmethod
    def _get_by_path(data: Any, path: str) -> Any:
        """Navigate door nested dict/list met dotted path."""
        if not path:
            return None
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    @staticmethod
    def _extract_json_path(data: Any, primary_path: str, fallback_path: str = None) -> Any:
        """Extract met fallback path."""
        result = Extractors._get_by_path(data, primary_path)
        if result:
            return result
        if fallback_path:
            return Extractors._get_by_path(data, fallback_path)
        return None
    
    @staticmethod
    def _clean_html(text: str) -> str:
        """Verwijder HTML tags uit tekst."""
        if not text:
            return text
        # Vervang <br /> door newline
        text = text.replace('<br />', '\n').replace('<br>', '\n')
        # Verwijder overige HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    @staticmethod
    def extract_meta_description(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """
        Extract description uit HTML meta tag.
        Gebruik: <meta name="description" content="...">
        """
        count = 0
        
        selector = spec.get("selector", "meta[name='description']")
        attribute = spec.get("attribute", "content")
        target_section = spec.get("target_section", "General")
        target_key = spec.get("target_key", "Description")
        
        elem = soup.select_one(selector)
        if elem and elem.has_attr(attribute):
            value = elem[attribute]
            if value:
                kv[target_section][target_key] = clean_text(value)
                count = 1
                print(f"   ✓ Found meta description: {value[:50]}...")
        
        if count == 0:
            print(f"   ✗ No meta description found with selector: {selector}")
        
        return count

    @staticmethod
    def extract_attribute(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """
        Extract attribuut van HTML element (bijv. image src).
        Ondersteunt meerdere selectors als fallback.
        """
        count = 0
        
        # Selector(s) ophalen - kan lijst of enkele string zijn
        selectors = spec.get("selectors", [])
        if not selectors:
            single = spec.get("selector")
            if single:
                selectors = [single]
        
        attribute = spec.get("attribute", "src")
        target_section = spec.get("target_section", "Product Info")
        target_key = spec.get("target_key", "Image URL")
        
        # ✨ NIEUW: Optie om eerste, laatste of alle matches te nemen
        take = spec.get("take", "first")  # Options: "first", "last", "all"
        
        # Probeer elke selector
        for selector in selectors:
            print(f"   🔎 Trying selector: {selector}")
            
            try:
                elems = soup.select(selector)
                
                if not elems:
                    print(f"   → No elements found")
                    continue
                
                print(f"   → Found {len(elems)} element(s)")
                
                # Filter elementen die het attribuut hebben
                valid_elems = [e for e in elems if e.has_attr(attribute)]
                
                if not valid_elems:
                    print(f"   → None have attribute '{attribute}'")
                    continue
                
                print(f"   → {len(valid_elems)} have attribute '{attribute}'")
                
                # Kies welke element(en) te nemen
                if take == "first":
                    value = valid_elems[0][attribute]
                    kv[target_section][target_key] = value
                    count = 1
                    print(f"   ✓ Found (first): {value}")
                    break
                
                elif take == "last":
                    value = valid_elems[-1][attribute]
                    kv[target_section][target_key] = value
                    count = 1
                    print(f"   ✓ Found (last): {value}")
                    break
                
                elif take == "all":
                    values = [e[attribute] for e in valid_elems]
                    kv[target_section][target_key] = values
                    count = len(values)
                    print(f"   ✓ Found {count} values")
                    break
            
            except Exception as e:
                print(f"   ⚠️  Selector failed: {selector} → {e}")
                continue
        
        # ✨ NIEUW: Fallback naar JSON-LD (structured data)
        if count == 0 and target_key == "Image URL":
            print("   🔎 Fallback: trying JSON-LD structured data...")
            script = soup.find("script", {"type": "application/ld+json", "id": "ld-script-product"})
            
            if script and script.string:
                try:
                    import json
                    data = json.loads(script.string)
                    
                    if "image" in data:
                        image_url = data["image"]
                        kv[target_section][target_key] = image_url
                        count = 1
                        print(f"   ✓ Found in JSON-LD: {image_url}")
                except Exception as e:
                    print(f"   ⚠️  JSON-LD parsing failed: {e}")
        
        if count == 0:
            print(f"   ✗ No {attribute} found")
        
        return count
    
    @staticmethod
    def extract_datasheet_link(soup: BeautifulSoup, spec: Dict, kv: Dict) -> int:
        """
        Vind datasheet link op basis van:
        1. data-ste attribuut met "Datasheet"
        2. href met "teddatasheet"
        3. Tekst bevat "productfiche" of "datasheet"
        """
        count = 0
        
        selectors = spec.get("selectors", [])
        if not selectors:
            selectors = [spec.get("selector", "a")]  # Fallback naar enkelvoud
        
        attribute = spec.get("attribute", "href")
        target_section = spec.get("target_section", "Downloads")
        target_key = spec.get("target_key", "Datasheet")
        
        # ✅ FIX: Gebruik soup.select() ZONDER :contains
        for selector in selectors:
            print(f"   🔎 Trying selector: {selector}")
            
            try:
                links = soup.select(selector)
                print(f"   → Found {len(links)} links")
                
                for link in links:
                    if link.has_attr(attribute):
                        url = link[attribute]
                        
                        # Valideer dat het een datasheet link is
                        if any(keyword in url.lower() for keyword in ['datasheet', 'teddatasheet']):
                            kv[target_section][target_key] = url
                            count = 1
                            print(f"   ✓ Found datasheet link: {url}")
                            break
                
                if count > 0:
                    break
            except Exception as e:
                print(f"   ⚠️  Selector failed: {selector} → {e}")
                continue
        
        # ✅ Fallback: BeautifulSoup's find() met lambda (werkt WEL)
        if count == 0:
            print("   🔎 Fallback: searching by text...")
            links = soup.find_all('a', string=lambda text: text and ('productfiche' in text.lower() or 'datasheet' in text.lower()))
            print(f"   → Found {len(links)} links by text")
            
            for link in links:
                if link.has_attr('href'):
                    url = link['href']
                    kv[target_section][target_key] = url
                    count = 1
                    print(f"   ✓ Found datasheet via text search: {url}")
                    break
        
        if count == 0:
            print(f"   ✗ No datasheet link found")
        
        return count
# ═══════════════════════════════════════════════════════════════
# MAIN SCRAPER CLASS
# ═══════════════════════════════════════════════════════════════

class ConfigDrivenScraper:
    """
    Configuration-driven HTML scraper.
    
    Gebruik:
        scraper = ConfigDrivenScraper(html)
        result = scraper.scrape()
    """
    
    EXTRACTOR_MAP = {
        "rows": Extractors.extract_rows,
        "li_split": Extractors.extract_li_split,
        "table": Extractors.extract_table,
        "dl": Extractors.extract_dl,
        "label_value": Extractors.extract_label_value,
        "product_variants": Extractors.extract_product_variants,
        "schneider_json": Extractors.extract_schneider_json,  

        "meta_description": Extractors.extract_meta_description,
        "attribute": Extractors.extract_attribute,
        "datasheet_link": Extractors.extract_datasheet_link,
    }
    
    def __init__(self, html: str):
        self.html = html
        self.soup = BeautifulSoup(html, "html.parser")
        self.configs = load_configs()
        self.vendor = None
        self.stats = defaultdict(int)
        self.extraction_timestamp = datetime.now()
    
    def scrape(self) -> Dict[str, Any]:
        """Main scraping method."""
        
        # 1. Detecteer vendor
        self.vendor = detect_vendor(self.soup, self.configs)
        vendor_config = self.configs.get(self.vendor, self.configs.get("generic", {}))
        
        print(f"🏭 Detected vendor: {vendor_config.get('name', self.vendor)}")
        
        # 2. Initialiseer result
        kv = defaultdict(dict)
        
        # 3. Run alle spec extractors voor deze vendor
        specs = vendor_config.get("specs", [])
        
        for spec in specs:
            spec_type = spec.get("type")
            extractor = self.EXTRACTOR_MAP.get(spec_type)
            
            if extractor:
                count = extractor(self.soup, spec, kv)
                self.stats[spec_type] += count
                print(f"   🔹 {spec_type}: {count} items gevonden")
        
        # 4. Cleanup en flatten
        result = self._cleanup(kv, vendor_config)

        # ✨ 5. NIEUW: Voeg metadata toe
        result["metadata"] = self._build_metadata()
        
        return result
    
    def _extract_canonical_url(self) -> Optional[str]:
        """Extract canonical URL uit HTML."""
        link = self.soup.find("link", rel="canonical")
        if link and link.has_attr("href"):
            return link["href"]
        return None

    def _build_metadata(self) -> Dict[str, str]:
        """
        Bouw metadata sectie met alleen:
        - Canonical URL
        - Extraction timestamp (dd/mm/yyyy HH:MM:SS)
        """
        metadata = {}
        
        # 1. Canonical URL
        canonical_url = self._extract_canonical_url()
        if canonical_url:
            metadata["canonical_url"] = canonical_url
        
        # 2. Extraction timestamp (Europees formaat)
        metadata["extraction_timestamp"] = self.extraction_timestamp.strftime("%d/%m/%Y %H:%M:%S")
        
        return metadata
    
    def _cleanup(self, kv: Dict, config: Dict) -> Dict:
        """Post-processing: cleanup en normalize."""
        
        # Convert defaultdict to regular dict
        cleaned_kv = {}
        
        for section, items in kv.items():
            if not items:
                continue
            
            cleaned_kv[section] = {}
            
            for key, value in items.items():
                # ✅ FIX: Check of value al een list is (van andere extractors)
                if isinstance(value, list):
                    # Verwijder duplicates (behoud volgorde)
                    unique_values = []
                    for v in value:
                        if v not in unique_values:
                            unique_values.append(v)
                    
                    # Flatten single-value arrays
                    if len(unique_values) == 1:
                        cleaned_kv[section][key] = unique_values[0]
                    else:
                        cleaned_kv[section][key] = unique_values
                else:
                    # ✅ Waarde is al een string/dict/int → direct opslaan
                    cleaned_kv[section][key] = value
        
        return {
            "vendor": config.get("name", self.vendor),
            "kv": cleaned_kv,
            "stats": dict(self.stats)
        }


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION
# ═══════════════════════════════════════════════════════════════

def scrape_html(html: str) -> Dict[str, Any]:
    """Convenience function om HTML te scrapen."""
    scraper = ConfigDrivenScraper(html)
    return scraper.scrape()


def scrape_file(filepath: str) -> Dict[str, Any]:
    """Convenience function om een HTML bestand te scrapen."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    scraper = ConfigDrivenScraper(html)
    return scraper.scrape()


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Configuration-Driven HTML Scraper                             ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    # Default test file of CLI argument
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        html_file = r"C:\Users\tomva\PlatformIO\my-node-project\src\scrapers\HTML_Siemens_5SY6Automaat.txt"
    
    print(f"📄 Input: {html_file}")
    
    if not os.path.exists(html_file):
        print(f"❌ Bestand niet gevonden: {html_file}")
        sys.exit(1)
    
    # Scrape
    result = scrape_file(html_file)
    
    # Output
    print(f"\n✅ Scraping voltooid!")
    print(f"   - Vendor: {result['vendor']}")
    print(f"   - Secties: {len(result['kv'])}")
    print(f"   - Stats: {result['stats']}")

    # ✨ NIEUW: Metadata info
    metadata = result.get("metadata", {})
    if "canonical_url" in metadata:
        print(f"   - URL: {metadata['canonical_url']}")
    print(f"   - Extractie: {metadata.get('extraction_timestamp', 'Unknown')}")
    
    # Save to JSON
    output_file = "config_scraped_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Preview
    print("\n📋 Preview (eerste 3 secties):")
    for i, (section, items) in enumerate(result["kv"].items()):
        if i >= 3:
            print("   ...")
            break
        print(f"   📁 {section}: {len(items)} items")
        for j, (key, value) in enumerate(items.items()):
            if j >= 2:
                print(f"      ...")
                break
            val_preview = str(value)[:50] + "..." if len(str(value)) > 50 else value
            print(f"      • {key}: {val_preview}")