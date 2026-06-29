"""Explorer page — browse, filter, and rank all feedstocks."""

import pandas as pd
import streamlit as st

from charts import YIELD_BASIS_OPTIONS, peak_oil_yield_bar, peak_oil_yield_radial, van_krevelen, van_krevelen_bubbles  # webapp/ is on sys.path
from nav import inject
from service import load_results

st.set_page_config(page_title="Explorer — Biomass Pyrolysis", layout="wide")
inject()

# Remove any stale vk_style session state from a previous page version
st.session_state.pop("vk_style", None)

st.title("Feedstock Explorer")
st.markdown(
    "Filter feedstocks by category, oil yield, or temperature, then inspect the charts and data table."
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
    st.warning("No results to display.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

# Category filter
categories = sorted(peak_df["category"].dropna().unique().tolist()) if "category" in peak_df.columns else []
selected_categories = st.sidebar.multiselect(
    "Biomass category",
    options=categories,
    default=[],
    key="sidebar_cat_filter",
    help="Select one or more categories to include.",
)

# Yield basis selector
basis_label = st.sidebar.selectbox(
    "Oil yield basis",
    options=list(YIELD_BASIS_OPTIONS.keys()),
    index=0,
    key="sidebar_basis",
    help= "Select the basis for oil yield (AR = as-received, includes moisture and ash; Dry = moisture excluded; DAF = dry-ash-free)."
)
basis_col = YIELD_BASIS_OPTIONS[basis_label]

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
if not selected_categories:
    st.info("← Select one or more biomass categories in the sidebar to display results.")
    st.stop()

filtered = peak_df.copy()

if selected_categories and "category" in filtered.columns:
    filtered = filtered[filtered["category"].isin(selected_categories)]

# ---------------------------------------------------------------------------
# Layout: chart then table
# ---------------------------------------------------------------------------
st.markdown(f"#### Oil yield ({basis_label})")
st.markdown(
    f"If there are any feedstocks in the chosen category it will be shown below: ({len(filtered)} feedstock(s) matched)"
)
chart_type = st.radio(
    "Chart type",
    options=["Radial", "Bar chart"],
    horizontal=False,
    label_visibility="collapsed",
    key="main_chart_type",
)
if chart_type == "Radial":
    st.plotly_chart(
        peak_oil_yield_radial(filtered, basis_col=basis_col),
        use_container_width=True,
    )
else:
    st.plotly_chart(
        peak_oil_yield_bar(filtered, basis_col=basis_col),
        use_container_width=True,
    )
with st.expander("📊 Data table — click to expand"):
    st.markdown(f"#### {len(filtered)} feedstock(s) matched")

# Select columns useful for display
    display_cols = [c for c in [
    "feedstock_id", "category", "subcategory",
    basis_col,
    "gas_yield_kg_per_kg" if basis_col == "oil_yield_kg_per_kg" else
        "gas_yield_kg_per_kg_dry" if basis_col.endswith("_dry") else "gas_yield_kg_per_kg_daf",
    "char_yield_kg_per_kg" if basis_col == "oil_yield_kg_per_kg" else
        "char_yield_kg_per_kg_dry" if basis_col.endswith("_dry") else "char_yield_kg_per_kg_daf",
    "temperature_c", "pressure_bar", "acceptance_flag",
        ] if c in filtered.columns]

    st.dataframe(
    filtered[display_cols].rename(columns={
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
# Van Krevelen diagram (collapsible)
# ---------------------------------------------------------------------------
with st.expander("📊 Van Krevelen diagram (H/C vs O/C) — click to expand"):
    st.markdown(
        "Each point is a feedstock coloured by category.  "
        "The Van Krevelen diagram shows the elemental composition of the feedstocks — "
        "biomass typically clusters in the upper-right region (high H/C, high O/C)."
    )
    # Filter results_df (which has the ultimate analysis columns) to the same categories
    vk_df = results_df[results_df["category"].isin(selected_categories)].copy() if "category" in results_df.columns else results_df.copy()
    vk_style = st.radio(
        "",
        options=["Interactive", "Bubbles"],
        horizontal=True,
    )
    if  vk_style == "Interactive":
        st.plotly_chart(van_krevelen(vk_df), use_container_width=True)
    elif vk_style == "Bubbles":
        st.pyplot(van_krevelen_bubbles(vk_df), use_container_width=True)
   

# ---------------------------------------------------------------------------
# Beginner explainer
# ---------------------------------------------------------------------------
with st.expander(" What do these columns mean❓ — click to expand"):
    st.markdown(
        f"""
        | Column | Meaning |
        |--------|---------|
        | Oil yield ({basis_label}) | kg of bio-oil produced per kg of feedstock |
        | Gas yield | kg of permanent gases (CO, CO₂, H₂, CH₄ …) per kg of feedstock |
        | Char yield | kg of solid char per kg of feedstock |
        | Temp (°C) | Temperature at which the peak oil yield was found |
        | Pressure (bar) | Operating pressure at peak conditions |

        Note: all yields are *theoretical equilibrium* values, not measured lab results.
        """
    )
