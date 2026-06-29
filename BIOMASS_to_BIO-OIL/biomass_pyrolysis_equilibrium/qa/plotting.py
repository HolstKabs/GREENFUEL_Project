"""Plotting utilities for workflow result analytics."""

from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import pandas as pd


YIELD_BASIS_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("oil_yield_kg_per_kg", "", "As-received", "kg/kg as-received"),
    ("oil_yield_kg_per_kg_dry", "_dry", "Dry basis", "kg/kg dry"),
    ("oil_yield_kg_per_kg_daf", "_daf", "DAF basis", "kg/kg daf"),
)


ROOT_CATEGORY_SCENARIOS: tuple[str, str, str] = ("P10", "Mean", "P90")


ROOT_CATEGORY_LOW_PERCENTILE: float = 0.10
ROOT_CATEGORY_HIGH_PERCENTILE: float = 0.90


STACK_COMPONENT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("oil_yield", "Oil", "#ff7f0e"),
)


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _prepare_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _available_yield_basis_specs(results_df: pd.DataFrame) -> list[tuple[str, str, str, str]]:
    return [spec for spec in YIELD_BASIS_SPECS if spec[0] in results_df.columns]


def _basis_component_columns(oil_yield_column: str) -> tuple[str, str, str]:
    suffix = ""
    if oil_yield_column.endswith("_dry"):
        suffix = "_dry"
    elif oil_yield_column.endswith("_daf"):
        suffix = "_daf"
    return (
        oil_yield_column,
        f"gas_yield_kg_per_kg{suffix}",
        f"char_yield_kg_per_kg{suffix}",
    )


def _normalize_bool_series(series: pd.Series) -> pd.Series:
    normalized: list[bool | None] = []
    for value in series:
        if pd.isna(value):
            normalized.append(None)
            continue
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "y"}:
                normalized.append(True)
                continue
            if lowered in {"false", "0", "no", "n"}:
                normalized.append(False)
                continue
            normalized.append(None)
            continue
        normalized.append(bool(value))
    return pd.Series(normalized, index=series.index, dtype="boolean")


def _pick_category_extreme_row(df: pd.DataFrame, value_column: str, mode: str) -> pd.Series:
    if mode not in {"min", "max"}:
        raise ValueError(f"Unsupported mode '{mode}'. Expected 'min' or 'max'.")

    sort_columns = [value_column]
    ascending = [mode == "min"]
    for optional in ("temperature_c", "pressure_bar", "feedstock_id", "subcategory"):
        if optional in df.columns:
            sort_columns.append(optional)
            ascending.append(True)

    ordered = df.sort_values(sort_columns, ascending=ascending, kind="mergesort")
    return ordered.iloc[0]


def _converged_to_unconverged_flag(value: object) -> bool | None:
    if pd.isna(value):
        return None
    return not bool(value)


def _aggregate_root_category_scenarios_one_basis(
    results_df: pd.DataFrame,
    oil_yield_column: str,
) -> pd.DataFrame:
    needed = {"category", oil_yield_column}
    if not needed.issubset(results_df.columns):
        return pd.DataFrame()

    df = results_df.copy()
    df["category"] = df["category"].astype(str).str.strip()
    df = df[(df["category"] != "") & (df["category"].str.lower() != "nan")]
    if df.empty:
        return pd.DataFrame()

    df[oil_yield_column] = _to_numeric(df[oil_yield_column])
    df = df.dropna(subset=[oil_yield_column]).copy()
    if df.empty:
        return pd.DataFrame()

    if "converged" in df.columns:
        df["converged_normalized"] = _normalize_bool_series(df["converged"])
    else:
        df["converged_normalized"] = pd.Series([None] * len(df), index=df.index, dtype="boolean")

    records: list[dict[str, object]] = []
    for category, group in df.groupby("category", sort=True):
        oil_values = _to_numeric(group[oil_yield_column]).dropna()
        if oil_values.empty:
            continue

        converged_values = group["converged_normalized"].dropna()
        unconverged_share: float | None
        if converged_values.empty:
            unconverged_share = None
        else:
            unconverged_share = float((~converged_values).sum()) / float(len(converged_values))

        unconverged_flag = None if unconverged_share is None else unconverged_share > 0.0
        for scenario, value in (
            ("P10", float(oil_values.quantile(ROOT_CATEGORY_LOW_PERCENTILE))),
            ("Mean", float(oil_values.mean())),
            ("P90", float(oil_values.quantile(ROOT_CATEGORY_HIGH_PERCENTILE))),
        ):
            records.append(
                {
                    "category": category,
                    "scenario": scenario,
                    "oil_yield": value,
                    "unconverged_flag": unconverged_flag,
                    "unconverged_share": unconverged_share,
                    "row_count": int(len(group)),
                }
            )

    aggregated = pd.DataFrame(records)
    if aggregated.empty:
        return aggregated

    aggregated["total_yield"] = aggregated["oil_yield"]
    return aggregated


