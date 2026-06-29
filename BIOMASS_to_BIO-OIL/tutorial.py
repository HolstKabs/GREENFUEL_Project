"""Tutorial script: run the biomass pyrolysis equilibrium workflow."""

import subprocess
import sys
from pathlib import Path

from biomass_pyrolysis_equilibrium import WorkflowConfig, run_workflow
from biomass_pyrolysis_equilibrium.config import EquilibriumConfig, SweepConfig
from biomass_pyrolysis_equilibrium.qa.artifacts import export_run_result
from tutorial_workbook_paths import get_selected_workbook_path


def main() -> None:
    workbook = get_selected_workbook_path()
    if not workbook.exists():
        raise FileNotFoundError(
            (
                f"Configured workbook path '{workbook}' does not exist. "
                "Set ACTIVE_WORKBOOK_PATH_KEY and WORKBOOK_PATHS in tutorial_workbook_paths.py."
            )
        )
    if not workbook.is_file():
        raise ValueError(
            (
                f"Configured workbook path '{workbook}' is not a file. "
                "Set WORKBOOK_PATHS[...] to a specific Excel file, e.g. '...\\Feedstock_table - USE THIS ONE.xlsx'."
            )
        )
    print(f"Using workbook: {workbook}")

    enable_sweep = True
    fast_tutorial_mode = False
    realism_mode = True

    if enable_sweep:
        if realism_mode:
            # Atmospheric operation with denser temperature sampling gives more robust theoretical estimates.
            sweep = SweepConfig(
                enabled=True,
                temperature_c_min=350.0,
                temperature_c_max=650.0,
                temperature_points=13,
                pressure_bar_min=1.0,
                pressure_bar_max=1.0,
                pressure_points=1,
            )
        else:
            sweep = SweepConfig(
                enabled=True,
                temperature_c_min=300.0,
                temperature_c_max=(700.0 if fast_tutorial_mode else 800.0),
                temperature_points=(3 if fast_tutorial_mode else 11),
                pressure_bar_min=1.0,
                pressure_bar_max=(1.0 if fast_tutorial_mode else 5.0),
                pressure_points=(1 if fast_tutorial_mode else 5),
            )
    else:
        sweep = SweepConfig(enabled=False)

    if realism_mode:
        equilibrium = EquilibriumConfig(
            max_iterations=1800,
            multi_start_attempts=8,
            max_wall_time_seconds_per_attempt=4.0,
            residual_tolerance=1e-7,
        )
    elif fast_tutorial_mode:
        equilibrium = EquilibriumConfig(
            max_iterations=120,
            multi_start_attempts=1,
            max_wall_time_seconds_per_attempt=0.25,
        )
    else:
        equilibrium = EquilibriumConfig()

    config = WorkflowConfig(sweep=sweep, equilibrium=equilibrium)

    conditions_per_feedstock = (
        sweep.temperature_points * sweep.pressure_points if sweep.enabled else 1
    )
    print(f"Fast tutorial mode: {fast_tutorial_mode}")
    print(f"Realism mode: {realism_mode}")
    print(f"Sweep conditions per feedstock: {conditions_per_feedstock}")

    result = run_workflow(str(workbook), config)
    output_dir = export_run_result(result, "yield_results.xlsx", include_plots=True)
    plot_paths = list(output_dir.glob("*.png")) if output_dir.is_dir() else []

    print(f"Processed rows: {len(result.results)}")
    print(f"Unmatched mappings: {len(result.unmatched_mappings)}")
    interrupted = any(w.code == "RUN_INTERRUPTED" for w in result.parse_warnings)
    if interrupted:
        print("Run was interrupted and returned partial results.")
    print(f"All outputs written to: {output_dir}")
    print(f"  - yield_results.xlsx (detailed)")
    print(f"  - yield_results_clean.xlsx (peak summary)")
    print(f"  - {len(plot_paths)} plot(s)")

    excel_generator_script = Path(__file__).with_name("excel_generator.py")
    if excel_generator_script.exists():
        print("Running excel_generator.py to create categorized Excel output...")
        subprocess.run([sys.executable, str(excel_generator_script)], check=True)
    else:
        print(
            "Skipped excel_generator.py: script not found next to tutorial.py."
        )


if __name__ == "__main__":
    main()