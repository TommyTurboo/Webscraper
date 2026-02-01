"""Generic extractors - Cross-vendor extraction strategies."""

from extractors.generic.table import TableExtractor
from extractors.generic.dl import DLExtractor
from extractors.generic.rows import RowsExtractor
from extractors.generic.li_split import LiSplitExtractor
from extractors.generic.label_value import LabelValueExtractor
from extractors.generic.datasheet import DatasheetLinkExtractor
from extractors.generic.image import ImageExtractor
from extractors.generic.meta_description import MetaDescriptionExtractor
from extractors.generic.text import TextExtractor
from extractors.generic.attribute import AttributeExtractor

__all__ = [
    "TableExtractor",
    "DLExtractor",
    "RowsExtractor",
    "LiSplitExtractor",
    "LabelValueExtractor",
    "DatasheetLinkExtractor",
    "ImageExtractor",
    "MetaDescriptionExtractor",
    "TextExtractor",
    "AttributeExtractor",
]