def _root_category_legend_handles() -> list[object]:
    handles: list[object] = []
    for _, label, color in STACK_COMPONENT_SPECS:
        handles.append(Patch(facecolor=color, edgecolor="white", label=label))
    handles.append(
        Line2D(
            [0],
            [0],
            color="#b22222",
            linestyle="--",
            linewidth=1.5,
            label="Contains unconverged runs",
        )
    )
    return handles


def _draw_root_category_scenario_axis(
    ax: plt.Axes,
    scenario_df: pd.DataFrame,
    scenario: str,
    basis_unit: str,
    y_label: str,
) -> None:
    if scenario_df.empty:
        ax.set_axis_off()
        ax.text(0.5, 0.5, f"No data for {scenario.lower()} scenario", ha="center", va="center")
        return

    scenario_df = scenario_df.sort_values("category").reset_index(drop=True)
    x_positions = list(range(len(scenario_df)))

    cumulative = pd.Series(0.0, index=scenario_df.index)
    for key, _, color in STACK_COMPONENT_SPECS:
        values = _to_numeric(scenario_df[key]).fillna(0.0)
        ax.bar(
            x_positions,
            values,
            bottom=cumulative,
            width=0.78,
            color=color,
            edgecolor="white",
            linewidth=0.4,
        )
        cumulative = cumulative + values

    totals = cumulative.to_list()
    max_total = max(totals) if totals else 0.0
    offset = 0.02 * max(1.0, max_total)

    for idx, total in enumerate(totals):
        unconverged_flag = scenario_df.loc[idx, "unconverged_flag"]
        if pd.isna(unconverged_flag) or not bool(unconverged_flag):
            continue

        ax.add_patch(
            Rectangle(
                (idx - 0.39, 0.0),
                0.78,
                max(total, 0.0),
                fill=False,
                edgecolor="#b22222",
                linestyle="--",
                linewidth=1.0,
            )
        )

        if scenario == "Mean" and pd.notna(scenario_df.loc[idx, "unconverged_share"]):
            flag_text = f"! {float(scenario_df.loc[idx, 'unconverged_share']):.0%}"
        else:
            flag_text = "!"

        ax.text(
            idx,
            total + offset,
            flag_text,
            color="#b22222",
            fontsize=7,
            rotation=90,
            ha="center",
            va="bottom",
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenario_df["category"], rotation=35, ha="right")
    ax.set_title(f"{scenario} scenario")
    ax.set_ylabel(y_label)
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(0.0, max_total * 1.14 if max_total > 0.0 else 1.0)


