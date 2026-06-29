"""Excel parser and cross-sheet matching logic."""

from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Dict, List, Optional, Sequence

import pandas as pd

try:
    from thefuzz import fuzz as thefuzz_fuzz
except Exception:  # pragma: no cover
    thefuzz_fuzz = None

from ..config import WorkflowConfig
from ..models import BioOilRecord, FeedstockRecord, RowWarning
from ..utils.exceptions import DataValidationError
from .contracts import ParsedWorkbook
from .normalizer import (
    canonicalize_name,
    first_matching_column,
    parse_numeric_cell,
    parse_true_marker,
    token_overlap_score,
)


def _resolve_columns(
    df: pd.DataFrame,
    aliases_map: Dict[str, tuple[str, ...]],
    required_targets: Optional[Sequence[str]] = None,
) -> tuple[Dict[str, str], List[str]]:
    """Resolve aliases against dataframe columns and return unresolved required targets."""

    resolved: Dict[str, str] = {}
    missing: List[str] = []
    required_set = set(aliases_map.keys()) if required_targets is None else set(required_targets)

    for target, aliases in aliases_map.items():
        col = first_matching_column(df.columns, aliases)
        if col is None:
            if target in required_set:
                missing.append(target)
        else:
            resolved[target] = col

    return resolved, missing


def _resolve_sheet_name(
    available_sheet_names: Sequence[str],
    desired_name: str,
    alternatives: Optional[Sequence[str]] = None,
) -> tuple[str, Optional[RowWarning]]:
    """Resolve a requested sheet name against available names with tolerant matching."""

    candidates: List[str] = [desired_name]
    if alternatives:
        for alt in alternatives:
            if alt and alt not in candidates:
                candidates.append(alt)

    # 1) Exact match first.
    for candidate in candidates:
        if candidate in available_sheet_names:
            return candidate, None

    # 2) Case/whitespace-insensitive match.
    by_lower = {sheet.strip().lower(): sheet for sheet in available_sheet_names}
    for candidate in candidates:
        hit = by_lower.get(candidate.strip().lower())
        if hit is not None:
            return (
                hit,
                RowWarning(
                    "SHEET_NAME_NORMALIZED",
                    f"Configured sheet '{desired_name}' resolved to workbook sheet '{hit}'.",
                ),
            )

    # 3) Canonical alphanumeric match (punctuation/hyphen tolerant).
    by_canonical: Dict[str, List[str]] = {}
    for sheet in available_sheet_names:
        key = canonicalize_name(sheet)
        by_canonical.setdefault(key, []).append(sheet)

    for candidate in candidates:
        key = canonicalize_name(candidate)
        hits = by_canonical.get(key, [])
        if len(hits) == 1:
            return (
                hits[0],
                RowWarning(
                    "SHEET_NAME_CANONICAL_MATCH",
                    f"Configured sheet '{desired_name}' resolved to workbook sheet '{hits[0]}' via canonical matching.",
                ),
            )
        if len(hits) > 1:
            return (
                hits[0],
                RowWarning(
                    "SHEET_NAME_AMBIGUOUS_CANONICAL",
                    (
                        f"Configured sheet '{desired_name}' matched multiple workbook sheets {hits}; "
                        f"using '{hits[0]}'."
                    ),
                ),
            )

    available = ", ".join(available_sheet_names)
    raise DataValidationError(
        (
            f"Worksheet named '{desired_name}' not found and no tolerant match succeeded. "
            f"Available sheets: {available}"
        )
    )


