"""Streamlit companion to AV Evidence's Cloudflare-hosted public dashboard."""

from __future__ import annotations

import streamlit as st

from av_safety.data import load_processed
from av_safety.ui import compare_view, methods_view, planner_view, rates_view

st.set_page_config(page_title="AV Evidence", page_icon="◎", layout="wide")
st.title("AV Evidence — autonomy, in perspective")
st.caption("Independent research · California DMV · historical 2020–2024 snapshot")
st.info(
    "Disengagements are not crashes. Reporting practices and testing conditions differ; "
    "these data cannot rank companies by safety."
)
data = st.cache_data(load_processed)()
annual = data["exposure"]
with st.sidebar:
    years = st.multiselect(
        "Reporting years", sorted(annual.year.unique()), default=sorted(annual.year.unique())
    )
    names = st.multiselect("Manufacturers", sorted(annual.manufacturer.unique()), default=["Waymo"])
    mode = st.selectbox("Testing permit", ["safety-driver", "driverless"])
    scale = st.selectbox("Rate unit · per miles", [1000, 100000])
    confidence = st.selectbox(
        "Confidence level", [0.95, 0.9, 0.99], format_func=lambda x: f"{x:.0%}"
    )
    method = st.selectbox("Interval method", ["Auto", "Poisson exact", "Negative binomial"])
    st.caption("Data retrieved September 16, 2026 UTC. Driverless: 2023–2024 only.")
selected = annual[
    annual.year.isin(years)
    & annual.manufacturer.isin(names)
    & (annual["mode"] == mode)
    & annual.eligible
]
units = data["units"]
units = units[units.year.isin(years) & units.manufacturer.isin(names) & (units["mode"] == mode)]
tabs = st.tabs(["Rates", "Compare", "Experiment Planner", "Methods & Limitations"])
for tab, renderer in zip(tabs[:3], [rates_view, compare_view, planner_view], strict=True):
    with tab:
        if selected.empty:
            st.info("No exposure in this selection. Choose a manufacturer and reporting year.")
        elif renderer == rates_view:
            renderer(selected, units, method, confidence, scale)
        elif renderer == compare_view:
            renderer(selected, confidence, scale)
        else:
            renderer(selected, units)
with tabs[3]:
    methods_view()
