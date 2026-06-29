"""Shared sidebar navigation — call inject() on every page."""

import streamlit as st


def inject() -> None:
    """Hide the auto-generated Streamlit nav and render custom page links."""
    st.markdown(
        """<style>
        [data-testid='stSidebarNav'] {display: none;}
        [data-testid='stSidebar'] > div:first-child {padding-top: 0rem;}
        </style>""",
        unsafe_allow_html=True,
    )

    st.markdown(
    """<style>
    [data-testid="stAlert"] {
        background-color: #10283f !important;
        border-color: #1f6410 !important; 
        border-radius: 20px !important;
    }
    [data-testid="stAlert"] * {
        color: #ffffff !important;
    }
 
    </style>""",
    unsafe_allow_html=True,
)

    st.sidebar.page_link("app.py", label="Home", icon="🏠")
    st.sidebar.page_link("pages/1_Explorer.py", label="Biomass Xplorer", icon="🔍")
    st.sidebar.page_link("pages/2_Comparison.py", label="Comparing-X/Y's", icon="📊")
    st.sidebar.page_link("pages/3_Environmental.py", label="Environmental ImpactsX", icon="🌱")
    st.sidebar.page_link("pages/4_Marine_Transport.py", label="Transportation of GoodsX", icon="🚢")
    st.sidebar.page_link("pages/5_About.py", label="About", icon="ℹ️")
    st.sidebar.markdown("---")


