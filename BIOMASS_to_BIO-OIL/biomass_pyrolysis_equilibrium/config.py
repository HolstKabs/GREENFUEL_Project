"""Configuration models for the biomass pyrolysis equilibrium workflow."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class SheetNames:
    """Excel sheet names used by the workflow."""

    feedstock: str = "w.proximate+ultimate"
    bio_oil: str = "bio-oil values"


@dataclass(frozen=True)
class ProcessingConfig:
    """Data cleaning and mapping behavior."""

    decimal_separator: str = ","
    range_separators: tuple[str, ...] = ("-", "–", "to")
    midpoint_for_ranges: bool = True
    incomplete_range_use_single_bound: bool = True
    canonical_match_min_token_overlap: float = 0.4
    enable_levenshtein_matching: bool = True
    levenshtein_min_ratio: float = 82.0
    matching_synonym_groups: tuple[tuple[str, ...], ...] = (
        ("wood", "timber", "sawdust"),
    )


@dataclass(frozen=True)
class ThermoConfig:
    """Thermodynamic settings and assumptions."""

    reference_temperature_k: float = 298.15
    pressure_pa: float = 101_325.0
    latent_heat_water_mj_per_kg: float = 2.26
    treat_ash_as_inert: bool = True
    use_temperature_adjusted_mu: bool = True


@dataclass(frozen=True)
class EquilibriumConfig:
    """Optimization settings for Gibbs minimization."""

    temperature_k: float = 773.15
    max_iterations: int = 1000
    tolerance: float = 1e-8
    residual_tolerance: float = 1e-6
    multi_start_attempts: int = 3
    max_wall_time_seconds_per_attempt: float | None = 5.0
    min_moles: float = 1e-12


@dataclass(frozen=True)
class SweepConfig:
    """Optional temperature-pressure sweep settings."""

    enabled: bool = False
    temperature_c_min: float = 300.0
    temperature_c_max: float = 800.0
    temperature_points: int = 11
    pressure_bar_min: float = 1.0
    pressure_bar_max: float = 5.0
    pressure_points: int = 5


@dataclass(frozen=True)
class SpeciesConfig:
    """Species pool and fallback behavior."""

    gas_species: List[str] = field(
        default_factory=lambda: [
            "CO2",
            "CO",
            "CH4",
            "H2",
            "H2O",
            "N2",
            "NH3",
            "H2S",
            "SO2",
            "O2",
        ]
    )
    include_char_species: bool = True
    include_generic_bio_oil_fallback: bool = True
    generic_bio_oil_formula: Dict[str, float] = field(
        default_factory=lambda: {"C": 8.0, "H": 8.0, "O": 3.0, "N": 0.0, "S": 0.0}
    )


@dataclass(frozen=True)
class WorkflowConfig:
    """Top-level workflow configuration."""

    sheets: SheetNames = field(default_factory=SheetNames)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    thermo: ThermoConfig = field(default_factory=ThermoConfig)
    equilibrium: EquilibriumConfig = field(default_factory=EquilibriumConfig)
    sweep: SweepConfig = field(default_factory=SweepConfig)
    species: SpeciesConfig = field(default_factory=SpeciesConfig)
    required_feedstock_columns: tuple[str, ...] = (
        "Feedstock Category",
        "Feedstock Subcategory",
        "M",
        "VM",
        "FC",
        "Ash",
        "C",
        "H",
        "O",
        "N",
        "S",
    )
    required_bio_oil_columns: tuple[str, ...] = (
        "Bio-oil Category",
        "Bio-oil Subcategory",
        "M",
        "Ash",
        "C",
        "H",
        "O",
        "N",
        "S",
    )
