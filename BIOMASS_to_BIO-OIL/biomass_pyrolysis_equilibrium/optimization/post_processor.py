"""Post-processing for yields and efficiency metrics."""

from __future__ import annotations

from typing import Dict, Sequence

from ..models import EquilibriumSolution, FeedstockRecord, Species, WorkflowRowResult
from ..thermodynamics.cp import (
    REFERENCE_TEMPERATURE_K,
    estimate_bio_oil_cp_kj_per_kg_k,
    estimate_char_cp_kj_per_kg_k,
    estimate_feedstock_cp_ar_kj_per_kg_k,
    estimate_feedstock_cp_dry_kj_per_kg_k,
    gas_mixture_cp_diagnostics,
)
from ..thermodynamics.heating_value import compute_hhv_mj_per_kg as _compute_hhv_mj_per_kg


LHV_BY_SPECIES_MJ_PER_KG = {
    "CH4": 50.0,
    "H2": 120.0,
    "CO": 10.1,
    "NH3": 18.6,
    "H2S": 15.3,
    "BIO_OIL": 17.0,
    "CHAR": 32.8,
}


# Fallback bio-oil HHV when no composition data is available.
# Representative mid-range for as-produced fast-pyrolysis oil (~20-25 wt% water).
HHV_BIO_OIL_FALLBACK_MJ_PER_KG: float = 19.5

# Atomic weights [g/mol] used for composition -> weight-percent conversion.
_ATOMIC_WEIGHTS: Dict[str, float] = {"C": 12.011, "H": 1.008, "O": 15.999, "N": 14.007, "S": 32.06}


def _bio_oil_hhv_from_composition(composition: Dict[str, float]) -> tuple[float, str]:
    """Compute bio-oil HHV [MJ/kg] from atomic formula using Channiwala-Parikh.

    `composition` maps element symbol -> atom count in the pseudocomponent formula
    (e.g. {"C": 8, "H": 8, "O": 3}).  Converts to weight-percent, then applies
    the same Channiwala-Parikh correlation used for feedstocks.  Returns
    (hhv_mj_per_kg, source_label).  Falls back to HHV_BIO_OIL_FALLBACK_MJ_PER_KG
    when composition is empty or yields zero mass.
    """
    mass = {el: composition.get(el, 0.0) * _ATOMIC_WEIGHTS[el] for el in ("C", "H", "O", "N", "S")}
    total_mass = sum(mass.values())
    if total_mass < 1e-9:
        return HHV_BIO_OIL_FALLBACK_MJ_PER_KG, "fallback:19.5_mj_per_kg"
    hhv = _compute_hhv_mj_per_kg(
        c_pct=mass["C"] / total_mass * 100,
        h_pct=mass["H"] / total_mass * 100,
        o_pct=mass["O"] / total_mass * 100,
        n_pct=mass["N"] / total_mass * 100,
        s_pct=mass["S"] / total_mass * 100,
        ash_pct=0.0,
    )
    return hhv, "channiwala_parikh:bio_oil_composition"


PARSER_ASSIST_PREFIXES = (
    "FEED_",
    "OIL_",
    "MAP_",
)


def _species_lookup(species: Sequence[Species]) -> Dict[str, Species]:
    return {sp.name: sp for sp in species}


def _phase_mass_yields(solution: EquilibriumSolution, species: Sequence[Species], feedstock: FeedstockRecord) -> tuple[float, float, float]:
    by_name = _species_lookup(species)

    gas_mass = 0.0
    oil_mass = 0.0
    char_mass = 0.0

    for name, n_mol in solution.species_moles.items():
        sp = by_name.get(name)
        if sp is None:
            continue
        mass_kg = n_mol * sp.molecular_weight_g_per_mol / 1000.0
        if sp.phase == "gas":
            gas_mass += mass_kg
        elif sp.phase == "liquid_oil":
            oil_mass += mass_kg
        elif sp.phase == "solid_char":
            char_mass += mass_kg

    # Carry ash as inert solid in char output for reporting consistency.
    char_mass += max(0.0, feedstock.ash_pct / 100.0)

    return oil_mass, gas_mass, char_mass


