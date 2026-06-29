"""Plotly chart builders for the biomass pyrolysis web app.

All functions accept a pandas DataFrame (from service.get_results()) and
return a plotly.graph_objects.Figure ready to pass to st.plotly_chart().
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for Streamlit
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_boxplot,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_538,
    theme_matplotlib,
    theme_set,
)

#set default theme for all the plots
theme_set(theme_matplotlib)

# Colour-blind-friendly palette (Wong 2011 / Okabe-Ito)
_CB_PALETTE = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermilion
    "#CC79A7",  # reddish purple
    "#999999",  # grey
]

_YIELD_BASIS_OPTIONS: dict[str, str] = {
    "As-received": "oil_yield_kg_per_kg",
    "Dry": "oil_yield_kg_per_kg_dry",
    "DAF": "oil_yield_kg_per_kg_daf",
}


def peak_oil_yield_radial(peak_df: pd.DataFrame, basis_col: str = "oil_yield_kg_per_kg") -> go.Figure:
    """Radial bar chart: each feedstock is a bar radiating from the centre (0 %) to its yield value."""
    if peak_df.empty or basis_col not in peak_df.columns:
        return _empty_figure("No data available")

    df = peak_df[["feedstock_id", "category", basis_col]].copy()
    df[basis_col] = pd.to_numeric(df[basis_col], errors="coerce")
    df = df.dropna(subset=[basis_col])
    df = df[df[basis_col] > 0].sort_values("category").reset_index(drop=True)

    if df.empty:
        return _empty_figure("No positive yield values to display")

    n = len(df)
    df["theta"] = df.index * (360.0 / n)
    bar_width = max(2.0, 270.0 / n)  # angular width in degrees — thinner with many feedstocks

    categories = sorted(df["category"].fillna("Unknown").unique())
    cat_colour = {cat: _CB_PALETTE[i % len(_CB_PALETTE)] for i, cat in enumerate(categories)}

    if basis_col.endswith("_daf"):
        basis_label = "DAF"
    elif basis_col.endswith("_dry"):
        basis_label = "Dry"
    else:
        basis_label = "As-received"

    fig = go.Figure()
    for cat in categories:
        grp = df[df["category"] == cat]
        fig.add_trace(go.Barpolar(
            r=grp[basis_col].tolist(),
            theta=grp["theta"].tolist(),
            name=cat,
            marker_color=cat_colour[cat],
            marker_line_color="white",
            marker_line_width=0.8,
            width=[bar_width] * len(grp),
            customdata=grp[["feedstock_id", "category"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Category: %{customdata[1]}<br>"
                f"Oil yield: %{{r:.1%}}<br>"
                f"Basis: {basis_label}<extra></extra>"
            ),
        ))

    r_max = max(1.0, df[basis_col].max() * 1.08)

    fig.update_layout(
        polar=dict(
            bgcolor="#eed9c4",
            radialaxis=dict(
                visible=True,
                range=[0, r_max],
                tickformat=".0%",
                tickfont=dict(size=20),
                gridcolor="#883434",
                linecolor="rgba(0,0,0,0)",
            ),
            angularaxis=dict(
                showticklabels=False,
                direction="clockwise",
                gridcolor="#883434",
                linecolor="rgba(0,0,0,0)",
            ),
        ),
        paper_bgcolor="#eed9c4",
        plot_bgcolor="#eed9c4",
        height=800,
        legend_title_text="Category",
        template="plotly_white",
        margin=dict(l=80, r=80, t=60, b=60),
    )
    fig.update_polars(hole=0)
    return fig


def peak_oil_yield_bar(peak_df: pd.DataFrame, basis_col: str = "oil_yield_kg_per_kg") -> go.Figure:
    """Ranked horizontal bar chart of peak oil yield per feedstock."""
    if peak_df.empty or basis_col not in peak_df.columns:
        return _empty_figure("No data available")

    df = peak_df[["feedstock_id", "category", basis_col]].copy()
    df[basis_col] = pd.to_numeric(df[basis_col], errors="coerce")
    df = df.dropna(subset=[basis_col]).sort_values(basis_col, ascending=True)

    fig = px.bar(
        df,
        x=basis_col,
        y="feedstock_id",
        color="category" if "category" in df.columns else None,
        color_discrete_sequence=_CB_PALETTE,
        orientation="h",
        labels={
            basis_col: "Oil yield (kg/kg)",
            "feedstock_id": "Feedstock",
            "category": "Category",
        },
        template="plotly_white",
    )
    fig.update_layout(
        xaxis_tickformat=".0%",
        legend_title_text="Category",
        margin=dict(l=10, r=10, t=30, b=10),
        height=max(300, len(df) * 24),
    )
    return fig

def yield_vs_temperature(
    results_df: pd.DataFrame,
    feedstock_ids: list[str],
    basis_col: str = "oil_yield_kg_per_kg",
) -> go.Figure:
    """Line chart of oil / gas / char yield vs. temperature for selected feedstocks.

    Oil yield is model-constrained to be nearly constant in the Gibbs equilibrium
    model; gas increases and char decreases with temperature, which is the
    physically meaningful temperature signal.
    """
    if results_df.empty or "temperature_c" not in results_df.columns:
        return _empty_figure("No data available")

    df = results_df[results_df["feedstock_id"].isin(feedstock_ids)].copy()

    if df.empty:
        return _empty_figure("No results for the selected feedstocks")

    # Derive companion columns (gas / char) from the chosen basis
    gas_col = basis_col.replace("oil_yield", "gas_yield")
    char_col = basis_col.replace("oil_yield", "char_yield")

    # Basis label suffix for axis title
    if basis_col.endswith("_daf"):
        basis_label = "DAF"
    elif basis_col.endswith("_dry"):
        basis_label = "Dry"
    else:
        basis_label = "As-received"

    df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

    product_cols = {
        "Oil": basis_col,
        "Gas": gas_col if gas_col in df.columns else None,
        "Char": char_col if char_col in df.columns else None,
    }
    product_cols = {k: v for k, v in product_cols.items() if v is not None}

    for col in product_cols.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["temperature_c"] + list(product_cols.values()))
    if df.empty:
        return _empty_figure("No valid data for selected feedstocks")

    # Average over pressure for a cleaner temperature profile
    agg = df.groupby(["feedstock_id", "temperature_c"], as_index=False)[list(product_cols.values())].mean()

    # Melt to long form: one row per (feedstock, temperature, product)
    id_vars = ["feedstock_id", "temperature_c"]
    value_vars = list(product_cols.values())
    agg_long = agg.melt(id_vars=id_vars, value_vars=value_vars, var_name="product_col", value_name="yield_value")
    col_to_label = {v: k for k, v in product_cols.items()}
    agg_long["Product"] = agg_long["product_col"].map(col_to_label)

    # Build traces manually so color=feedstock, dash=product
    dash_map = {"Oil": "solid", "Gas": "dash", "Char": "dot"}
    color_cycle = _CB_PALETTE

    fig = go.Figure()
    feedstock_color: dict[str, str] = {}
    for fi, fid in enumerate(feedstock_ids):
        feedstock_color[fid] = color_cycle[fi % len(color_cycle)]

    for product_name in ["Oil", "Gas", "Char"]:
        if product_name not in col_to_label.values():
            continue
        subset = agg_long[agg_long["Product"] == product_name].sort_values("temperature_c")
        for fi, fid in enumerate(feedstock_ids):
            fdata = subset[subset["feedstock_id"] == fid]
            if fdata.empty:
                continue
            show_legend = product_name == "Oil"
            fig.add_trace(go.Scatter(
                x=fdata["temperature_c"],
                y=fdata["yield_value"],
                mode="lines+markers",
                name=fid,
                legendgroup=fid,
                showlegend=show_legend,
                line=dict(color=feedstock_color[fid], dash=dash_map[product_name], width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{fid}</b><br>{product_name}<br>Temp: %{{x}}°C<br>Yield: %{{y:.1%}}<extra></extra>",
            ))

    # Add invisible traces to create a "Product" legend section
    for product_name, dash in dash_map.items():
        if product_name not in col_to_label.values():
            continue
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines",
            name=f"— {product_name}",
            line=dict(color="grey", dash=dash, width=2),
            showlegend=True,
        ))

    fig.update_layout(
        xaxis_title="Temperature (°C)",
        yaxis_title=f"Yield kg/kg ({basis_label}, avg over pressure)",
        yaxis_tickformat=".0%",
        legend_title_text="Feedstock / Product",
        template="plotly_white",
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def van_krevelen(results_df: pd.DataFrame) -> go.Figure:
    """Van Krevelen H/C vs O/C scatter coloured by category."""
    hc_col, oc_col = "h_c_ratio_daf", "o_c_ratio_daf"

    df = results_df.drop_duplicates(subset=["feedstock_id"]).copy() if "feedstock_id" in results_df.columns else results_df.copy()

    # Compute H/C and O/C from ultimate analysis columns if pre-computed ratio cols are absent
    if hc_col not in df.columns or oc_col not in df.columns:
        c_col, h_col, o_col = "feedstock_c_pct_daf", "feedstock_h_pct_daf", "feedstock_o_pct_daf"
        if not {c_col, h_col, o_col}.issubset(df.columns):
            return _empty_figure("H/C and O/C ratios cannot be computed — ultimate analysis columns missing")
        df[c_col] = pd.to_numeric(df[c_col], errors="coerce")
        df[h_col] = pd.to_numeric(df[h_col], errors="coerce")
        df[o_col] = pd.to_numeric(df[o_col], errors="coerce")
        # Atomic ratios: divide wt% by atomic weight to get molar amounts, then ratio to C
        c_mol = df[c_col] / 12.011
        df[hc_col] = (df[h_col] / 1.008) / c_mol.replace(0, float("nan"))
        df[oc_col] = (df[o_col] / 15.999) / c_mol.replace(0, float("nan"))

    df[hc_col] = pd.to_numeric(df[hc_col], errors="coerce")
    df[oc_col] = pd.to_numeric(df[oc_col], errors="coerce")
    df = df.dropna(subset=[hc_col, oc_col])

    if df.empty:
        return _empty_figure("No H/C or O/C data available")

    fig = px.scatter(
        df,
        x=oc_col,
        y=hc_col,
        color="category" if "category" in df.columns else None,
        hover_name="feedstock_id" if "feedstock_id" in df.columns else None,
        color_discrete_sequence=_CB_PALETTE,
        title="Van Krevelen Diagram",
        subtitle="scatter plot of H/C vs O/C atomic ratios for each feedstock",
        labels={
            hc_col: "H/C atomic ratio",
            oc_col: "O/C atomic ratio",
            "category": "Category",
            "title": "Van Krevelen Diagram",
            "subtitle": "scatter plot of H/C vs O/C atomic ratios for each feedstock",
        },
        template="plotly_white",
    )
    fig.update_layout(
        legend_title_text="Category",
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig

def van_krevelen_bubbles(results_df: pd.DataFrame) -> plt.Figure:
    """Van Krevelen bubble chart: bubble size = peak oil yield, colour = category."""
    hc_col, oc_col = "h_c_ratio_daf", "o_c_ratio_daf"

    df = results_df.drop_duplicates(subset=["feedstock_id"]).copy() if "feedstock_id" in results_df.columns else results_df.copy()

    if hc_col not in df.columns or oc_col not in df.columns:
        c_col, h_col, o_col = "feedstock_c_pct_daf", "feedstock_h_pct_daf", "feedstock_o_pct_daf"
        if not {c_col, h_col, o_col}.issubset(df.columns):
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Ultimate analysis columns missing", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")
            return fig
        df[c_col] = pd.to_numeric(df[c_col], errors="coerce")
        df[h_col] = pd.to_numeric(df[h_col], errors="coerce")
        df[o_col] = pd.to_numeric(df[o_col], errors="coerce")
        c_mol = df[c_col] / 12.011
        df[hc_col] = (df[h_col] / 1.008) / c_mol.replace(0, float("nan"))
        df[oc_col] = (df[o_col] / 15.999) / c_mol.replace(0, float("nan"))

    df[hc_col] = pd.to_numeric(df[hc_col], errors="coerce")
    df[oc_col] = pd.to_numeric(df[oc_col], errors="coerce")
    df = df.dropna(subset=[hc_col, oc_col])

    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No H/C or O/C data available", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return fig

    # Bubble size = peak oil yield per feedstock
    yield_col = "oil_yield_kg_per_kg"
    if yield_col in results_df.columns and "feedstock_id" in results_df.columns:
        peak = (
            results_df.groupby("feedstock_id")[yield_col]
            .max()
            .reset_index()
            .rename(columns={yield_col: "peak_oil_yield"})
        )
        peak["peak_oil_yield"] = pd.to_numeric(peak["peak_oil_yield"], errors="coerce")
        df = df.merge(peak, on="feedstock_id", how="left")
        size_col = "peak_oil_yield"
    else:
        df["_size"] = 0.5
        size_col = "_size"

    categories = sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else []
    colour_map = {cat: _CB_PALETTE[i % len(_CB_PALETTE)] for i, cat in enumerate(categories)}

    colour_aes = "category" if "category" in df.columns else None
    base_aes = aes(x=oc_col, y=hc_col, size=size_col)

    p = (
        ggplot(df, base_aes)
        + geom_point(aes(fill=colour_aes), stroke=0, alpha=0.5)
        + geom_point(aes(color=colour_aes), fill="none")
        + scale_fill_manual(values=colour_map)
        + scale_color_manual(values=colour_map)
        + labs(
            x="O/C atomic ratio",
            y="H/C atomic ratio",
            fill="Category",
            color="Category",
            size="Peak oil yield",
            title="Van Krevelen Diagram",
            subtitle=f"Bubble size = peak bio-oil yield",
        )
        + theme_538()
        + theme(
            plot_background=element_rect(fill="#eed9c4", color="#eed9c4"),
            panel_background=element_rect(fill="#eed9c4"),
            legend_background=element_rect(fill="#eed9c4", color="#eed9c4"),
            plot_title=element_text(size=13, weight="bold"),
            plot_subtitle=element_text(size=10),
            legend_title=element_text(size=9, weight="bold"),
            figure_size=(9, 6),
        )
    )

    return p.draw()


# Monte Carlo box-plot colours (match the notebook's saved PNGs).
_MC_BOX_FILL = "#9ecae1"
_MC_BOX_LINE = "#08519c"
_MC_DET_COLOUR = "#d62728"  # deterministic (single-point) score marker


def montecarlo_box(
    samples_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    category: str,
    unit: str,
) -> go.Figure:
    """Monte Carlo box-and-whisker plot for one impact *category*.

    One box per biomass type, built from raw MC iterations in *samples_df*.
    Only the single most extreme upper and lower outlier are shown per box to
    keep the chart readable.  The deterministic score from *summary_df* is
    overlaid as a red diamond.
    """
    d = samples_df[samples_df["category"] == category].copy()
    if d.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Monte Carlo data", x=0.5, y=0.5, showarrow=False,
                           xref="paper", yref="paper", font={"size": 14})
        fig.update_layout(template="plotly_white")
        return fig

    d["score"] = pd.to_numeric(d["score"], errors="coerce")
    d = d.dropna(subset=["score"])
    order = sorted(d["biomass_type"].astype(str).unique())

    fig = go.Figure()

    # --- Dummy legend traces (invisible, appear first so legend is consistent) ---
    fig.add_trace(go.Box(
        y=[None], name="MC distribution (box: IQR, whiskers: 1.5×IQR)",
        marker_color=_MC_BOX_LINE, fillcolor=_MC_BOX_FILL, line_color=_MC_BOX_LINE,
        showlegend=True, visible="legendonly",
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker={"color": _MC_BOX_LINE, "size": 6, "opacity": 0.7, "symbol": "circle"},
        name="Most extreme outlier",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker={"color": _MC_DET_COLOUR, "size": 10, "symbol": "diamond"},
        name="Deterministic score",
        showlegend=True,
    ))

    for btype in order:
        vals = d.loc[d["biomass_type"].astype(str) == btype, "score"].values
        q1, q3 = float(pd.Series(vals).quantile(0.25)), float(pd.Series(vals).quantile(0.75))
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        outliers = vals[(vals < lower_fence) | (vals > upper_fence)]
        # Keep only the single most extreme outlier on each side.
        extreme_outliers: list[float] = []
        low_out = outliers[outliers < lower_fence]
        high_out = outliers[outliers > upper_fence]
        if len(low_out):
            extreme_outliers.append(float(low_out.min()))
        if len(high_out):
            extreme_outliers.append(float(high_out.max()))

        fig.add_trace(go.Box(
            y=vals,
            name=btype,
            boxpoints=False,
            marker_color=_MC_BOX_LINE,
            fillcolor=_MC_BOX_FILL,
            line_color=_MC_BOX_LINE,
            showlegend=False,
        ))

        # Overlay the single extreme outlier points manually.
        if extreme_outliers:
            fig.add_trace(go.Scatter(
                x=[btype] * len(extreme_outliers),
                y=extreme_outliers,
                mode="markers",
                marker={"color": _MC_BOX_LINE, "size": 6, "opacity": 0.7, "symbol": "circle"},
                showlegend=False,
                hovertemplate="%{y:.4g}<extra></extra>",
            ))

    # Deterministic single-point score overlaid as a red diamond.
    if summary_df is not None and not summary_df.empty and "deterministic_score" in summary_df.columns:
        det = summary_df[summary_df["category"] == category][["biomass_type", "deterministic_score"]].copy()
        det["biomass_type"] = det["biomass_type"].astype(str)
        det = det[det["biomass_type"].isin(order)].dropna(subset=["deterministic_score"])
        if not det.empty:
            fig.add_trace(go.Scatter(
                x=det["biomass_type"].tolist(),
                y=det["deterministic_score"].tolist(),
                mode="markers",
                marker={"color": _MC_DET_COLOUR, "size": 10, "symbol": "diamond"},
                showlegend=False,
                hovertemplate="%{x}: %{y:.4g}<extra>Deterministic</extra>",
            ))

    fig.update_layout(
        title={"text": category, "font": {"size": 13, "color": "#333333"}},
        yaxis_title=unit,
        xaxis_title="",
        paper_bgcolor="#eed9c4",
        plot_bgcolor="#eed9c4",
        font={"color": "#333333"},
        margin={"t": 50, "b": 60, "l": 60, "r": 20},
        height=420,
        xaxis={"tickangle": -20},
        legend={
            "title": {"text": "Legend", "font": {"size": 11}},
            "bgcolor": "rgba(238,217,196,0.85)",
            "bordercolor": "#aaaaaa",
            "borderwidth": 1,
            "font": {"size": 10},
            "orientation": "v",
            "yanchor": "top",
            "y": 0.99,
            "xanchor": "right",
            "x": 0.99,
        },
    )
    return fig


def comparison_bar(
    peak_df: pd.DataFrame,
    feedstock_ids: list[str],
    basis_col: str = "oil_yield_kg_per_kg",
) -> go.Figure:
    """Grouped bar chart comparing oil/gas/char yields for selected feedstocks."""
    if peak_df.empty:
        return _empty_figure("No data available")

    suffix = ""
    if basis_col.endswith("_dry"):
        suffix = "_dry"
    elif basis_col.endswith("_daf"):
        suffix = "_daf"

    oil_col = f"oil_yield_kg_per_kg{suffix}"
    gas_col = f"gas_yield_kg_per_kg{suffix}"
    char_col = f"char_yield_kg_per_kg{suffix}"

    df = peak_df[peak_df["feedstock_id"].isin(feedstock_ids)].copy()

    frames = []
    for col, label in [(oil_col, "Bio-oil"), (gas_col, "Gas"), (char_col, "Char")]:
        if col not in df.columns:
            continue
        tmp = df[["feedstock_id", col]].copy()
        tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
        tmp = tmp.rename(columns={col: "yield"})
        tmp["product"] = label
        frames.append(tmp)

    if not frames:
        return _empty_figure("Yield columns not found")

    combined = pd.concat(frames, ignore_index=True)

    fig = px.bar(
        combined,
        x="feedstock_id",
        y="yield",
        color="product",
        barmode="group",
        color_discrete_map={"Bio-oil": _CB_PALETTE[0], "Gas": _CB_PALETTE[1], "Char": _CB_PALETTE[2]},
        labels={
            "yield": "Yield (kg/kg)",
            "feedstock_id": "Feedstock",
            "product": "Product",
        },
        template="plotly_white",
    )
    fig.update_layout(
        yaxis_tickformat=".0%",
        xaxis_tickangle=-30,
        legend_title_text="Product",
        margin=dict(l=10, r=10, t=30, b=80),
    )
    return fig


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#666666"),
    )
    fig.update_layout(
        xaxis_visible=False,
        yaxis_visible=False,
        template="plotly_white",
        margin=dict(l=10, r=10, t=30, b=10),
        height=300,
    )
    return fig


# Expose the basis options dict so pages can build dropdowns from it
YIELD_BASIS_OPTIONS = _YIELD_BASIS_OPTIONS
