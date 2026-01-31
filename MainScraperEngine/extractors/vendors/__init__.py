"""Vendor-specific extractors."""

from extractors.vendors.schneider import SchneiderJSONExtractor
from extractors.vendors.nexans import NexansVariantsExtractor

__all__ = [
    "SchneiderJSONExtractor",
    "NexansVariantsExtractor",
]
