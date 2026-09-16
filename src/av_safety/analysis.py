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
