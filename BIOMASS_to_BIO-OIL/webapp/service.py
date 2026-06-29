"""Service layer for the Biomass Pyrolysis Explorer.

Loading strategy (in order):
  1. Read the most recent pair of output Excel files produced by tutorial.py
     (yield_results_*.xlsx + yield_results_clean_*.xlsx) — instant, no solver.
  2. If no output files exist, fall back to running the live solver against the
     input workbook.  The fast_mode toggle only affects this fallback path.

The dict returned by load_results() always has the same keys as
workflow_result_to_dataframes(), plus an extra "_source_info" key that pages
can use to show the user where the data came from.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st


def _read_all_sheets(path) -> dict[str, pd.DataFrame] | None:
    """Read every sheet of an xlsx into a {name: DataFrame} dict.

    Resilient to OneDrive / Excel file locks: if a direct open is denied
    (PermissionError), copy the file to a temp location and read the copy.
    Returns None if the file cannot be read at all.
    """
    try:
        return pd.read_excel(path, sheet_name=None)
    except (PermissionError, OSError):
        pass
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = os.path.join(td, Path(path).name)
            shutil.copy2(path, tmp)
            return pd.read_excel(tmp, sheet_name=None)
    except Exception:  # noqa: BLE001
        return None

# Ensure the project root (parent of webapp/) is on sys.path so that
# `biomass_pyrolysis_equilibrium` is importable regardless of where
# Streamlit was launched from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# The consolidated GREENFUEL_PROJECT root (one level above BIOMASS_to_BIO-OIL).
# It also holds LCA_PROJECT/, where the LCA + Monte Carlo result folders live.
_GREENFUEL_ROOT = _PROJECT_ROOT.parent

from biomass_pyrolysis_equilibrium import WorkflowConfig, run_workflow  # noqa: E402
from biomass_pyrolysis_equilibrium.config import SweepConfig
from biomass_pyrolysis_equilibrium.qa.reporting import workflow_result_to_dataframes

# ---------------------------------------------------------------------------
# Output-file loading (primary path)
# ---------------------------------------------------------------------------

# Sheets written to the full yield_results_*.xlsx file
_FULL_SHEETS = ("results", "warnings", "realism_summary", "percentiles_by_feedstock", "oil_yield_mismatch")


def _resolve_first_existing_dir(candidates: list[Path]) -> Path | None:
    """Return the first existing directory from candidates, or None."""
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _resolve_results_dir(candidates: list[Path], pattern: str) -> Path | None:
    """First existing candidate dir; else search LCA_PROJECT/ for *pattern* files.

    Keeps result discovery working no matter where inside the consolidated
    project the LCA / Monte Carlo output folders end up living, so the webapp
    runs entirely from this folder.
    """
    found = _resolve_first_existing_dir(candidates)
    if found is not None:
        return found
    search_root = _GREENFUEL_ROOT / "LCA_PROJECT"
    if search_root.exists():
        for match in sorted(search_root.rglob(pattern)):
            return match.parent
    return None


def _find_latest_output_pair() -> tuple[Path, Path] | None:
    """Return (full_path, clean_path) for the most recent output files, or None.

    Looks inside timestamped folders (yield_results_YYYYMMDD_HHMMSS/) for
    yield_results.xlsx and yield_results_clean.xlsx.
    """
    dirs = list_result_dirs()
    if not dirs:
        return None
    # First entry is newest (list_result_dirs returns newest-first)
    folder_name, _ = dirs[0]
    return _pair_from_dir(folder_name)


def list_result_dirs() -> list[tuple[str, str]]:
    """Return all available result folders as (folder_name, display_label) pairs, newest first."""
    result_dirs = sorted(
        [p for p in _PROJECT_ROOT.iterdir() if p.is_dir() and p.name.startswith("yield_results_")],
        reverse=True,
    )
    out = []
    for d in result_dirs:
        if (d / "yield_results.xlsx").exists() and (d / "yield_results_clean.xlsx").exists():
            label = _timestamp_from_path(d / "yield_results.xlsx")
            out.append((d.name, label))
    return out


def _pair_from_dir(folder_name: str) -> tuple[Path, Path] | None:
    """Return (full_path, clean_path) for a specific result folder name, or None."""
    d = _PROJECT_ROOT / folder_name
    full_path = d / "yield_results.xlsx"
    clean_path = d / "yield_results_clean.xlsx"
    if full_path.exists() and clean_path.exists():
        return full_path, clean_path
    return None


@st.cache_data(show_spinner=False)
def _load_from_files(full_path: str, clean_path: str) -> Dict[str, pd.DataFrame]:
    """Read DataFrames from the two output xlsx files."""
    dfs: Dict[str, pd.DataFrame] = {}

    full_xl = pd.ExcelFile(full_path)
    for sheet in _FULL_SHEETS:
        if sheet in full_xl.sheet_names:
            dfs[sheet] = full_xl.parse(sheet)

    clean_xl = pd.ExcelFile(clean_path)
    if "peak_results" in clean_xl.sheet_names:
        dfs["peak_results"] = clean_xl.parse("peak_results")

    return dfs


def _timestamp_from_path(path: Path) -> str:
    """Parse the YYYYMMDD_HHMMSS suffix from the parent folder name."""
    # e.g. .../yield_results_20260424_123151/yield_results.xlsx → "24 Apr 2026, 12:31"
    folder_name = path.parent.name  # yield_results_20260424_123151
    parts = folder_name.split("_")
    try:
        dt = datetime.strptime(f"{parts[-2]}_{parts[-1]}", "%Y%m%d_%H%M%S")
        return dt.strftime("%d %b %Y, %H:%M").lstrip("0")
    except (ValueError, IndexError):
        return folder_name


# ---------------------------------------------------------------------------
# Live-solver fallback (used only when no output files exist)
# ---------------------------------------------------------------------------

def _find_workbook() -> Path:
    """Locate the input workbook for the live-solver fallback."""
    candidates: list[Path] = []

    # Reuse the same workbook configuration as tutorial.py when available.
    try:
        from tutorial_workbook_paths import get_selected_workbook_path

        selected = get_selected_workbook_path()
        if selected.exists() and selected.is_file():
            candidates.append(selected)
    except Exception:  # noqa: BLE001
        pass

    candidates.extend(
        [
            _PROJECT_ROOT / "Feedstock_reference" / "Feedstock_table - USE THIS ONE.xlsx",
            _PROJECT_ROOT / "demo_data" / "demo_workbook.xlsx",
        ]
    )

    # Final fallback: pick the first feedstock workbook found anywhere in the project tree.
    candidates.extend(sorted(_PROJECT_ROOT.rglob("Feedstock_table*.xlsx")))

    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "No output files and no input workbook found.  "
        "Run tutorial.py first to generate output files, or place the input "
        f"workbook at {_PROJECT_ROOT / 'Feedstock_reference' / 'Feedstock_table - USE THIS ONE.xlsx'}."
    )


def _build_config(fast_mode: bool) -> WorkflowConfig:
    if fast_mode:
        sweep = SweepConfig(
            enabled=True,
            temperature_c_min=300.0,
            temperature_c_max=800.0,
            temperature_points=6,
            pressure_bar_min=1.0,
            pressure_bar_max=1.0,
            pressure_points=1,
        )
    else:
        sweep = SweepConfig(
            enabled=True,
            temperature_c_min=300.0,
            temperature_c_max=800.0,
            temperature_points=11,
            pressure_bar_min=1.0,
            pressure_bar_max=5.0,
            pressure_points=5,
        )
    return WorkflowConfig(sweep=sweep)


@st.cache_data(show_spinner=False)
def _run_live_solver(workbook_path: str, fast_mode: bool) -> Dict[str, pd.DataFrame]:
    config = _build_config(fast_mode)
    run_result = run_workflow(workbook_path, config)
    return workflow_result_to_dataframes(run_result)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_results(fast_mode: bool, result_dir: str | None = None) -> Dict[str, pd.DataFrame]:
    """Return reporting DataFrames plus a '_source_info' metadata key.

    If result_dir (a folder name like 'yield_results_20260424_123151') is given,
    load from that specific folder.  Otherwise fall back to the most recent folder,
    then the live solver.
    """
    if result_dir:
        pair = _pair_from_dir(result_dir)
    else:
        pair = _find_latest_output_pair()

    if pair is not None:
        full_path, clean_path = pair
        dfs = _load_from_files(str(full_path), str(clean_path))
        dfs["_source_info"] = pd.DataFrame([{
            "source": "file",
            "label": f"Output file from {_timestamp_from_path(full_path)}",
            "full_path": str(full_path),
            "clean_path": str(clean_path),
        }])
        return dfs

    # No output files — run the solver
    workbook_path = str(_find_workbook())
    dfs = _run_live_solver(workbook_path, fast_mode)
    dfs["_source_info"] = pd.DataFrame([{
        "source": "solver",
        "label": f"Live solver ({'fast' if fast_mode else 'full'} mode)",
        "full_path": workbook_path,
        "clean_path": "",
    }])
    return dfs


# ---------------------------------------------------------------------------
# LCA results loading (Brightway / ReCiPe per-MJ bio-oil impacts)
# ---------------------------------------------------------------------------

# One xlsx per biomass type, produced by GREENFUEL_LCA_biomass.ipynb.  Each file
# has an "All Categories" sheet with columns: biomass_type, category, score, unit.
# score == impact per 1 MJ of usable bio-oil (the functional unit).
_LCA_DIR_CANDIDATES = [
    _PROJECT_ROOT / "LCA_results",
    _PROJECT_ROOT / "lca_results",
    _PROJECT_ROOT / "results" / "LCA_results",
    _PROJECT_ROOT / "webapp" / "data" / "LCA_results",
    # Consolidated project layout: LCA outputs live under LCA_PROJECT/.
    _GREENFUEL_ROOT / "LCA_PROJECT" / "Project biomass" / "LCA_results",
]

_LCA_COLUMNS = ["biomass_type", "category", "unit", "score"]
_LCA_SHEET = "All Categories"


@st.cache_data(show_spinner=False)
def load_lca_results(lca_dir: str | None = None) -> pd.DataFrame:
    """Load every ``lca_results_*.xlsx`` in *lca_dir* into one tidy DataFrame.

    Returns columns ``[biomass_type, category, unit, score]`` where ``score`` is
    the ReCiPe 2016 midpoint (H) impact per 1 MJ of usable bio-oil.  Dynamically
    picks up whatever result files exist (4 today, up to 9 expected) — no code
    change needed as more biomass types are added.  Returns an empty frame (with
    the right columns) if the folder or files are missing, so callers can show a
    friendly message instead of crashing.
    """
    base = Path(lca_dir) if lca_dir else _resolve_results_dir(_LCA_DIR_CANDIDATES, "lca_results_*.xlsx")
    if base is None or not base.exists():
        return pd.DataFrame(columns=_LCA_COLUMNS)

    frames: list[pd.DataFrame] = []
    for f in sorted(base.glob("lca_results_*.xlsx")):
        sheets = _read_all_sheets(f)
        if not sheets or _LCA_SHEET not in sheets:
            continue
        d = sheets[_LCA_SHEET]
        keep = [c for c in _LCA_COLUMNS if c in d.columns]
        if "biomass_type" not in keep or "category" not in keep or "score" not in keep:
            continue
        frames.append(d[keep].copy())

    if not frames:
        return pd.DataFrame(columns=_LCA_COLUMNS)

    out = pd.concat(frames, ignore_index=True)
    out["score"] = pd.to_numeric(out["score"], errors="coerce")
    out = out.dropna(subset=["biomass_type", "category", "score"])
    for col in _LCA_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    return out[_LCA_COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Monte Carlo results loading (uncertainty analysis, GREENFUEL_LCA_biomass.ipynb)
# ---------------------------------------------------------------------------

# One xlsx per biomass type, produced by the notebook's Monte Carlo step (100
# iterations, Brightway use_distributions=True).  Each file has:
#   - "Summary"            : one row per impact category (deterministic_score,
#                            mc_mean/std, cv_pct, quartiles, whiskers, ...)
#   - "Raw_All_Categories" : biomass_type, iteration, <cat1>..<cat4>  (raw samples)
# The 4 categories are chosen per biomass, so we read them dynamically.
_MC_DIR_CANDIDATES = [
    _PROJECT_ROOT / "Monte_carlo_analysis",
    _PROJECT_ROOT / "monte_carlo_analysis",
    _PROJECT_ROOT / "results" / "Monte_carlo_analysis",
    _PROJECT_ROOT / "webapp" / "data" / "Monte_carlo_analysis",
    # Consolidated project layout: Monte Carlo outputs live under LCA_PROJECT/.
    _GREENFUEL_ROOT / "LCA_PROJECT" / "Project biomass" / "Monte_carlo_analysis",
]

_MC_SUMMARY_SHEET = "Summary"
_MC_RAW_SHEET = "Raw_All_Categories"
_MC_SAMPLE_COLUMNS = ["biomass_type", "category", "iteration", "score"]


@st.cache_data(show_spinner=False)
def load_montecarlo_results(mc_dir: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load every ``montecarlo_*.xlsx`` in *mc_dir*.

    Returns ``(samples_df, summary_df)``:
      - ``samples_df``  tidy long format ``[biomass_type, category, iteration, score]``
        (the raw Monte Carlo iterations, melted from "Raw_All_Categories").
      - ``summary_df``  the per-category summary rows (incl. ``deterministic_score``,
        ``mc_mean``, ``cv_pct``, whiskers, ...).
    Dynamically picks up whatever files exist (1 today, up to 9 expected).  Both
    frames come back empty (with sensible columns) if the folder/files are missing,
    and individual unreadable / OneDrive-locked files are skipped.
    """
    base = Path(mc_dir) if mc_dir else _resolve_results_dir(_MC_DIR_CANDIDATES, "montecarlo_*.xlsx")
    empty = (pd.DataFrame(columns=_MC_SAMPLE_COLUMNS), pd.DataFrame())
    if base is None or not base.exists():
        return empty

    sample_frames: list[pd.DataFrame] = []
    summary_frames: list[pd.DataFrame] = []
    for f in sorted(base.glob("montecarlo_*.xlsx")):
        sheets = _read_all_sheets(f)
        if not sheets or _MC_RAW_SHEET not in sheets:
            continue
        raw = sheets[_MC_RAW_SHEET]
        if _MC_SUMMARY_SHEET in sheets:
            summary_frames.append(sheets[_MC_SUMMARY_SHEET])

        id_vars = [c for c in ("biomass_type", "iteration") if c in raw.columns]
        cat_cols = [c for c in raw.columns if c not in id_vars]
        if "biomass_type" not in id_vars or not cat_cols:
            continue
        long = raw.melt(id_vars=id_vars, value_vars=cat_cols,
                        var_name="category", value_name="score")
        sample_frames.append(long)

    if not sample_frames:
        return empty

    samples = pd.concat(sample_frames, ignore_index=True)
    samples["score"] = pd.to_numeric(samples["score"], errors="coerce")
    samples = samples.dropna(subset=["biomass_type", "category", "score"])
    if "iteration" not in samples.columns:
        samples["iteration"] = pd.NA
    samples = samples[_MC_SAMPLE_COLUMNS].reset_index(drop=True)

    summary = pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame()
    return samples, summary
