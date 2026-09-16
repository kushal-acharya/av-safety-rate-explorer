"""Offline audit checks on committed source-derived tables."""

import pandas as pd

from av_safety.data import build, load_processed


def test_exposure_and_event_reconciliation():
    tables = load_processed()
    exposure, events, units = tables["exposure"], tables["events"], tables["units"]
    assert (exposure.miles >= 0).all()
    assert (units.reported_events >= 0).all()
    assert (exposure.event_difference == 0).all()
    assert exposure.query('manufacturer == "Waymo"').miles.between(100_000, 10_000_000).all()
    keys = ["year", "mode", "manufacturer"]
    matched = events.merge(exposure[keys + ["miles"]], on=keys, how="left")
    assert matched.miles.notna().all()
    assert (matched.miles > 0).all()
    valid = events[events.date_in_period]
    assert ((valid.date.dt.year == valid.year) | (valid.date.dt.year == valid.year - 1)).all()
    assert (~events.date_in_period).sum() == 13


def test_deterministic_rebuild_when_raw_available():
    from av_safety.data import ROOT

    if not (ROOT / "data/raw/2020/safety-driver-mileage.csv").exists():
        return  # Fresh clones intentionally exclude raw files.
    first, second = build(), build()
    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name])
