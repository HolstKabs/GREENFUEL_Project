"""Species candidate pool builder for equilibrium runs."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..config import WorkflowConfig
from ..models import BioOilRecord, FeedstockRecord, RowWarning, Species
from .bio_oil import bio_oil_record_to_species, generic_bio_oil_species
from .registry import base_species_registry


def build_candidate_species(
    feedstock: FeedstockRecord,
    mapped_bio_oil: Optional[BioOilRecord],
    config: WorkflowConfig,
) -> Tuple[List[Species], List[RowWarning]]:
    """Build candidate product species list for one feedstock."""

    warnings: List[RowWarning] = []
    registry = base_species_registry(config)

    selected: List[Species] = []
    for name in config.species.gas_species:
        species = registry.get(name)
        if species is not None:
            selected.append(species)

    if config.species.include_char_species and "CHAR" in registry:
        selected.append(registry["CHAR"])

    if mapped_bio_oil is not None:
        oil_species, oil_warnings = bio_oil_record_to_species(mapped_bio_oil, config)
        selected.append(oil_species)
        warnings.extend(oil_warnings)
    elif config.species.include_generic_bio_oil_fallback:
        oil_species, oil_warnings = generic_bio_oil_species(config)
        selected.append(oil_species)
        warnings.extend(oil_warnings)
    else:
        warnings.append(
            RowWarning(
                "BIO_OIL_EXCLUDED",
                f"No mapped bio-oil record for feedstock '{feedstock.feedstock_id}' and generic fallback disabled.",
                severity="error",
            )
        )

    return selected, warnings