def _require_columns(
    df: pd.DataFrame,
    aliases_map: Dict[str, tuple[str, ...]],
    sheet_name: str,
    required_targets: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    resolved, missing = _resolve_columns(df, aliases_map, required_targets)

    if missing:
        raise DataValidationError(
            f"Missing required columns in '{sheet_name}': {', '.join(missing)}"
        )
    return resolved


def _read_sheet_with_detected_header(
    workbook: pd.ExcelFile,
    sheet_name: str,
    aliases_map: Dict[str, tuple[str, ...]],
    required_targets: Sequence[str],
    max_header_scan_rows: int = 6,
) -> tuple[pd.DataFrame, Optional[RowWarning]]:
    """Read sheet by scanning early rows to detect the best header row."""

    best_df: Optional[pd.DataFrame] = None
    best_missing: Optional[List[str]] = None
    best_header = 0

    for header_row in range(max_header_scan_rows):
        candidate_df = pd.read_excel(workbook, sheet_name=sheet_name, header=header_row)
        _, missing = _resolve_columns(candidate_df, aliases_map, required_targets)

        if best_missing is None or len(missing) < len(best_missing):
            best_df = candidate_df
            best_missing = missing
            best_header = header_row

        if not missing:
            if header_row == 0:
                return candidate_df, None
            return (
                candidate_df,
                RowWarning(
                    "HEADER_ROW_AUTO_DETECTED",
                    f"Sheet '{sheet_name}' parsed with header row index {header_row} (0-based).",
                ),
            )

    assert best_df is not None
    assert best_missing is not None
    raise DataValidationError(
        (
            f"Missing required columns in '{sheet_name}': {', '.join(best_missing)}. "
            f"Tried header rows 0..{max_header_scan_rows - 1}; best match was row {best_header}."
        )
    )


def _feedstock_aliases() -> Dict[str, tuple[str, ...]]:
    return {
        "category": ("Feedstock Category", "Feedstock category", "category", "Unnamed: 0", "Unnamed:0"),
        "subcategory": (
            "Feedstock Subcategory",
            "Feedstock subcategory",
            "subcategory",
            "Feedstock",
            "Unnamed: 1",
            "Unnamed:1",
        ),
        "moisture": ("M", "Moisture", "Moisture (M)"),
        "vm": (
            "VM",
            "Volatile Matter",
            "Volatile matter",
            "Organic Matter / Volatile matter",
            "Organic matter / volatile matter",
        ),
        "fc": ("FC", "Fixed Carbon", "Fixed carbon"),
        "ash": ("Ash",),
        "c": ("C", "Carbon"),
        "h": ("H", "Hydrogen"),
        "o": ("O", "Oxygen"),
        "n": ("N", "Nitrogen"),
        "s": ("S", "Sulphur", "Sulfur"),
        "reference": ("Reference", "References", "0"),
        "suitability": ("Pyrolysis suitability", "Pyrolysis Suitability", "Suitability"),
        "regionality": ("Regionality", "regionality", "Unnamed: 15", "Unnamed:15"),
        "lit_oil_ar": (
            "Oil yield",
            "Oil yield (as-received)",
            "Oil yield as-received",
            "Oil yield as received",
            "Literature oil yield",
            "Literature oil yield (as-received)",
            "Literature oil yield as-received",
            "Literature oil yield as received",
            "Oil yield (%)",
            "Oil yield wt%",
        ),
        "lit_oil_ar_min": (
            "Oil yield min",
            "Oil yield min (as-received)",
            "Oil yield minimum (as-received)",
            "Literature oil yield min",
            "Literature oil yield min (as-received)",
        ),
        "lit_oil_ar_max": (
            "Oil yield max",
            "Oil yield max (as-received)",
            "Oil yield maximum (as-received)",
            "Literature oil yield max",
            "Literature oil yield max (as-received)",
        ),
        "lit_oil_dry": (
            "Oil yield (dry)",
            "Oil yield dry",
            "Literature oil yield (dry)",
            "Literature oil yield dry",
            "Oil yield dry (%)",
            "Oil yield dry wt%",
        ),
        "lit_oil_dry_min": (
            "Oil yield dry min",
            "Oil yield min (dry)",
            "Literature oil yield dry min",
            "Literature oil yield min (dry)",
        ),
        "lit_oil_dry_max": (
            "Oil yield dry max",
            "Oil yield max (dry)",
            "Literature oil yield dry max",
            "Literature oil yield max (dry)",
        ),
        "lit_oil_daf": (
            "Oil yield (daf)",
            "Oil yield daf",
            "Literature oil yield (daf)",
            "Literature oil yield daf",
            "Oil yield daf (%)",
            "Oil yield daf wt%",
        ),
        "lit_oil_daf_min": (
            "Oil yield daf min",
            "Oil yield min (daf)",
            "Literature oil yield daf min",
            "Literature oil yield min (daf)",
        ),
        "lit_oil_daf_max": (
            "Oil yield daf max",
            "Oil yield max (daf)",
            "Literature oil yield daf max",
            "Literature oil yield max (daf)",
        ),
    }


_FULL_RANGE_PATTERN = re.compile(r"^([-+]?\d+(?:[\.,]\d+)?)[-–]([-+]?\d+(?:[\.,]\d+)?)$")


def _parse_decimal_fragment(fragment: str, decimal_separator: str) -> float:
    normalized = fragment.strip()
    if decimal_separator == ",":
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "")
        normalized = normalized.replace(",", ".")
    return float(normalized)


