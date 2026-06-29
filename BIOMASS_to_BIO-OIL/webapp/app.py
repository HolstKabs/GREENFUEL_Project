"""Biomass Pyrolysis Explorer — Streamlit entry point.

Run with:
    streamlit run webapp/app.py
"""

import streamlit as st
st.set_page_config(
    page_title="Home — Biomass Pyrolysis",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys as _sys
from pathlib import Path as _Path
_webapp_dir = _Path(__file__).resolve().parent
if str(_webapp_dir) not in _sys.path:
    _sys.path.insert(0, str(_webapp_dir))

from nav import inject  # webapp/ is on sys.path
inject()

# ---------------------------------------------------------------------------
# Landing page content
# ---------------------------------------------------------------------------
st.title("Biomass Pyrolysis Explorer")

col_intro, col_image = st.columns(2)

with col_intro:
   st.markdown(
    """

    Different types of biomass has been categorized into for example; agricultural residues, wood chips, algae, sewage sludge, and many more. \n
    Each of these feedstocks can produce very different amounts of bio-oil when heated. 
    This website presents to you results from multiple tools that have calculated the theoretical maximum bio-oil yield for a wide range of feedstocks, and the environmental impact of producing that oil.
    
    This helps you understand **which feedstocks are worth pursuing**, how much oil they can yield, and what the
    environmental cost of producing that oil actually is.

    Behind the scenes, a thermodynamic model calculates the theoretical maximum bio-oil,
    gas, and char output for each feedstock across a range of temperatures and pressures.
    
    Those results are then fed into a full **life cycle assessment (LCA)** so you can see
    not just the bio-oil yield, but also the different impact categories calculated with LCIA methods.
    
    Finally, the model can also calculate the effect of **marine transport** on the overall carbon footprint of producing bio-oil from a given feedstock,
    including the effect of shipping biomass across the world.

    **Where to start:**
    - **Biomass Xplorer** — browse all feedstocks, filter by category or yield, and spot the best candidates
    - **Comparing-X/Y's** — pick different feedstocks and compare them side-by-side on yield or many other metrics
    - **Environmental ImpactsX** — explore the LCA results, with Monte Carlo uncertainty ranges, to see how the feedstocks compare on environmental impact
    - **Transportation of GoodsX:** see how far, long-distance container shipping, can travel and how it changes, when the feedstock types changes.
    """
)

with col_image:
    _, img_col, _ = st.columns([1, 8, 1])
    with img_col:
        st.image(str(_webapp_dir / "Images" / "MissionGreenFuels.jpg"), caption="Mission Green Fuels Roadmap frontpage, from: https://missiongreenfuels.dk/roadmap-for-green-fuels/", use_container_width=True)

with st.expander("How does the model work? (click to expand)"):
    st.image(str(_webapp_dir / "Images" / "biomass_pyrolysis_chart.png"), caption="Pyrolysis process flow diagram (created with AI)", width=900)
    st.markdown(
        """
        With biomass ultimate and proximate analysis inserted into a thermodynamic model,
        the **theoretical maximum bio-oil yield** can be calculated for each feedstock across a range of temperatures and pressures.  The model
        uses the Gibbs free energy minimisation method to find the equilibrium product distribution.
        
        **Equilibrium modelling** finds the product distribution that minimises the total
        Gibbs free energy of the system at a given temperature and pressure.  It is a
        *theoretical upper bound* — real reactors are kinetically limited and will differ.

        Key outputs per feedstock:
        | Symbol | Meaning |
        |--------|---------|
        | Oil yield | kg of bio-oil per kg of feedstock fed |
        | Gas yield | kg of permanent gases (CO, CO₂, CH₄, H₂ …) per kg fed |
        | Char yield | kg of solid char per kg of feedstock fed |

        Yields are reported on three bases:
        - **As-received (AR)** — includes all moisture and ash
        - **Dry** — moisture excluded
        - **DAF** (dry-ash-free) — moisture and ash both excluded; best for comparing
          different feedstocks on a like-for-like basis
        """
    )
    


    
st.divider()
footer_logo, footer_text = st.columns([1, 6])
with footer_logo:
    st.image(str(_webapp_dir / "Images" / "DTU_Logo_Corporate_Red_RGB.png"), width=120)
with footer_text:
    st.caption(
        "Source code and LCA models are maintained internally at DTU. "
        "For access or collaboration enquiries, contact the development team.")  
    