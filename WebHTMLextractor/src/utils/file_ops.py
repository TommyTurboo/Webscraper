import os
import re
from urllib.parse import urlparse
from pathlib import Path

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def read_urls(filepath):
    if not os.path.exists(filepath):
        # Maak dummy file aan als hij niet bestaat
        ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w') as f:
            f.write("# P plak je URLs hier, 1 per regel\n")
        return []

    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    return urls

def save_html(output_dir, url, content):
    filename = safe_filename_from_url(url)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def safe_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/')
    
    if path:
        filename = f"{domain}_{path}"
    else:
        filename = domain
    
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return f"{filename[:200].rstrip('_.')}.html"