def _parse_optional_benchmark_cell(
    raw_value: object,
    config: WorkflowConfig,
    warning_prefix: str,
) -> tuple[Optional[float], Optional[float], Optional[float], list[RowWarning]]:
    warnings: list[RowWarning] = []
    if raw_value is None:
        return None, None, None, warnings
    if isinstance(raw_value, float) and pd.isna(raw_value):
        return None, None, None, warnings

    text = str(raw_value).strip()
    if not text or text.lower() == "nan":
        return None, None, None, warnings

    compact = text.replace(" ", "")
    full_range = _FULL_RANGE_PATTERN.match(compact)
    if full_range is not None:
        low = _parse_decimal_fragment(full_range.group(1), config.processing.decimal_separator)
        high = _parse_decimal_fragment(full_range.group(2), config.processing.decimal_separator)
        if low > high:
            low, high = high, low
        if config.processing.midpoint_for_ranges:
            value = (low + high) / 2.0
            warnings.append(
                RowWarning(
                    f"{warning_prefix}_RANGE_MIDPOINT",
                    f"Range '{text}' converted to midpoint for benchmark comparison.",
                )
            )
        else:
            value = low
            warnings.append(
                RowWarning(
                    f"{warning_prefix}_RANGE_LOWER",
                    f"Range '{text}' converted to lower bound for benchmark comparison.",
                )
            )
        return value, low, high, warnings

    value, parse_warnings = parse_numeric_cell(
        raw_value,
        decimal_separator=config.processing.decimal_separator,
        midpoint_for_ranges=config.processing.midpoint_for_ranges,
        incomplete_range_use_single_bound=config.processing.incomplete_range_use_single_bound,
        warning_prefix=warning_prefix,
    )
    warnings.extend(parse_warnings)
    return value, None, None, warnings


def _normalize_benchmark_to_kg_per_kg(
    value: Optional[float],
    column_name: Optional[str],
    warning_prefix: str,
) -> tuple[Optional[float], list[RowWarning]]:
    if value is None:
        return None, []

    warnings: list[RowWarning] = []
    normalized = float(value)
    column_normalized = "" if column_name is None else canonicalize_name(column_name)

    explicit_percent_units = any(token in column_normalized for token in ("pct", "percent", "wt"))
    if explicit_percent_units and normalized > 1.0:
        normalized = normalized / 100.0
    elif normalized > 1.0:
        normalized = normalized / 100.0
        warnings.append(
            RowWarning(
                f"{warning_prefix}_UNIT_ASSUMED_PERCENT",
                f"Benchmark value from column '{column_name or 'unknown'}' assumed to be percent and converted to kg/kg.",
            )
        )

    return normalized, warnings


def _parse_oil_yield_benchmark_triplet(
    row: pd.Series,
    aliases: Dict[str, str],
    config: WorkflowConfig,
    base_key: str,
    warning_prefix: str,
) -> tuple[dict[str, Optional[float]], list[RowWarning]]:
    warnings: list[RowWarning] = []

    value_key = f"{base_key}"
    min_key = f"{base_key}_min"
    max_key = f"{base_key}_max"

    value, range_min, range_max, value_warnings = _parse_optional_benchmark_cell(
        row[aliases[value_key]] if value_key in aliases else None,
        config,
        f"{warning_prefix}_VALUE",
    )
    warnings.extend(value_warnings)

    explicit_min, _, _, min_warnings = _parse_optional_benchmark_cell(
        row[aliases[min_key]] if min_key in aliases else None,
        config,
        f"{warning_prefix}_MIN",
    )
    warnings.extend(min_warnings)

    explicit_max, _, _, max_warnings = _parse_optional_benchmark_cell(
        row[aliases[max_key]] if max_key in aliases else None,
        config,
        f"{warning_prefix}_MAX",
    )
    warnings.extend(max_warnings)

    low = explicit_min if explicit_min is not None else range_min
    high = explicit_max if explicit_max is not None else range_max
    representative = value

    if representative is None and low is not None and high is not None:
        representative = (low + high) / 2.0
    if representative is not None and low is None and high is None:
        low = representative
        high = representative

    if low is not None and high is not None and low > high:
        low, high = high, low
        warnings.append(
            RowWarning(
                f"{warning_prefix}_MIN_MAX_SWAPPED",
                "Benchmark min/max were reversed and have been swapped.",
            )
        )

    representative, rep_warnings = _normalize_benchmark_to_kg_per_kg(
        representative,
        aliases.get(value_key),
        warning_prefix,
    )
    low, low_warnings = _normalize_benchmark_to_kg_per_kg(
        low,
        aliases.get(min_key) if min_key in aliases else aliases.get(value_key),
        warning_prefix,
    )
    high, high_warnings = _normalize_benchmark_to_kg_per_kg(
        high,
        aliases.get(max_key) if max_key in aliases else aliases.get(value_key),
        warning_prefix,
    )
    warnings.extend(rep_warnings)
    warnings.extend(low_warnings)
    warnings.extend(high_warnings)

    return {"value": representative, "min": low, "max": high}, warnings


