"""Marine Transport Impact — what does a container-ship voyage cost if it runs on
bio-oil instead of heavy fuel oil (HFO)?

Method (re-expressing a real ecoinvent container-ship process):
  1. Transport work       W   = cargo [t] × distance [km]                  [t·km]
  2. Fuel energy          E   = W × energy intensity [MJ/t·km]             [MJ]
  3. Impact of the voyage I   = E × bio-oil impact per MJ (real LCA score) [unit]

Bio-oil scores are the ReCiPe 2016 midpoint (H) results per 1 MJ of usable
bio-oil (functional unit), loaded live from the LCA_results folder.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import lca_meta as meta
from nav import inject
from service import load_lca_results, load_results

st.set_page_config(page_title="Marine Transport — Biomass Pyrolysis", layout="wide")
inject()


def _voyage_html(rows, origin: str, destination: str, distance: float,
                 basis_label: str, endpoint_label: str, hfo_co2: str = "") -> str:
    """Build the stylized journey-strip HTML (rendered via components.html).

    One lane per biomass: a route from *origin* to *destination*, with the traveled
    portion drawn solid (fading to transparent at the tip) and a ship marker at the
    reach point, the bio-oil's net CO₂ printed above the ship. ``rows`` =
    [{biomass, reach (fraction of route), yield_class, co2 (label), verdict, vcls}].

    A single finish line (the destination, at reach = 1.0) runs through all lanes; it
    is NOT pinned to the right edge, so biomass that beat it draw *past* the line (into
    a faint "beyond" zone) and biomass that fall short stop before it. ``hfo_co2`` is
    the traditional HFO ship's voyage CO₂, shown above the finish-line flag.
    """
    valid = [r["reach"] for r in rows if r["reach"] is not None and r["reach"] == r["reach"]]
    max_reach = max(valid) if valid else 1.0
    axis_max = max(1.08, min(max_reach * 1.08, 3.0))  # headroom past the furthest, capped
    flag_pos = min(1.0 / axis_max, 1.0) * 100.0

    if flag_pos >= 70:
        endpt_tx = "translateX(-100%)"
    elif flag_pos <= 14:
        endpt_tx = "translateX(0)"
    else:
        endpt_tx = "translateX(-50%)"

    css = (
        "<style>"
        "body{margin:0;font-family:'Segoe UI',Roboto,sans-serif;background:#eed9c4;color:#10283f;}"
        ".wrap{padding:4px 2px;}"
        ".hdr{display:flex;align-items:flex-end;font-size:12px;font-weight:700;color:#174C4F;margin:2px 0 4px;}"
        ".hdr .s1{width:175px;}.hdr .mid{flex:1;position:relative;height:40px;}"
        ".hdr .origin{position:absolute;left:0;bottom:0;}"
        ".hdr .endpt{position:absolute;bottom:0;white-space:nowrap;text-align:center;line-height:1.15;}"
        ".hdr .endpt .hfo{display:block;font-size:11px;color:#c0392b;}"
        ".hdr .s2{width:160px;text-align:right;color:#7a6a52;font-weight:600;align-self:flex-end;}"
        ".lanes{position:relative;z-index:0;}"
        ".finishline{position:absolute;left:175px;right:160px;top:0;bottom:0;pointer-events:none;z-index:2;}"
        ".finishline .vline{position:absolute;top:0;bottom:0;border-left:2px dashed #174C4F;transform:translateX(-50%);}"
        ".lane{display:flex;align-items:center;gap:10px;margin:7px 0;}"
        ".lbl{width:165px;}.lbl .name{font-size:13px;font-weight:600;line-height:1.1;}"
        ".lbl .chip{display:inline-block;margin-top:3px;font-size:10px;color:#fff;padding:1px 7px;border-radius:9px;}"
        ".track{position:relative;flex:1;height:48px;}"
        ".beyond{position:absolute;top:0;bottom:0;background:rgba(31,100,16,.08);border-radius:3px;}"
        ".base{position:absolute;top:64%;left:0;right:0;height:3px;transform:translateY(-50%);"
        "background:repeating-linear-gradient(90deg,#cbb89c 0 7px,transparent 7px 13px);}"
        ".fill{position:absolute;top:64%;left:0;height:7px;border-radius:4px;transform:translateY(-50%);}"
        ".ship{position:absolute;top:64%;transform:translate(-50%,-60%);font-size:18px;z-index:3;"
        "filter:drop-shadow(0 1px 1px rgba(0,0,0,.35));}"
        ".co2{position:absolute;top:3px;font-size:11px;font-weight:700;color:#10283f;white-space:nowrap;z-index:3;}"
        ".verdict{width:150px;font-size:12px;font-weight:700;text-align:right;}"
        ".verdict.good{color:#1f6410;}.verdict.bad{color:#c0392b;}.verdict.na{color:#999;}"
        "</style>"
    )
    hfo_line = f'<span class="hfo">🛢️ HFO ship: {hfo_co2}</span>' if hfo_co2 else ""
    header = (
        f'<div class="hdr"><div class="s1"></div>'
        f'<div class="mid"><span class="origin">🟢 {origin}</span>'
        f'<span class="endpt" style="left:{flag_pos:.1f}%;transform:{endpt_tx}">'
        f'{hfo_line}🏁 {endpoint_label}</span></div>'
        f'<div class="s2">{basis_label} · {distance:,.0f} km</div></div>'
    )
    lanes = []
    for r in rows:
        b, reach, yclass = r["biomass"], r["reach"], r["yield_class"]
        color = meta.YIELD_COLORS.get(yclass, "#999999")
        verdict = r.get("verdict", "")
        vcls = r.get("vcls", "na")
        co2 = r.get("co2", "")
        if reach is None or reach != reach:      # NaN
            disp = 0.0
        elif reach == float("inf"):              # carbon-neutral / -negative bio-oil
            disp = 100.0
        else:
            disp = min(max(reach, 0.0) / axis_max, 1.0) * 100.0
        # Keep the CO2 label from spilling off the track edges.
        if disp >= 85:
            co2_tx = "translateX(-100%)"
        elif disp <= 15:
            co2_tx = "translateX(0)"
        else:
            co2_tx = "translateX(-50%)"
        co2_html = f'<div class="co2" style="left:{disp:.1f}%;transform:{co2_tx}">{co2}</div>' if co2 else ""
        lanes.append(
            f'<div class="lane"><div class="lbl"><div class="name">{b}</div>'
            f'<div class="chip" style="background:{color}">{yclass} yield</div></div>'
            f'<div class="track">'
            f'<div class="beyond" style="left:{flag_pos:.1f}%;right:0;"></div>'
            f'<div class="base"></div>'
            f'<div class="fill" style="width:{disp:.1f}%;'
            f'background:linear-gradient(90deg,{color} 0%,{color} 82%,{color}00 100%);"></div>'
            f'{co2_html}'
            f'<div class="ship" style="left:{disp:.1f}%">🚢</div></div>'
            f'<div class="verdict {vcls}">{verdict}</div></div>'
        )
    finishline = f'<div class="finishline"><div class="vline" style="left:{flag_pos:.1f}%"></div></div>'
    lanes_block = f'<div class="lanes">{finishline}{"".join(lanes)}</div>'
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>" + css
        + "</head><body><div class='wrap'>" + header + lanes_block + "</div></body></html>"
    )


def _fmt_co2(kg: float) -> str:
    """Human-readable CO₂-eq mass (tonnes for large voyages, kg for tiny ones)."""
    if kg >= 1e6:
        return f"{kg / 1000:,.0f} t CO₂-eq"
    if kg >= 1e3:
        return f"{kg / 1000:,.1f} t CO₂-eq"
    return f"{kg:,.0f} kg CO₂-eq"


st.title("🚢 Example of Container Shipping Impact")
st.markdown(
    "Container ships normally burn **heavy fuel oil (HFO)**, a cheap but dirty fossil fuel. This page showcases scenarios and explores a greener alternative: running the **same ship on bio-oil** made from "
    "biomass (plant and crop waste).\n\n"

    "### **Voyage:** #" \
    "\n\n A container ship carrying 100,000 tonnes of goods travels 20,000 kilometers from China to Denmark to supply the danish consumers. A single ship serves many ports, though — so we count only the share actually bound for Denmark (about **30,000 tonnes** by default). You can change the ship's load, the Denmark-bound share, and the distance in the sidebar. "
    "\n\nThe picture below shows **how far each bio-oil could carry the cargo** compared with "
    "a normal fossil-fuelled ship. On the left you can see the biomass type eg. Olive kernels, just below is the *yield class.* \n\n (*The yield class is indicating whether the biomass type after converting to bio-oil can produce high, medium or low yields.*)"
    "\n\n Just a little to the right shows the origin port, then the dashed line 🏁 marks where the container ship, using heavy fuel oil, gets to the destination and thus has exhausted its carbon budget (it reaches Denmark exactly). " \
    "\n\n The solid portion of each lane shows how far the same ship would get if it ran on bio-oil made from that biomass type. Marking where its carbon budget is spent with a 🚢. " \
    "This means the biomass types that doesn't emit a lot of CO2 will sail **past** the dashed line. While the biomass types that emit a lot will stall short of it. This comparison not only shows if a biomass type has a high or low bio-oil yield but includes the potential CO2 impact from each bio-oil." \

)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
fast_mode = st.session_state.get("fast_mode", True)
result_dir = st.session_state.get("selected_result_dir", None)

try:
    with st.spinner("Loading LCA results …"):
        lca_df = load_lca_results()
        dfs = load_results(fast_mode, result_dir=result_dir)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"Error loading data: {exc}")
    st.stop()

if lca_df.empty:
    st.warning(
        "No LCA result files found. Expected one or more `lca_results_*.xlsx` files "
        "(sheet *All Categories*) in the project's `LCA_results` folder. Run "
        "`GREENFUEL_LCA_biomass.ipynb` for each biomass type to generate them."
    )
    st.stop()

results_df = dfs.get("results", pd.DataFrame())

# Bio-oil yield class + energy density per biomass (matches the LCA's own yield logic).
yields = meta.bio_oil_energy_table(sorted(lca_df["biomass_type"].unique()), results_df)

# ---------------------------------------------------------------------------
# Sidebar — scenario controls
# ---------------------------------------------------------------------------
st.sidebar.header("Voyage scenario")

st.session_state.setdefault("mt_tonnes", meta.DEFAULT_TONNES)
st.session_state.setdefault("mt_dk_tonnes", meta.DEFAULT_DK_TONNES)
st.session_state.setdefault("mt_distance", meta.DEFAULT_DISTANCE_KM)


def _apply_preset(tonnes: float, distance: float) -> None:
    st.session_state["mt_tonnes"] = float(tonnes)
    st.session_state["mt_distance"] = float(distance)


st.sidebar.caption("Quick presets")
preset_cols = st.sidebar.columns(len(meta.SCENARIO_PRESETS))
for col, (label, t, d) in zip(preset_cols, meta.SCENARIO_PRESETS):
    col.button(label, use_container_width=True, on_click=_apply_preset, args=(t, d))

total_cargo = st.sidebar.number_input(
    "Total ship cargo (tonnes)", min_value=1.0, step=1_000.0, format="%.0f", key="mt_tonnes",
    help="The whole ship's load — context only. A container ship serves many ports, so only a "
         "share of this is bound for Denmark.",
)
cargo_to_dk = st.sidebar.number_input(
    "Goods bound for Denmark (tonnes)", min_value=1.0, step=1_000.0, format="%.0f", key="mt_dk_tonnes",
    help="Only the share of the cargo actually delivered to Denmark. The voyage's impact is "
         "allocated to this amount (impact scales with tonne-kilometres).",
)
distance = st.sidebar.number_input(
    "Distance (km)", min_value=1.0, step=100.0, format="%.0f", key="mt_distance",
    help="Sea distance for the Denmark-bound leg (Shanghai → Denmark ≈ 20,000 km).",
)

with st.sidebar.expander("⚙️ Advanced assumptions"):
    st.caption(
        "Reference values from literature."
        "\n\n Only change if you have specific values for your scenario."
    )
    intensity = st.number_input(
        "Ship energy intensity (MJ per tonne-km)",
        min_value=0.0001, value=meta.MJ_PER_TKM_DEFAULT, step=0.01, format="%.4f",
    )
    hfo_lhv = st.number_input(
        "HFO lower heating value (MJ/kg)",
        min_value=1.0, value=meta.HFO_LHV_DEFAULT, step=0.1, format="%.1f",
    )
    hfo_gwp = st.number_input(
        "Fossil HFO climate benchmark (kg CO₂-eq / MJ)",
        min_value=0.0, value=meta.HFO_GWP_DEFAULT, step=0.005, format="%.4f",
        help="Cradle-to-combustion: combustion ≈ 0.0756 + upstream ≈ 0.0094.",
    )
    st.caption(f"⇒ ≈ {1000 * intensity / hfo_lhv:.2f} g HFO per tonne-km")

st.sidebar.markdown("---")
all_categories = sorted(lca_df["category"].unique())
selected_categories = st.sidebar.multiselect(
    "Impact categories",
    options=all_categories,
    default=meta.default_categories(all_categories),
    help="Chosen from recipe midpoint Default: climate change, land use and eutrophication. All 18 available.",
)

all_biomass = sorted(lca_df["biomass_type"].unique())
selected_biomass = st.sidebar.multiselect(
    "Biomass types", options=all_biomass, default=all_biomass,
)

per_tkm = st.sidebar.checkbox(
    "Show per tonne-km (intensity)", value=False,
    help="Divide voyage totals by the transport work to compare fuels independent of voyage size.",
)

st.sidebar.markdown("---")
st.sidebar.subheader("Voyage illustration")
reach_basis = st.sidebar.radio(
    "Reach basis",
    options=["Energy (yield)", "Carbon parity"],
    help=(
        "**Energy (yield)** — how far the bio-oil energy from a fixed mass of feedstock (yield × HHV) "
        "carries the cargo; the figure above each ship is that bio-oil's net CO₂. **Carbon parity** — "
        "how far each bio-oil travels on the same carbon budget as a fossil-HFO ship (reach = CI_HFO ÷ CI_bio)."
    ),
)
if reach_basis == "Energy (yield)":
    feedstock_tonnes = st.sidebar.number_input(
        "Feedstock loaded (tonnes)", min_value=1.0, value=meta.DEFAULT_FEEDSTOCK_TONNES,
        step=1_000.0, format="%.0f",
    )
else:
    feedstock_tonnes = meta.DEFAULT_FEEDSTOCK_TONNES
with st.sidebar.expander("Route labels"):
    origin = st.text_input("Origin", value=meta.DEFAULT_ORIGIN)
    destination = st.text_input("Destination", value=meta.DEFAULT_DESTINATION)

if not selected_categories:
    st.info("← Select at least one impact category in the sidebar.")
    st.stop()
if not selected_biomass:
    st.info("← Select at least one biomass type in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------
# Allocate the voyage to Denmark's share of the cargo: impact scales with
# tonne-kilometres, so only the Denmark-bound tonnes carry the burden.
tkm = cargo_to_dk * distance
mj_fuel = tkm * intensity
dk_share = cargo_to_dk / total_cargo if total_cargo > 0 else float("nan")
scale = intensity if per_tkm else mj_fuel  # multiplier applied to score [per MJ]
basis_note = "per tonne-km" if per_tkm else "for the Denmark-bound goods"

work = lca_df[lca_df["biomass_type"].isin(selected_biomass)].merge(
    yields[["biomass_type", "oil_yield_kg_per_kg", "yield_class"]],
    on="biomass_type", how="left",
)
work["value"] = work["score"] * scale

# ---------------------------------------------------------------------------
# Voyage illustration (hero) — can each bio-oil carry the cargo the whole way?
# ---------------------------------------------------------------------------
st.subheader(f"Can we use the bio-oil as fuel to reach {destination}?")

_gwp_scores = (
    lca_df[lca_df["category"].map(meta.is_gwp)].set_index("biomass_type")["score"].to_dict()
)
_energy = yields.set_index("biomass_type")["energy_per_kg_biomass"].to_dict()
_yclass = yields.set_index("biomass_type")["yield_class"].to_dict()

reach_rows = []
for b in selected_biomass:
    e = _energy.get(b)
    s = _gwp_scores.get(b)

    # Net CO2 of the bio-oil made from the fixed feedstock mass (same basis as the
    # energy reach): score [kg CO2-eq / MJ] x total bio-oil energy [MJ], in tonnes.
    # Negative = net carbon removed; positive = emitted.
    if e is not None and pd.notna(e) and s is not None and pd.notna(s):
        co2_t = s * (feedstock_tonnes * 1000.0 * e) / 1000.0
        co2_label = f"{co2_t:+,.0f} t CO₂"
    else:
        co2_label = ""

    if reach_basis == "Carbon parity":
        if s is None:
            frac = float("nan")        # genuinely no GWP score for this biomass
        elif s <= 0:
            frac = float("inf")        # carbon-neutral / -negative bio-oil never spends the budget
        else:
            frac = hfo_gwp / s
    else:
        frac = ((feedstock_tonnes * 1000.0 * e) / mj_fuel) if (e and mj_fuel > 0 and pd.notna(e)) else float("nan")

    # Verdict (basis-neutral: share of the route the ship reaches).
    if frac is None or frac != frac:
        verdict, vcls = "no data", "na"
    elif frac == float("inf"):
        verdict, vcls = "✓ carbon-negative", "good"
    elif frac >= 1.0:
        verdict, vcls = f"✓ {frac * 100:.0f}% of route", "good"
    else:
        verdict, vcls = f"✗ {frac * 100:.0f}% of route", "bad"

    reach_rows.append({
        "biomass": b, "reach": frac, "yield_class": _yclass.get(b, "Unknown"),
        "co2": co2_label, "verdict": verdict, "vcls": vcls,
    })

# Best reach first; NaN ("no data") last.
reach_rows.sort(key=lambda r: (r["reach"] != r["reach"], -(r["reach"] if r["reach"] == r["reach"] else 0.0)))

if reach_basis == "Carbon parity":
    _basis_label = "carbon-parity reach"
    _endpoint_label = f"{destination} · fossil-HFO limit"
else:
    _basis_label = "equal-feedstock reach"
    _endpoint_label = destination

# Traditional HFO container ship: CO2 to make the same Denmark voyage (the finish line).
_hfo_voyage_co2 = f"{hfo_gwp * mj_fuel / 1000.0:+,.0f} t CO₂"

components.html(
    _voyage_html(reach_rows, origin, destination, distance, _basis_label, _endpoint_label, _hfo_voyage_co2),
    height=90 + len(reach_rows) * 64 + 8,
)

if reach_basis == "Carbon parity":
    hfo_budget_kg = mj_fuel * hfo_gwp
    st.caption(
        f"Each ship is given the **same carbon footprint as a conventional fossil-HFO ship** for this "
        f"route — about **{_fmt_co2(hfo_budget_kg)}** ({mj_fuel:,.0f} MJ × {hfo_gwp:.3f} kg CO₂-eq/MJ). "
        f"The dashed 🏁 line marks where that fossil-HFO ship runs out (it reaches {destination} exactly). "
        "Reach = CI of HFO ÷ CI of the bio-oil, so cleaner fuels sail **past** it (into the green zone) "
        "and high-carbon fuels stall short. 🚢 marks where each bio-oil's carbon budget is spent. "
        "Bio-oils with a **net-negative** carbon footprint never spend the budget — they are flagged "
        "**carbon-negative** and sail the full track. The figure above each ship is that bio-oil's net "
        f"CO₂ from {feedstock_tonnes:,.0f} t of feedstock (negative = carbon removed)."
    )
else:
    st.caption(
        f"From **{feedstock_tonnes:,.0f} t of feedstock**, each biomass yields a different amount of "
        "bio-oil energy (oil yield × HHV); 🚢 marks how far that energy carries the cargo. The figure "
        "above each ship is that bio-oil's **net CO₂** — a **negative** value means the bio-oil is a net "
        "carbon **sink** (removes CO₂), versus fossil HFO which always **emits**. Higher-yield biomass "
        "reach further — adjust the feedstock loaded in the sidebar."
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------------------
with st.expander(" Advanced scenario analysis: voyage impacts across categories"):
    st.caption(
        "Calculate the impact of the voyage in each category: transport work × energy intensity × "
        "bio-oil impact per MJ (real LCA score). The bars below show the impact per category for each "
        "biomass type; compare against the fossil-HFO benchmark for climate change."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Transport work", f"{tkm:,.0f} t·km",
        help=f"Denmark-bound cargo ({cargo_to_dk:,.0f} t) × distance ({distance:,.0f} km).",
    )
    m2.metric(
        "Fuel energy", f"{mj_fuel:,.0f} MJ",
        help=f"= {mj_fuel / 1000:,.1f} GJ  =  {mj_fuel / 3600:,.1f} MWh",
    )

    gwp_cat = next((c for c in lca_df["category"].unique() if meta.is_gwp(c)), None)
    if gwp_cat is not None:
        gwp = work[work["category"] == gwp_cat].dropna(subset=["value"])
        if not gwp.empty:
            best = gwp.loc[gwp["value"].idxmin()]
            bench = hfo_gwp * scale
            delta = 100.0 * (best["value"] - bench) / bench if bench else float("nan")
            m3.metric(
                f"Best bio-oil GWP ({best['biomass_type']})",
                f"{best['value']:,.0f} kg CO₂-eq",
                delta=f"{delta:+.0f}% vs fossil HFO",
                delta_color="inverse",
                help=f"Fossil HFO benchmark {basis_note}: {bench:,.0f} kg CO₂-eq.",
            )

    st.caption(
        f"Scenario: **{cargo_to_dk:,.0f} t bound for Denmark** "
        f"({dk_share:.0%} of a {total_cargo:,.0f} t ship) over **{distance:,.0f} km**  ·  "
        f"values shown **{basis_note}**  ·  "
        f"{len(selected_biomass)} biomass type(s), {len(selected_categories)} category(ies)."
    )

    # ---------------------------------------------------------------------------
    # Per-category charts (coloured by bio-oil yield class)
    # ---------------------------------------------------------------------------
    def _bar(cat: str) -> go.Figure:
        sub = work[work["category"] == cat].dropna(subset=["value"]).sort_values("value")
        if sub.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        unit = str(sub["unit"].iloc[0])
        x_unit = f"{unit} / t·km" if per_tkm else unit
        fig = px.bar(
            sub, x="value", y="biomass_type", orientation="h",
            color="yield_class", color_discrete_map=meta.YIELD_COLORS,
            category_orders={"yield_class": meta.YIELD_ORDER},
            labels={"value": x_unit, "biomass_type": "Biomass", "yield_class": "Bio-oil yield"},
            template="plotly_white",
            custom_data=["yield_class", "oil_yield_kg_per_kg"],
        )
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>%{x:.4g} " + x_unit
            + "<br>Yield: %{customdata[0]} (%{customdata[1]:.0%})<extra></extra>"
        )
        # Fossil HFO reference line — meaningful for climate only.
        if meta.is_gwp(cat):
            bench = hfo_gwp * scale
            fig.add_vline(
                x=bench, line_dash="dash", line_color="#10283f",
                annotation_text="Fossil HFO", annotation_position="top",
            )
        fig.update_layout(
            title=cat,
            showlegend=True, legend_title_text="Bio-oil yield",
            margin=dict(l=10, r=10, t=45, b=10),
            height=max(260, len(sub) * 34 + 90),
        )
        return fig


    cols = st.columns(2)
    for i, cat in enumerate(selected_categories):
        with cols[i % 2]:
            st.plotly_chart(_bar(cat), use_container_width=True)

    if any(meta.is_gwp(c) for c in selected_categories):
        st.caption(
            "The dashed line is an **approximate fossil-HFO benchmark** (combustion + upstream); "
            "it is shown for climate change only. Bio-oil's combustion CO₂ is biogenic (≈ neutral), "
            "so the bars are the *production* impact of the bio-oil."
        )
    
# ---------------------------------------------------------------------------
# Data table
# ---------------------------------------------------------------------------
with st.expander("📋 Data table"):
    tbl = work[["biomass_type", "yield_class", "oil_yield_kg_per_kg", "category", "unit", "score", "value"]].copy()
    tbl["oil_yield_kg_per_kg"] = (tbl["oil_yield_kg_per_kg"] * 100).round(1)
    tbl = tbl.rename(columns={
        "biomass_type": "Biomass",
        "yield_class": "Yield class",
        "oil_yield_kg_per_kg": "Oil yield (%)",
        "category": "Impact category",
        "unit": "Unit (per MJ)",
        "score": "Impact per MJ",
        "value": f"Impact {basis_note}",
    })
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------------
with st.expander("❓ Method, data & assumptions"):
    st.markdown(
        f"""
        **Calculation**

        1. Transport work `W = Denmark-bound cargo × distance = {cargo_to_dk:,.0f} t × {distance:,.0f} km = {tkm:,.0f} t·km`
        2. Fuel energy `E = W × {intensity:.4f} MJ/t·km = {mj_fuel:,.0f} MJ`
        3. Voyage impact `I = E × (bio-oil impact per MJ)` — one value per impact category

        **Allocation** — a container ship serves many ports, so we count only the share of the
        cargo bound for Denmark ({cargo_to_dk:,.0f} t = {dk_share:.0%} of the {total_cargo:,.0f} t ship).
        Because impact scales with tonne-kilometres, this is a clean mass-based allocation — the
        Danish goods carry exactly their share of the voyage, with no double-counting.

        **Data**
        - Bio-oil impacts are real **ReCiPe 2016 v1.03 midpoint (H)** results, functional unit
          = **1 MJ of usable bio-oil**.
        - **Bio-oil yield class** uses the same yield the LCA assumed (highest-oil-yield match of
          the biomass name against the yield `results` sheet): High ≥ {meta.YIELD_HIGH_MIN:.0%},
          Low < {meta.YIELD_LOW_MAX:.0%}.

        **Assumptions & caveats**
        - Energy intensity ({intensity:.4f} MJ/t·km) and the HFO benchmark are **external reference
          values**, editable in the sidebar — verify against the ecoinvent container-ship LCI.
        - The comparison assumes **equal energy delivery** per MJ; bio-oil's lower energy density /
          combustion efficiency is **not** modelled (you would need somewhat more bio-oil in practice).
        - **Bio-oil combustion CO₂ is biogenic (≈ neutral)** while **fossil HFO combustion CO₂ counts** —
          that is why low-yield biomass (e.g. *Walnut shell 1*) can exceed the fossil HFO benchmark on
          climate, while high-yield biomass (e.g. *Olive kernels*, *Poplar 4*) falls well below it.
        - The fossil-HFO benchmark is approximate and shown for **climate change only**. A proper
          per-tonne-km fossil benchmark for the other categories would come from running the ecoinvent
          container-ship process through ReCiPe in Brightway.
        """
    )
