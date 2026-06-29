"""Transform workflow run results to tabular QA artifacts."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

from ..models import RowWarning, WorkflowRunResult
from .validator import acceptance_summary, classify_acceptance


def _warnings_to_df(warnings: List[RowWarning]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"code": w.code, "message": w.message, "severity": w.severity} for w in warnings]
    )


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_div(numerator: float, denominator: float | None) -> float | None:
    if denominator is None or denominator <= 0.0:
        return None
    return numerator / denominator


def _contains_any_token(value: str, tokens: tuple[str, ...]) -> bool:
    if not value:
        return False
    return any(token in value for token in tokens)


def _realism_summary_df(results_df: pd.DataFrame, run_result: WorkflowRunResult) -> pd.DataFrame:
    if results_df.empty:
        return pd.DataFrame(
            [
                {
                    "total_rows": 0.0,
                    "unique_feedstocks": 0.0,
                    "converged_rows": 0.0,
                    "converged_fraction": 0.0,
                    "pass_rows": 0.0,
                    "accept_rows": 0.0,
                    "review_rows": 0.0,
                    "review_fraction": 0.0,
                    "generic_bio_oil_rows": 0.0,
                    "generic_bio_oil_fraction": 0.0,
                    "unmatched_mappings_count": float(len(run_result.unmatched_mappings)),
                    "max_residual_observed": 0.0,
                }
            ]
        )

    total_rows = float(len(results_df))
    unique_feedstocks = float(results_df["feedstock_id"].nunique()) if "feedstock_id" in results_df.columns else 0.0

    converged_series = results_df["converged"] if "converged" in results_df.columns else pd.Series([False] * len(results_df))
    converged_rows = float(pd.to_numeric(converged_series, errors="coerce").fillna(0).astype(bool).sum())
    converged_fraction = converged_rows / max(total_rows, 1.0)

    pass_rows = float((results_df.get("acceptance_flag", pd.Series([""] * len(results_df))) == "PASS").sum())
    accept_rows = float((results_df.get("acceptance_flag", pd.Series([""] * len(results_df))) == "ACCEPT").sum())
    review_rows = float((results_df.get("acceptance_flag", pd.Series([""] * len(results_df))) == "REVIEW").sum())
    review_fraction = review_rows / max(total_rows, 1.0)

    warning_codes = results_df.get("warning_codes", pd.Series([""] * len(results_df))).astype(str)
    generic_tokens = ("BIO_OIL_GENERIC_FALLBACK", "MAP_NO_BIO_OIL_MATCH")
    generic_bio_oil_rows = float(sum(_contains_any_token(code, generic_tokens) for code in warning_codes))
    generic_bio_oil_fraction = generic_bio_oil_rows / max(total_rows, 1.0)

    max_residual_observed = float(pd.to_numeric(results_df.get("max_residual", pd.Series([0.0])), errors="coerce").fillna(0.0).max())

    return pd.DataFrame(
        [
            {
                "total_rows": total_rows,
                "unique_feedstocks": unique_feedstocks,
                "converged_rows": converged_rows,
                "converged_fraction": converged_fraction,
                "pass_rows": pass_rows,
                "accept_rows": accept_rows,
                "review_rows": review_rows,
                "review_fraction": review_fraction,
                "generic_bio_oil_rows": generic_bio_oil_rows,
                "generic_bio_oil_fraction": generic_bio_oil_fraction,
                "unmatched_mappings_count": float(len(run_result.unmatched_mappings)),
                "max_residual_observed": max_residual_observed,
            }
        ]
    )


def _oil_yield_percentiles_by_feedstock_df(results_df: pd.DataFrame) -> pd.DataFrame:
    if results_df.empty or "feedstock_id" not in results_df.columns:
        return pd.DataFrame()

    converged_mask = pd.to_numeric(results_df.get("converged", pd.Series([False] * len(results_df))), errors="coerce").fillna(0).astype(bool)
    filtered = results_df.loc[converged_mask].copy()
    if filtered.empty:
        return pd.DataFrame()

    basis_specs = (
        ("oil_yield_kg_per_kg", "as_received"),
        ("oil_yield_kg_per_kg_dry", "dry"),
        ("oil_yield_kg_per_kg_daf", "daf"),
    )

    frames: list[pd.DataFrame] = []
    grouping_cols = ["feedstock_id", "category", "subcategory"]
    grouping_cols = [c for c in grouping_cols if c in filtered.columns]

    for yield_col, basis_name in basis_specs:
        if yield_col not in filtered.columns:
            continue

        temp = filtered[grouping_cols + [yield_col]].copy()
        temp[yield_col] = pd.to_numeric(temp[yield_col], errors="coerce")
        temp = temp.dropna(subset=[yield_col])
        if temp.empty:
            continue

        grouped = temp.groupby(grouping_cols, as_index=False)[yield_col].agg(
            runs="count",
            oil_yield_p10=lambda s: s.quantile(0.10),
            oil_yield_p50="median",
            oil_yield_mean="mean",
            oil_yield_p90=lambda s: s.quantile(0.90),
            oil_yield_min="min",
            oil_yield_max="max",
        )
        grouped.insert(len(grouping_cols), "basis", basis_name)
        frames.append(grouped)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    sort_cols = [c for c in ("feedstock_id", "basis") if c in combined.columns]
    return combined.sort_values(sort_cols).reset_index(drop=True)


def _oil_yield_mismatch_df(results_df: pd.DataFrame) -> pd.DataFrame:
    if results_df.empty:
        return pd.DataFrame()

    basis_specs = (
        (
            "as_received",
            "oil_yield_kg_per_kg",
            "literature_oil_yield_ar_kg_per_kg",
            "literature_oil_yield_ar_min_kg_per_kg",
            "literature_oil_yield_ar_max_kg_per_kg",
        ),
        (
            "dry",
            "oil_yield_kg_per_kg_dry",
            "literature_oil_yield_dry_kg_per_kg",
            "literature_oil_yield_dry_min_kg_per_kg",
            "literature_oil_yield_dry_max_kg_per_kg",
        ),
        (
            "daf",
            "oil_yield_kg_per_kg_daf",
            "literature_oil_yield_daf_kg_per_kg",
            "literature_oil_yield_daf_min_kg_per_kg",
            "literature_oil_yield_daf_max_kg_per_kg",
        ),
    )

    static_cols = [
        "feedstock_id",
        "category",
        "subcategory",
        "temperature_k",
        "temperature_c",
        "pressure_pa",
        "pressure_bar",
        "converged",
        "max_residual",
        "acceptance_flag",
    ]

    records: list[dict[str, object]] = []
    for _, row in results_df.iterrows():
        for basis, predicted_key, benchmark_key, benchmark_min_key, benchmark_max_key in basis_specs:
            if predicted_key not in results_df.columns:
                continue

            predicted = pd.to_numeric(pd.Series([row.get(predicted_key)]), errors="coerce").iloc[0]
            benchmark = pd.to_numeric(pd.Series([row.get(benchmark_key)]), errors="coerce").iloc[0]
            benchmark_min = pd.to_numeric(pd.Series([row.get(benchmark_min_key)]), errors="coerce").iloc[0]
            benchmark_max = pd.to_numeric(pd.Series([row.get(benchmark_max_key)]), errors="coerce").iloc[0]

            if pd.isna(predicted):
                continue

            if pd.isna(benchmark_min) and not pd.isna(benchmark):
                benchmark_min = benchmark
            if pd.isna(benchmark_max) and not pd.isna(benchmark):
                benchmark_max = benchmark

            if pd.isna(benchmark) and not pd.isna(benchmark_min) and not pd.isna(benchmark_max):
                benchmark = (benchmark_min + benchmark_max) / 2.0

            if pd.isna(benchmark) and pd.isna(benchmark_min) and pd.isna(benchmark_max):
                continue

            in_range: bool | None
            out_of_range_distance: float | None
            if not pd.isna(benchmark_min) and not pd.isna(benchmark_max):
                in_range = bool(benchmark_min <= predicted <= benchmark_max)
                if in_range:
                    out_of_range_distance = 0.0
                elif predicted < benchmark_min:
                    out_of_range_distance = float(benchmark_min - predicted)
                else:
                    out_of_range_distance = float(predicted - benchmark_max)
            else:
                in_range = None
                out_of_range_distance = None

            absolute_error = None if pd.isna(benchmark) else float(abs(predicted - benchmark))
            relative_error = None
            if absolute_error is not None and not pd.isna(benchmark) and benchmark > 0.0:
                relative_error = float(absolute_error / benchmark)

            record: dict[str, object] = {
                "basis": basis,
                "predicted_oil_yield_kg_per_kg": float(predicted),
                "benchmark_oil_yield_kg_per_kg": None if pd.isna(benchmark) else float(benchmark),
                "benchmark_oil_yield_min_kg_per_kg": None if pd.isna(benchmark_min) else float(benchmark_min),
                "benchmark_oil_yield_max_kg_per_kg": None if pd.isna(benchmark_max) else float(benchmark_max),
                "absolute_error_kg_per_kg": absolute_error,
                "relative_error_fraction": relative_error,
                "in_range": in_range,
                "out_of_range_distance_kg_per_kg": out_of_range_distance,
            }
            for col in static_cols:
                if col in results_df.columns:
                    record[col] = row.get(col)
            records.append(record)

    if not records:
        return pd.DataFrame()

    mismatch_df = pd.DataFrame(records)
    preferred_order = [
        "feedstock_id",
        "category",
        "subcategory",
        "temperature_k",
        "temperature_c",
        "pressure_pa",
        "pressure_bar",
        "basis",
        "predicted_oil_yield_kg_per_kg",
        "benchmark_oil_yield_kg_per_kg",
        "benchmark_oil_yield_min_kg_per_kg",
        "benchmark_oil_yield_max_kg_per_kg",
        "absolute_error_kg_per_kg",
        "relative_error_fraction",
        "in_range",
        "out_of_range_distance_kg_per_kg",
        "converged",
        "max_residual",
        "acceptance_flag",
    ]
    ordered_existing = [col for col in preferred_order if col in mismatch_df.columns]
    trailing = [col for col in mismatch_df.columns if col not in ordered_existing]
    return mismatch_df[ordered_existing + trailing]


def _peak_yields_by_feedstock_df(results_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per feedstock: the scenario with the highest converged oil yield."""
    if results_df.empty or "feedstock_id" not in results_df.columns:
        return pd.DataFrame()

    converged_mask = (
        pd.to_numeric(results_df.get("converged", pd.Series([False] * len(results_df))), errors="coerce")
        .fillna(0)
        .astype(bool)
    )
    converged = results_df.loc[converged_mask].copy()
    if converged.empty:
        return pd.DataFrame()

    oil_col = "oil_yield_kg_per_kg"
    if oil_col not in converged.columns:
        return pd.DataFrame()

    converged[oil_col] = pd.to_numeric(converged[oil_col], errors="coerce")
    converged = converged.dropna(subset=[oil_col])
    if converged.empty:
        return pd.DataFrame()

    idx = converged.groupby("feedstock_id")[oil_col].idxmax()
    peak_df = converged.loc[idx].copy()

    # Restrict to the exact columns needed for the clean summary sheet.
    clean_cols = [
        "feedstock_id",
        "category",
        "subcategory",
        "temperature_c",
        "oil_yield_kg_per_kg",
        "oil_yield_kg_per_kg_dry",
        "oil_yield_kg_per_kg_daf",
        "bio_oil_hhv_mj_per_kg",
        "bio_oil_energy_hhv_mj_per_kg_biomass",
        "kg_biomass_per_mj_bio_oil_hhv",
        
    ]
    peak_df = peak_df[[c for c in clean_cols if c in peak_df.columns]]

    sort_cols = [c for c in ("category", "subcategory", "feedstock_id") if c in peak_df.columns]
    return peak_df.sort_values(sort_cols).reset_index(drop=True)


