"""Small Streamlit view functions; statistical computation stays in pure modules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from av_safety.analysis import summarize
from av_safety.plots import power_figure, rates_figure
from av_safety.stats import miles_needed, poisson_rate_ci, power_curve, rate_ratio_ci, rule_of_three
from av_safety.text import METHODS

cached_summary = st.cache_data(summarize)


def rates_view(
    annual: pd.DataFrame, units: pd.DataFrame, method: str, confidence: float, scale: int
) -> None:
    """Render estimates, intervals, downloadable evidence and zero-event bounds."""
    table = cached_summary(annual, units, method, confidence)
    miles, events = float(annual.miles.sum()), int(annual.events.sum())
    p = poisson_rate_ci(events, miles, 1 - confidence)
    columns = st.columns(3)
    columns[0].metric("Exposure · miles", f"{miles:,.1f}")
    columns[1].metric("Reported disengagements · events", f"{events:,}")
    rate = f"{p.rate * scale:.4g}" if events else f"< {p.upper * scale:.4g}"
    columns[2].metric(f"Observed pooled rate / {scale:,} miles", rate)
    st.caption(
        f"Observed pooled {confidence:.0%} exact CI: "
        f"[{p.lower * scale:.4g}, {p.upper * scale:.4g}] per {scale:,} miles."
    )
    st.plotly_chart(rates_figure(table, scale, confidence), width="stretch")
    st.caption(
        "Orange dots mark zero-event upper bounds. NB fitted rates may differ from "
        "observed pooled rates. Every estimate uses miles as its denominator."
    )
    for warning in table.warning.unique():
        if warning:
            st.warning(warning)
    display = table[["group", "events", "miles", "rate", "lower", "upper", "method"]].copy()
    for col in ["rate", "lower", "upper"]:
        display[col] *= scale
    display.loc[display.events == 0, "rate"] = np.nan
    st.dataframe(display, width="stretch", hide_index=True)
    st.caption(
        f"Rate/lower/upper are per {scale:,} miles at {confidence:.0%} confidence. "
        "A blank zero-event rate means upper-bound-only reporting."
    )
    st.download_button("Download rates CSV", display.to_csv(index=False), "rates.csv", "text/csv")
    with st.expander("Zero events are not zero risk"):
        m = st.number_input(
            "Hypothetical zero-event exposure · miles", min_value=1.0, value=100000.0
        )
        st.write(
            f"{confidence:.0%} one-sided upper bound: "
            f"{rule_of_three(m, confidence) * scale:.4g} per {scale:,} miles."
        )
        st.caption("At 95%, the one-sided coefficient is 2.996; two-sided is 3.689.")


def compare_view(annual: pd.DataFrame, confidence: float, scale: int) -> None:
    """Compare two disjoint reporting groups using the Poisson reference model."""
    if len(annual) < 2:
        st.info("Select at least two reporting groups to compare.")
        return
    rows = annual.copy().reset_index(drop=True)
    labels = (rows.manufacturer + " · " + rows.year.astype(str)).tolist()
    a = st.selectbox("Group A · reference", range(len(rows)), format_func=lambda i: labels[i])
    choices = [i for i in range(len(rows)) if i != a]
    b = st.selectbox("Group B · comparison", choices, format_func=lambda i: labels[i])
    left, right = rows.iloc[a], rows.iloc[b]
    for column, row in zip(st.columns(2), [left, right], strict=True):
        ci = poisson_rate_ci(int(row.events), float(row.miles), 1 - confidence)
        column.write(
            f"**{row.manufacturer} · {row.year}**: {row.events:,} events / {row.miles:,.1f} miles"
        )
        column.write(
            f"{confidence:.0%} exact interval: [{ci.lower * scale:.4g}, "
            f"{ci.upper * scale:.4g}] per {scale:,} miles"
        )
    result = rate_ratio_ci(
        int(left.events), float(left.miles), int(right.events), float(right.miles), 1 - confidence
    )
    st.write("Rate ratio B/A", result)
    st.caption(
        f"{confidence:.0%} comparison interval. Group rates are always Poisson here. "
        "Overdispersion can make this inference too optimistic; no multiplicity adjustment."
    )
    st.warning("Different testing conditions and reporting practices prevent causal safety claims.")


def planner_view(annual: pd.DataFrame, units: pd.DataFrame) -> None:
    """Render editable planning assumptions, event counts, exposure and power."""
    baseline = float(annual.events.sum() / annual.miles.sum() * 1000)
    if baseline == 0:
        st.info("Zero observed events do not supply a positive planning rate. Enter an assumption.")
        baseline = 0.1
    rate = (
        st.number_input(
            "Baseline events per 1,000 miles", min_value=0.000001, value=baseline, format="%.6f"
        )
        / 1000
    )
    reduction = st.slider("Target relative reduction (%)", 1, 80, 10) / 100
    alpha = st.selectbox("Significance level α", [0.05, 0.01, 0.1])
    power = st.selectbox("Power", [0.8, 0.9, 0.95])
    phi = st.number_input("Quasi-Poisson design effect φ (not NB2 α)", min_value=1.0, value=1.0)
    allocation = st.slider("Fraction of total miles in A", 0.1, 0.9, 0.5)
    two_sided = st.checkbox("Two-sided test", value=True)
    result = miles_needed(rate, reduction, alpha, power, phi, allocation, two_sided)
    for col, side in zip(st.columns(2), ["a", "b"], strict=True):
        col.metric(f"Arm {side.upper()} exposure · miles", f"{result[f'miles_{side}']:,.0f}")
        col.metric(f"Arm {side.upper()} expected events", f"{result[f'events_{side}']:,.1f}")
    st.metric("Total exposure · miles", f"{result['total_miles']:,.0f}")
    grid = np.linspace(0, result["total_miles"] * 2, 100)
    curve = power_curve(rate, reduction, grid, alpha, phi, allocation, two_sided)
    st.plotly_chart(
        power_figure(pd.DataFrame({"miles": grid, "power": curve}), power), width="stretch"
    )
    st.caption(
        "Normal approximation with alternative variance and a constant design effect. "
        "Assumes independent arms, stable rates and a fixed, prespecified analysis."
    )


def methods_view() -> None:
    """Display source, assumptions, conventions and limitations."""
    st.markdown(METHODS)
