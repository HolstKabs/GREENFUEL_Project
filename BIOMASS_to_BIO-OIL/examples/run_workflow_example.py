"""Example script for running the biomass workflow on an Excel workbook."""

from pathlib import Path

from biomass_pyrolysis_equilibrium import WorkflowConfig, run_workflow
from biomass_pyrolysis_equilibrium.qa.artifacts import export_run_result


def main() -> None:
    workbook = Path("Feedstock_table.xlsx")
    if not workbook.exists():
        raise FileNotFoundError(
            "Expected 'Feedstock_table.xlsx' in current directory. Update path in run_workflow_example.py if needed."
        )

    config = WorkflowConfig()
    run_result = run_workflow(str(workbook), config)

    written_path = export_run_result(run_result, "yield_results.xlsx")
    print(f"Processed rows: {len(run_result.results)}")
    print(f"Unmatched mappings: {len(run_result.unmatched_mappings)}")
    print(f"Output written to {written_path}")


if __name__ == "__main__":
    main()
