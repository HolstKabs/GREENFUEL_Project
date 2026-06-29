"""Comparison page — compare yield profiles for selected feedstocks."""

import pandas as pd
import streamlit as st

from charts import YIELD_BASIS_OPTIONS, comparison_bar, yield_vs_temperature  # webapp/ is on sys.path
from nav import inject
from service import load_results

st.set_page_config(page_title="Comparison — Biomass Pyrolysis", layout="wide")
inject()

st.title("Feedstock Comparison")
st.markdown(
    "Select 2–8 feedstocks to compare their bio-oil, gas, and char yields side-by-side, "
    "and to see how oil yield changes with temperature."
)

# ---------------------------------------------------------------------------
# Load results
# ---------------------------------------------------------------------------
fast_mode = st.session_state.get("fast_mode", True)
result_dir = st.session_state.get("selected_result_dir", None)

try:
    with st.spinner("Loading results …"):
        dfs = load_results(fast_mode, result_dir=result_dir)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"Solver error: {exc}")
    st.stop()

peak_df = dfs.get("peak_results", pd.DataFrame())
results_df = dfs.get("results", pd.DataFrame())

if peak_df.empty:
    st.warning("No results available.")
    st.stop()

# ---------------------------------------------------------------------------
# Step 1 — Category filter
# ---------------------------------------------------------------------------
st.sidebar.header("Step 1 — Select biomass category")
categories = sorted(peak_df["category"].dropna().unique().tolist()) if "category" in peak_df.columns else []
selected_categories = st.sidebar.multiselect(
    "Step 1 — Select biomass category",
    options=categories,
    default=[],
    help="Filter feedstocks by category before selecting individual ones.",
)

if not selected_categories:
    st.info("← Select at least one biomass category to continue.")
    st.stop()

# ---------------------------------------------------------------------------
# Step 2 — Feedstock selector (filtered by category)
# ---------------------------------------------------------------------------
filtered_feedstocks = sorted(
    peak_df[peak_df["category"].isin(selected_categories)]["feedstock_id"].dropna().unique().tolist()
) if "feedstock_id" in peak_df.columns else []

selected = st.sidebar.multiselect(
    "Step 2 — Select feedstocks to compare (2–8 recommended)",
    options=filtered_feedstocks,
    default=[],
    help="Type to search by feedstock name.",
)

if not selected:
    st.info("← Select at least one feedstock to continue.")
    st.stop()

# ---------------------------------------------------------------------------
# Step 3 — Yield basis
# ---------------------------------------------------------------------------
basis_label = st.sidebar.selectbox(
    "Step 3 — Yield basis",
    options=list(YIELD_BASIS_OPTIONS.keys()),
    index=0,
    help="Choose how yields are normalised.",
)
basis_col = YIELD_BASIS_OPTIONS[basis_label]

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
st.subheader("Yields at peak conditions")
st.caption(f"Basis: {basis_label} — each group shows oil, gas, and char for the best-converged condition per feedstock")
st.plotly_chart(
        comparison_bar(peak_df, feedstock_ids=selected, basis_col=basis_col),
        use_container_width=True,
    )

st.subheader("Yields vs. temperature")
st.caption(f"Basis: {basis_label}.  \n" 
        "Solid = Oil, dashed = Gas, dotted = Char (averaged over pressure).  \n"
        "Oil yield is nearly constant in the Gibbs equilibrium model; Gas/Char show the real temperature response.")
st.plotly_chart(
        yield_vs_temperature(results_df, feedstock_ids=selected, basis_col=basis_col),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Data table for selected feedstocks
# ---------------------------------------------------------------------------
with st.expander("📊 Data table — click to expand"):
    st.subheader("Peak-condition data for selected feedstocks")
    st.caption(f"#### {len(selected)} feedstock(s) matched")

    disp_cols = [c for c in [
    "feedstock_id", "category", "subcategory",
    basis_col,
    "gas_yield_kg_per_kg" if basis_col == "oil_yield_kg_per_kg" else
        "gas_yield_kg_per_kg_dry" if basis_col.endswith("_dry") else "gas_yield_kg_per_kg_daf",
    "char_yield_kg_per_kg" if basis_col == "oil_yield_kg_per_kg" else
        "char_yield_kg_per_kg_dry" if basis_col.endswith("_dry") else "char_yield_kg_per_kg_daf",
    "temperature_c", "pressure_bar", "acceptance_flag",
] if c in peak_df.columns]

    selected_peak = peak_df[peak_df["feedstock_id"].isin(selected)][disp_cols]
    st.dataframe(
    selected_peak.rename(columns={
        "feedstock_id": "Feedstock",
        "category": "Category",
        "subcategory": "Subcategory",
        basis_col: f"Oil yield ({basis_label})",
        "temperature_c": "Temp (°C)",
        "pressure_bar": "Pressure (bar)",
        "acceptance_flag": "QA flag",
    }),
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------------
# Expert section
# ---------------------------------------------------------------------------
with st.expander("🔬 Expert view — full solver details for selected feedstocks"):
    expert_cols = [c for c in [
        "feedstock_id", "category",
        "oil_yield_kg_per_kg", "gas_yield_kg_per_kg", "char_yield_kg_per_kg",
        "temperature_c", "pressure_bar",
        "converged", "max_residual", "acceptance_flag",
        "net_energy_efficiency_ratio",
    ] if c in results_df.columns]

    expert_df = results_df[results_df["feedstock_id"].isin(selected)][expert_cols].copy()
    for col in ("max_residual", "oil_yield_kg_per_kg", "gas_yield_kg_per_kg", "char_yield_kg_per_kg"):
        if col in expert_df.columns:
            expert_df[col] = pd.to_numeric(expert_df[col], errors="coerce")

    st.dataframe(expert_df, use_container_width=True, hide_index=True)

