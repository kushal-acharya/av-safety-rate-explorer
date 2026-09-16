"""Ensure category normalization preserves records and uses the correct denominator."""

import pandas as pd
import pytest

from av_safety.analysis import context_summary
from av_safety.data import CONTEXT_CATEGORIES, KEYS, context_aggregates, load_processed


def test_context_conserves_all_reported_events():
    tables = load_processed()
    contexts = context_aggregates(tables["events"])
    for dimension, frame in contexts.items():
        assert set(frame.category) <= set(CONTEXT_CATEGORIES[dimension])
        totals = frame.groupby(KEYS)["count"].sum()
        expected = tables["events"].groupby(KEYS).size()
        pd.testing.assert_series_equal(totals, expected, check_names=False)
        assert int(frame["count"].sum()) == 22958


def test_ambiguous_labels_remain_unknown():
    rows = pd.DataFrame(
        {
            "year": [2024] * 3,
            "mode": ["driverless"] * 3,
            "manufacturer": ["Fixture"] * 3,
            "initiated_by": ["Yes", "Operator", "Test Driver, Av System"],
            "location": ["Urban", "Express Way", "Street"],
            "cause_category": ["Unknown"] * 3,
        }
    )
    result = context_aggregates(rows)
    assert result["initiated_by"].iloc[0]["category"] == "Unknown"
    assert result["initiated_by"].iloc[0]["count"] == 3
    assert result["location"].set_index("category").loc["Unknown", "count"] == 2
    assert rows.initiated_by.tolist() == ["Yes", "Operator", "Test Driver, Av System"]


def test_category_rates_use_all_miles_and_zero_categories_have_bounds():
    tables = load_processed()
    annual = tables["exposure"].query('manufacturer == "Waymo" and mode == "driverless"')
    result = context_summary(tables["events"], annual, "location", 0.95)
    assert result.events.sum() == 36
    assert (result.miles == annual.miles.sum()).all()
    assert result.rate.sum() == pytest.approx(36 / annual.miles.sum())
    assert result.share.sum() == pytest.approx(1)
    assert (result.loc[result.events == 0, "upper"] > 0).all()
