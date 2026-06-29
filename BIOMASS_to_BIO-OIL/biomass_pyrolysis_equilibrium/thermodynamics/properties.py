"""Thermodynamic property calculations for feedstocks."""

from __future__ import annotations

from typing import Dict, List

from ..config import WorkflowConfig
from ..models import FeedstockRecord, RowWarning, ThermoProperties
from ..utils.constants import ELEMENT_STANDARD_ENTROPIES, STANDARD_FORMATION_ENTHALPY
from .heating_value import compute_hhv_mj_per_kg, compute_lhv_mj_per_kg
from .stoichiometry import feedstock_element_moles_per_kg_as_received


def _element_reference_entropy_j_per_kg_k(element_moles: Dict[str, float]) -> float:
    """Compute reference elemental entropy term [J/kg/K] using atom-basis values."""

    return sum(
        element_moles[element] * ELEMENT_STANDARD_ENTROPIES[element]
        for element in ("C", "H", "O", "N", "S")
    )


def _estimate_biomass_absolute_entropy_j_per_kg_k(record: FeedstockRecord, element_moles: Dict[str, float]) -> float:
    """Estimate biomass absolute entropy [J/kg/K] using a conservative heuristic.

    This is intentionally explicit as a fallback assumption because formulations.md
    does not yet define a unique entropy correlation.
    """

    total_atom_moles = sum(max(0.0, value) for value in element_moles.values())
    oxygenation_ratio = record.o_pct_daf / max(record.c_pct_daf, 1e-9)
    factor = 0.85 + 0.25 * max(0.0, min(2.0, oxygenation_ratio))
    return 8.314462618 * total_atom_moles * factor


def _compute_delta_hf_kj_per_kg(lhv_mj_per_kg: float, element_moles: Dict[str, float]) -> float:
    """Compute feedstock formation enthalpy [kJ/kg] from LHV and product terms."""

    n_c = element_moles["C"]
    n_h2o = element_moles["H"] / 2.0
    n_s = element_moles["S"]

    return (
        n_c * STANDARD_FORMATION_ENTHALPY["CO2"]
        + n_h2o * STANDARD_FORMATION_ENTHALPY["H2O"]
        + n_s * STANDARD_FORMATION_ENTHALPY["SO2"]
        - lhv_mj_per_kg * 1000.0
    )


def compute_feedstock_thermo(record: FeedstockRecord, config: WorkflowConfig) -> ThermoProperties:
    """Compute thermodynamic properties for one feedstock record."""

    warnings: List[RowWarning] = list(record.warnings)

    hhv = compute_hhv_mj_per_kg(
        c_pct=record.c_pct_daf,
        h_pct=record.h_pct_daf,
        o_pct=record.o_pct_daf,
        n_pct=record.n_pct_daf,
        s_pct=record.s_pct_daf,
        ash_pct=record.ash_pct,
    )
    lhv = compute_lhv_mj_per_kg(
        hhv_mj_per_kg=hhv,
        h_pct=record.h_pct_daf,
        moisture_pct=record.moisture_pct,
        latent_heat_water_mj_per_kg=config.thermo.latent_heat_water_mj_per_kg,
    )

    element_moles = feedstock_element_moles_per_kg_as_received(record, config)
    delta_hf = _compute_delta_hf_kj_per_kg(lhv, element_moles)

    s_ref = _element_reference_entropy_j_per_kg_k(element_moles)
    s_abs = _estimate_biomass_absolute_entropy_j_per_kg_k(record, element_moles)
    delta_sf = s_abs - s_ref

    warnings.append(
        RowWarning(
            "ENTROPY_FALLBACK_HEURISTIC",
            "Biomass absolute entropy estimated with heuristic fallback; replace with calibrated model when available.",
        )
    )

    delta_gf = delta_hf - config.thermo.reference_temperature_k * (delta_sf / 1000.0)

    return ThermoProperties(
        feedstock_id=record.feedstock_id,
        hhv_mj_per_kg=hhv,
        lhv_mj_per_kg=lhv,
        delta_hf_kj_per_kg=delta_hf,
        delta_sf_j_per_kg_k=delta_sf,
        delta_gf_kj_per_kg=delta_gf,
        element_moles_per_kg_feedstock=element_moles,
        warnings=warnings,
    )