def _extract_literature_oil_yield_benchmarks(
    row: pd.Series,
    aliases: Dict[str, str],
    config: WorkflowConfig,
) -> tuple[dict[str, Optional[float]], list[RowWarning]]:
    warnings: list[RowWarning] = []
    values: dict[str, Optional[float]] = {
        "literature_oil_yield_ar_kg_per_kg": None,
        "literature_oil_yield_ar_min_kg_per_kg": None,
        "literature_oil_yield_ar_max_kg_per_kg": None,
        "literature_oil_yield_dry_kg_per_kg": None,
        "literature_oil_yield_dry_min_kg_per_kg": None,
        "literature_oil_yield_dry_max_kg_per_kg": None,
        "literature_oil_yield_daf_kg_per_kg": None,
        "literature_oil_yield_daf_min_kg_per_kg": None,
        "literature_oil_yield_daf_max_kg_per_kg": None,
    }

    for source_key, output_prefix, warning_prefix in (
        ("lit_oil_ar", "literature_oil_yield_ar", "FEED_LIT_OIL_AR"),
        ("lit_oil_dry", "literature_oil_yield_dry", "FEED_LIT_OIL_DRY"),
        ("lit_oil_daf", "literature_oil_yield_daf", "FEED_LIT_OIL_DAF"),
    ):
        parsed, parsed_warnings = _parse_oil_yield_benchmark_triplet(
            row,
            aliases,
            config,
            source_key,
            warning_prefix,
        )
        warnings.extend(parsed_warnings)
        values[f"{output_prefix}_kg_per_kg"] = parsed["value"]
        values[f"{output_prefix}_min_kg_per_kg"] = parsed["min"]
        values[f"{output_prefix}_max_kg_per_kg"] = parsed["max"]

    return values, warnings


def _bio_oil_aliases() -> Dict[str, tuple[str, ...]]:
    return {
        "category": ("Bio-oil Category", "Bio-oil category", "Category", "Unnamed: 0", "Unnamed:0"),
        "subcategory": (
            "Bio-oil Subcategory",
            "Bio-oil subcategory",
            "Subcategory",
            "Unnamed: 1",
            "Unnamed:1",
        ),
        "moisture": ("M", "Moisture"),
        "ash": ("Ash",),
        "c": ("C", "Carbon"),
        "h": ("H", "Hydrogen"),
        "o": ("O", "Oxygen"),
        "n": ("N", "Nitrogen"),
        "s": ("S", "Sulphur", "Sulfur"),
        "lhv": ("LHV", "LHV(MJ/kg)", "Lower Heating Value", "Lower heating value", "Unnamed: 9", "Unnamed:9"),
        "hhv": (
            "HHV",
            "HHV(MJ/kg)",
            "Higher Heating Value",
            "Higher heating value",
            "Unnamed: 10",
            "Unnamed:10",
        ),
        "reference": ("Reference", "References", "Unnamed: 11", "Unnamed:11"),
        "regionality": ("Regionality", "regionality", "Unnamed: 12", "Unnamed:12"),
        "measurement": (
            "Measurement or Calculation",
            "Measurement",
            "Calculation",
            "Unnamed: 13",
            "Unnamed:13",
            "Unnamed: 14",
            "Unnamed:14",
        ),
    }


