"""About page — purpose, authorship, and funding."""

import sys

import streamlit as st
from pathlib import Path as _Path
_webapp_dir = _Path(__file__).resolve().parent
if str(_webapp_dir) not in sys.path:
    sys.path.insert(0, str(_webapp_dir))
from nav import inject

st.set_page_config(page_title="About — Biomass Pyrolysis", layout="wide")
inject()

st.title("About this App")
st.markdown(
    "This web application is an interactive tool for exploring the results of a "
    "**biomass-to-bio-oil** study. It lets researchers, "
    "engineers, and policy-makers browse pyrolysis yields, compare feedstocks, inspect "
    "potential impacts of different environmental impact categories, and evaluate the effect of marine transport on "
    "the overall carbon footprint — all within a single, browser-based interface.\n\n"
    "The underlying LCA model was built with [Brightway2.5](https://brightway.dev/) and "
    "uses the **ReCiPe 2016 midpoint (H)** characterisation method. Monte Carlo "
    "uncertainty analysis is included to quantify how "
    "input-data variability propagates to the final impact scores."
)
st.divider()
col_developers, col_researchers = st.columns(2)

with col_developers:
    st.subheader("Development Team")
    st.markdown(
        "- **Dr. Ali Akbar Eftekhari** — DTU Quantitative Sustainability Assessment (QSA),"
        "Project lead, supervisor and researcher \n"
        "- **Kasper Holst** — DTU Quantitative Sustainability Assessment (QSA), \n"
        "Researcher, biomass-to-bio-oil calculator developer, webpage developer and LCA model developer\n" 
        "- **Dr. Olivier Jolliet** — DTU Quantitative Sustainability Assessment (QSA), "
        "Line manager."
    )

with col_researchers:
    st.subheader("Research Team")
    st.markdown(
        "- **Dr. Ali Akbar Eftekhari** — DTU Quantitative Sustainability Assessment (QSA),"
        "Project lead, supervisor and researcher \n"
        "- **Kasper Holst** — DTU Quantitative Sustainability Assessment (QSA), \n"
        "Researcher, biomass-to-bio-oil calculator developer, webpage developer and LCA model developer\n" 
        "- **Dr. Georgios Manthos** — DTU Quantitative Sustainability Assessment (QSA), "
        "Researcher and external supervisor."
    )
st.divider()

col_dev, col_fund = st.columns(2)

with col_dev:
    st.subheader("Development")
    st.markdown(
        "Developed at the **Technical University of Denmark (DTU)** as part of ongoing "
        "research into sustainable fuel pathways from lignocellulosic and waste biomass.\n\n"
        "**Contact:** holst@dtu.dk"
    )

with col_fund:
    st.subheader("Funding")
    st.markdown(
        "This work was carried out under the **GreenFuel project**, which investigates "
        "the production of advanced biofuels from domestic and imported biomass residues. "
        "The project is supported by funding from the Danish Energy Agency and related "
        "national and European research programmes."
    )
    


st.divider()
footer_logo, footer_text = st.columns([1, 6])
with footer_logo:
    st.image(str(_webapp_dir.parent / "Images" / "DTU_Logo_Corporate_Red_RGB.png"), width=120)
with footer_text:
    st.caption(
        "Source code and LCA models are maintained internally at DTU. "
        "For access or collaboration enquiries, contact the development team.")