def _plot_root_category_oil_percentile_summary_one_basis(
    results_df: pd.DataFrame,
    output_dir: Path,
    yield_column: str,
    filename_suffix: str,
    basis_title: str,
    basis_unit: str,
) -> Path | None:
    aggregated = _aggregate_root_category_scenarios_one_basis(results_df, yield_column)
    if aggregated.empty:
        return None

    fig, axes = plt.subplots(1, len(ROOT_CATEGORY_SCENARIOS), figsize=(16.5, 5.8), sharey=True)
    for idx, scenario in enumerate(ROOT_CATEGORY_SCENARIOS):
        scenario_df = aggregated[aggregated["scenario"] == scenario]
        y_label = f"Yield [{basis_unit}]" if idx == 0 else ""
        _draw_root_category_scenario_axis(axes[idx], scenario_df, scenario, basis_unit, y_label)

    fig.suptitle(f"Root Category Oil Yield Percentile Summary ({basis_title})")
    fig.legend(
        handles=_root_category_legend_handles(),
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 1.03),
    )

    output = output_dir / f"root_category_oil_percentile_summary{filename_suffix}.png"
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.92))
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_root_category_oil_percentile_summary_all_bases(results_df: pd.DataFrame, output_dir: Path) -> Path | None:
    aggregated_by_basis: list[tuple[tuple[str, str, str, str], pd.DataFrame]] = []
    for basis_spec in _available_yield_basis_specs(results_df):
        aggregated = _aggregate_root_category_scenarios_one_basis(results_df, basis_spec[0])
        if not aggregated.empty:
            aggregated_by_basis.append((basis_spec, aggregated))

    if len(aggregated_by_basis) < 2:
        return None

    row_count = len(aggregated_by_basis)
    col_count = len(ROOT_CATEGORY_SCENARIOS)
    fig, axes = plt.subplots(
        row_count,
        col_count,
        figsize=(16.5, 4.8 * row_count),
        sharey="row",
    )

    if row_count == 1:
        axes = [axes]

    for row_idx, (basis_spec, aggregated) in enumerate(aggregated_by_basis):
        _, _, basis_title, basis_unit = basis_spec
        for col_idx, scenario in enumerate(ROOT_CATEGORY_SCENARIOS):
            scenario_df = aggregated[aggregated["scenario"] == scenario]
            y_label = f"{basis_title}\nYield [{basis_unit}]" if col_idx == 0 else ""
            _draw_root_category_scenario_axis(
                axes[row_idx][col_idx],
                scenario_df,
                scenario,
                basis_unit,
                y_label,
            )

    fig.suptitle("Root Category Oil Yield Percentile Summary (All Bases)")
    fig.legend(
        handles=_root_category_legend_handles(),
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 1.01),
    )

    output = output_dir / "root_category_oil_percentile_summary_all_bases.png"
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_root_category_oil_percentile_summary(results_df: pd.DataFrame, output_dir: Path) -> List[Path]:
    outputs: List[Path] = []
    for yield_column, filename_suffix, basis_title, basis_unit in _available_yield_basis_specs(results_df):
        maybe_path = _plot_root_category_oil_percentile_summary_one_basis(
            results_df,
            output_dir,
            yield_column,
            filename_suffix,
            basis_title,
            basis_unit,
        )
        if maybe_path is not None:
            outputs.append(maybe_path)

    combined_path = _plot_root_category_oil_percentile_summary_all_bases(results_df, output_dir)
    if combined_path is not None:
        outputs.append(combined_path)

    return outputs


def _plot_van_krevelen_one_basis(
    results_df: pd.DataFrame,
    output_dir: Path,
    yield_column: str,
    filename_suffix: str,
    basis_title: str,
    basis_unit: str,
) -> Path | None:
    needed = {"feedstock_c_pct_daf", "feedstock_h_pct_daf", "feedstock_o_pct_daf", yield_column}
    if not needed.issubset(results_df.columns):
        return None

    c = _to_numeric(results_df["feedstock_c_pct_daf"])
    h = _to_numeric(results_df["feedstock_h_pct_daf"])
    o = _to_numeric(results_df["feedstock_o_pct_daf"])
    oil_yield = _to_numeric(results_df[yield_column])

    mask = (c > 0) & h.notna() & o.notna() & oil_yield.notna()
    if not mask.any():
        return None

    h_over_c = h[mask] / c[mask]
    o_over_c = o[mask] / c[mask]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    scatter = ax.scatter(o_over_c, h_over_c, c=oil_yield[mask], cmap="viridis", alpha=0.8, edgecolors="none")
    ax.set_xlabel("O/C")
    ax.set_ylabel("H/C")
    if filename_suffix:
        ax.set_title(f"Van Krevelen Diagram ({basis_title})")
    else:
        ax.set_title("Van Krevelen Diagram")
    ax.grid(True, alpha=0.3)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label(f"Oil yield [{basis_unit}]")

    output = output_dir / f"van_krevelen{filename_suffix}.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_van_krevelen(results_df: pd.DataFrame, output_dir: Path) -> List[Path]:
    outputs: List[Path] = []
    for yield_column, filename_suffix, basis_title, basis_unit in _available_yield_basis_specs(results_df):
        maybe_path = _plot_van_krevelen_one_basis(
            results_df,
            output_dir,
            yield_column,
            filename_suffix,
            basis_title,
            basis_unit,
        )
        if maybe_path is not None:
            outputs.append(maybe_path)
    return outputs


def _ternary_xy(c: float, h: float, o: float) -> tuple[float, float] | None:
    total = c + h + o
    if total <= 0:
        return None
    cf = c / total
    hf = h / total
    of = o / total
    x = hf + 0.5 * of
    y = (sqrt(3.0) / 2.0) * of
    _ = cf  # retained for readability in barycentric derivation
    return x, y