def _build_feedstock_records(df: pd.DataFrame, config: WorkflowConfig) -> tuple[List[FeedstockRecord], List[RowWarning]]:
    aliases = _require_columns(
        df,
        _feedstock_aliases(),
        config.sheets.feedstock,
        required_targets=(
            "category",
            "subcategory",
            "ash",
            "c",
            "h",
            "o",
        ),
    )
    all_warnings: List[RowWarning] = []
    rows: List[FeedstockRecord] = []
    current_category: Optional[str] = None

    for _, row in df.iterrows():
        cat = str(row[aliases["category"]]).strip()
        sub = str(row[aliases["subcategory"]]).strip()

        if not cat or cat.lower() == "nan":
            cat = "" if current_category is None else current_category
        else:
            current_category = cat

        if not cat or cat.lower() == "nan" or not sub or sub.lower() == "nan":
            continue

        parsed: Dict[str, Optional[float]] = {}
        row_warnings: List[RowWarning] = []

        def _parse_field(target_key: str, warning_key: str) -> Optional[float]:
            if target_key not in aliases:
                row_warnings.append(
                    RowWarning(
                        f"{warning_key}_COLUMN_MISSING",
                        f"Column for '{target_key}' not found; value set by fallback if available.",
                    )
                )
                return None
            value, warnings = parse_numeric_cell(
                row[aliases[target_key]],
                decimal_separator=config.processing.decimal_separator,
                midpoint_for_ranges=config.processing.midpoint_for_ranges,
                incomplete_range_use_single_bound=config.processing.incomplete_range_use_single_bound,
                warning_prefix=warning_key,
            )
            row_warnings.extend(warnings)
            return value

        for target_key, warning_key in (
            ("moisture", "FEED_M"),
            ("vm", "FEED_VM"),
            ("fc", "FEED_FC"),
            ("ash", "FEED_ASH"),
            ("c", "FEED_C"),
            ("h", "FEED_H"),
            ("o", "FEED_O"),
            ("n", "FEED_N"),
            ("s", "FEED_S"),
        ):
            parsed[target_key] = _parse_field(target_key, warning_key)

        # Required chemistry basis for inclusion.
        if any(parsed[k] is None for k in ("ash", "c", "h", "o")):
            all_warnings.extend(row_warnings)
            continue

        # Step 1: allow proximate gaps with explicit helper metadata.
        if parsed["moisture"] is None:
            parsed["moisture"] = 0.0
            row_warnings.append(
                RowWarning(
                    "FEED_M_DEFAULT_0",
                    "Moisture missing; defaulted to 0.0 wt% for row inclusion.",
                )
            )

        if parsed["vm"] is None and parsed["fc"] is not None:
            parsed["vm"] = max(0.0, 100.0 - float(parsed["moisture"]) - float(parsed["fc"]) - float(parsed["ash"]))
            row_warnings.append(
                RowWarning(
                    "FEED_VM_BALANCE_ESTIMATE",
                    "VM missing; estimated from proximate balance 100 - M - FC - Ash.",
                )
            )
        elif parsed["fc"] is None and parsed["vm"] is not None:
            parsed["fc"] = max(0.0, 100.0 - float(parsed["moisture"]) - float(parsed["vm"]) - float(parsed["ash"]))
            row_warnings.append(
                RowWarning(
                    "FEED_FC_BALANCE_ESTIMATE",
                    "FC missing; estimated from proximate balance 100 - M - VM - Ash.",
                )
            )
        elif parsed["vm"] is None and parsed["fc"] is None:
            parsed["vm"] = 0.0
            parsed["fc"] = max(0.0, 100.0 - float(parsed["moisture"]) - float(parsed["ash"]))
            row_warnings.append(
                RowWarning(
                    "FEED_VM_DEFAULT_0",
                    "VM and FC missing; VM defaulted to 0.0 wt%.",
                )
            )
            row_warnings.append(
                RowWarning(
                    "FEED_FC_BALANCE_ESTIMATE",
                    "VM and FC missing; FC estimated from proximate balance 100 - M - Ash.",
                )
            )

        # Step 2: default missing N and S to 0.
        if parsed["n"] is None:
            parsed["n"] = 0.0
            row_warnings.append(
                RowWarning(
                    "FEED_N_DEFAULT_0",
                    "Nitrogen missing; defaulted to 0.0 wt% daf.",
                )
            )

        if parsed["s"] is None:
            parsed["s"] = 0.0
            row_warnings.append(
                RowWarning(
                    "FEED_S_DEFAULT_0",
                    "Sulfur missing; defaulted to 0.0 wt% daf.",
                )
            )

        feedstock_id = canonicalize_name(f"{cat}::{sub}")
        reference_raw = row[aliases["reference"]] if "reference" in aliases else None
        suitability_raw = row[aliases["suitability"]] if "suitability" in aliases else None
        regionality_raw = row[aliases["regionality"]] if "regionality" in aliases else None
        benchmark_values, benchmark_warnings = _extract_literature_oil_yield_benchmarks(row, aliases, config)
        row_warnings.extend(benchmark_warnings)

        rows.append(
            FeedstockRecord(
                feedstock_id=feedstock_id,
                category=cat,
                subcategory=sub,
                moisture_pct=float(parsed["moisture"]),
                volatile_matter_pct=float(parsed["vm"]),
                fixed_carbon_pct=float(parsed["fc"]),
                ash_pct=float(parsed["ash"]),
                c_pct_daf=float(parsed["c"]),
                h_pct_daf=float(parsed["h"]),
                o_pct_daf=float(parsed["o"]),
                n_pct_daf=float(parsed["n"]),
                s_pct_daf=float(parsed["s"]),
                reference=None if reference_raw is None else str(reference_raw),
                pyrolysis_suitability=None if suitability_raw is None else str(suitability_raw),
                regionality=None if regionality_raw is None else str(regionality_raw),
                literature_oil_yield_ar_kg_per_kg=benchmark_values["literature_oil_yield_ar_kg_per_kg"],
                literature_oil_yield_ar_min_kg_per_kg=benchmark_values["literature_oil_yield_ar_min_kg_per_kg"],
                literature_oil_yield_ar_max_kg_per_kg=benchmark_values["literature_oil_yield_ar_max_kg_per_kg"],
                literature_oil_yield_dry_kg_per_kg=benchmark_values["literature_oil_yield_dry_kg_per_kg"],
                literature_oil_yield_dry_min_kg_per_kg=benchmark_values["literature_oil_yield_dry_min_kg_per_kg"],
                literature_oil_yield_dry_max_kg_per_kg=benchmark_values["literature_oil_yield_dry_max_kg_per_kg"],
                literature_oil_yield_daf_kg_per_kg=benchmark_values["literature_oil_yield_daf_kg_per_kg"],
                literature_oil_yield_daf_min_kg_per_kg=benchmark_values["literature_oil_yield_daf_min_kg_per_kg"],
                literature_oil_yield_daf_max_kg_per_kg=benchmark_values["literature_oil_yield_daf_max_kg_per_kg"],
                warnings=row_warnings,
            )
        )
        all_warnings.extend(row_warnings)

    return rows, all_warnings


