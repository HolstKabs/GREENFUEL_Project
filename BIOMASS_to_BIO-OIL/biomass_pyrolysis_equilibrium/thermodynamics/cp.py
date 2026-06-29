"""Specific heat capacity (Cp) estimators for feedstock and product phases.

Gas Cp retrieval is chemicals-first (preferred), with optional CoolProp fallback.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, Sequence

from ..models import EquilibriumSolution, FeedstockRecord, Species


REFERENCE_TEMPERATURE_K = 298.15
WATER_CP_KJ_PER_KG_K = 4.186


GAS_SPECIES_TO_CASRN: Dict[str, str] = {
    "CO2": "124-38-9",
    "CO": "630-08-0",
    "CH4": "74-82-8",
    "H2": "1333-74-0",
    "H2O": "7732-18-5",
    "N2": "7727-37-9",
    "NH3": "7664-41-7",
    "H2S": "7783-06-4",
    "SO2": "7446-09-5",
    "O2": "7782-44-7",
}


COOLPROP_FLUIDS: Dict[str, str] = {
    "CO2": "CO2",
    "CO": "CO",
    "CH4": "Methane",
    "H2": "Hydrogen",
    "H2O": "Water",
    "N2": "Nitrogen",
    "NH3": "Ammonia",
    "H2S": "HydrogenSulfide",
    "SO2": "SulfurDioxide",
    "O2": "Oxygen",
}


FALLBACK_GAS_CP_MOLAR_J_PER_MOL_K: Dict[str, float] = {
    "CO2": 50.5,
    "CO": 33.6,
    "CH4": 47.1,
    "H2": 29.0,
    "H2O": 37.0,
    "N2": 31.0,
    "NH3": 44.0,
    "H2S": 38.0,
    "SO2": 46.0,
    "O2": 32.0,
}


try:
    import chemicals.heat_capacity as _chem_hc
except Exception:  # pragma: no cover - optional dependency
    _chem_hc = None

try:
    import CoolProp.CoolProp as _coolprop
except Exception:  # pragma: no cover - optional dependency
    _coolprop = None


_CHEMICALS_DATA_LOADED = False


def _ensure_chemicals_data_loaded() -> bool:
    global _CHEMICALS_DATA_LOADED
    if _chem_hc is None:
        return False
    if not _CHEMICALS_DATA_LOADED:
        _chem_hc._load_Cp_data()
        _CHEMICALS_DATA_LOADED = True
    return True


def estimate_feedstock_cp_dry_kj_per_kg_k(record: FeedstockRecord, temperature_k: float) -> float:
    """Estimate dry-feedstock Cp [kJ/kg/K] from composition and temperature.

    This is a pragmatic correlation intended for workflow-level energy accounting.
    """

    t_c = max(0.0, temperature_k - 273.15)
    oxygen_term = 0.0040 * max(0.0, record.o_pct_daf)
    hydrogen_term = 0.0020 * max(0.0, record.h_pct_daf)
    temperature_term = 0.0030 * t_c
    return max(0.50, 0.75 + oxygen_term + hydrogen_term + temperature_term)


def estimate_feedstock_cp_ar_kj_per_kg_k(record: FeedstockRecord, temperature_k: float) -> float:
    """Estimate as-received feedstock Cp [kJ/kg/K] by moisture-weighted mixing."""

    moisture_frac = max(0.0, min(1.0, record.moisture_pct / 100.0))
    cp_dry = estimate_feedstock_cp_dry_kj_per_kg_k(record, temperature_k)
    return (1.0 - moisture_frac) * cp_dry + moisture_frac * WATER_CP_KJ_PER_KG_K


def estimate_bio_oil_cp_kj_per_kg_k(composition: Dict[str, float], temperature_k: float) -> float:
    """Estimate bio-oil Cp [kJ/kg/K] from pseudo-species composition and temperature."""

    t_c = max(0.0, temperature_k - 273.15)
    c = max(composition.get("C", 0.0), 1e-12)
    o_c = max(0.0, composition.get("O", 0.0) / c)
    h_c = max(0.0, composition.get("H", 0.0) / c)
    return max(1.00, 1.15 + 0.0016 * t_c + 0.35 * o_c + 0.04 * h_c)


def estimate_char_cp_kj_per_kg_k(temperature_k: float) -> float:
    """Estimate char Cp [kJ/kg/K] as a simple temperature correlation."""

    t_c = max(0.0, temperature_k - 273.15)
    return max(0.40, 0.62 + 0.0012 * t_c)


def _cp_from_chemicals(species_name: str, temperature_k: float) -> tuple[float, str] | None:
    if not _ensure_chemicals_data_loaded():
        return None

    casrn = GAS_SPECIES_TO_CASRN.get(species_name)
    if casrn is None:
        return None

    webbook = getattr(_chem_hc, "WebBook_Shomate_gases", {})
    model = webbook.get(casrn)
    if model is not None:
        try:
            cp = float(model.calculate(temperature_k))
        except Exception:
            cp = float(model.force_calculate(temperature_k))
        if cp > 0.0:
            return cp, "chemicals:webbook_shomate"

    trc = getattr(_chem_hc, "TRC_gas_data", None)
    if trc is not None and casrn in trc.index:
        row = trc.loc[casrn]
        cp = float(
            _chem_hc.TRCCp(
                temperature_k,
                float(row["a0"]),
                float(row["a1"]),
                float(row["a2"]),
                float(row["a3"]),
                float(row["a4"]),
                float(row["a5"]),
                float(row["a6"]),
                float(row["a7"]),
            )
        )
        if cp > 0.0:
            return cp, "chemicals:trc"

    poling = getattr(_chem_hc, "Cp_data_Poling", None)
    if poling is not None and casrn in poling.index:
        row = poling.loc[casrn]
        cp = float(
            _chem_hc.Poling(
                temperature_k,
                float(row["a0"]),
                float(row["a1"]),
                float(row["a2"]),
                float(row["a3"]),
                float(row["a4"]),
            )
        )
        if cp > 0.0:
            return cp, "chemicals:poling"

    return None


def _cp_from_coolprop(species_name: str, temperature_k: float, pressure_pa: float) -> tuple[float, str] | None:
    if _coolprop is None:
        return None

    fluid = COOLPROP_FLUIDS.get(species_name)
    if fluid is None:
        return None

    try:
        cp = float(
            _coolprop.PropsSI(
                "Cpmolar",
                "T",
                max(1.0, temperature_k),
                "P",
                max(1.0, pressure_pa),
                fluid,
            )
        )
    except Exception:
        return None

    if cp <= 0.0:
        return None
    return cp, "coolprop"


def gas_species_cp_molar_j_per_mol_k(
    species_name: str,
    temperature_k: float,
    pressure_pa: float = 101_325.0,
) -> tuple[float, str]:
    """Return gas species Cp [J/mol/K] and source label."""

    from_chemicals = _cp_from_chemicals(species_name, temperature_k)
    if from_chemicals is not None:
        return from_chemicals

    from_coolprop = _cp_from_coolprop(species_name, temperature_k, pressure_pa)
    if from_coolprop is not None:
        return from_coolprop

    return FALLBACK_GAS_CP_MOLAR_J_PER_MOL_K.get(species_name, 30.0), "fallback:constant"


def _serialize_source_counts(source_counts: Counter[str]) -> str:
    if not source_counts:
        return ""
    return "|".join(f"{source}={count}" for source, count in source_counts.most_common())


def gas_mixture_cp_diagnostics(
    solution: EquilibriumSolution,
    species: Sequence[Species],
    temperature_k: float,
    pressure_pa: float,
) -> tuple[float, float, float, str, str, float]:
    """Return gas mixture Cp with provenance diagnostics.

    Returns:
    - Cp_molar_mix [J/mol/K]
    - Cp_mass_mix [kJ/kg/K]
    - Mean molecular weight [g/mol]
    - Dominant data source label
    - Source-count summary string (for example "chemicals:webbook_shomate=4|fallback:constant=1")
    - Fallback mole fraction [0, 1]
    """

    by_name = {sp.name: sp for sp in species}

    gas_rows: list[tuple[str, float, float]] = []
    for name, n_mol in solution.species_moles.items():
        sp = by_name.get(name)
        if sp is None or sp.phase != "gas":
            continue
        if n_mol <= 0.0:
            continue
        gas_rows.append((name, float(n_mol), float(sp.molecular_weight_g_per_mol)))

    if not gas_rows:
        return 0.0, 0.0, 0.0, "none", "", 0.0

    total_moles = sum(n_mol for _, n_mol, _ in gas_rows)
    cp_molar_mix = 0.0
    mw_mix = 0.0
    source_counts: Counter[str] = Counter()
    fallback_mole_fraction = 0.0

    for name, n_mol, mw_i in gas_rows:
        yi = n_mol / total_moles
        cp_i, source = gas_species_cp_molar_j_per_mol_k(name, temperature_k, pressure_pa)
        cp_molar_mix += yi * cp_i
        mw_mix += yi * mw_i
        source_counts[source] += 1
        if source.startswith("fallback"):
            fallback_mole_fraction += yi

    cp_mass_mix = 0.0 if mw_mix <= 0.0 else cp_molar_mix / mw_mix
    dominant_source = source_counts.most_common(1)[0][0]
    return (
        cp_molar_mix,
        cp_mass_mix,
        mw_mix,
        dominant_source,
        _serialize_source_counts(source_counts),
        fallback_mole_fraction,
    )


def gas_mixture_cp(
    solution: EquilibriumSolution,
    species: Sequence[Species],
    temperature_k: float,
    pressure_pa: float,
) -> tuple[float, float, float, str]:
    """Return gas mixture Cp metrics.

    Returns:
    - Cp_molar_mix [J/mol/K]
    - Cp_mass_mix [kJ/kg/K]
    - Mean molecular weight [g/mol]
    - Dominant data source label
    """

    cp_molar_mix, cp_mass_mix, mw_mix, dominant_source, _, _ = gas_mixture_cp_diagnostics(
        solution,
        species,
        temperature_k,
        pressure_pa,
    )
    return cp_molar_mix, cp_mass_mix, mw_mix, dominant_source
