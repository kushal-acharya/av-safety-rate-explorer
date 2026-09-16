"""Shared aggregation and model-selection logic for the Streamlit companion."""

from __future__ import annotations

import pandas as pd

from av_safety.stats import Rate, dispersion_test, nb_rate_ci, poisson_rate_ci


def summarize(
    annual: pd.DataFrame, units: pd.DataFrame, method: str, confidence: float
) -> pd.DataFrame:
    """Return a rate table by year for one manufacturer, otherwise by manufacturer."""
    by = "year" if annual.manufacturer.nunique() == 1 else "manufacturer"
    records = []
    for key, group in annual.groupby(by):
        miles, events = float(group.miles.sum()), int(group.events.sum())
        if miles <= 0:
            continue
        unit = units[units[by] == key]
        positive = unit[unit.miles > 0]
        diag = dispersion_test(positive.reported_events, positive.miles)
        result = poisson_rate_ci(events, miles, 1 - confidence)
        use_nb = method == "Negative binomial" or (method == "Auto" and diag["overdispersed"])
        invalid = ((unit.miles == 0) & (unit.reported_events > 0)).any()
        if use_nb and invalid:
            result = Rate(
                result.rate,
                result.lower,
                result.upper,
                warning="Zero-mile unit has events; NB disabled.",
            )
        elif use_nb and events:
            result = nb_rate_ci(positive.reported_events, positive.miles, 1 - confidence)
        records.append(
            {
                "group": str(key),
                "events": events,
                "miles": miles,
                **result.to_dict(),
                "phi": diag["phi"],
            }
        )
    return pd.DataFrame(records)


def context_summary(
    events: pd.DataFrame, annual: pd.DataFrame, dimension: str, confidence: float
) -> pd.DataFrame:
    """Use the full selected exposure for each category's exact Poisson interval."""
    from av_safety.data import CONTEXT_CATEGORIES, KEYS, context_aggregates

    if dimension not in CONTEXT_CATEGORIES:
        raise ValueError("Unknown event context dimension")
    selected = events.merge(annual[KEYS], on=KEYS, how="inner", validate="many_to_one")
    if len(selected) != int(annual.events.sum()):
        raise ValueError("Context counts do not reconcile with annual event totals")
    miles = float(annual.miles.sum())
    counts = context_aggregates(selected)[dimension].groupby("category")["count"].sum()
    records = []
    for category in CONTEXT_CATEGORIES[dimension]:
        count = int(counts.get(category, 0))
        records.append(
            {
                "category": category,
                "events": count,
                "miles": miles,
                "share": count / len(selected) if len(selected) else None,
                **poisson_rate_ci(count, miles, 1 - confidence).to_dict(),
            }
        )
    return pd.DataFrame(records)
