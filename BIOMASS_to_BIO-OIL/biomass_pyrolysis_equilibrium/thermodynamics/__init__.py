"""Thermodynamic calculations for biomass and product species."""

from .cp import (
	REFERENCE_TEMPERATURE_K,
	estimate_bio_oil_cp_kj_per_kg_k,
	estimate_char_cp_kj_per_kg_k,
	estimate_feedstock_cp_ar_kj_per_kg_k,
	estimate_feedstock_cp_dry_kj_per_kg_k,
	gas_mixture_cp,
	gas_species_cp_molar_j_per_mol_k,
)
from .properties import compute_feedstock_thermo

__all__ = [
	"compute_feedstock_thermo",
	"REFERENCE_TEMPERATURE_K",
	"estimate_feedstock_cp_dry_kj_per_kg_k",
	"estimate_feedstock_cp_ar_kj_per_kg_k",
	"estimate_bio_oil_cp_kj_per_kg_k",
	"estimate_char_cp_kj_per_kg_k",
	"gas_species_cp_molar_j_per_mol_k",
	"gas_mixture_cp",
]