def _build_bio_oil_records(df: pd.DataFrame, config: WorkflowConfig) -> tuple[List[BioOilRecord], List[RowWarning]]:
    aliases = _require_columns(
        df,
        _bio_oil_aliases(),
        config.sheets.bio_oil,
        required_targets=("category", "subcategory", "c", "h", "o"),
    )
    all_warnings: List[RowWarning] = []
    rows: List[BioOilRecord] = []
    current_category: Optional[str] = None

    for _, row in df.iterrows():
        cat = str(row[aliases["category"]]).strip()
        sub = str(row[aliases["subcategory"]]).strip()

        if not cat or cat.lower() == "nan":
            cat = "" if current_category is None else current_category
        else:
            current_category = cat

        if not cat or cat.lower() == "nan" or not sub or sub.lower() == "nan":
            continue

        parsed: Dict[str, Optional[float]] = {}
        row_warnings: List[RowWarning] = []

        def _parse_field(target_key: str, warning_key: str) -> Optional[float]:
            if target_key not in aliases:
                row_warnings.append(
                    RowWarning(
                        f"{warning_key}_COLUMN_MISSING",
                        f"Column for '{target_key}' not found; value set by fallback if available.",
                    )
                )
                return None
            value, warnings = parse_numeric_cell(
                row[aliases[target_key]],
                decimal_separator=config.processing.decimal_separator,
                midpoint_for_ranges=config.processing.midpoint_for_ranges,
                incomplete_range_use_single_bound=config.processing.incomplete_range_use_single_bound,
                warning_prefix=warning_key,
            )
            row_warnings.extend(warnings)
            return value

        for target_key, warning_key in (
            ("moisture", "OIL_M"),
            ("ash", "OIL_ASH"),
            ("c", "OIL_C"),
            ("h", "OIL_H"),
            ("o", "OIL_O"),
            ("n", "OIL_N"),
            ("s", "OIL_S"),
        ):
            parsed[target_key] = _parse_field(target_key, warning_key)

        # Step 3: keep CHO rows even if moisture/ash are missing.
        if any(parsed[k] is None for k in ("c", "h", "o")):
            all_warnings.extend(row_warnings)
            continue

        if parsed["moisture"] is None:
            parsed["moisture"] = 0.0
            row_warnings.append(
                RowWarning(
                    "OIL_M_DEFAULT_0",
                    "Bio-oil moisture missing; defaulted to 0.0 wt%.",
                )
            )

        if parsed["ash"] is None:
            parsed["ash"] = 0.0
            row_warnings.append(
                RowWarning(
                    "OIL_ASH_DEFAULT_0",
                    "Bio-oil ash missing; defaulted to 0.0 wt%.",
                )
            )

        if parsed["n"] is None:
            parsed["n"] = 0.0
            row_warnings.append(
                RowWarning(
                    "OIL_N_DEFAULT_0",
                    "Bio-oil nitrogen missing; defaulted to 0.0 wt%.",
                )
            )

        if parsed["s"] is None:
            parsed["s"] = 0.0
            row_warnings.append(
                RowWarning(
                    "OIL_S_DEFAULT_0",
                    "Bio-oil sulfur missing; defaulted to 0.0 wt%.",
                )
            )

        lhv = None
        if "lhv" in aliases:
            lhv, warnings = parse_numeric_cell(
                row[aliases["lhv"]],
                decimal_separator=config.processing.decimal_separator,
                midpoint_for_ranges=config.processing.midpoint_for_ranges,
                incomplete_range_use_single_bound=config.processing.incomplete_range_use_single_bound,
                warning_prefix="OIL_LHV",
            )
            row_warnings.extend(warnings)

        hhv = None
        if "hhv" in aliases:
            hhv, warnings = parse_numeric_cell(
                row[aliases["hhv"]],
                decimal_separator=config.processing.decimal_separator,
                midpoint_for_ranges=config.processing.midpoint_for_ranges,
                incomplete_range_use_single_bound=config.processing.incomplete_range_use_single_bound,
                warning_prefix="OIL_HHV",
            )
            row_warnings.extend(warnings)

        reference_raw = row[aliases["reference"]] if "reference" in aliases else None
        regionality_raw = row[aliases["regionality"]] if "regionality" in aliases else None
        measurement_raw = row[aliases["measurement"]] if "measurement" in aliases else None

        rows.append(
            BioOilRecord(
                bio_oil_id=canonicalize_name(f"{cat}::{sub}"),
                category=cat,
                subcategory=sub,
                moisture_pct=float(parsed["moisture"]),
                ash_pct=float(parsed["ash"]),
                c_pct_daf=float(parsed["c"]),
                h_pct_daf=float(parsed["h"]),
                o_pct_daf=float(parsed["o"]),
                n_pct_daf=float(parsed["n"]),
                s_pct_daf=float(parsed["s"]),
                lhv_mj_per_kg=lhv,
                hhv_mj_per_kg=hhv,
                reference=None if reference_raw is None else str(reference_raw),
                regionality=None if regionality_raw is None else str(regionality_raw),
                measurement_or_calculation_true=parse_true_marker(measurement_raw),
                warnings=row_warnings,
            )
        )
        all_warnings.extend(row_warnings)

    return rows, all_warnings


