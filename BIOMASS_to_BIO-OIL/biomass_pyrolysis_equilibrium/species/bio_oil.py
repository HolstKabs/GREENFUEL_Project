"""Bio-oil pseudo-species generation from sheet data or fallback composition."""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..config import WorkflowConfig
from ..models import BioOilRecord, RowWarning, Species
from ..utils.constants import ATOMIC_WEIGHTS, STANDARD_FORMATION_ENTHALPY


def _composition_from_wt_percent(c_pct: float, h_pct: float, o_pct: float, n_pct: float, s_pct: float) -> Dict[str, float]:
    """Create pseudo-molecular composition normalized to one carbon atom if available."""

    moles = {
        "C": c_pct / ATOMIC_WEIGHTS["C"],
        "H": h_pct / ATOMIC_WEIGHTS["H"],
        "O": o_pct / ATOMIC_WEIGHTS["O"],
        "N": n_pct / ATOMIC_WEIGHTS["N"],
        "S": s_pct / ATOMIC_WEIGHTS["S"],
    }
    c_ref = moles["C"] if moles["C"] > 0 else 1.0
    return {element: max(0.0, value / c_ref) for element, value in moles.items()}


def _mw_from_composition(composition: Dict[str, float]) -> float:
    return sum(ATOMIC_WEIGHTS[element] * coeff for element, coeff in composition.items())


def _estimate_delta_hf_kj_per_mol(composition: Dict[str, float], lhv_mj_per_kg: float, molecular_weight_g_per_mol: float) -> float:
    """Estimate pseudo-species formation enthalpy [kJ/mol] from LHV and product terms."""

    lhv_kj_per_mol = lhv_mj_per_kg * molecular_weight_g_per_mol
    n_c = composition.get("C", 0.0)
    n_h2o = composition.get("H", 0.0) / 2.0
    n_s = composition.get("S", 0.0)
    return (
        n_c * STANDARD_FORMATION_ENTHALPY["CO2"]
        + n_h2o * STANDARD_FORMATION_ENTHALPY["H2O"]
        + n_s * STANDARD_FORMATION_ENTHALPY["SO2"]
        - lhv_kj_per_mol
    )


def _estimate_entropy_j_per_mol_k(composition: Dict[str, float]) -> float:
    """Heuristic pseudo-species entropy estimate."""

    total_atoms = sum(composition.values())
    oxygenation = composition.get("O", 0.0) / max(composition.get("C", 1.0), 1e-9)
    return 120.0 + 8.0 * total_atoms + 20.0 * oxygenation


def bio_oil_record_to_species(record: BioOilRecord, config: WorkflowConfig) -> Tuple[Species, List[RowWarning]]:
    """Convert a bio-oil row into a pseudo-species model for equilibrium."""

    warnings: List[RowWarning] = []

    composition = _composition_from_wt_percent(
        record.c_pct_daf,
        record.h_pct_daf,
        record.o_pct_daf,
        record.n_pct_daf,
        record.s_pct_daf,
    )
    mw = _mw_from_composition(composition)

    lhv = record.lhv_mj_per_kg
    if lhv is None:
        if record.hhv_mj_per_kg is not None:
            lhv = record.hhv_mj_per_kg * 0.92
            warnings.append(
                RowWarning(
                    "BIO_OIL_LHV_ESTIMATED_FROM_HHV",
                    "LHV missing in bio-oil row; estimated as 0.92 * HHV.",
                )
            )
        else:
            lhv = 17.0
            warnings.append(
                RowWarning(
                    "BIO_OIL_LHV_FALLBACK",
                    "Both LHV and HHV missing; applied generic LHV fallback 17.0 MJ/kg.",
                )
            )

    delta_hf = _estimate_delta_hf_kj_per_mol(composition, lhv, mw)
    s0 = _estimate_entropy_j_per_mol_k(composition)
    warnings.append(
        RowWarning(
            "BIO_OIL_THERMO_HEURISTIC",
            "Bio-oil thermodynamic properties estimated from pseudo-species heuristics.",
        )
    )

    return (
        Species(
            name="BIO_OIL",
            phase="liquid_oil",
            composition=composition,
            molecular_weight_g_per_mol=mw,
            delta_hf_kj_per_mol=delta_hf,
            s0_j_per_mol_k=s0,
        ),
        warnings,
    )


def generic_bio_oil_species(config: WorkflowConfig) -> Tuple[Species, List[RowWarning]]:
    """Build generic bio-oil pseudo-species fallback from config."""

    comp = dict(config.species.generic_bio_oil_formula)
    mw = _mw_from_composition(comp)
    lhv_fallback = 17.0
    delta_hf = _estimate_delta_hf_kj_per_mol(comp, lhv_fallback, mw)
    s0 = _estimate_entropy_j_per_mol_k(comp)

    warnings = [
        RowWarning(
            "BIO_OIL_GENERIC_FALLBACK",
            "No mappable bio-oil row found; using generic literature-inspired pseudo-species fallback.",
        )
    ]

    return (
        Species(
            name="BIO_OIL",
            phase="liquid_oil",
            composition=comp,
            molecular_weight_g_per_mol=mw,
            delta_hf_kj_per_mol=delta_hf,
            s0_j_per_mol_k=s0,
        ),
        warnings,
    )
