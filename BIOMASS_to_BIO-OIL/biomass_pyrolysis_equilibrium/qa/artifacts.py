"""Export workflow outputs to Excel or CSV artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .plotting import save_default_plots
from .reporting import workflow_result_to_dataframes
from ..models import WorkflowRunResult


def _write_excel(frames: dict[str, object], output: Path) -> None:
    """Write multi-sheet Excel output."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with __import__("pandas").ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in frames.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)


def _timestamped_output_path(output: Path) -> Path:
    """Create a timestamped output path to avoid file name collisions."""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = output.with_suffix("")
    return output.with_name(f"{stem.name}_{ts}{output.suffix}")


def export_plot_artifacts(run_result: WorkflowRunResult, output_dir: str) -> list[Path]:
    """Export default analysis plots based on result rows."""

    frames = workflow_result_to_dataframes(run_result)
    return save_default_plots(frames["results"], output_dir)


def export_run_result(
    run_result: WorkflowRunResult,
    output_path: str,
    *,
    include_plots: bool = False,
    plots_output_dir: str | None = None,
) -> Path:
    """Export outputs and diagnostics to xlsx or csv files.

    If `output_path` ends in `.xlsx`, a timestamped multi-sheet workbook is created.
    Otherwise a set of CSV files with suffixes are written.

    Returns the primary written artifact path.
    """

    output = Path(output_path)
    frames = workflow_result_to_dataframes(run_result)

    if output.suffix.lower() == ".xlsx":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = output.with_suffix("").name
        output_dir = output.parent / f"{stem}_{ts}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write the full detailed workbook inside the folder.
        detailed_frames = {k: v for k, v in frames.items() if k != "peak_results"}
        _write_excel(detailed_frames, output_dir / f"{stem}.xlsx")

        # Write the clean 1-row-per-biomass summary inside the same folder.
        if "peak_results" in frames and not frames["peak_results"].empty:
            _write_excel({"peak_results": frames["peak_results"]}, output_dir / f"{stem}_clean.xlsx")

        if include_plots:
            target_plots_dir = plots_output_dir or str(output_dir)
            export_plot_artifacts(run_result, target_plots_dir)

        return output_dir

    stem = output.with_suffix("")
    output.parent.mkdir(parents=True, exist_ok=True)
    for name, df in frames.items():
        df.to_csv(stem.parent / f"{stem.name}_{name}.csv", index=False)
    if include_plots:
        target_plots_dir = plots_output_dir or str(stem) + "_plots"
        export_plot_artifacts(run_result, target_plots_dir)
    return stem.parent / f"{stem.name}_results.csv"
