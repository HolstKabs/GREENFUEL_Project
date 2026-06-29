"""Metadata helpers for the LCA biomass types.

Two jobs:
  1. Attach a bio-oil yield class (High / Medium / Low) to each LCA biomass type,
     using the SAME matching logic as GREENFUEL_LCA_biomass.ipynb so the yield we
     show is exactly the one the LCA assumed.
  2. Hold the shipping / fossil-HFO assumptions and the default impact-category
     selection used by the Marine Transport page.

All numeric assumptions are exposed so the page can let the reader edit them.
"""

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Bio-oil yield classification
# ---------------------------------------------------------------------------
# Thresholds on the as-received oil yield (kg bio-oil / kg biomass).  Tunable.
# Defaults give a clean spread across the 9 expected biomass types:
#   High (>= 0.55): Poplar 4, Grape seeds 1, Olive kernels
#   Medium:         Branches and leaves from poplar tree 3, Maple fruit
#   Low  (< 0.25):  Oak wood1, peanut hulls, fir mill waste, Walnut shell 1
YIELD_LOW_MAX = 0.25
YIELD_HIGH_MIN = 0.55

# Stable colours for the three classes (greener = higher yield).
YIELD_COLORS = {
    "High": "#1f6410",
    "Medium": "#E69F00",
    "Low": "#D55E00",
    "Unknown": "#999999",
}
YIELD_ORDER = ["High", "Medium", "Low", "Unknown"]


def classify_yield(oil_yield: float | None) -> str:
    """Map an as-received oil yield (fraction) to High / Medium / Low."""
    if oil_yield is None or pd.isna(oil_yield):
        return "Unknown"
    if oil_yield < YIELD_LOW_MAX:
        return "Low"
    if oil_yield >= YIELD_HIGH_MIN:
        return "High"
    return "Medium"


def match_oil_yield(biomass_type: str, results_df: pd.DataFrame) -> float:
    """Bio-oil yield the LCA would have used for *biomass_type*.

    Replicates the notebook: partial, case-insensitive match of the biomass name
    against the ``subcategory`` column of the yield ``results`` sheet, then the
    highest ``oil_yield_kg_per_kg`` among the matches.  Returns NaN if no match.
    """
    if results_df is None or results_df.empty:
        return float("nan")
    if "subcategory" not in results_df.columns or "oil_yield_kg_per_kg" not in results_df.columns:
        return float("nan")
    mask = results_df["subcategory"].astype(str).str.contains(
        str(biomass_type), case=False, na=False, regex=False
    )
    matched = results_df[mask]
    if matched.empty:
        return float("nan")
    return float(pd.to_numeric(matched["oil_yield_kg_per_kg"], errors="coerce").max())


def category_for_biomass(biomass_type: str, results_df: pd.DataFrame) -> str:
    """Biomass category (Wood / Agricultural wastes / Residues and wastes) for a name.

    Same matching rule as ``match_oil_yield``: partial, case-insensitive match of the
    name against the ``subcategory`` column of the yield ``results`` sheet, returning
    the ``category`` of the highest-oil-yield match.  Returns "Unknown" if no match.
    """
    if results_df is None or results_df.empty:
        return "Unknown"
    if "subcategory" not in results_df.columns or "category" not in results_df.columns:
        return "Unknown"
    mask = results_df["subcategory"].astype(str).str.contains(
        str(biomass_type), case=False, na=False, regex=False
    )
    matched = results_df[mask]
    if matched.empty:
        return "Unknown"
    if "oil_yield_kg_per_kg" in matched.columns:
        row = matched.loc[pd.to_numeric(matched["oil_yield_kg_per_kg"], errors="coerce").idxmax()]
        return str(row["category"])
    return str(matched.iloc[0]["category"])


def yield_table(biomass_types, results_df: pd.DataFrame) -> pd.DataFrame:
    """Return [biomass_type, oil_yield_kg_per_kg, yield_class] for each name."""
    rows = []
    for b in biomass_types:
        y = match_oil_yield(b, results_df)
        rows.append({
            "biomass_type": b,
            "oil_yield_kg_per_kg": y,
            "yield_class": classify_yield(y),
        })
    return pd.DataFrame(rows)


