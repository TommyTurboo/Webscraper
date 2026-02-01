"""
╔════════════════════════════════════════════════════════════════╗
║  Extractors - Modular extraction strategies                   ║
║  Generic + Vendor-specific hybrid approach                    ║
╚════════════════════════════════════════════════════════════════╝
"""

from extractors.base import BaseExtractor

# Generic extractors (cross-vendor)
from extractors.generic import (
    TableExtractor,
    DLExtractor,
    RowsExtractor,
    LiSplitExtractor,
    LabelValueExtractor,
    DatasheetLinkExtractor,
    ImageExtractor,
    MetaDescriptionExtractor,
    TextExtractor,
    AttributeExtractor,
)

# Vendor-specific extractors (complex cases)
from extractors.vendors import (
    ABBJSONExtractor,
    SchneiderJSONExtractor,
    NexansVariantsExtractor,
    PhoenixPdfExtractor,
    VegaPdfExtractor,
)

# Extractor registry - maps YAML type to extractor class
EXTRACTOR_REGISTRY = {
    # Generic types
    "table": TableExtractor,
    "dl": DLExtractor,
    "rows": RowsExtractor,
    "li_split": LiSplitExtractor,
    "label_value": LabelValueExtractor,
    
    # Specialized generic types
    "datasheet_link": DatasheetLinkExtractor,
    "attribute": AttributeExtractor,  # ✨ Fixed: was ImageExtractor
    "text": TextExtractor,  # ✨ NEW
    "meta_description": MetaDescriptionExtractor,    # Vendor-specific types
    "abb_json": ABBJSONExtractor,
    "schneider_json": SchneiderJSONExtractor,
    "product_variants": NexansVariantsExtractor,
    "phoenix_pdf": PhoenixPdfExtractor,
    "vega_pdf": VegaPdfExtractor,
}

__all__ = [
    "BaseExtractor",
    "EXTRACTOR_REGISTRY",
    # Generic
    "TableExtractor",
    "DLExtractor",
    "RowsExtractor",
    "LiSplitExtractor",
    "LabelValueExtractor",
    "DatasheetLinkExtractor",
    "ImageExtractor",
    "MetaDescriptionExtractor",
    "TextExtractor",
    "AttributeExtractor",    # Vendor-specific
    "ABBJSONExtractor",
    "SchneiderJSONExtractor",
    "NexansVariantsExtractor",
    "PhoenixPdfExtractor",
    "VegaPdfExtractor",
]
