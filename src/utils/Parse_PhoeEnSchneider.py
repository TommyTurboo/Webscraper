import sys
import os
import json
import re
import subprocess
import html as _html
try:
    from bs4 import BeautifulSoup
except Exception:
    print("Missing dependency: beautifulsoup4 (and optional lxml). Install with:")
    print(r"  python -m pip install beautifulsoup4 lxml")
    sys.exit(1)

r"""
Usage:
  python -m pip install beautifulsoup4 lxml
  python Parse_PhoeEnSchneider.py "C:\path\to\Relay.html"

Output:
  parsed_full_phoenix.json (or parsed_full_schneider.json) next to the HTML file
"""

# small per-domain selector config (CSS selectors usable with BeautifulSoup.select)
domain_configs = {
    "phoenix": {
        "detect": lambda s: bool(s.select('meta[name="crisp-metrics"], [data-product-id]')) or 'Phoenix' in (s.title.string if s.title else ''),
        "selectors": {
            "title": "#pr-headline .pr-product-title__designation, title",
            "subheadline": "#pr-subheadline span, [data-product-id]",
            "shortDescription": "#pr-short-description, meta[name=\"description\"]",
            "imagesDataAttr": "#pr-asset-modal__data-source, #pr-asset-gallery",
            "technicalTables": ".pr-technical-data table, .pr-technical-data",
            "commercialTable": "#pr-section-commercial-data-table",
            "downloads": "#pr-downloads, #pr-asset-links"
        }
    },
    "schneider": {
        "detect": lambda s: any('schneider' in (m.get('content','').lower()) for m in s.select('meta[name="generator"]')) or ('schneider' in (s.title.string.lower() if s.title else '')),
        "selectors": {
            "title": "h1.product-title, title",
            "subheadline": ".product-id, #productNumber, meta[name=\"productId\"]",
            "shortDescription": ".short-desc, meta[name=\"description\"]",
            "imagesDataAttr": ".product-gallery, #gallery",
            "technicalTables": ".tech-specs table, table.specifications",
            "commercialTable": ".commercial-data table"
        }
    },
    "siemens": {
        "detect": lambda s: 'siemens' in (s.select_one('link[rel="canonical"]').get('href','').lower() if s.select_one('link[rel="canonical"]') else '') or any('siemens' in m.get('content','').lower() for m in s.select('meta')),
        "selectors": {
            "title": "h1.product-headline, h1.product-title, h1[class*='product'], h1, title",
            "subheadline": ".article-number, .product-number, [class*='article'], meta[name='description']",
            "shortDescription": "meta[name='description'], .product-description, .short-description",
            "imagesDataAttr": "[data-product-images], .product-gallery, .product-image, .image-gallery",
            "technicalTables": "table[class*='spec'], table[class*='technical'], table[class*='data'], .specifications table, .technical-data table, table",
            "commercialTable": ".commercial-data, table[class*='commercial'], table[class*='pricing']",
            "downloads": "a[href*='datasheet'], a[href*='download'], a[href$='.pdf']"
        }
    }
}

def text_of(node):
    return node.get_text(" ", strip=True) if node else ""