def workflow_result_to_dataframes(run_result: WorkflowRunResult) -> Dict[str, pd.DataFrame]:
    """Convert result object into a dict of report dataframes."""

    result_rows = []
    for row in run_result.results:
        acceptance_flag, acceptance_reason = classify_acceptance(row.converged, row.max_residual)
        temperature_k = row.temperature_k
        pressure_pa = row.pressure_pa
        moisture_pct_ar = _to_float(row.metadata.get("feedstock_moisture_pct_ar"))
        ash_pct_ar = _to_float(row.metadata.get("feedstock_ash_pct_ar"))
        cp_feedstock_dry = _to_float(row.metadata.get("cp_feedstock_dry_kj_per_kg_k"))
        cp_feedstock_ar = _to_float(row.metadata.get("cp_feedstock_ar_kj_per_kg_k"))
        cp_bio_oil = _to_float(row.metadata.get("cp_bio_oil_kj_per_kg_k"))
        cp_char = _to_float(row.metadata.get("cp_char_kj_per_kg_k"))
        cp_gas_molar = _to_float(row.metadata.get("cp_gas_molar_j_per_mol_k"))
        cp_gas_mass = _to_float(row.metadata.get("cp_gas_mass_kj_per_kg_k"))
        gas_mixture_mw = _to_float(row.metadata.get("gas_mixture_mw_g_per_mol"))
        delta_t_from_ref = _to_float(row.metadata.get("delta_t_from_ref_k"))
        sensible_heat_feedstock = _to_float(row.metadata.get("sensible_heat_feedstock_mj_per_kg"))
        sensible_heat_products = _to_float(row.metadata.get("sensible_heat_products_mj_per_kg"))
        output_fuel_energy = _to_float(row.metadata.get("output_fuel_energy_mj_per_kg"))
        net_fuel_energy = _to_float(row.metadata.get("net_fuel_energy_mj_per_kg"))
        net_energy_efficiency_ratio = _to_float(row.metadata.get("net_energy_efficiency_ratio"))
        cp_gas_fallback_fraction = _to_float(row.metadata.get("cp_gas_fallback_fraction"))
        literature_oil_yield_ar = _to_float(row.metadata.get("literature_oil_yield_ar_kg_per_kg"))
        literature_oil_yield_ar_min = _to_float(row.metadata.get("literature_oil_yield_ar_min_kg_per_kg"))
        literature_oil_yield_ar_max = _to_float(row.metadata.get("literature_oil_yield_ar_max_kg_per_kg"))
        literature_oil_yield_dry = _to_float(row.metadata.get("literature_oil_yield_dry_kg_per_kg"))
        literature_oil_yield_dry_min = _to_float(row.metadata.get("literature_oil_yield_dry_min_kg_per_kg"))
        literature_oil_yield_dry_max = _to_float(row.metadata.get("literature_oil_yield_dry_max_kg_per_kg"))
        literature_oil_yield_daf = _to_float(row.metadata.get("literature_oil_yield_daf_kg_per_kg"))
        literature_oil_yield_daf_min = _to_float(row.metadata.get("literature_oil_yield_daf_min_kg_per_kg"))
        literature_oil_yield_daf_max = _to_float(row.metadata.get("literature_oil_yield_daf_max_kg_per_kg"))
        input_feedstock_hhv = _to_float(row.metadata.get("input_feedstock_hhv_mj_per_kg"))
        gross_energy_efficiency_ratio = _to_float(row.metadata.get("gross_energy_efficiency_ratio"))
        gross_efficiency_consistency_abs_error = _to_float(
            row.metadata.get("gross_efficiency_consistency_abs_error")
        )
        net_minus_gross_efficiency_ratio = _to_float(row.metadata.get("net_minus_gross_efficiency_ratio"))

        dry_mass_factor = None
        if moisture_pct_ar is not None:
            dry_mass_factor = max(0.0, 1.0 - moisture_pct_ar / 100.0)

        # Keep daf normalization consistent with stoichiometry assumptions used by the solver.
        daf_mass_factor = None
        if dry_mass_factor is not None and ash_pct_ar is not None:
            daf_mass_factor = dry_mass_factor * max(0.0, 1.0 - ash_pct_ar / 100.0)

        oil_yield_dry = _safe_div(row.oil_yield_kg_per_kg, dry_mass_factor)
        gas_yield_dry = _safe_div(row.gas_yield_kg_per_kg, dry_mass_factor)
        char_yield_dry = _safe_div(row.char_yield_kg_per_kg, dry_mass_factor)

        oil_yield_daf = _safe_div(row.oil_yield_kg_per_kg, daf_mass_factor)
        gas_yield_daf = _safe_div(row.gas_yield_kg_per_kg, daf_mass_factor)

        ash_mass_kg_per_kg_ar = 0.0 if ash_pct_ar is None else max(0.0, ash_pct_ar / 100.0)
        organic_char_yield_ar = max(0.0, row.char_yield_kg_per_kg - ash_mass_kg_per_kg_ar)
        char_yield_daf = _safe_div(organic_char_yield_ar, daf_mass_factor)

        result_rows.append(
            {
                "feedstock_id": row.feedstock_id,
                "category": row.category,
                "subcategory": row.subcategory,
                "temperature_k": temperature_k,
                "temperature_c": (None if temperature_k is None else temperature_k - 273.15),
                "pressure_pa": pressure_pa,
                "pressure_bar": (None if pressure_pa is None else pressure_pa / 100000.0),
                "feedstock_moisture_pct_ar": moisture_pct_ar,
                "feedstock_ash_pct_ar": ash_pct_ar,
                "oil_yield_kg_per_kg": row.oil_yield_kg_per_kg,
                "gas_yield_kg_per_kg": row.gas_yield_kg_per_kg,
                "char_yield_kg_per_kg": row.char_yield_kg_per_kg,
                "oil_yield_kg_per_kg_dry": oil_yield_dry,
                "gas_yield_kg_per_kg_dry": gas_yield_dry,
                "char_yield_kg_per_kg_dry": char_yield_dry,
                "oil_yield_kg_per_kg_daf": oil_yield_daf,
                "gas_yield_kg_per_kg_daf": gas_yield_daf,
                "char_yield_kg_per_kg_daf": char_yield_daf,
                "literature_oil_yield_ar_kg_per_kg": literature_oil_yield_ar,
                "literature_oil_yield_ar_min_kg_per_kg": literature_oil_yield_ar_min,
                "literature_oil_yield_ar_max_kg_per_kg": literature_oil_yield_ar_max,
                "literature_oil_yield_dry_kg_per_kg": literature_oil_yield_dry,
                "literature_oil_yield_dry_min_kg_per_kg": literature_oil_yield_dry_min,
                "literature_oil_yield_dry_max_kg_per_kg": literature_oil_yield_dry_max,
                "literature_oil_yield_daf_kg_per_kg": literature_oil_yield_daf,
                "literature_oil_yield_daf_min_kg_per_kg": literature_oil_yield_daf_min,
                "literature_oil_yield_daf_max_kg_per_kg": literature_oil_yield_daf_max,
                "cp_feedstock_dry_kj_per_kg_k": cp_feedstock_dry,
                "cp_feedstock_dry_source": row.metadata.get("cp_feedstock_dry_source", ""),
                "cp_feedstock_ar_kj_per_kg_k": cp_feedstock_ar,
                "cp_feedstock_ar_source": row.metadata.get("cp_feedstock_ar_source", ""),
                "cp_bio_oil_kj_per_kg_k": cp_bio_oil,
                "cp_bio_oil_source": row.metadata.get("cp_bio_oil_source", ""),
                "cp_char_kj_per_kg_k": cp_char,
                "cp_char_source": row.metadata.get("cp_char_source", ""),
                "cp_gas_molar_j_per_mol_k": cp_gas_molar,
                "cp_gas_mass_kj_per_kg_k": cp_gas_mass,
                "gas_mixture_mw_g_per_mol": gas_mixture_mw,
                "cp_gas_source": row.metadata.get("cp_gas_source", ""),
                "cp_gas_source_counts": row.metadata.get("cp_gas_source_counts", ""),
                "cp_gas_fallback_fraction": cp_gas_fallback_fraction,
                "delta_t_from_ref_k": delta_t_from_ref,
                "input_feedstock_hhv_mj_per_kg": input_feedstock_hhv,
                "sensible_heat_feedstock_mj_per_kg": sensible_heat_feedstock,
                "sensible_heat_products_mj_per_kg": sensible_heat_products,
                "output_fuel_energy_mj_per_kg": output_fuel_energy,
                "gross_energy_efficiency_ratio": gross_energy_efficiency_ratio,
                "gross_efficiency_consistency_abs_error": gross_efficiency_consistency_abs_error,
                "net_fuel_energy_mj_per_kg": net_fuel_energy,
                "net_energy_efficiency_ratio": net_energy_efficiency_ratio,
                "net_minus_gross_efficiency_ratio": net_minus_gross_efficiency_ratio,
                "energy_accounting_status": row.metadata.get("energy_accounting_status", ""),
                "efficiency_ratio": row.efficiency_ratio,
                "acceptance_flag": acceptance_flag,
                "acceptance_reason": acceptance_reason,
                "converged": row.converged,
                "max_residual": row.max_residual,
                "warning_codes": "|".join(w.code for w in row.warnings),
                "reference": row.metadata.get("reference", ""),
                "regionality": row.metadata.get("regionality", ""),
                "pyrolysis_suitability": row.metadata.get("pyrolysis_suitability", ""),
                "feedstock_c_pct_daf": row.metadata.get("feedstock_c_pct_daf", ""),
                "feedstock_h_pct_daf": row.metadata.get("feedstock_h_pct_daf", ""),
                "feedstock_o_pct_daf": row.metadata.get("feedstock_o_pct_daf", ""),
                "feedstock_n_pct_daf": row.metadata.get("feedstock_n_pct_daf", ""),
                "feedstock_s_pct_daf": row.metadata.get("feedstock_s_pct_daf", ""),
                "parser_assist_count": row.metadata.get("parser_assist_count", "0"),
                "parser_assist_codes": row.metadata.get("parser_assist_codes", ""),
                "parser_assist_messages": row.metadata.get("parser_assist_messages", ""),
                "bio_oil_hhv_mj_per_kg": _to_float(row.metadata.get("bio_oil_hhv_mj_per_kg")),
                "bio_oil_hhv_source": row.metadata.get("bio_oil_hhv_source", ""),
                "bio_oil_energy_hhv_mj_per_kg_biomass": _to_float(row.metadata.get("bio_oil_energy_hhv_mj_per_kg_biomass")),
                "kg_biomass_per_mj_bio_oil_hhv": _to_float(row.metadata.get("kg_biomass_per_mj_bio_oil_hhv")),
            }
        )

    results_df = pd.DataFrame(result_rows)
    return {
        "results": results_df,
        "peak_results": _peak_yields_by_feedstock_df(results_df),
        "acceptance_summary": pd.DataFrame([acceptance_summary(run_result)]),
        "realism_summary": _realism_summary_df(results_df, run_result),
        "oil_percentiles": _oil_yield_percentiles_by_feedstock_df(results_df),
        "oil_yield_mismatch": _oil_yield_mismatch_df(results_df),
        "unmatched_mappings": pd.DataFrame({"feedstock_id": run_result.unmatched_mappings}),
        "parse_warnings": _warnings_to_df(run_result.parse_warnings),
        "solver_warnings": _warnings_to_df(run_result.solver_warnings),
    }