def _plot_ternary_cho(results_df: pd.DataFrame, output_dir: Path) -> Path | None:
    needed = {"feedstock_c_pct_daf", "feedstock_h_pct_daf", "feedstock_o_pct_daf"}
    if not needed.issubset(results_df.columns):
        return None

    subset = results_df[["feedstock_id", "feedstock_c_pct_daf", "feedstock_h_pct_daf", "feedstock_o_pct_daf"]].drop_duplicates()
    c_vals = _to_numeric(subset["feedstock_c_pct_daf"])
    h_vals = _to_numeric(subset["feedstock_h_pct_daf"])
    o_vals = _to_numeric(subset["feedstock_o_pct_daf"])

    points_x: list[float] = []
    points_y: list[float] = []
    for c, h, o in zip(c_vals, h_vals, o_vals):
        if pd.isna(c) or pd.isna(h) or pd.isna(o):
            continue
        xy = _ternary_xy(float(c), float(h), float(o))
        if xy is None:
            continue
        points_x.append(xy[0])
        points_y.append(xy[1])

    if not points_x:
        return None

    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    triangle_x = [0.0, 1.0, 0.5, 0.0]
    triangle_y = [0.0, 0.0, sqrt(3.0) / 2.0, 0.0]
    ax.plot(triangle_x, triangle_y, color="black", linewidth=1.2)
    ax.scatter(points_x, points_y, s=20, alpha=0.75, color="#1f77b4")

    ax.text(-0.03, -0.03, "C", fontsize=11)
    ax.text(1.01, -0.03, "H", fontsize=11)
    ax.text(0.49, sqrt(3.0) / 2.0 + 0.03, "O", fontsize=11)
    ax.set_title("C-H-O Ternary Composition")
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.08, sqrt(3.0) / 2.0 + 0.08)
    ax.set_aspect("equal")
    ax.axis("off")

    output = output_dir / "ternary_cho.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_yield_vs_temperature_one_basis(
    results_df: pd.DataFrame,
    output_dir: Path,
    yield_column: str,
    filename_suffix: str,
    basis_title: str,
    basis_unit: str,
) -> Path | None:
    needed = {"temperature_c", "pressure_bar", yield_column}
    if not needed.issubset(results_df.columns):
        return None

    df = results_df.copy()
    df["temperature_c"] = _to_numeric(df["temperature_c"])
    df["pressure_bar"] = _to_numeric(df["pressure_bar"])
    df[yield_column] = _to_numeric(df[yield_column])

    df = df.dropna(subset=["temperature_c", "pressure_bar", yield_column])
    if df.empty or df["temperature_c"].nunique() < 2:
        return None

    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    grouped = (
        df.groupby(["pressure_bar", "temperature_c"], as_index=False)[yield_column]
        .mean()
        .sort_values(["pressure_bar", "temperature_c"])
    )

    for pressure_bar, group in grouped.groupby("pressure_bar"):
        ax.plot(
            group["temperature_c"],
            group[yield_column],
            marker="o",
            linewidth=1.5,
            markersize=4,
            label=f"{pressure_bar:g} bar",
        )

    ax.set_xlabel("Temperature [C]")
    ax.set_ylabel(f"Mean oil yield [{basis_unit}]")
    if filename_suffix:
        ax.set_title(f"Yield vs Temperature ({basis_title})")
    else:
        ax.set_title("Yield vs Temperature")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    output = output_dir / f"yield_vs_temperature{filename_suffix}.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_yield_vs_temperature(results_df: pd.DataFrame, output_dir: Path) -> List[Path]:
    outputs: List[Path] = []
    for yield_column, filename_suffix, basis_title, basis_unit in _available_yield_basis_specs(results_df):
        maybe_path = _plot_yield_vs_temperature_one_basis(
            results_df,
            output_dir,
            yield_column,
            filename_suffix,
            basis_title,
            basis_unit,
        )
        if maybe_path is not None:
            outputs.append(maybe_path)
    return outputs


