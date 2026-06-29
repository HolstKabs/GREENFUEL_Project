"""Base species registry used by equilibrium solver."""

from __future__ import annotations

from typing import Dict

from ..config import WorkflowConfig
from ..models import Species
from ..utils.constants import ATOMIC_WEIGHTS


def _mw_from_composition(composition: Dict[str, float]) -> float:
    return sum(ATOMIC_WEIGHTS[element] * coeff for element, coeff in composition.items())


def base_species_registry(config: WorkflowConfig) -> Dict[str, Species]:
    """Return canonical gas and solid species entries."""

    registry = {
        "CO2": Species("CO2", "gas", {"C": 1, "O": 2}, _mw_from_composition({"C": 1, "O": 2}), -393.52, 213.79),
        "CO": Species("CO", "gas", {"C": 1, "O": 1}, _mw_from_composition({"C": 1, "O": 1}), -110.53, 197.66),
        "CH4": Species("CH4", "gas", {"C": 1, "H": 4}, _mw_from_composition({"C": 1, "H": 4}), -74.87, 186.25),
        "H2": Species("H2", "gas", {"H": 2}, _mw_from_composition({"H": 2}), 0.0, 130.68),
        "H2O": Species("H2O", "gas", {"H": 2, "O": 1}, _mw_from_composition({"H": 2, "O": 1}), -241.826, 188.84),
        "N2": Species("N2", "gas", {"N": 2}, _mw_from_composition({"N": 2}), 0.0, 191.5),
        "NH3": Species("NH3", "gas", {"N": 1, "H": 3}, _mw_from_composition({"N": 1, "H": 3}), -46.11, 192.77),
        "H2S": Species("H2S", "gas", {"H": 2, "S": 1}, _mw_from_composition({"H": 2, "S": 1}), -20.6, 205.7),
        "SO2": Species("SO2", "gas", {"S": 1, "O": 2}, _mw_from_composition({"S": 1, "O": 2}), -296.81, 248.2),
        "O2": Species("O2", "gas", {"O": 2}, _mw_from_composition({"O": 2}), 0.0, 205.15),
    }

    if config.species.include_char_species:
        registry["CHAR"] = Species("CHAR", "solid_char", {"C": 1}, _mw_from_composition({"C": 1}), 0.0, 5.74)

    return registry