def _map_feedstocks_to_bio_oils(
    feedstocks: List[FeedstockRecord],
    bio_oils: List[BioOilRecord],
    min_token_overlap: float,
    enable_levenshtein_matching: bool,
    levenshtein_min_ratio: float,
    matching_synonym_groups: Sequence[Sequence[str]],
) -> tuple[Dict[str, Optional[BioOilRecord]], List[str]]:
    synonym_lookup = _build_synonym_lookup(matching_synonym_groups)

    by_exact_raw = {oil.bio_oil_id: oil for oil in bio_oils}
    by_exact_normalized: Dict[str, BioOilRecord] = {}
    by_category: Dict[str, List[BioOilRecord]] = {}
    for oil in bio_oils:
        normalized_exact_key = canonicalize_name(
            (
                f"{_normalize_with_synonyms(oil.category, synonym_lookup)}::"
                f"{_normalize_with_synonyms(oil.subcategory, synonym_lookup)}"
            )
        )
        by_exact_normalized.setdefault(normalized_exact_key, oil)

        normalized_category_key = _normalize_with_synonyms(oil.category, synonym_lookup)
        by_category.setdefault(normalized_category_key, []).append(oil)

    mapping: Dict[str, Optional[BioOilRecord]] = {}
    unmatched: List[str] = []

    for feed in feedstocks:
        exact_key_raw = canonicalize_name(f"{feed.category}::{feed.subcategory}")
        if exact_key_raw in by_exact_raw:
            mapping[feed.feedstock_id] = by_exact_raw[exact_key_raw]
            continue

        normalized_category = _normalize_with_synonyms(feed.category, synonym_lookup)
        normalized_subcategory = _normalize_with_synonyms(feed.subcategory, synonym_lookup)
        normalized_exact_key = canonicalize_name(f"{normalized_category}::{normalized_subcategory}")
        if normalized_exact_key in by_exact_normalized:
            matched = by_exact_normalized[normalized_exact_key]
            mapping[feed.feedstock_id] = matched
            feed.warnings.append(
                RowWarning(
                    "MAP_SYNONYM_NORMALIZED",
                    f"Mapped via synonym normalization to '{matched.category}::{matched.subcategory}'.",
                )
            )
            continue

        best: Optional[BioOilRecord] = None
        best_score = 0.0
        for oil in bio_oils:
            score = token_overlap_score(
                normalized_subcategory,
                _normalize_with_synonyms(oil.subcategory, synonym_lookup),
            )
            if score > best_score:
                best_score = score
                best = oil

        if best is not None and best_score >= min_token_overlap:
            mapping[feed.feedstock_id] = best
            feed.warnings.append(
                RowWarning(
                    "MAP_SUBCATEGORY_FUZZY",
                    f"Mapped via fuzzy subcategory match to '{best.category}::{best.subcategory}' (score={best_score:.2f}).",
                )
            )
            continue

        if enable_levenshtein_matching:
            best_ratio = 0.0
            best_levenshtein: Optional[BioOilRecord] = None
            for oil in bio_oils:
                ratio = _levenshtein_ratio(
                    normalized_subcategory,
                    _normalize_with_synonyms(oil.subcategory, synonym_lookup),
                )
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_levenshtein = oil

            if best_levenshtein is not None and best_ratio >= levenshtein_min_ratio:
                mapping[feed.feedstock_id] = best_levenshtein
                feed.warnings.append(
                    RowWarning(
                        "MAP_SUBCATEGORY_LEVENSHTEIN",
                        (
                            f"Mapped via Levenshtein fallback to '{best_levenshtein.category}::"
                            f"{best_levenshtein.subcategory}' (ratio={best_ratio:.1f})."
                        ),
                    )
                )
                continue

        # Step 4: category-level fallback matching.
        cat_candidates = by_category.get(normalized_category, [])
        if cat_candidates:
            best_cat = max(
                cat_candidates,
                key=lambda oil: token_overlap_score(
                    normalized_subcategory,
                    _normalize_with_synonyms(oil.subcategory, synonym_lookup),
                )
            )
            mapping[feed.feedstock_id] = best_cat
            feed.warnings.append(
                RowWarning(
                    "MAP_CATEGORY_FALLBACK",
                    (
                        f"No reliable subcategory match; used category-level fallback "
                        f"'{best_cat.category}::{best_cat.subcategory}'."
                    ),
                )
            )
        else:
            mapping[feed.feedstock_id] = None
            unmatched.append(feed.feedstock_id)
            feed.warnings.append(
                RowWarning(
                    "MAP_NO_BIO_OIL_MATCH",
                    "No bio-oil mapping found at subcategory or category level; generic fallback species may be used later.",
                )
            )

    return mapping, unmatched