def parse_key_value_table(table):
    out = {}
    # Siemens-specifieke structuur: thead met categorieën, tbody met key-value rows
    categories = []
    category_sections = {}
    
    # Check for thead categories (Siemens style)
    thead = table.find('thead')
    if thead:
        for th in thead.find_all('th'):
            cat_text = text_of(th).strip()
            if cat_text and cat_text not in ["", "Product related", "Pricing related", "Delivery related"]:
                categories.append(cat_text)
    
    # Parse tbody rows
    tbody = table.find('tbody') or table
    current_category = None
    
    for tr in tbody.find_all('tr', recursive=False):
        # Check if this is a category header row (Siemens often uses rowspan or special styling)
        cells = tr.find_all(['td', 'th'])
        
        # Skip empty rows
        if not cells:
            continue
            
        # Check for category header (usually has colspan or single cell with bold text)
        if len(cells) == 1 or (cells[0].get('colspan') or cells[0].get('rowspan')):
            header_text = text_of(cells[0]).strip()
            if header_text and len(header_text) < 100:  # Category names are typically short
                current_category = header_text
                category_sections[current_category] = {}
                continue
        
        # Parse key-value pairs
        if len(cells) >= 2:
            key = text_of(cells[0]).replace("\n", " ").strip()
            val = text_of(cells[1]).replace("\n", " ").strip()
            
            if key:
                # Store with category prefix if available
                if current_category and current_category in category_sections:
                    category_sections[current_category][key] = val
                else:
                    out[key] = val
        else:
            # dt/dd fallback
            dt = tr.select_one("dt")
            dd = tr.select_one("dd")
            if dt:
                key = text_of(dt).strip()
                val = text_of(dd) if dd else ""
                if current_category and current_category in category_sections:
                    category_sections[current_category][key] = val
                else:
                    out[key] = val
    
    # Merge category sections into main output
    if category_sections:
        for cat, items in category_sections.items():
            out[cat] = items
    
    # fallback: rows with two children (generic parser)
    if not out and not category_sections:
        for tr in tbody.find_all('tr'):
            children = [c for c in tr.children if getattr(c, 'name', None)]
            if len(children) >= 2:
                k = text_of(children[0])
                v = text_of(children[1])
                if k:
                    out[k] = v
    
    return out

def extract_jsonld(soup):
    out = []
    for tag in soup.select('script[type="application/ld+json"]'):
        txt = tag.string or tag.get_text()
        if not txt:
            continue
        try:
            out.append(json.loads(txt))
        except Exception:
            # try to fix common HTML-escaped quotes
            try:
                fixed = txt.replace('&quot;', '"')
                out.append(json.loads(fixed))
            except Exception:
                # ignore parse errors
                continue
    return out

# helper: balanced JSON/array extractor (handles strings and escapes)
def extract_balanced_json(s, start_pos=0):
    """Return first balanced JSON object or array (from { or [) starting at start_pos.
    Returns (text, (start, end)) or (None, None) if not found."""
    if not s or start_pos < 0 or start_pos >= len(s):
        return None, None
    i_obj = s.find('{', start_pos)
    i_arr = s.find('[', start_pos)
    # choose earliest non -1
    if i_obj == -1 or (i_arr != -1 and i_arr < i_obj):
        i = i_arr
        opening = '['
        closing = ']'
    else:
        i = i_obj
        opening = '{'
        closing = '}'
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
            elif ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return s[i:idx+1], (i, idx+1)
    return None, None