def _best_match_row(biomass_type: str, results_df: pd.DataFrame):
    """The highest-oil-yield yield-``results`` row matching *biomass_type*, or None."""
    if results_df is None or results_df.empty:
        return None
    if "subcategory" not in results_df.columns or "oil_yield_kg_per_kg" not in results_df.columns:
        return None
    mask = results_df["subcategory"].astype(str).str.contains(
        str(biomass_type), case=False, na=False, regex=False
    )
    matched = results_df[mask]
    if matched.empty:
        return None
    oil = pd.to_numeric(matched["oil_yield_kg_per_kg"], errors="coerce")
    if oil.notna().sum() == 0:
        return None
    return results_df.loc[oil.idxmax()]


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def bio_oil_energy_table(biomass_types, results_df: pd.DataFrame) -> pd.DataFrame:
    """Per-biomass yield, bio-oil HHV and bio-oil energy density.

    Returns ``[biomass_type, oil_yield_kg_per_kg, bio_oil_hhv_mj_per_kg,
    energy_per_kg_biomass, yield_class]`` where ``energy_per_kg_biomass`` (MJ of
    usable bio-oil per kg of feedstock) = oil yield × bio-oil HHV — the quantity
    that drives the energy/yield reach metric.
    """
    rows = []
    for b in biomass_types:
        row = _best_match_row(b, results_df)
        if row is None:
            y = h = float("nan")
        else:
            y = _to_float(row.get("oil_yield_kg_per_kg"))
            h = _to_float(row.get("bio_oil_hhv_mj_per_kg"))
        e = y * h if (pd.notna(y) and pd.notna(h)) else float("nan")
        rows.append({
            "biomass_type": b,
            "oil_yield_kg_per_kg": y,
            "bio_oil_hhv_mj_per_kg": h,
            "energy_per_kg_biomass": e,
            "yield_class": classify_yield(y),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Impact-category defaults
# ---------------------------------------------------------------------------
# Category strings in the LCA files look like "global warming potential (GWP100)".
# Default selection requested: GWP + agricultural land occupation + eutrophication
# (freshwater + marine).  Matched by the code in parentheses so it is robust.
DEFAULT_CATEGORY_CODES = ["(GWP100)", "(LOP)", "(FEP)", "(MEP)"]


def is_gwp(category: str) -> bool:
    """True for the global-warming category (the only one with an HFO benchmark)."""
    c = str(category).lower()
    return "gwp100" in c or "global warming" in c


def default_categories(available: list[str]) -> list[str]:
    """Pick the default categories present in *available* (preserves its order)."""
    return [c for c in available if any(code in str(c) for code in DEFAULT_CATEGORY_CODES)]


def gwp_by_feedstock(lca_df: pd.DataFrame, peak_df: pd.DataFrame) -> dict:
    """Map each completed LCA biomass type onto its ``feedstock_id`` in *peak_df*.

    Returns ``{feedstock_id: gwp_score}`` (kg CO₂-eq per MJ bio-oil). Matching uses
    the same partial, case-insensitive ``subcategory`` rule as the LCA notebook, so
    only the handful of feedstocks with a completed LCA get a value.
    """
    out: dict = {}
    if lca_df is None or lca_df.empty or peak_df is None or peak_df.empty:
        return out
    if "subcategory" not in peak_df.columns or "feedstock_id" not in peak_df.columns:
        return out
    gwp_rows = lca_df[lca_df["category"].map(is_gwp)]
    subcats = peak_df["subcategory"].astype(str)
    for _, r in gwp_rows.iterrows():
        name = str(r["biomass_type"])
        mask = subcats.str.contains(name, case=False, na=False, regex=False)
        for fid in peak_df.loc[mask, "feedstock_id"].unique():
            out[fid] = float(r["score"])
    return out


# ---------------------------------------------------------------------------
# Shipping & fossil-HFO assumptions  (editable on the page)
# ---------------------------------------------------------------------------
# NOTE: these are external reference values, NOT taken from the Brightway model.
# Ideally verify MJ_PER_TKM and the HFO benchmark against the ecoinvent
# "transport, freight, sea, container ship, heavy fuel oil" LCI.
MJ_PER_TKM_DEFAULT = 0.1236      # ship fuel energy per tonne-km  (~3 g HFO/tkm)
HFO_LHV_DEFAULT = 41.2           # heavy fuel oil lower heating value [MJ/kg]

# Approximate fossil-HFO climate benchmark, cradle-to-combustion [kg CO2-eq / MJ].
HFO_GWP_COMBUSTION = 0.0756      # direct combustion (3.114 kg CO2/kg / 41.2 MJ/kg)
HFO_GWP_UPSTREAM = 0.0094        # extraction + refining + delivery (literature)
HFO_GWP_DEFAULT = HFO_GWP_COMBUSTION + HFO_GWP_UPSTREAM  # ~0.085

# Scenario presets: (label, cargo tonnes, distance km).
SCENARIO_PRESETS = [
    ("China → Denmark", 100_000.0, 20_000.0),
]
DEFAULT_TONNES = 100_000.0          # total ship cargo (context)
DEFAULT_DK_TONNES = 30_000.0        # share actually bound for Denmark (drives the calc)
DEFAULT_DISTANCE_KM = 20_000.0

# Feedstock loaded for the energy/yield reach metric (tonnes of biomass).
DEFAULT_FEEDSTOCK_TONNES = 15_000.0

# Voyage-illustration endpoint labels (editable on the page).
DEFAULT_ORIGIN = "China"
DEFAULT_DESTINATION = "Denmark"