def _output_energy_mj_per_kg_feedstock(solution: EquilibriumSolution, species: Sequence[Species]) -> float:
    by_name = _species_lookup(species)
    output_energy = 0.0
    for name, n_mol in solution.species_moles.items():
        sp = by_name.get(name)
        if sp is None:
            continue
        mass_kg = n_mol * sp.molecular_weight_g_per_mol / 1000.0
        output_energy += mass_kg * LHV_BY_SPECIES_MJ_PER_KG.get(name, 0.0)
    return output_energy


def _energy_efficiency(solution: EquilibriumSolution, species: Sequence[Species], feedstock_hhv_mj_per_kg: float) -> float:
    output_energy = _output_energy_mj_per_kg_feedstock(solution, species)
    input_energy = max(feedstock_hhv_mj_per_kg, 1e-9)
    return output_energy / input_energy


def _unique_preserve_order(values: Sequence[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _parser_assist_metadata(solution: EquilibriumSolution) -> Dict[str, str]:
    assists = [w for w in solution.warnings if w.code.startswith(PARSER_ASSIST_PREFIXES)]
    if not assists:
        return {
            "parser_assist_count": "0",
            "parser_assist_codes": "",
            "parser_assist_messages": "",
        }

    codes = _unique_preserve_order([w.code for w in assists])
    messages = _unique_preserve_order([w.message for w in assists])
    return {
        "parser_assist_count": str(len(assists)),
        "parser_assist_codes": "|".join(codes),
        "parser_assist_messages": " || ".join(messages),
    }


def _cp_energy_metadata(
    feedstock: FeedstockRecord,
    solution: EquilibriumSolution,
    species: Sequence[Species],
    oil_yield: float,
    gas_yield: float,
    char_yield: float,
    feedstock_hhv_mj_per_kg: float,
    output_energy_mj_per_kg: float,
    efficiency_ratio: float,
) -> Dict[str, str]:
    by_name = _species_lookup(species)
    bio_oil_species = by_name.get("BIO_OIL")
    bio_oil_composition = {"C": 8.0, "H": 8.0, "O": 3.0}
    cp_bio_oil_source = "fallback:generic_bio_oil_composition"
    if bio_oil_species is not None and bio_oil_species.composition:
        bio_oil_composition = dict(bio_oil_species.composition)
        cp_bio_oil_source = "correlation:bio_oil_pseudocomp_v1"

    hhv_bio_oil_mj_per_kg, hhv_bio_oil_source = _bio_oil_hhv_from_composition(bio_oil_composition)

    cp_feedstock_dry = estimate_feedstock_cp_dry_kj_per_kg_k(feedstock, solution.temperature_k)
    cp_feedstock_ar = estimate_feedstock_cp_ar_kj_per_kg_k(feedstock, solution.temperature_k)
    cp_bio_oil = estimate_bio_oil_cp_kj_per_kg_k(bio_oil_composition, solution.temperature_k)
    cp_char = estimate_char_cp_kj_per_kg_k(solution.temperature_k)
    cp_gas_molar, cp_gas_mass, gas_mw, gas_cp_source, gas_cp_source_counts, gas_cp_fallback_fraction = gas_mixture_cp_diagnostics(
        solution,
        species,
        solution.temperature_k,
        solution.pressure_pa,
    )

    delta_t_k = max(0.0, solution.temperature_k - REFERENCE_TEMPERATURE_K)
    sensible_heat_feedstock_mj = cp_feedstock_ar * delta_t_k / 1000.0
    sensible_heat_products_mj = (
        oil_yield * cp_bio_oil + gas_yield * cp_gas_mass + char_yield * cp_char
    ) * delta_t_k / 1000.0

    net_fuel_energy_mj_per_kg = output_energy_mj_per_kg - sensible_heat_feedstock_mj
    input_energy_mj_per_kg = max(feedstock_hhv_mj_per_kg, 1e-9)
    gross_energy_efficiency_ratio = output_energy_mj_per_kg / input_energy_mj_per_kg
    gross_efficiency_consistency_abs_error = abs(gross_energy_efficiency_ratio - efficiency_ratio)
    net_energy_efficiency_ratio = net_fuel_energy_mj_per_kg / input_energy_mj_per_kg
    net_minus_gross_efficiency_ratio = net_energy_efficiency_ratio - gross_energy_efficiency_ratio

    energy_accounting_status = "OK"
    if net_fuel_energy_mj_per_kg > output_energy_mj_per_kg + 1e-9:
        energy_accounting_status = "WARN_NET_GT_GROSS"
    elif gross_efficiency_consistency_abs_error > 1e-10:
        energy_accounting_status = "WARN_GROSS_MISMATCH"

    return {
        "cp_feedstock_dry_kj_per_kg_k": str(cp_feedstock_dry),
        "cp_feedstock_dry_source": "correlation:feedstock_dry_v1",
        "cp_feedstock_ar_kj_per_kg_k": str(cp_feedstock_ar),
        "cp_feedstock_ar_source": "correlation:feedstock_moisture_mix_v1",
        "cp_bio_oil_kj_per_kg_k": str(cp_bio_oil),
        "cp_bio_oil_source": cp_bio_oil_source,
        "cp_char_kj_per_kg_k": str(cp_char),
        "cp_char_source": "correlation:char_linear_v1",
        "cp_gas_molar_j_per_mol_k": str(cp_gas_molar),
        "cp_gas_mass_kj_per_kg_k": str(cp_gas_mass),
        "gas_mixture_mw_g_per_mol": str(gas_mw),
        "cp_gas_source": gas_cp_source,
        "cp_gas_source_counts": gas_cp_source_counts,
        "cp_gas_fallback_fraction": str(gas_cp_fallback_fraction),
        "delta_t_from_ref_k": str(delta_t_k),
        "input_feedstock_hhv_mj_per_kg": str(input_energy_mj_per_kg),
        "sensible_heat_feedstock_mj_per_kg": str(sensible_heat_feedstock_mj),
        "sensible_heat_products_mj_per_kg": str(sensible_heat_products_mj),
        "output_fuel_energy_mj_per_kg": str(output_energy_mj_per_kg),
        "gross_energy_efficiency_ratio": str(gross_energy_efficiency_ratio),
        "gross_efficiency_consistency_abs_error": str(gross_efficiency_consistency_abs_error),
        "net_fuel_energy_mj_per_kg": str(net_fuel_energy_mj_per_kg),
        "net_energy_efficiency_ratio": str(net_energy_efficiency_ratio),
        "net_minus_gross_efficiency_ratio": str(net_minus_gross_efficiency_ratio),
        "energy_accounting_status": energy_accounting_status,
        # --- kg biomass per 1 MJ of usable bio-oil (HHV basis) ---
        # f = oil_yield           [kg oil / kg biomass]
        # E = f x HHV_bio_oil     [MJ / kg biomass]
        # m = 1 / E               [kg biomass / MJ bio-oil]
        "bio_oil_hhv_mj_per_kg": str(hhv_bio_oil_mj_per_kg),
        "bio_oil_hhv_source": hhv_bio_oil_source,
        "bio_oil_energy_hhv_mj_per_kg_biomass": str(oil_yield * hhv_bio_oil_mj_per_kg),
        "kg_biomass_per_mj_bio_oil_hhv": str(1.0 / max(oil_yield * hhv_bio_oil_mj_per_kg, 1e-9)),
    }


def to_workflow_row_result(
    feedstock: FeedstockRecord,
    solution: EquilibriumSolution,
    species: Sequence[Species],
    feedstock_hhv_mj_per_kg: float,
) -> WorkflowRowResult:
    """Convert solver output to reporting row with yields and metadata."""

    oil_yield, gas_yield, char_yield = _phase_mass_yields(solution, species, feedstock)
    output_energy_mj_per_kg = _output_energy_mj_per_kg_feedstock(solution, species)
    efficiency_ratio = _energy_efficiency(solution, species, feedstock_hhv_mj_per_kg)

    metadata = {
        "reference": "" if feedstock.reference is None else feedstock.reference,
        "regionality": "" if feedstock.regionality is None else feedstock.regionality,
        "pyrolysis_suitability": "" if feedstock.pyrolysis_suitability is None else feedstock.pyrolysis_suitability,
        "feedstock_moisture_pct_ar": str(feedstock.moisture_pct),
        "feedstock_ash_pct_ar": str(feedstock.ash_pct),
        "feedstock_c_pct_daf": str(feedstock.c_pct_daf),
        "feedstock_h_pct_daf": str(feedstock.h_pct_daf),
        "feedstock_o_pct_daf": str(feedstock.o_pct_daf),
        "feedstock_n_pct_daf": str(feedstock.n_pct_daf),
        "feedstock_s_pct_daf": str(feedstock.s_pct_daf),
        "literature_oil_yield_ar_kg_per_kg": ""
        if feedstock.literature_oil_yield_ar_kg_per_kg is None
        else str(feedstock.literature_oil_yield_ar_kg_per_kg),
        "literature_oil_yield_ar_min_kg_per_kg": ""
        if feedstock.literature_oil_yield_ar_min_kg_per_kg is None
        else str(feedstock.literature_oil_yield_ar_min_kg_per_kg),
        "literature_oil_yield_ar_max_kg_per_kg": ""
        if feedstock.literature_oil_yield_ar_max_kg_per_kg is None
        else str(feedstock.literature_oil_yield_ar_max_kg_per_kg),
        "literature_oil_yield_dry_kg_per_kg": ""
        if feedstock.literature_oil_yield_dry_kg_per_kg is None
        else str(feedstock.literature_oil_yield_dry_kg_per_kg),
        "literature_oil_yield_dry_min_kg_per_kg": ""
        if feedstock.literature_oil_yield_dry_min_kg_per_kg is None
        else str(feedstock.literature_oil_yield_dry_min_kg_per_kg),
        "literature_oil_yield_dry_max_kg_per_kg": ""
        if feedstock.literature_oil_yield_dry_max_kg_per_kg is None
        else str(feedstock.literature_oil_yield_dry_max_kg_per_kg),
        "literature_oil_yield_daf_kg_per_kg": ""
        if feedstock.literature_oil_yield_daf_kg_per_kg is None
        else str(feedstock.literature_oil_yield_daf_kg_per_kg),
        "literature_oil_yield_daf_min_kg_per_kg": ""
        if feedstock.literature_oil_yield_daf_min_kg_per_kg is None
        else str(feedstock.literature_oil_yield_daf_min_kg_per_kg),
        "literature_oil_yield_daf_max_kg_per_kg": ""
        if feedstock.literature_oil_yield_daf_max_kg_per_kg is None
        else str(feedstock.literature_oil_yield_daf_max_kg_per_kg),
    }
    metadata.update(_parser_assist_metadata(solution))
    metadata.update(
        _cp_energy_metadata(
            feedstock,
            solution,
            species,
            oil_yield,
            gas_yield,
            char_yield,
            feedstock_hhv_mj_per_kg,
            output_energy_mj_per_kg,
            efficiency_ratio,
        )
    )

    return WorkflowRowResult(
        feedstock_id=feedstock.feedstock_id,
        category=feedstock.category,
        subcategory=feedstock.subcategory,
        oil_yield_kg_per_kg=oil_yield,
        gas_yield_kg_per_kg=gas_yield,
        char_yield_kg_per_kg=char_yield,
        efficiency_ratio=efficiency_ratio,
        converged=solution.converged,
        max_residual=solution.max_residual,
        temperature_k=solution.temperature_k,
        pressure_pa=solution.pressure_pa,
        warnings=list(solution.warnings),
        metadata=metadata,
    )