def robust_parse_blob(blob, allow_js_fallback=True):
    """Try progressive parsing: clean → json.loads → demjson3 → node eval.
    Returns (parsed_obj or None, cleaned_text)."""
    if not blob or not isinstance(blob, str):
        return None, blob
    txt = blob.strip()
    # unescape HTML entities
    txt = _html.unescape(txt)
    # if blob uses literal backslash sequences ("\n") turn into real escapes
    if '\\n' in txt and '\n' not in txt:
        try:
            txt = bytes(txt, "utf-8").decode("unicode_escape")
        except Exception:
            pass
    # remove JS comments (naïef but useful)
    txt_no_comments = re.sub(r'//.*?$|/\*[\s\S]*?\*/', '', txt, flags=re.MULTILINE)
    # trivial JS→JSON fixes
    cleaned = re.sub(r'\bundefined\b', 'null', txt_no_comments)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    # additional JS → JSON fixes for minified code
    cleaned = re.sub(r'\b!0\b', 'true', cleaned)   # !0 → true
    cleaned = re.sub(r'\b!1\b', 'false', cleaned)  # !1 → false
    cleaned = re.sub(r'(\d+)e(\d+)', lambda m: str(int(m.group(1)) * (10 ** int(m.group(2)))), cleaned)  # 1e4 → 10000
    # quote unquoted keys (more aggressive for minified JS)
    cleaned = re.sub(r'([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', cleaned)
    # try balanced extraction (object/array)
    obj_text, span = extract_balanced_json(cleaned, 0) or (None, None)
    attempt = obj_text if obj_text else cleaned

    # try strict JSON
    try:
        return json.loads(attempt), attempt
    except Exception:
        pass

    # try demjson3 if available (tolerant)
    try:
        import demjson3
        try:
            return demjson3.decode(attempt), attempt
        except Exception:
            pass
    except Exception:
        pass

    # optional: evaluate in node safely and JSON.stringify result
    if allow_js_fallback:
        try:
            node_cmd = [
                "node", "-e",
                "const v = (" + attempt.replace("\n", " ") + "); console.log(JSON.stringify(v))"
            ]
            res = subprocess.run(node_cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout:
                return json.loads(res.stdout.strip()), attempt
        except Exception:
            pass

    return None, attempt

def extract_plain_all_data(html_text):
    """Generieke extractor voor attributes zoals plain-all-data='...'. Return parsed object or None."""
    if not html_text:
        return None
    key = 'plain-all-data="'
    start = html_text.find(key)
    if start == -1:
        return None
    after = start + len(key)
    end_marker = '" plain-product-id='
    end = html_text.find(end_marker, after)
    if end == -1:
        # fallback: try closing quote
        end = html_text.find('"', after)
        if end == -1:
            return None
    blob = html_text[after:end]
    blob = _html.unescape(blob).strip()
    # try balanced extraction then robust parse
    obj_text, _ = extract_balanced_json(blob, 0)
    candidate = obj_text if obj_text else blob
    parsed, _ = robust_parse_blob(candidate, allow_js_fallback=True) if candidate else (None, candidate)
    return parsed if parsed is not None else None

def extract_data_attributes(soup, debug=False):
    """Extract large JSON-like content from data-* attributes (generic)."""
    results = []
    for tag in soup.find_all(attrs=lambda x: any(k.startswith('data-') for k in (x or {}))):
        for attr, val in tag.attrs.items():
            if not attr.startswith('data-') or not isinstance(val, str) or len(val) < 100:
                continue
            # try balanced extraction + robust parse
            obj_text, _ = extract_balanced_json(val, 0)
            candidate = obj_text if obj_text else val
            parsed, _ = robust_parse_blob(candidate, allow_js_fallback=False)
            if parsed:
                results.append({"pattern": f"data-{attr}", "raw": candidate, "parsed": parsed, "foundIn": f"<{tag.name} {attr}>"})
                if debug:
                    print(f"[extract_data_attributes] parsed {attr} from <{tag.name}> len={len(val)}")
    return results

def extract_embedded_json(soup, html_text=None, debug=True):
    """Zoek en parse grote JSON-objecten in <script> tags of in de ruwe HTML.
    Retourneert lijst met dicts: {'pattern': ..., 'raw': ..., 'parsed': obj or None}"""
    results = []
    patterns = [
        (r'window\.__INITIAL_STATE__\s*=\s*([\s\S]{100,});', "INITIAL_STATE"),
        (r'window\.__PRELOADED_STATE__\s*=\s*([\s\S]{100,});', "PRELOADED_STATE"),
        (r'(?:var|let|const)\s+[\w$]+\s*=\s*([\s\S]{100,});', "VAR_OBJECT"),
        (r'dataLayer\s*=\s*(\[[\s\S]{50,}\]);', "DATALAYER_ARRAY"),
        (r'=\s*(\{[\s\S]{200,}\})', "BIG_OBJECT_FALLBACK"),
        (r'<script[^>]*type=["\']application/json["\'][^>]*>([\s\S]{50,})</script>', "SCRIPT_JSON_TAG"),
        (r'<script[^>]*>([\s\S]{100,})</script>', "SCRIPT_TAG_FALLBACK")
    ]

    scripts = soup.find_all("script")
    if debug:
        raw_count = html_text.count("<script") if html_text else 0
        print(f"[extract_embedded_json] BS scripts found: {len(scripts)}; raw '<script' occurrences: {raw_count}")

    sources = []
    # collect text from script tags first
    for tag in scripts:
        txt = tag.string or tag.get_text()
        if txt:
            sources.append(("<script>", txt))
    # fallback: if no scripts or to capture escaped script blocks, include full html
    if html_text:
        sources.append(("<html>", html_text))

    for src_name, txt in sources:
        if not txt or len(txt) < 50:
            continue
        for pat, name in patterns:
            for m in re.finditer(pat, txt, re.IGNORECASE):
                blob_raw = m.group(1).strip().rstrip(';')
                # try to extract a balanced JSON object/array first from the matched text
                obj_text, _ = extract_balanced_json(blob_raw, 0)
                blob = obj_text if obj_text else blob_raw

                # If the matched blob contains literal backslash-escapes (e.g. "\\n", "\\uXXXX")
                # but not actual newlines, unescape them so json.loads can parse.
                if '\\n' in blob and '\n' not in blob:
                    try:
                        # decode unicode/escape sequences (turns "\n" -> actual newline, "\u00E9" -> é, etc.)
                        blob = bytes(blob, "utf-8").decode("unicode_escape")
                    except Exception:
                        # non-fatal: keep original blob if decoding fails
                        pass

                entry = {"pattern": name, "raw": blob, "parsed": None, "foundIn": src_name}
                # skip if it clearly contains functions/expressions we don't want to eval
                if "function(" in blob or "=>" in blob:
                    results.append(entry)
                    continue
                
                # use robust_parse_blob for consistent parsing
                parsed, cleaned = robust_parse_blob(blob, allow_js_fallback=True)
                
                # debug: when still not parsed, store short raw snippet to help diagnostics
                if parsed is None and debug:
                    snippet = (blob[:1000] + '...') if len(blob) > 1000 else blob
                    print(f"[extract_embedded_json] failed to parse pattern={name} foundIn={src_name} len={len(blob)}; snippet:\n{snippet}\n---")

                if parsed is not None:
                    entry["parsed"] = parsed
                results.append(entry)

    if debug:
        print(f"[extract_embedded_json] blobs matched: {len(results)}; parsed: {sum(1 for r in results if r['parsed'] is not None)}")
    return results

def extract_images(soup, selectors=None):
    imgs = set()
    # og/twitter
    for m in soup.select('meta[property="og:image"], meta[name="twitter:image"]'):
        v = m.get("content")
        if v:
            imgs.add(v)
    # img tags
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src") or img.get("srcset")
        if src:
            if " " in src:
                src = src.split()[0]
            imgs.add(src)
    # data attributes (Phoenix style)
    if selectors and selectors.get("imagesDataAttr"):
        for node in soup.select(selectors["imagesDataAttr"]):
            v = node.get("data-pictures")
            if v:
                try:
                    arr = json.loads(v.replace('&quot;', '"'))
                    if isinstance(arr, list):
                        for it in arr:
                            for key in ("mediumSrc","largeSrc","smallSrc","extraLargeSrc","url","src"):
                                if isinstance(it, dict) and it.get(key):
                                    imgs.add(it.get(key))
                except Exception:
                    continue
    return list(imgs)

def guess_domain(soup):
    for key, cfg in domain_configs.items():
        try:
            if cfg["detect"](soup):
                return key
        except Exception:
            continue
    canonical = ""
    link = soup.select_one('link[rel="canonical"]')
    if link and link.get("href"):
        canonical = link.get("href")
    if "phoenixcontact" in canonical:
        return "phoenix"
    if "schneider" in canonical:
        return "schneider"
    if "siemens" in canonical:
        return "siemens"
    return "generic"

def main(html_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    
    # Check if HTML is empty or too small
    if len(html.strip()) < 100:
        print(f"WARNING: HTML file appears empty or too small ({len(html)} bytes)")
        print("Please verify that siemens.html contains the actual page content")
        return None
    
    soup = BeautifulSoup(html, "lxml")

    domain_guess = guess_domain(soup)
    cfg = domain_configs.get(domain_guess, {})

    jsonld = extract_jsonld(soup)
    meta = {}
    for m in soup.find_all("meta"):
        name = m.get("name") or m.get("property")
        content = m.get("content")
        if name and content:
            meta[name.lower()] = content

    # Extract embedded JSON from scripts
    embedded_json = extract_embedded_json(soup, html, debug=True)
    
    # Try to find plain-all-data (many Schneider pages embed full product payload here)
    plain_all = extract_plain_all_data(html)
    if plain_all:
        # add to embedded list
        embedded_json.insert(0, {"pattern":"plain-all-data","raw":None,"parsed":plain_all,"foundIn":"attribute"})
        print(f"[main] extracted plain-all-data: {len(str(plain_all))} chars")
    
    # Also scan data-* attributes for JSON payloads (common in React/Angular apps)
    data_attrs = extract_data_attributes(soup, debug=True)
    if data_attrs:
        print(f"[main] extracted {len(data_attrs)} data-* attributes with JSON")
        embedded_json.extend(data_attrs)

    # base fields
    title_sel = cfg.get("selectors", {}).get("title", "title")
    title_node = soup.select_one(title_sel)
    title = text_of(title_node) if title_node else (jsonld[0].get("name") if jsonld and isinstance(jsonld[0], dict) and jsonld[0].get("name") else "")

    sub_sel = cfg.get("selectors", {}).get("subheadline", '[data-product-id], #pr-subheadline span, meta[name="productId"]')
    sub_node = soup.select_one(sub_sel)
    product_id = text_of(sub_node) if sub_node else ""
    if not product_id:
        can = soup.select_one('link[rel="canonical"]')
        if can and can.get("href"):
            product_id = can.get("href").rstrip("/").split("/")[-1]
    if not product_id:
        product_id = meta.get("productid") or meta.get("gcid") or (meta.get("og:url", "").rstrip("/").split("/")[-1] if meta.get("og:url") else "")

    short_sel = cfg.get("selectors", {}).get("shortDescription", 'meta[name="description"], #pr-short-description')
    desc_node = soup.select_one(short_sel)
    description = ""
    if desc_node:
        description = desc_node.get("content") if desc_node.has_attr("content") else text_of(desc_node)
    if not description and jsonld and isinstance(jsonld[0], dict):
        description = jsonld[0].get("description") or ""
    description = description or meta.get("description","")

    images = extract_images(soup, cfg.get("selectors"))

    # parse technical tables - IMPROVED FOR SIEMENS
    specs = {}
    table_selectors = cfg.get("selectors", {}).get("technicalTables", "table")
    tables_found = 0
    for sel in [s.strip() for s in table_selectors.split(",")]:
        for table in soup.select(sel):
            tables_found += 1
            candidate = parse_key_value_table(table)
            if candidate:
                # For Siemens, preserve nested structure if exists
                if any(isinstance(v, dict) for v in candidate.values()):
                    specs.update(candidate)
                else:
                    for k, v in candidate.items():
                        if k not in specs:
                            specs[k] = v
    
    print(f"[main] Found {tables_found} tables, extracted {len(specs)} spec entries")

    # commercial
    commercial = {}
    com_sel = cfg.get("selectors", {}).get("commercialTable")
    if com_sel:
        for node in soup.select(com_sel):
            commercial.update(parse_key_value_table(node))
    else:
        node = soup.select_one("#pr-section-commercial-data-table")
        if node:
            commercial.update(parse_key_value_table(node))

    # downloads - IMPROVED FOR SIEMENS
    downloads = []
    dl_sel = cfg.get("selectors", {}).get("downloads", "a[href]")
    for a in soup.select(dl_sel):
        href = a.get("href")
        if not href:
            continue
        # Make absolute URLs
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            canonical = soup.select_one('link[rel="canonical"]')
            if canonical and canonical.get("href"):
                from urllib.parse import urljoin
                href = urljoin(canonical.get("href"), href)
        low = href.lower()
        if low.endswith(".pdf") or "/download" in low or "datasheet" in low or "manual" in low:
            downloads.append(href)

    normalized = {
        "sourceDomain": domain_guess,
        "base": {
            "title": title,
            "productId": product_id,
            "description": description,
            "canonical": (soup.select_one('link[rel="canonical"]').get("href") if soup.select_one('link[rel="canonical"]') else ""),
            "meta": meta,
            "jsonld": jsonld
        },
        "images": images,
        "specs": specs,
        "commercial": commercial,
        "downloads": list(set(downloads)),  # Remove duplicates
        "rawHtmlFile": os.path.basename(html_path),
        "embeddedJson": embedded_json,
        "plainAllData": plain_all,
        "generatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    }

    out_name = f"parsed_full_{domain_guess}.json"
    out_path = os.path.join(os.path.dirname(html_path), out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    print("Wrote", out_path)
    return out_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Parse_PhoeEnSchneider.py <html-file>")
        sys.exit(1)
    html_file = os.path.abspath(sys.argv[1])
    main(html_file)