def _plot_yield_basis_comparison(results_df: pd.DataFrame, output_dir: Path) -> Path | None:
    if "temperature_c" not in results_df.columns:
        return None

    available_specs = _available_yield_basis_specs(results_df)
    if len(available_specs) < 2:
        return None

    df = results_df.copy()
    df["temperature_c"] = _to_numeric(df["temperature_c"])

    value_columns: list[str] = []
    for yield_column, _, _, _ in available_specs:
        df[yield_column] = _to_numeric(df[yield_column])
        value_columns.append(yield_column)

    df = df.dropna(subset=["temperature_c"])
    if df.empty or df["temperature_c"].nunique() < 2:
        return None

    grouped = (
        df.groupby("temperature_c", as_index=False)[value_columns]
        .mean()
        .sort_values("temperature_c")
    )

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for yield_column, _, basis_title, _ in available_specs:
        if yield_column not in grouped.columns:
            continue
        series = grouped[yield_column]
        if series.notna().sum() == 0:
            continue
        ax.plot(
            grouped["temperature_c"],
            series,
            marker="o",
            linewidth=1.5,
            markersize=4,
            label=basis_title,
        )

    ax.set_xlabel("Temperature [C]")
    ax.set_ylabel("Mean oil yield [kg/kg by basis]")
    ax.set_title("Yield Basis Comparison")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    output = output_dir / "yield_basis_comparison.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_peak_yield_vs_temperature_one_basis(
    results_df: pd.DataFrame,
    output_dir: Path,
    yield_column: str,
    filename_suffix: str,
    basis_title: str,
    basis_unit: str,
) -> Path | None:
    needed = {"feedstock_id", "temperature_c", yield_column}
    if not needed.issubset(results_df.columns):
        return None

    df = results_df.copy()
    df["temperature_c"] = _to_numeric(df["temperature_c"])
    df[yield_column] = _to_numeric(df[yield_column])
    df = df.dropna(subset=["feedstock_id", "temperature_c", yield_column]).copy()
    if df.empty:
        return None

    df["feedstock_id"] = df["feedstock_id"].astype(str).str.strip()
    df = df[(df["feedstock_id"] != "") & (df["feedstock_id"].str.lower() != "nan")]
    if df.empty:
        return None

    # Highest yield per biomass; ties are resolved by choosing the lowest temperature.
    peak_rows = (
        df.sort_values(["feedstock_id", yield_column, "temperature_c"], ascending=[True, False, True])
        .drop_duplicates(subset=["feedstock_id"], keep="first")
        .sort_values(["temperature_c", "feedstock_id"])
    )
    if peak_rows.empty:
        return None

    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    biomass_count = peak_rows["feedstock_id"].nunique()

    if biomass_count <= 20:
        for feedstock_id, group in peak_rows.groupby("feedstock_id"):
            ax.scatter(
                group["temperature_c"],
                group[yield_column],
                s=36,
                alpha=0.85,
                label=feedstock_id,
            )
        ax.legend(frameon=False, fontsize=8, ncol=2)
    else:
        ax.scatter(
            peak_rows["temperature_c"],
            peak_rows[yield_column],
            s=28,
            alpha=0.8,
            color="#1f77b4",
        )

    ax.set_xlabel("Temperature at peak oil yield [C]")
    ax.set_ylabel(f"Peak oil yield [{basis_unit}]")
    if filename_suffix:
        ax.set_title(f"Peak Oil Yield vs Temperature by Biomass ({basis_title})")
    else:
        ax.set_title("Peak Oil Yield vs Temperature by Biomass")
    ax.grid(True, alpha=0.3)
    ax.text(
        0.01,
        0.01,
        f"Biomass types: {biomass_count}",
        transform=ax.transAxes,
        fontsize=8,
        alpha=0.7,
        ha="left",
        va="bottom",
    )

    output = output_dir / f"peak_yield_vs_temperature{filename_suffix}.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_peak_yield_vs_temperature(results_df: pd.DataFrame, output_dir: Path) -> List[Path]:
    outputs: List[Path] = []
    for yield_column, filename_suffix, basis_title, basis_unit in _available_yield_basis_specs(results_df):
        maybe_path = _plot_peak_yield_vs_temperature_one_basis(
            results_df,
            output_dir,
            yield_column,
            filename_suffix,
            basis_title,
            basis_unit,
        )
        if maybe_path is not None:
            outputs.append(maybe_path)
    return outputs


