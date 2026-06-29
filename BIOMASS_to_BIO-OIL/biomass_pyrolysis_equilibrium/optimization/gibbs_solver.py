"""Gibbs objective and constraint builders."""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from ..models import Species
from ..utils.constants import P0_PA, R_J_PER_MOL_K


ELEMENTS = ("C", "H", "O", "N", "S")


def build_element_matrix(species: Sequence[Species]) -> np.ndarray:
    """Build element stoichiometry matrix A with shape (n_elements, n_species)."""

    matrix = np.zeros((len(ELEMENTS), len(species)), dtype=float)
    for i, element in enumerate(ELEMENTS):
        for j, sp in enumerate(species):
            matrix[i, j] = sp.composition.get(element, 0.0)
    return matrix


def base_gibbs_kj_per_mol(species: Species, temperature_k: float) -> float:
    """Compute g_i^0(T) = h_i^0 - T * s_i^0."""

    return species.delta_hf_kj_per_mol - temperature_k * (species.s0_j_per_mol_k / 1000.0)


def gibbs_objective(
    n: np.ndarray,
    species: Sequence[Species],
    temperature_k: float,
    pressure_pa: float,
) -> float:
    """Compute total Gibbs free energy [kJ] for mixed phases."""

    eps = 1e-20
    gas_idx = [i for i, sp in enumerate(species) if sp.phase == "gas"]
    gas_total = float(np.sum(n[gas_idx])) if gas_idx else 0.0

    g_total = 0.0
    for i, sp in enumerate(species):
        ni = max(float(n[i]), 0.0)
        if ni <= 0.0:
            continue

        mu = base_gibbs_kj_per_mol(sp, temperature_k)
        if sp.phase == "gas" and gas_total > 0.0:
            yi = ni / gas_total
            mu += (R_J_PER_MOL_K * temperature_k / 1000.0) * np.log(max(yi * pressure_pa / P0_PA, eps))

        g_total += ni * mu

    return g_total


def element_balance_residuals(
    n: np.ndarray,
    species: Sequence[Species],
    b_vector: Dict[str, float],
) -> Dict[str, float]:
    """Return absolute element residuals after optimization."""

    matrix = build_element_matrix(species)
    b = np.array([b_vector[e] for e in ELEMENTS], dtype=float)
    residual_vec = np.abs(matrix @ n - b)
    return {element: float(residual_vec[i]) for i, element in enumerate(ELEMENTS)}


def detect_unrepresented_elements(species: Sequence[Species], b_vector: Dict[str, float]) -> List[str]:
    """Detect elements present in feed but absent from species pool."""

    matrix = build_element_matrix(species)
    missing: List[str] = []
    for i, element in enumerate(ELEMENTS):
        if b_vector[element] > 1e-14 and np.allclose(matrix[i, :], 0.0):
            missing.append(element)
    return missing


def initial_guesses(
    species: Sequence[Species],
    b_vector: Dict[str, float],
    min_moles: float,
) -> List[np.ndarray]:
    """Generate deterministic multi-start initial guesses."""

    matrix = build_element_matrix(species)
    b = np.array([b_vector[e] for e in ELEMENTS], dtype=float)

    guesses: List[np.ndarray] = []

    try:
        lsq = np.linalg.lstsq(matrix, b, rcond=None)[0]
        base = np.maximum(lsq, min_moles)
    except np.linalg.LinAlgError:
        base = np.full(len(species), 1.0)

    guesses.append(base)
    guesses.append(np.maximum(base * 0.5, min_moles))

    uniform = np.full(len(species), max(min_moles, float(np.sum(b)) / max(len(species), 1)))
    guesses.append(uniform)
    return guesses
