"""Top-level workflow orchestration for biomass equilibrium analysis."""

from __future__ import annotations

import itertools
from typing import Optional

from ..config import WorkflowConfig
from ..data.parser import parse_input_workbook
from ..models import RowWarning, WorkflowRunResult
from ..optimization.executor import solve_feedstock_equilibrium
from ..optimization.post_processor import to_workflow_row_result
from ..species.candidate_pool import build_candidate_species
from ..thermodynamics.properties import compute_feedstock_thermo
from ..utils.logging_config import get_logger


logger = get_logger(__name__)


def _linspace(start: float, stop: float, points: int) -> list[float]:
    if points < 1:
        raise ValueError("Sweep points must be >= 1.")
    if points == 1:
        return [float(start)]
    step = (stop - start) / (points - 1)
    return [float(start + i * step) for i in range(points)]


def _sweep_conditions(config: WorkflowConfig) -> list[tuple[float, float]]:
    if not config.sweep.enabled:
        return [(config.equilibrium.temperature_k, config.thermo.pressure_pa)]

    if config.sweep.temperature_c_max < config.sweep.temperature_c_min:
        raise ValueError("Sweep temperature_c_max must be >= temperature_c_min.")
    if config.sweep.pressure_bar_max < config.sweep.pressure_bar_min:
        raise ValueError("Sweep pressure_bar_max must be >= pressure_bar_min.")

    temp_c_values = _linspace(
        config.sweep.temperature_c_min,
        config.sweep.temperature_c_max,
        config.sweep.temperature_points,
    )
    pressure_bar_values = _linspace(
        config.sweep.pressure_bar_min,
        config.sweep.pressure_bar_max,
        config.sweep.pressure_points,
    )

    return [
        (temp_c + 273.15, pressure_bar * 100000.0)
        for temp_c, pressure_bar in itertools.product(temp_c_values, pressure_bar_values)
    ]


def run_workflow(excel_path: str, config: Optional[WorkflowConfig] = None) -> WorkflowRunResult:
    """Run the complete feedstock-to-equilibrium workflow."""

    cfg = WorkflowConfig() if config is None else config
    parsed = parse_input_workbook(excel_path, cfg)
    conditions = _sweep_conditions(cfg)

    row_results = []
    parse_warnings = list(parsed.parse_warnings)
    solver_warnings: list[RowWarning] = []

    def _finalize_result() -> WorkflowRunResult:
        return WorkflowRunResult(
            results=row_results,
            unmatched_mappings=parsed.unmatched_feedstocks,
            parse_warnings=parse_warnings,
            solver_warnings=solver_warnings,
        )

    for feedstock in parsed.feedstocks:
        try:
            mapped_bio_oil = parsed.feedstock_to_bio_oil.get(feedstock.feedstock_id)

            species, species_warnings = build_candidate_species(feedstock, mapped_bio_oil, cfg)
            thermo = compute_feedstock_thermo(feedstock, cfg)
            thermo.warnings.extend(species_warnings)

            for temperature_k, pressure_pa in conditions:
                solution = solve_feedstock_equilibrium(
                    feedstock,
                    thermo,
                    species,
                    cfg,
                    temperature_k=temperature_k,
                    pressure_pa=pressure_pa,
                )
                solver_warnings.extend(solution.warnings)

                row_result = to_workflow_row_result(feedstock, solution, species, thermo.hhv_mj_per_kg)
                row_results.append(row_result)

        except KeyboardInterrupt:
            warning = RowWarning(
                code="RUN_INTERRUPTED",
                message=(
                    "Workflow interrupted during optimization; "
                    "returning partial results collected so far."
                ),
                severity="warning",
            )
            parse_warnings.append(warning)
            logger.warning("Workflow interrupted; returning partial results.")
            return _finalize_result()

        except Exception as exc:  # noqa: BLE001
            warning = RowWarning(
                code="ROW_RUNTIME_EXCEPTION",
                message=f"Feedstock '{feedstock.feedstock_id}' failed with exception: {exc}",
                severity="error",
            )
            parse_warnings.append(warning)
            logger.exception("Feedstock row failed: %s", feedstock.feedstock_id)

    return _finalize_result()