def _build_synonym_lookup(groups: Sequence[Sequence[str]]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for group in groups:
        canonical = [canonicalize_name(value) for value in group if str(value).strip()]
        canonical = [value for value in canonical if value]
        if not canonical:
            continue

        preferred = canonical[0]
        for value in canonical:
            lookup[value] = preferred
    return lookup


def _normalize_with_synonyms(value: str, synonym_lookup: Dict[str, str]) -> str:
    normalized = canonicalize_name(value)
    if not normalized:
        return normalized

    direct = synonym_lookup.get(normalized)
    if direct is not None:
        normalized = direct

    tokens = [synonym_lookup.get(token, token) for token in normalized.split()]
    return " ".join(tokens)


def _levenshtein_ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if thefuzz_fuzz is not None:
        return float(thefuzz_fuzz.token_set_ratio(left, right))
    return 100.0 * SequenceMatcher(None, left, right).ratio()


def parse_input_workbook(excel_path: str, config: WorkflowConfig) -> ParsedWorkbook:
    """Parse, normalize, and map both relevant workbook sheets."""

    parse_warnings: List[RowWarning] = []

    with pd.ExcelFile(excel_path) as workbook:
        feed_sheet, feed_sheet_warning = _resolve_sheet_name(
            workbook.sheet_names,
            config.sheets.feedstock,
            alternatives=("W.Proximate+Ultimate", "w proximate+ultimate", "w proximate ultimate"),
        )
        bio_sheet, bio_sheet_warning = _resolve_sheet_name(
            workbook.sheet_names,
            config.sheets.bio_oil,
            alternatives=("Bio-oil values", "bio oil values", "bio-oil-values"),
        )

        if feed_sheet_warning is not None:
            parse_warnings.append(feed_sheet_warning)
        if bio_sheet_warning is not None:
            parse_warnings.append(bio_sheet_warning)

        feed_df, feed_header_warning = _read_sheet_with_detected_header(
            workbook,
            feed_sheet,
            _feedstock_aliases(),
            required_targets=(
                "category",
                "subcategory",
                "ash",
                "c",
                "h",
                "o",
            ),
        )
        bio_df, bio_header_warning = _read_sheet_with_detected_header(
            workbook,
            bio_sheet,
            _bio_oil_aliases(),
            required_targets=("category", "subcategory", "c", "h", "o"),
        )

        if feed_header_warning is not None:
            parse_warnings.append(feed_header_warning)
        if bio_header_warning is not None:
            parse_warnings.append(bio_header_warning)

    feedstocks, feed_warnings = _build_feedstock_records(feed_df, config)
    bio_oils, bio_warnings = _build_bio_oil_records(bio_df, config)
    mapping, unmatched = _map_feedstocks_to_bio_oils(
        feedstocks,
        bio_oils,
        min_token_overlap=config.processing.canonical_match_min_token_overlap,
        enable_levenshtein_matching=config.processing.enable_levenshtein_matching,
        levenshtein_min_ratio=config.processing.levenshtein_min_ratio,
        matching_synonym_groups=config.processing.matching_synonym_groups,
    )

    return ParsedWorkbook(
        feedstocks=feedstocks,
        bio_oils=bio_oils,
        feedstock_to_bio_oil=mapping,
        unmatched_feedstocks=unmatched,
        parse_warnings=[*parse_warnings, *feed_warnings, *bio_warnings],
    )
