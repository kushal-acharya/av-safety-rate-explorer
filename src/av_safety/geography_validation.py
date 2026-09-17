"""Semantic checks for the frozen geographic inputs, independent of file hashes."""

from __future__ import annotations

import math

import pandas as pd
from pandas.api.types import is_numeric_dtype

SCHEMAS = {
    "cells": {"city", "cell_id", "metric", "benchmark_count", "human_miles", "waymo_miles"},
    "inputs": {
        "city",
        "metric",
        "waymo_miles",
        "baseline_ipmm",
        "published_matched_ipmm",
        "published_events",
    },
    "events": {"source_row", "report_id", "year_month", "city", "in_transport", "injury", "airbag"},
}


def _numeric(
    frame: pd.DataFrame, column: str, *, positive: bool = False, integer: bool = False
) -> None:
    if not is_numeric_dtype(frame[column]):
        raise ValueError(f"{column} must be numeric, finite and nonnegative")
    values = pd.to_numeric(frame[column], errors="coerce")
    if not values.map(math.isfinite).all() or (values < 0).any():
        raise ValueError(f"{column} must be finite and nonnegative")
    if positive and (values <= 0).any():
        raise ValueError(f"{column} must be positive")
    if integer and (values % 1 != 0).any():
        raise ValueError(f"{column} must contain integer values")


def validate_geography(
    cells: pd.DataFrame,
    inputs: pd.DataFrame,
    events: pd.DataFrame,
    cities: set[str],
    metrics: set[str],
) -> None:
    """Reject invalid cohorts before inference; retain documented source ID ambiguities.

    Blank report IDs and repeated report IDs are permitted because the frozen source
    contains both. Source CSV row numbers, not report IDs, identify event rows. This
    validates structure and membership, not independent adjudication of collisions.
    """
    for name, frame in [("cells", cells), ("inputs", inputs), ("events", events)]:
        if set(frame.columns) != SCHEMAS[name] or frame.empty:
            raise ValueError(f"Unexpected {name} schema or empty table")
    for column in ["benchmark_count", "human_miles", "waymo_miles"]:
        _numeric(cells, column, positive=column == "human_miles")
    for column in ["waymo_miles", "baseline_ipmm", "published_matched_ipmm", "published_events"]:
        _numeric(
            inputs,
            column,
            positive=column != "published_events",
            integer=column == "published_events",
        )
    if not cells.cell_id.str.fullmatch(r"[1-9][0-9]{18}", na=False).all():
        raise ValueError("cell_id must preserve the 19-digit source identifier")
    if cells.duplicated(["city", "metric", "cell_id"]).any():
        raise ValueError("duplicate city/metric/cell")
    if set(cells.city) != cities or set(cells.metric) != metrics:
        raise ValueError("unexpected geographic or outcome scope")
    expected = {(city, metric) for city in cities for metric in metrics}
    if set(zip(inputs.city, inputs.metric, strict=True)) != expected or len(inputs) != len(
        expected
    ):
        raise ValueError("expected exactly nine city/metric inputs")
    for _, group in cells.groupby(["city", "cell_id"]):
        if set(group.metric) != metrics:
            raise ValueError("each geographic cell must have every selected outcome")
        if group.human_miles.nunique() != 1 or group.waymo_miles.nunique() != 1:
            raise ValueError("mileage must agree across outcomes within a cell")
    for _, group in inputs.groupby("city"):
        if group.waymo_miles.nunique() != 1:
            raise ValueError("city mileage must agree across outcome inputs")
        if group.loc[group.metric != "airbag", "published_events"].nunique() != 1:
            raise ValueError("injury reference variants must use the same Waymo event count")
    for column in ["source_row", "year_month", "in_transport", "injury", "airbag"]:
        _numeric(events, column, integer=True)
    if events.source_row.duplicated().any() or (events.source_row < 2).any():
        raise ValueError("source_row must be unique CSV row numbers starting at 2")
    if len(events) != 523 or set(events.source_row) != set(range(2, 525)):
        raise ValueError("source_row must preserve every consecutive source CSV row (523 expected)")
    if set(events.city) != cities | {"AUSTIN"}:
        raise ValueError("unexpected event city scope")
    if not events.report_id.str.fullmatch(r"(?:[0-9]+-[0-9]+)?", na=False).all():
        raise ValueError("malformed report_id; blank source identifiers are allowed")
    months = events.year_month % 100
    if not (events.year_month.between(202009, 202412) & months.between(1, 12)).all():
        raise ValueError("event date outside the frozen window or invalid calendar month")
    for column in ["in_transport", "injury", "airbag"]:
        if not events[column].isin([0, 1]).all():
            raise ValueError(f"{column} membership must be 0 or 1")
    selected = (events.injury == 1) | (events.airbag == 1)
    if (events.loc[selected, "in_transport"] != 1).any():
        raise ValueError("selected outcome outside in-transport source cohort")
