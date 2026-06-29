"""Feedstock-level Gibbs minimization executor."""

from __future__ import annotations

from time import perf_counter
from typing import Dict, List, Sequence

import numpy as np
from scipy.optimize import minimize

from ..config import WorkflowConfig
from ..models import EquilibriumSolution, FeedstockRecord, RowWarning, Species, ThermoProperties
from .gibbs_solver import (
    ELEMENTS,
    build_element_matrix,
    detect_unrepresented_elements,
    element_balance_residuals,
    gibbs_objective,
    initial_guesses,
)


class _SolverAttemptTimeout(RuntimeError):
    """Raised when one optimization attempt exceeds wall-time budget."""


def solve_feedstock_equilibrium(
    feedstock: FeedstockRecord,
    thermo: ThermoProperties,
    species: Sequence[Species],
    config: WorkflowConfig,
    temperature_k: float | None = None,
    pressure_pa: float | None = None,
) -> EquilibriumSolution:
    """Solve Gibbs minimization for one feedstock record."""

    run_temperature_k = config.equilibrium.temperature_k if temperature_k is None else float(temperature_k)
    run_pressure_pa = config.thermo.pressure_pa if pressure_pa is None else float(pressure_pa)

    b_vector = {e: float(thermo.element_moles_per_kg_feedstock.get(e, 0.0)) for e in ELEMENTS}
    warnings: List[RowWarning] = list(thermo.warnings)

    missing_elements = detect_unrepresented_elements(species, b_vector)
    if missing_elements:
        msg = f"Species pool does not represent required elements: {', '.join(missing_elements)}"
        warnings.append(RowWarning("MISSING_ELEMENT_SPECIES", msg, severity="error"))
        return EquilibriumSolution(
            feedstock_id=feedstock.feedstock_id,
            temperature_k=run_temperature_k,
            pressure_pa=run_pressure_pa,
            species_moles={sp.name: 0.0 for sp in species},
            element_residuals={e: b_vector[e] for e in ELEMENTS},
            max_residual=max(b_vector.values()) if b_vector else 0.0,
            converged=False,
            g_total_kj=float("inf"),
            solver_message=msg,
            warnings=warnings,
        )

    matrix = build_element_matrix(species)
    b = np.array([b_vector[e] for e in ELEMENTS], dtype=float)

    def objective(x: np.ndarray) -> float:
        return gibbs_objective(
            x,
            species,
            temperature_k=run_temperature_k,
            pressure_pa=run_pressure_pa,
        )

    constraints = [
        {
            "type": "eq",
            "fun": lambda x, row=i: float(np.dot(matrix[row, :], x) - b[row]),
        }
        for i in range(matrix.shape[0])
    ]

    bounds = [(config.equilibrium.min_moles, None) for _ in species]

    best_result = None
    best_objective = float("inf")

    for attempt_index, guess in enumerate(
        initial_guesses(species, b_vector, config.equilibrium.min_moles)
    ):
        if attempt_index >= config.equilibrium.multi_start_attempts:
            break

        attempt_started = perf_counter()

        def _callback(_x: np.ndarray) -> None:
            max_wall_time = config.equilibrium.max_wall_time_seconds_per_attempt
            if max_wall_time is None:
                return
            if max_wall_time < 0:
                return
            if perf_counter() - attempt_started >= max_wall_time:
                raise _SolverAttemptTimeout(
                    f"Attempt {attempt_index + 1} exceeded {max_wall_time:.2f}s wall-time limit."
                )

        try:
            result = minimize(
                objective,
                x0=guess,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                callback=_callback,
                options={
                    "maxiter": config.equilibrium.max_iterations,
                    "ftol": config.equilibrium.tolerance,
                    "disp": False,
                },
            )
        except _SolverAttemptTimeout as timeout_exc:
            warnings.append(
                RowWarning(
                    "SOLVER_ATTEMPT_TIMEOUT",
                    str(timeout_exc),
                    severity="warning",
                )
            )
            continue

        if result.success and result.fun < best_objective:
            best_result = result
            best_objective = float(result.fun)

    if best_result is None:
        warnings.append(
            RowWarning(
                "SOLVER_DID_NOT_CONVERGE",
                "All multi-start attempts failed to converge.",
                severity="error",
            )
        )
        return EquilibriumSolution(
            feedstock_id=feedstock.feedstock_id,
            temperature_k=run_temperature_k,
            pressure_pa=run_pressure_pa,
            species_moles={sp.name: 0.0 for sp in species},
            element_residuals={e: b_vector[e] for e in ELEMENTS},
            max_residual=max(b_vector.values()) if b_vector else 0.0,
            converged=False,
            g_total_kj=float("inf"),
            solver_message="No converged attempt.",
            warnings=warnings,
        )

    n_opt = np.maximum(best_result.x, 0.0)
    residuals = element_balance_residuals(n_opt, species, b_vector)
    max_res = max(residuals.values()) if residuals else 0.0

    if max_res > config.equilibrium.residual_tolerance:
        warnings.append(
            RowWarning(
                "BALANCE_RESIDUAL_HIGH",
                f"Max element residual {max_res:.3e} exceeds tolerance {config.equilibrium.residual_tolerance:.3e}.",
                severity="warning",
            )
        )

    return EquilibriumSolution(
        feedstock_id=feedstock.feedstock_id,
        temperature_k=run_temperature_k,
        pressure_pa=run_pressure_pa,
        species_moles={sp.name: float(n_opt[i]) for i, sp in enumerate(species)},
        element_residuals=residuals,
        max_residual=max_res,
        converged=bool(best_result.success),
        g_total_kj=float(best_result.fun),
        solver_message=str(best_result.message),
        warnings=warnings,
    )
