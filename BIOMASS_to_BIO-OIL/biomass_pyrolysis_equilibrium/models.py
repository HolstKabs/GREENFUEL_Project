"""Domain models used across the workflow."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RowWarning:
    """Structured warning attached to one feedstock row."""

    code: str
    message: str
    severity: str = "warning"


@dataclass
class FeedstockRecord:
    """Normalized feedstock row from the w.proximate+ultimate sheet."""

    feedstock_id: str
    category: str
    subcategory: str
    moisture_pct: float
    volatile_matter_pct: float
    fixed_carbon_pct: float
    ash_pct: float
    c_pct_daf: float
    h_pct_daf: float
    o_pct_daf: float
    n_pct_daf: float
    s_pct_daf: float
    reference: Optional[str] = None
    pyrolysis_suitability: Optional[str] = None
    regionality: Optional[str] = None
    literature_oil_yield_ar_kg_per_kg: Optional[float] = None
    literature_oil_yield_ar_min_kg_per_kg: Optional[float] = None
    literature_oil_yield_ar_max_kg_per_kg: Optional[float] = None
    literature_oil_yield_dry_kg_per_kg: Optional[float] = None
    literature_oil_yield_dry_min_kg_per_kg: Optional[float] = None
    literature_oil_yield_dry_max_kg_per_kg: Optional[float] = None
    literature_oil_yield_daf_kg_per_kg: Optional[float] = None
    literature_oil_yield_daf_min_kg_per_kg: Optional[float] = None
    literature_oil_yield_daf_max_kg_per_kg: Optional[float] = None
    warnings: List[RowWarning] = field(default_factory=list)


@dataclass
class BioOilRecord:
    """Normalized bio-oil row from the bio-oil values sheet."""

    bio_oil_id: str
    category: str
    subcategory: str
    moisture_pct: float
    ash_pct: float
    c_pct_daf: float
    h_pct_daf: float
    o_pct_daf: float
    n_pct_daf: float
    s_pct_daf: float
    lhv_mj_per_kg: Optional[float] = None
    hhv_mj_per_kg: Optional[float] = None
    reference: Optional[str] = None
    regionality: Optional[str] = None
    measurement_or_calculation_true: Optional[bool] = None
    warnings: List[RowWarning] = field(default_factory=list)


@dataclass
class Species:
    """Candidate equilibrium species with elemental composition and properties."""

    name: str
    phase: str
    composition: Dict[str, float]
    molecular_weight_g_per_mol: float
    delta_hf_kj_per_mol: float
    s0_j_per_mol_k: float


@dataclass
class ThermoProperties:
    """Computed thermodynamic properties for a feedstock."""

    feedstock_id: str
    hhv_mj_per_kg: float
    lhv_mj_per_kg: float
    delta_hf_kj_per_kg: float
    delta_sf_j_per_kg_k: float
    delta_gf_kj_per_kg: float
    element_moles_per_kg_feedstock: Dict[str, float]
    warnings: List[RowWarning] = field(default_factory=list)


@dataclass
class EquilibriumSolution:
    """Optimization output for one feedstock at one condition."""

    feedstock_id: str
    temperature_k: float
    pressure_pa: float
    species_moles: Dict[str, float]
    element_residuals: Dict[str, float]
    max_residual: float
    converged: bool
    g_total_kj: float
    solver_message: str
    warnings: List[RowWarning] = field(default_factory=list)


@dataclass
class WorkflowRowResult:
    """Merged row-level output with metadata and QA state."""

    feedstock_id: str
    category: str
    subcategory: str
    oil_yield_kg_per_kg: float
    gas_yield_kg_per_kg: float
    char_yield_kg_per_kg: float
    efficiency_ratio: float
    converged: bool
    max_residual: float
    temperature_k: Optional[float] = None
    pressure_pa: Optional[float] = None
    warnings: List[RowWarning] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowRunResult:
    """Container for full-run tabular outputs and diagnostics."""

    results: List[WorkflowRowResult]
    unmatched_mappings: List[str]
    parse_warnings: List[RowWarning]
    solver_warnings: List[RowWarning]
