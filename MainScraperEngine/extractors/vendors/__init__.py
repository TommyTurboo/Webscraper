"""Vendor-specific extractors."""

from extractors.vendors.abb import ABBJSONExtractor
from extractors.vendors.schneider import SchneiderJSONExtractor
from extractors.vendors.nexans import NexansVariantsExtractor
from extractors.vendors.phoenix_pdf import PhoenixPdfExtractor
from extractors.vendors.vega_pdf import VegaPdfExtractor

__all__ = [
    "ABBJSONExtractor",
    "SchneiderJSONExtractor",
    "NexansVariantsExtractor",
    "PhoenixPdfExtractor",
    "VegaPdfExtractor",
]