def _plot_peak_yield_basis_comparison(results_df: pd.DataFrame, output_dir: Path) -> Path | None:
    needed = {"feedstock_id", "temperature_c"}
    if not needed.issubset(results_df.columns):
        return None

    available_specs = _available_yield_basis_specs(results_df)
    if len(available_specs) < 2:
        return None

    df = results_df.copy()
    df["temperature_c"] = _to_numeric(df["temperature_c"])
    df = df.dropna(subset=["feedstock_id", "temperature_c"]).copy()
    if df.empty:
        return None

    df["feedstock_id"] = df["feedstock_id"].astype(str).str.strip()
    df = df[(df["feedstock_id"] != "") & (df["feedstock_id"].str.lower() != "nan")]
    if df.empty:
        return None

    marker_cycle = (
        "o",
        "s",
        "^",
        "D",
        "v",
        "P",
        "X",
        "<",
        ">",
        "*",
        "h",
        "8",
        "p",
    )
    feedstock_ids = sorted(df["feedstock_id"].unique())
    marker_by_feedstock = {
        feedstock_id: marker_cycle[i % len(marker_cycle)]
        for i, feedstock_id in enumerate(feedstock_ids)
    }

    basis_color_by_column = {
        "oil_yield_kg_per_kg": "#1f77b4",
        "oil_yield_kg_per_kg_dry": "#ff7f0e",
        "oil_yield_kg_per_kg_daf": "#2ca02c",
    }

    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    plotted_any = False
    basis_handles: list[Line2D] = []
    for yield_column, _, basis_title, _ in available_specs:
        if yield_column not in df.columns:
            continue

        basis_df = df[["feedstock_id", "temperature_c", yield_column]].copy()
        basis_df[yield_column] = _to_numeric(basis_df[yield_column])
        basis_df = basis_df.dropna(subset=[yield_column])
        if basis_df.empty:
            continue

        peak_rows = (
            basis_df.sort_values(["feedstock_id", yield_column, "temperature_c"], ascending=[True, False, True])
            .drop_duplicates(subset=["feedstock_id"], keep="first")
            .sort_values(["temperature_c", "feedstock_id"])
        )
        if peak_rows.empty:
            continue

        color = basis_color_by_column.get(yield_column, "#1f77b4")
        for _, row in peak_rows.iterrows():
            feedstock_id = row["feedstock_id"]
            ax.scatter(
                row["temperature_c"],
                row[yield_column],
                s=34,
                alpha=0.8,
                marker=marker_by_feedstock[feedstock_id],
                color=color,
                edgecolors="black",
                linewidths=0.25,
            )

        basis_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="None",
                markerfacecolor=color,
                markeredgecolor="black",
                markeredgewidth=0.25,
                markersize=7,
                label=basis_title,
            )
        )
        plotted_any = True

    if not plotted_any:
        plt.close(fig)
        return None

    ax.set_xlabel("Temperature at peak oil yield [C]")
    ax.set_ylabel("Peak oil yield [kg/kg by basis]")
    ax.set_title("Peak Yield Basis Comparison")
    ax.grid(True, alpha=0.3)

    basis_legend = ax.legend(handles=basis_handles, title="Yield basis", frameon=False, loc="upper left")
    ax.add_artist(basis_legend)

    max_feedstock_legend = 14
    feedstock_ids_for_legend = feedstock_ids[:max_feedstock_legend]
    feedstock_handles = [
        Line2D(
            [0],
            [0],
            marker=marker_by_feedstock[feedstock_id],
            linestyle="None",
            markerfacecolor="#b0b0b0",
            markeredgecolor="black",
            markeredgewidth=0.25,
            markersize=7,
            label=feedstock_id,
        )
        for feedstock_id in feedstock_ids_for_legend
    ]

    ax.legend(
        handles=feedstock_handles,
        title="Biomass type (marker)",
        frameon=False,
        fontsize=7,
        loc="upper right",
        ncol=2,
    )

    if len(feedstock_ids) > max_feedstock_legend:
        ax.text(
            0.01,
            0.01,
            (
                f"Showing first {max_feedstock_legend} marker mappings "
                f"of {len(feedstock_ids)} biomass types"
            ),
            transform=ax.transAxes,
            fontsize=8,
            alpha=0.7,
            ha="left",
            va="bottom",
        )

    output = output_dir / "peak_yield_basis_comparison.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _biomass_type_label(row: pd.Series) -> str:
    subcategory = str(row.get("subcategory", "")).strip()
    if subcategory and subcategory.lower() != "nan":
        return subcategory
    feedstock_id = str(row.get("feedstock_id", "")).strip()
    if feedstock_id and feedstock_id.lower() != "nan":
        return feedstock_id
    return "unknown"


