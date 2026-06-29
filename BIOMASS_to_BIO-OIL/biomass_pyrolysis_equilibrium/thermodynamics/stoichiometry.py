"""Stoichiometric conversions from proximate/ultimate data to element inventories."""

from __future__ import annotations

from typing import Dict

from ..config import WorkflowConfig
from ..models import FeedstockRecord
from ..utils.constants import ATOMIC_WEIGHTS


def feedstock_element_moles_per_kg_as_received(
    record: FeedstockRecord,
    config: WorkflowConfig,
) -> Dict[str, float]:
    """Compute element moles per kg as-received feedstock.

    Assumptions:
    - Proximate moisture/ash are on as-received basis.
    - Ultimate analysis is on dry ash-free (daf) basis.
    - Ash is inert and removed from reacting mass if configured.
    """

    dry_mass_kg = max(0.0, 1.0 - record.moisture_pct / 100.0)
    if config.thermo.treat_ash_as_inert:
        reactive_mass_kg = dry_mass_kg * max(0.0, 1.0 - record.ash_pct / 100.0)
    else:
        reactive_mass_kg = dry_mass_kg

    mass_by_element_kg = {
        "C": reactive_mass_kg * (record.c_pct_daf / 100.0),
        "H": reactive_mass_kg * (record.h_pct_daf / 100.0),
        "O": reactive_mass_kg * (record.o_pct_daf / 100.0),
        "N": reactive_mass_kg * (record.n_pct_daf / 100.0),
        "S": reactive_mass_kg * (record.s_pct_daf / 100.0),
    }

    return {
        element: (mass_by_element_kg[element] * 1000.0) / ATOMIC_WEIGHTS[element]
        for element in ("C", "H", "O", "N", "S")
    }
