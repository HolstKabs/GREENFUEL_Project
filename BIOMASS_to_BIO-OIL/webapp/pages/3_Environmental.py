"""Environmental Impacts — Monte Carlo uncertainty / sensitivity viewer.

Shows the Life Cycle Impact Assessment (LCIA) and a Monte Carlo uncertainty for each
biomass type: a box-and-whisker plot per impact category,
with the deterministic (single-point) LCA score to see how the
point estimate sits within the simulated uncertainty.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import lca_meta as meta
from charts import montecarlo_box
from service import load_montecarlo_results, load_results
from nav import inject

st.set_page_config(page_title="Environmental Impacts — Biomass Pyrolysis", layout="wide")
inject()

st.title("Environmental Impacts")
st.markdown(
    "**Monte Carlo uncertainty analysis** of the cradle-to-grave LCA (Brightway, "
    "100 iterations, ReCiPe 2016 midpoint H). Each box shows the simulated spread for an "
    "impact category; the **red diamond ◆ marks the deterministic (single-point) score**, so "
    "you can see how robust each result is to the underlying data uncertainty."
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
fast_mode = st.session_state.get("fast_mode", True)
result_dir = st.session_state.get("selected_result_dir", None)

try:
    with st.spinner("Loading Monte Carlo results …"):
        samples_df, summary_df = load_montecarlo_results()
        dfs = load_results(fast_mode, result_dir=result_dir)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"Error loading data: {exc}")
    st.stop()

if samples_df.empty:
    st.warning(
        "No Monte Carlo result files found. Expected one or more `montecarlo_*.xlsx` files "
        "(sheets *Summary* and *Raw_All_Categories*) in the project's `Monte_carlo_analysis` "
        "folder. Run the Monte Carlo step in `GREENFUEL_LCA_biomass.ipynb` for each biomass type."
    )
    st.stop()

results_df = dfs.get("results", pd.DataFrame())

# Biomass category (Wood / Agricultural wastes / Residues and wastes) per MC biomass.
biomass_types = sorted(samples_df["biomass_type"].astype(str).unique())
cat_of = {b: meta.category_for_biomass(b, results_df) for b in biomass_types}

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

biomass_categories = sorted({cat_of[b] for b in biomass_types})
selected_categories = st.sidebar.multiselect(
    "Biomass category", options=biomass_categories, default=biomass_categories,
    help="Only categories with Monte Carlo results are shown.",
)

if not selected_categories:
    st.info("← Select a biomass category in the sidebar to display results.")
    st.stop()

available_biomass = [b for b in biomass_types if cat_of[b] in selected_categories]
selected_biomass = st.sidebar.multiselect(
    "Biomass type", options=available_biomass, default=available_biomass,
    help="Only biomass types with completed Monte Carlo results are available.",
)

if not selected_biomass:
    st.info("← Select at least one biomass type in the sidebar.")
    st.stop()

samples = samples_df[samples_df["biomass_type"].astype(str).isin(selected_biomass)].copy()
summary = (
    summary_df[summary_df["biomass_type"].astype(str).isin(selected_biomass)].copy()
    if not summary_df.empty else summary_df
)

# ---------------------------------------------------------------------------
# Impact-category box plots (GWP first, then the rest)
# ---------------------------------------------------------------------------
impact_categories = sorted(samples["category"].unique())
impact_categories.sort(key=lambda c: (not meta.is_gwp(c), c))  # GWP first

# Unit per impact category (from the Summary sheet).
unit_of: dict = {}
if not summary.empty and {"category", "unit"}.issubset(summary.columns):
    unit_of = summary.drop_duplicates("category").set_index("category")["unit"].astype(str).to_dict()

st.caption(
    f"Showing **{len(selected_biomass)}** biomass type(s) across **{len(impact_categories)}** "
    "impact categories. Boxes = Monte Carlo spread (median line, box = Q1–Q3, whiskers = "
    "1.5·IQR, points = outliers); ◆ = deterministic score."
)

cols = st.columns(2)
for i, cat in enumerate(impact_categories):
    with cols[i % 2]:
        fig = montecarlo_box(samples, summary, cat, unit_of.get(cat, ""))
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Summary statistics (optional detail)
# ---------------------------------------------------------------------------
if not summary.empty:
    with st.expander("📋 Monte Carlo summary statistics"):
        show_cols = [c for c in (
            "biomass_type", "category", "unit", "deterministic_score", "mc_mean", "mc_std",
            "cv_pct", "q1", "median", "q3", "lower_whisker", "upper_whisker", "n_iterations",
        ) if c in summary.columns]
        st.dataframe(
            summary[show_cols].rename(columns={
                "biomass_type": "Biomass",
                "category": "Impact category",
                "unit": "Unit",
                "deterministic_score": "Deterministic",
                "mc_mean": "MC mean",
                "mc_std": "MC std",
                "cv_pct": "CV (%)",
                "median": "Median",
                "lower_whisker": "Lower whisker",
                "upper_whisker": "Upper whisker",
                "n_iterations": "Iterations",
            }),
            use_container_width=True, hide_index=True,
        )

with st.expander("❓ How to read this"):
    st.markdown(
        """
        Each box summarises the **Monte Carlo simulation** (Brightway `use_distributions=True`):
        the ecoinvent exchange and characterisation uncertainties are resampled many times and the
        LCA re-run, giving a distribution of scores per impact category.

        - **Box** = inter-quartile range (Q1–Q3); **line** = median; **whiskers** = 1.5·IQR;
          **points** = outliers beyond the whiskers.
        - **◆ red diamond** = the single deterministic LCA score. If it sits near the median and the
          box is narrow, the result is **robust**; a wide box (or the diamond far from the median)
          means the result is **sensitive** to the input uncertainty.
        - The four categories are chosen per biomass: climate change (GWP) plus the three
          highest-impact categories for that feedstock.
        """
    )
