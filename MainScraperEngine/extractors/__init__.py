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
)

# Vendor-specific extractors (complex cases)
from extractors.vendors import (
    SchneiderJSONExtractor,
    NexansVariantsExtractor,
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
    "attribute": ImageExtractor,  # Legacy naam
    "meta_description": MetaDescriptionExtractor,
    
    # Vendor-specific types
    "schneider_json": SchneiderJSONExtractor,
    "product_variants": NexansVariantsExtractor,
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
    # Vendor-specific
    "SchneiderJSONExtractor",
    "NexansVariantsExtractor",
]