def _plot_root_category_oil_vs_temperature_one_basis(
    results_df: pd.DataFrame,
    output_dir: Path,
    yield_column: str,
    filename_suffix: str,
    basis_title: str,
    basis_unit: str,
) -> Path | None:
    needed = {"category", "temperature_c", yield_column}
    if not needed.issubset(results_df.columns):
        return None

    df = results_df.copy()
    df["category"] = df["category"].astype(str).str.strip()
    df = df[(df["category"] != "") & (df["category"].str.lower() != "nan")].copy()
    if df.empty:
        return None

    df["temperature_c"] = _to_numeric(df["temperature_c"])
    df[yield_column] = _to_numeric(df[yield_column])
    df = df.dropna(subset=["temperature_c", yield_column]).copy()
    if df.empty:
        return None

    df["biomass_type"] = df.apply(_biomass_type_label, axis=1)
    df = df[df["biomass_type"] != "unknown"].copy()
    if df.empty:
        return None

    grouped = (
        df.groupby(["category", "biomass_type", "temperature_c"], as_index=False)[yield_column]
        .mean()
        .sort_values(["category", "biomass_type", "temperature_c"])
    )
    if grouped.empty:
        return None

    category_names = sorted(grouped["category"].unique())
    if not category_names:
        return None

    col_count = 2 if len(category_names) > 1 else 1
    row_count = (len(category_names) + col_count - 1) // col_count
    fig, axes = plt.subplots(
        row_count,
        col_count,
        figsize=(8.4 * col_count, 4.8 * row_count),
        sharex=True,
        sharey=True,
    )

    if row_count == 1 and col_count == 1:
        axes_list = [axes]
    elif row_count == 1 or col_count == 1:
        axes_list = list(axes)
    else:
        axes_list = [ax for row_axes in axes for ax in row_axes]

    marker_cycle = ("o", "s", "^", "D", "v", "P", "X", "<", ">", "*", "h", "8", "p")
    line_cycle = ("-", "--", "-.", ":")

    for idx, category in enumerate(category_names):
        ax = axes_list[idx]
        category_df = grouped[grouped["category"] == category]
        biomass_types = sorted(category_df["biomass_type"].unique())

        for series_index, biomass_type in enumerate(biomass_types):
            series = category_df[category_df["biomass_type"] == biomass_type]
            marker = marker_cycle[series_index % len(marker_cycle)]
            linestyle = line_cycle[(series_index // len(marker_cycle)) % len(line_cycle)]
            ax.plot(
                series["temperature_c"],
                series[yield_column],
                marker=marker,
                linestyle=linestyle,
                linewidth=1.4,
                markersize=4,
                label=biomass_type,
            )

        ax.set_title(category)
        ax.set_xlabel("Temperature [C]")
        if idx % col_count == 0:
            ax.set_ylabel(f"Oil yield [{basis_unit}]")
        ax.grid(True, alpha=0.3)

        if len(biomass_types) <= 12:
            ax.legend(frameon=False, fontsize=7)
        else:
            ax.text(
                0.01,
                0.99,
                f"Biomass types: {len(biomass_types)}",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=7,
                alpha=0.75,
            )

    for spare_ax in axes_list[len(category_names):]:
        spare_ax.set_axis_off()

    fig.suptitle(f"Oil Yield vs Temperature by Root Category ({basis_title})")
    output = output_dir / f"root_category_oil_vs_temperature{filename_suffix}.png"
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def plot_root_category_oil_vs_temperature(
    results_df: pd.DataFrame,
    output_dir: str | Path,
) -> List[Path]:
    """Plot oil yield versus temperature by root category in separate subplots.

    For each available oil-yield basis in the result dataframe, this function
    creates one figure where each root category is shown in its own subplot.
    Within each subplot, biomass types are drawn as separate lines with distinct
    marker and line-style combinations.

    Example:
        from biomass_pyrolysis_equilibrium.qa.plotting import plot_root_category_oil_vs_temperature
        generated = plot_root_category_oil_vs_temperature(frames["results"], "yield_results_plots")
        print(generated)

    Args:
        results_df: Workflow results dataframe, typically frames["results"].
        output_dir: Directory where PNG artifacts are written.

    Returns:
        A list of generated plot paths.
    """

    target = _prepare_output_dir(output_dir)
    outputs: List[Path] = []
    for yield_column, filename_suffix, basis_title, basis_unit in _available_yield_basis_specs(results_df):
        maybe_path = _plot_root_category_oil_vs_temperature_one_basis(
            results_df,
            target,
            yield_column,
            filename_suffix,
            basis_title,
            basis_unit,
        )
        if maybe_path is not None:
            outputs.append(maybe_path)
    return outputs


def _plot_peak_oil_yield_by_biomass_one_basis(
    results_df: pd.DataFrame,
    output_dir: Path,
    yield_column: str,
    filename_suffix: str,
    basis_title: str,
    basis_unit: str,
) -> Path | None:
    """Bar chart: one bar per biomass at its peak oil yield, coloured by category."""
    needed = {"feedstock_id", "temperature_c", yield_column}
    if not needed.issubset(results_df.columns):
        return None

    df = results_df.copy()
    df["temperature_c"] = _to_numeric(df["temperature_c"])
    df[yield_column] = _to_numeric(df[yield_column])
    df = df.dropna(subset=["feedstock_id", "temperature_c", yield_column]).copy()
    if df.empty:
        return None

    df["feedstock_id"] = df["feedstock_id"].astype(str).str.strip()
    df = df[(df["feedstock_id"] != "") & (df["feedstock_id"].str.lower() != "nan")]
    if df.empty:
        return None

    # One row per biomass: highest yield, ties resolved by lowest temperature.
    peak_rows = (
        df.sort_values(["feedstock_id", yield_column, "temperature_c"], ascending=[True, False, True])
        .drop_duplicates(subset=["feedstock_id"], keep="first")
        .copy()
    )

    # Sort by category then feedstock for a grouped visual layout.
    sort_cols = [c for c in ("category", "subcategory", "feedstock_id") if c in peak_rows.columns]
    peak_rows = peak_rows.sort_values(sort_cols).reset_index(drop=True)
    if peak_rows.empty:
        return None

    # Assign a consistent colour per category.
    category_col = "category" if "category" in peak_rows.columns else None
    categories = sorted(peak_rows[category_col].dropna().unique()) if category_col else []
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(categories)}
    bar_colors = (
        [color_map.get(str(cat), "#aaaaaa") for cat in peak_rows[category_col]]
        if category_col
        else ["#1f77b4"] * len(peak_rows)
    )

    n = len(peak_rows)
    fig_width = max(10.0, n * 0.55)
    fig, ax = plt.subplots(figsize=(fig_width, 6.4))

    x_positions = list(range(n))
    bars = ax.bar(
        x_positions,
        peak_rows[yield_column].values,
        color=bar_colors,
        edgecolor="white",
        linewidth=0.6,
        width=0.72,
        zorder=2,
    )

    # Annotate each bar with the temperature that produced the peak yield.
    for bar, temp in zip(bars, peak_rows["temperature_c"].values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.004,
            f"{temp:.0f}°C",
            ha="center",
            va="bottom",
            fontsize=6.5,
            rotation=90,
            color="#333333",
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(peak_rows["feedstock_id"].values, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel(f"Peak oil yield [{basis_unit}]")
    ax.set_xlabel("Biomass type")
    title = (
        f"Peak Oil Yield by Biomass ({basis_title})"
        if filename_suffix
        else "Peak Oil Yield by Biomass"
    )
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3, zorder=1)
    ax.set_axisbelow(True)

    # Category legend.
    if categories:
        legend_handles = [
            Patch(facecolor=color_map[cat], edgecolor="white", label=cat)
            for cat in categories
        ]
        ax.legend(
            handles=legend_handles,
            title="Category",
            frameon=False,
            fontsize=8,
            loc="upper right",
        )

    ax.text(
        0.01, 0.99,
        f"n = {n} biomass types  |  bar labels = temperature at peak yield",
        transform=ax.transAxes,
        fontsize=7,
        alpha=0.65,
        ha="left",
        va="top",
    )

    output = output_dir / f"peak_oil_yield_by_biomass{filename_suffix}.png"
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _plot_peak_oil_yield_by_biomass(results_df: pd.DataFrame, output_dir: Path) -> List[Path]:
    outputs: List[Path] = []
    for yield_column, filename_suffix, basis_title, basis_unit in _available_yield_basis_specs(results_df):
        maybe_path = _plot_peak_oil_yield_by_biomass_one_basis(
            results_df, output_dir, yield_column, filename_suffix, basis_title, basis_unit
        )
        if maybe_path is not None:
            outputs.append(maybe_path)
    return outputs


def save_default_plots(results_df: pd.DataFrame, output_dir: str | Path) -> List[Path]:
    """Generate default analysis plots from results dataframe."""

    target = _prepare_output_dir(output_dir)
    outputs: List[Path] = []

    outputs.extend(_plot_van_krevelen(results_df, target))

    for maybe_path in (
        _plot_ternary_cho(results_df, target),
        _plot_yield_basis_comparison(results_df, target),
        _plot_peak_yield_basis_comparison(results_df, target),
    ):
        if maybe_path is not None:
            outputs.append(maybe_path)

    outputs.extend(_plot_peak_yield_vs_temperature(results_df, target))
    outputs.extend(_plot_peak_oil_yield_by_biomass(results_df, target))
    outputs.extend(_plot_root_category_oil_percentile_summary(results_df, target))
    outputs.extend(plot_root_category_oil_vs_temperature(results_df, target))

    return outputs
