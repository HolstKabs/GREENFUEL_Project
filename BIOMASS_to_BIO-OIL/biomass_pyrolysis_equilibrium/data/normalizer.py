"""Normalization helpers for messy spreadsheet values."""

from __future__ import annotations

import re
import math
from typing import Iterable, Optional

from ..models import RowWarning


def canonicalize_name(value: str) -> str:
    """Normalize names for matching across sheets."""

    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", str(value).strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def token_overlap_score(left: str, right: str) -> float:
    """Compute token overlap ratio in [0, 1] for fuzzy matching."""

    left_tokens = set(canonicalize_name(left).split())
    right_tokens = set(canonicalize_name(right).split())
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    return overlap / max(len(left_tokens), len(right_tokens))


def _normalize_number_string(text: str, decimal_separator: str) -> str:
    normalized = text.strip()
    if decimal_separator == ",":
        normalized = normalized.replace(".", "") if "," in normalized and "." in normalized else normalized
        normalized = normalized.replace(",", ".")
    return normalized


def parse_numeric_cell(
    raw_value: object,
    *,
    decimal_separator: str,
    midpoint_for_ranges: bool,
    incomplete_range_use_single_bound: bool,
    warning_prefix: str,
) -> tuple[Optional[float], list[RowWarning]]:
    """Parse single values or ranges from Excel cell content."""

    warnings: list[RowWarning] = []

    if raw_value is None:
        warnings.append(RowWarning(f"{warning_prefix}_MISSING", "Missing numeric value."))
        return None, warnings

    if isinstance(raw_value, (int, float)):
        if isinstance(raw_value, float) and math.isnan(raw_value):
            warnings.append(RowWarning(f"{warning_prefix}_MISSING", "Missing numeric value."))
            return None, warnings
        return float(raw_value), warnings

    text = str(raw_value).strip()
    if not text:
        warnings.append(RowWarning(f"{warning_prefix}_EMPTY", "Empty numeric value."))
        return None, warnings

    compact = text.replace(" ", "")
    # Handle complete ranges like 10-20 or 10,5-20,7
    full_range = re.match(r"^([-+]?\d+(?:[\.,]\d+)?)[-–]([-+]?\d+(?:[\.,]\d+)?)$", compact)
    if full_range:
        low = float(_normalize_number_string(full_range.group(1), decimal_separator))
        high = float(_normalize_number_string(full_range.group(2), decimal_separator))
        if midpoint_for_ranges:
            warnings.append(RowWarning(f"{warning_prefix}_RANGE_MIDPOINT", f"Range '{text}' converted to midpoint."))
            return (low + high) / 2.0, warnings
        warnings.append(RowWarning(f"{warning_prefix}_RANGE_LOWER", f"Range '{text}' converted to lower bound."))
        return low, warnings

    # Handle incomplete ranges like 10- or -20
    incomplete_left = re.match(r"^([-+]?\d+(?:[\.,]\d+)?)[-–]$", compact)
    incomplete_right = re.match(r"^[-–]([-+]?\d+(?:[\.,]\d+)?)$", compact)
    if incomplete_left or incomplete_right:
        if not incomplete_range_use_single_bound:
            warnings.append(
                RowWarning(
                    f"{warning_prefix}_INCOMPLETE_RANGE",
                    f"Incomplete range '{text}' requires clarification.",
                    severity="error",
                )
            )
            return None, warnings

        chosen = incomplete_left.group(1) if incomplete_left else incomplete_right.group(1)
        warnings.append(
            RowWarning(
                f"{warning_prefix}_INCOMPLETE_RANGE_ASSUMED",
                f"Incomplete range '{text}' converted using available bound.",
            )
        )
        return float(_normalize_number_string(chosen, decimal_separator)), warnings

    normalized = _normalize_number_string(compact, decimal_separator)
    try:
        return float(normalized), warnings
    except ValueError:
        warnings.append(
            RowWarning(
                f"{warning_prefix}_PARSE_FAILED",
                f"Could not parse numeric value '{text}'.",
                severity="error",
            )
        )
        return None, warnings


def parse_true_marker(raw_value: object) -> Optional[bool]:
    """Parse TRUE/FALSE-like flags from strings."""

    if raw_value is None:
        return None
    text = str(raw_value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def first_matching_column(columns: Iterable[str], aliases: Iterable[str]) -> Optional[str]:
    """Return first matching column name among aliases (case-insensitive)."""

    by_lower = {str(col).strip().lower(): col for col in columns}
    for alias in aliases:
        hit = by_lower.get(alias.strip().lower())
        if hit is not None:
            return hit
    return None
