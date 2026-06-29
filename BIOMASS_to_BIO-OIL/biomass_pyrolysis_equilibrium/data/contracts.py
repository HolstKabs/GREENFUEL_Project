"""Data contracts used by parser and workflow."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..models import BioOilRecord, FeedstockRecord, RowWarning


@dataclass
class ParsedWorkbook:
    """Structured parsed workbook output."""

    feedstocks: List[FeedstockRecord]
    bio_oils: List[BioOilRecord]
    feedstock_to_bio_oil: Dict[str, Optional[BioOilRecord]]
    unmatched_feedstocks: List[str]
    parse_warnings: List[RowWarning]
