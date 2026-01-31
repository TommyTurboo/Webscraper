"""
╔════════════════════════════════════════════════════════════════╗
║  Utilities - Helper functies voor text cleaning               ║
╚════════════════════════════════════════════════════════════════╝
"""
import re
from typing import List, Optional
from bs4 import Tag


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
